# Layout Calculations

This document explains how each layout currently computes node positions and connector geometry.

## Layout architecture

The `layout/` package is organized around a small geometry pipeline:

1. `layout/registry.py` selects the engine for the requested layout kind.
2. `layout/shared.py` handles common measurement, wrapping, depth-aware sizing, and scene-bound helpers.
3. A concrete engine (`tree_layout.py`, `synoptic_layout.py`, `synoptic_boxes_layout.py`, or `radial_layout.py`) computes positions and edge geometry.
4. The engine returns a generic `LayoutScene` made of `LayoutBox` and `LayoutEdge`.

This keeps a strict split:

- `shared.py` owns common measurement rules
- each engine owns only its own placement strategy
- render code receives a layout-agnostic scene and does not know which engine produced it

## Shared concepts used by all layouts

All layout engines start from `measure_nodes(...)` in `layout/shared.py`.

That shared step does the following:

1. Compute node depth from the parsed tree.
2. Choose a base width from depth-based layout rules.
3. Expand width when needed so a single word never overflows.
4. Wrap title and body text.
5. Build an initial `LayoutBox` with width, height, and text lines.

The shared helpers also define:

- `get_h_gap_for_depth(...)`
- `get_v_gap_for_depth(...)`
- `build_scene(...)`
- scene bounds collection

From there, each layout uses its own geometry strategy.

## Page-size awareness

All layouts now receive page dimensions through `LayoutConfig.page_width` and `LayoutConfig.page_height`.

Current page presets available from the CLI are:

- `a4`: portrait A4
- `a4_landscape`: landscape A4
- `square`: square page

Current impact on layout engines:

- `tree` uses page aspect ratio both during candidate selection and final viewport fitting
- `radial` uses page size for center placement and final fitting
- `synoptic` and `synoptic_boxes` render correctly on the chosen page size, but they do not yet run a dedicated optimization pass for portrait or square aspect ratios

## Tree layout

File: `layout/tree_layout.py`

### Goal

Create a top-down hierarchy where parents sit above their descendants, while still adapting the visible box width to content and available paper space.

### Current calculation flow

1. Measure all nodes with `measure_nodes(...)`.
2. Try several compactness profiles by scaling:
   - base node width
   - horizontal gap
   - vertical gap
3. For each profile, recursively compute subtree widths.
4. Choose the profile whose resulting scene best fits the page.

### How subtree width is computed

For leaf nodes:

- `subtree_width = box.width`

For internal nodes:

1. Recursively compute every child subtree width.
2. Sum child subtree widths and horizontal gaps.
3. Compute a visible parent width from text and child band:
   - minimum: enough width to avoid breaking words
   - preferred: width required by the current text content
   - maximum: based on children width
     - `100%` of combined child width if there is only one child
     - `90%` if there are multiple children
4. Re-measure the parent text using that final visible width.
5. Set:
   - `box.width = visible parent width`
   - `box.subtree_width = max(box.width, total_children_width)`

Important detail:

- the visible parent box can be narrower than the subtree band
- the subtree band remains the real placement width used to center the parent above the children

### How positions are assigned

Placement is recursive:

- roots are placed from left to right
- each node is centered inside its subtree band
- children are placed in one row below the parent
- child row width is centered inside the parent subtree band

So the visible parent width and the subtree band are separate concepts.

### Edge geometry

Tree connectors are orthogonal polylines:

- vertical down from parent
- horizontal segment at mid-gap
- vertical down to child

Relation labels are drawn around the horizontal segment.

### Page fitting behavior

After scene construction:

- `tree` can scale down or up
- `tree` chooses among several geometry candidates using the available page proportions
- leftover free space is centered by the viewport

That means the tree engine first optimizes scene proportions, then the viewport performs final page fitting.

## Synoptic boxes layout

File: `layout/synoptic_boxes_layout.py`

### Goal

Create a left-to-right synoptic chart with boxed nodes, where branch height determines vertical allocation.

### Current calculation flow

1. Measure all nodes.
2. Recursively compute subtree height per node.
3. Place nodes by columns.
4. Draw orthogonal connectors with optional labels.

### How subtree height is computed

For leaf nodes:

- subtree height is the node's own height

For internal nodes:

1. Compute subtree height of each child.
2. Sum child subtree heights plus vertical gaps.
3. Use:
   - `subtree_height = max(box.height, children_total_height)`

This guarantees a parent always has enough vertical space to contain the full child group.

### How positions are assigned

Placement is recursive:

- roots are stacked vertically
- each node is vertically centered inside its subtree height
- children are placed in the next column to the right
- the full child group is vertically centered inside the parent subtree span

This produces a balanced synoptic chart with explicit boxes.

