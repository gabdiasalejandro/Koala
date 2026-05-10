# Layout Calculations

This document explains how each layout currently computes node positions and connector geometry.

## Layout architecture

Tree layouts live under `src/koala/layout/tree/`.

The tree layout package is organized around a small geometry pipeline:

1. `src/koala/layout/tree/registry.py` selects the engine for the requested tree layout kind.
2. `src/koala/layout/shared/measurement.py` handles common measurement, wrapping, depth-aware sizing, and scene-bound helpers.
3. A concrete engine (`tree.py`, `synoptic.py`, `synoptic_boxes.py`, or `radial.py`) computes positions and edge geometry.
4. The engine returns a generic `LayoutScene` made of `LayoutBox` and `LayoutEdge`.

This keeps a strict split:

- `layout/shared/measurement.py` owns common measurement rules
- each engine owns only its own placement strategy
- render code receives a layout-agnostic scene and does not know which engine produced it

## Shared concepts used by all layouts

All tree layout engines start from `measure_nodes(...)` in
`src/koala/layout/shared/measurement.py`.

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

File: `src/koala/layout/tree/tree.py`

### Goal

Create a top-down hierarchy where parents sit above their descendants, while still adapting the visible box width to content and available paper space.

### Current calculation flow

1. Measure all nodes with `measure_nodes(...)`.
2. Try several compactness profiles by scaling:
   - base node width
   - horizontal gap
   - vertical gap
3. For each profile, run a parent re-measurement pass and then place nodes
   using a contour-based packing algorithm.
4. Choose the profile whose resulting scene best fits the page.

### How parent width is chosen

Parent re-measurement still runs bottom-up before placement. For leaves,
`box.width` stays as measured. For internal nodes:

1. Recursively measure every child first.
2. Compute the naive sum of child widths plus horizontal gaps.
3. Choose a visible parent width clamped between:
   - minimum: enough width to avoid breaking words
   - preferred: the width the parent text would naturally need
   - maximum: a fraction of the combined child width
     (`100%` for one child, `90%` for multiple)
4. Re-measure the parent text using that final width.

This step decides only the parent box size. The horizontal placement of the
subtree is decided in the next step.

### How positions are assigned

Placement uses Walker's algorithm with the linear-time improvement from
Buchheim, Jünger, and Leipert (2002). Concretely:

1. A bottom-up pass assigns a preliminary `x` to each node and resolves
   conflicts between sibling subtrees by walking their left and right
   contours through threaded pointers. When a subtree would overlap its
   left neighbor, the algorithm shifts it just enough to clear the contour.
2. A top-down pass adds accumulated modifiers and writes the final
   `box.x = preliminary_x + accumulated_modifier - box.width / 2`.
3. Y positions are aligned per depth: each level uses the maximum height of
   the boxes at that depth plus the per-depth vertical gap.
4. A final offset moves the leftmost point of each tree to `config.margin_x`,
   then multi-root layouts move the cursor by the actual subtree footprint
   plus `config.h_gap_base`.

Why this matters: with the contour-based packing, two sibling subtrees can
**interpenetrate** their empty halves. A subtree that is wide at the top and
narrow at the bottom can sit next to one shaped the opposite way without
each reserving its own column. For asymmetric maps this typically yields
20–25% narrower scenes than a strict band-sum approach, while leaves and
non-overlapping subtrees still produce the same visual result.

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

File: `src/koala/layout/tree/synoptic_boxes.py`

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

File: `src/koala/layout/tree/synoptic.py`

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
2. Keep a fixed bracket body defined by:
   - bracket spine
   - top and bottom hooks
   - a single peak on the inner side
3. Slide that peak vertically toward the parent center, clamped inside the child-group span.

Unlike `tree` and `synoptic_boxes`, this layout intentionally omits relation labels because the visual priority is grouping, not edge annotation.

At render time, the SVG backend stylizes that geometry as a smooth brace-shaped path. The brace keeps a stable silhouette and only the peak position moves to follow the parent vertically.

### Page fitting behavior

Current behavior:

- the selected page size changes final page dimensions and viewport fitting
- no extra aspect-ratio-specific optimization is implemented yet

That means `synoptic` can be rendered on portrait, landscape, or square pages, but its internal column math remains the same.

## Radial layout

File: `src/koala/layout/tree/radial.py`

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

The radial engine works in three passes:

1. Build conservative per-depth radii:
   - based on radial projected extents between adjacent depths
   - then increased when needed for tangential separation around the ring
2. Auto-tune for saturated parents using the multi-ring chooser:
   - when a single parent has many children at the same depth, those
     children are alternated by angular order into two sub-rings (inner
     and outer)
   - the chooser computes radii for both the single-ring and multi-ring
     options and keeps the configuration with the smaller maximum radius
   - sub-ring assignment is per parent: a hub with twenty children may
     split while smaller siblings on the same depth stay on one ring
3. Run a local compaction pass:
   - each node is tested closer to the center along its own ray
   - the move is accepted only if the box still avoids collisions

The chooser is automatic and has no public configuration. For typical maps
with ≤ 12 children per parent the single-ring layout always wins, so
behavior matches the classic radial output exactly. The crossover where
multi-ring starts to win sits around 13 children per parent and grows
significantly from there: a hub with fifty children produces roughly half
the maximum radius compared to forcing all of them onto a single ring.

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

Relation labels in `radial` are now resolved after node placement:

- the node layout itself is not recomputed for labels
- each label gets a collision-aware position near its edge
- horizontal text is preferred; mild rotation is used only when it improves fit
- the edge line is split around the label bounds so the final SVG reads like `---- label ---->`
- label bounds are included in final scene bounds so page fitting does not crop them

### Page fitting behavior

After scene construction:

- `radial` can scale down or up
- radial content is centered in the page
- several candidate rotations are evaluated against the selected page ratio
- different page sizes therefore affect both final scale and the chosen orientation

## Summary table

| Layout | Primary axis | Recursive metric | Connector style | Labels |
| --- | --- | --- | --- | --- |
| `tree` | Top-down | Walker contour packing on remeasured widths | Orthogonal vertical-horizontal-vertical | Yes |
| `synoptic_boxes` | Left-to-right | Subtree height | Orthogonal horizontal-vertical-horizontal | Yes |
| `synoptic` | Left-to-right | Subtree height | Bracket polyline per child group | No |
| `radial` | Center-out | Subtree weight + auto-tuned single/multi-ring radius + per-node compaction | Straight line from border anchor to border anchor, split around relation labels | Yes |

## Notes about current heuristics

Some layout behavior is intentionally heuristic rather than purely formulaic:

- `tree` tries multiple compactness profiles before choosing a final scene
- `tree` remeasures parents before running Walker's contour-based placement
- `radial` uses projected extents plus a post-placement collision-aware compaction pass
- `radial` chooses between single-ring and multi-ring layouts per rotation by
  picking the option with the smaller maximum radius
- `radial` also resolves relation labels in a separate post-layout pass instead of feeding them back into node placement
- shared text measurement is deterministic but approximate
- shared title sizing first reduces font size to fit the longest word
  (capped by `title_word_fit_max_drop`), then keeps reducing for line count
  down to `title_size_min`; character-level word splitting is a last resort

This is enough for stable diagram generation while keeping the system simple to modify.
