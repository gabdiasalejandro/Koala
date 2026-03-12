# Layout Calculations

This document explains how each layout currently computes node positions and connector geometry.

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
2. Count leaves per subtree.
3. Assign angular spans using leaf counts.
4. Compute a radius for each depth.
5. Refine radii to avoid tangential overlap.
6. Place nodes around the center.
7. Build straight connectors between parent and child anchors.

### Angular distribution

Leaf count drives angular weight:

- a subtree with more leaves gets a larger angle span
- each node angle is the midpoint of its assigned angular interval

If there is a single root:

- the root itself stays at the center
- its children split the full circle

If there are multiple roots:

- roots themselves split the full circle

### Radial distance calculation

The radius for each depth is built in stages:

1. Compute a minimum radial step from the previous depth:
   - based on box extents projected in the radial direction
2. Increase radius when needed for tangential separation:
   - compare adjacent nodes around the ring
   - require enough chord distance between their projected tangential extents
3. Recheck that radius still remains larger than the previous depth radius plus the minimum radial step

This produces concentric rings that avoid obvious box overlap.

### Position assignment

For each node:

- take the angle assigned to the node
- take the radius for the node depth
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
- different page sizes change the usable centered area and therefore the final visual scale

## Summary table

| Layout | Primary axis | Recursive metric | Connector style | Labels |
| --- | --- | --- | --- | --- |
| `tree` | Top-down | Subtree width | Orthogonal vertical-horizontal-vertical | Yes |
| `synoptic_boxes` | Left-to-right | Subtree height | Orthogonal horizontal-vertical-horizontal | Yes |
| `synoptic` | Left-to-right | Subtree height | Bracket polyline per child group | No |
| `radial` | Center-out | Leaf count + per-depth radius | Straight line from border anchor to border anchor | Yes |

## Notes about current heuristics

Some layout behavior is intentionally heuristic rather than purely formulaic:

- `tree` tries multiple compactness profiles before choosing a final scene
- `tree` remeasures parents after final width selection
- `radial` uses projected extents instead of exact collision solving
- shared text measurement is deterministic but approximate

This is enough for stable diagram generation while keeping the system simple to modify.