### Edge geometry

Edges are orthogonal:

- horizontal from parent
- vertical in the middle
- horizontal into the child

Relation labels are positioned near the middle vertical segment.

### Page fitting behavior

Current behavior:

- the layout uses the selected page size for final SVG output
- viewport fitting can scale the scene down if needed
- there is no extra layout-specific search yet for portrait or square pages

So `synoptic_boxes` already adapts to the target paper size at render time, but not yet through dedicated geometry rebalancing.

## Synoptic layout

File: `layout/synoptic_layout.py`

### Goal

Keep the same column-based hierarchy as `synoptic_boxes`, but replace per-child box connectors with visual grouping brackets.

### Current calculation flow

This engine reuses the same measurement and positioning strategy as `synoptic_boxes`:

1. Measure nodes.
2. Compute subtree heights.
3. Assign positions by columns.
4. Build one bracket connector per child group.

### Bracket construction

For each node with children:

1. Collect the topmost and bottommost child bounds.
2. Compute a midpoint across the whole child group.
3. Draw a multi-segment polyline:
   - short connector out of the parent
   - elbow toward the group center
   - bracket spine
   - top and bottom hooks

Unlike `tree` and `synoptic_boxes`, this layout intentionally omits relation labels because the visual priority is grouping, not edge annotation.

At render time, the SVG backend can stylize that bracket geometry as a smoother brace-shaped path so the final `{` connectors read more clearly than a raw orthogonal polyline.

### Page fitting behavior

Current behavior:

- the selected page size changes final page dimensions and viewport fitting
- no extra aspect-ratio-specific optimization is implemented yet

That means `synoptic` can be rendered on portrait, landscape, or square pages, but its internal column math remains the same.

## Radial layout

File: `layout/radial_layout.py`

### Goal

Place the concept map around a center, with angular distribution driven by subtree size and radial distances driven by overlap avoidance.

### Current calculation flow

1. Measure all nodes.
2. Compute a subtree weight that mixes structure and visual footprint.
3. Assign angular spans from those subtree weights.
4. Compute a base radius for each depth.
5. Refine radii to avoid tangential overlap.
6. Try several global rotations and keep the one that best fits the target page.
7. Pull nodes inward along their own ray while they still do not collide.
8. Build straight connectors between parent and child anchors.

### Angular distribution

Angular weight is now heuristic rather than purely structural:

- each subtree gets weight from both descendant structure and box footprint
- bulky but shallow branches can therefore receive more angular room
- each node angle is the midpoint of its assigned angular interval

If there is a single root:

- the root itself stays at the center
- its children split the full circle

If there are multiple roots:

- roots themselves split the full circle

### Radial distance calculation

The radial engine now works in two passes:

1. Build conservative per-depth radii:
   - based on radial projected extents between adjacent depths
   - then increased when needed for tangential separation around the ring
2. Run a local compaction pass:
   - each node is tested closer to the center along its own ray
   - the move is accepted only if the box still avoids collisions

This keeps the layout stable while recovering slack left by the conservative ring estimate.

### Position assignment

For each node:

- take the angle assigned to the node
- take the base radius for the node depth, then compact it if local slack exists
- place the box center at:
  - `center_x + radius * cos(angle)`
  - `center_y + radius * sin(angle)`

The single root case places the root box exactly at page center.

### Edge geometry

Edges are simple straight segments between parent and child.

The endpoints are not box centers:

- each endpoint is anchored on the box border in the direction of the other node

This avoids lines crossing through node rectangles.

### Page fitting behavior

After scene construction:

- `radial` can scale down or up
- radial content is centered in the page
- several candidate rotations are evaluated against the selected page ratio
- different page sizes therefore affect both final scale and the chosen orientation

## Summary table

| Layout | Primary axis | Recursive metric | Connector style | Labels |
| --- | --- | --- | --- | --- |
| `tree` | Top-down | Subtree width | Orthogonal vertical-horizontal-vertical | Yes |
| `synoptic_boxes` | Left-to-right | Subtree height | Orthogonal horizontal-vertical-horizontal | Yes |
| `synoptic` | Left-to-right | Subtree height | Bracket polyline per child group | No |
| `radial` | Center-out | Subtree weight + compacted per-node radius | Straight line from border anchor to border anchor | Yes |

## Notes about current heuristics

Some layout behavior is intentionally heuristic rather than purely formulaic:

- `tree` tries multiple compactness profiles before choosing a final scene
- `tree` remeasures parents after final width selection
- `radial` uses projected extents plus a post-placement collision-aware compaction pass
- shared text measurement is deterministic but approximate

This is enough for stable diagram generation while keeping the system simple to modify.
