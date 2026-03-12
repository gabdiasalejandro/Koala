# Tutorial

This tutorial is a practical guide to writing Koala documents and choosing good render settings.

It covers:

- core DSL syntax
- optional metadata with `@...`
- available themes
- available typography presets
- semantic kinds with `kind::`
- available page sizes
- practical suggestions for getting better visuals

## 1. Smallest useful document

The smallest meaningful Koala file looks like this:

```text
1 DSL Platform
Defines the main concept.

organizes -> 1.1 Core
Contains parser, models, and validations.

renders -> 1.2 Render
Generates SVG output.
```

What this means:

- `1` creates a root node
- the following line becomes its body text
- `1.1` and `1.2` become children of `1`
- `organizes` and `renders` are relation labels from the parent

## 2. Hierarchy syntax

Koala uses numbered hierarchy:

- `1`, `2`, `3` are roots
- `1.1`, `1.2` are children of `1`
- `1.1.1` is a child of `1.1`

Example:

```text
1 Biology
General topic.

1.1 Cell
Basic unit of life.

1.1.1 Membrane
Defines the boundary of the cell.
```

### Optional super-root

You can use `0` as an optional super-root:

```text
0 Biology
Global topic.

1 Cell
Basic unit of life.

2 Genetics
Study of heredity.
```

In that case, `1` and `2` become children of `0`.

## 3. Body text

Any non-empty line after a valid node header becomes body text for that node until a new node header appears.

Example:

```text
1 Cell
The cell is the basic unit of life.
All living organisms are composed of one or more cells.
```

That produces one node with two body lines.

## 4. Relations

Relations are optional and appear before the node number:

```text
contains -> 1.1 Nucleus
depends on -> 1.2 Membrane
```

Both `->` and `→` are accepted.

If you do not include a relation, the parent-child connector still exists, but is treated as implicit.

## 5. Semantic kinds with `kind::`

`kind::` lets you mark a node semantically so themes can style it differently.

Example:

```text
hl:: 1 Important Concept
hl:: contains -> 1.1 Highlighted Child
```

Current behavior:

- kinds are normalized to lowercase
- if omitted, the kind becomes `default`
- current built-in themes include styling for `hl`

Use `kind::` when a concept should visually stand out, not on every node.

## 6. Metadata with `@`

Koala supports optional document-level metadata using lines that start with `@`.

Example:

```text
@layout tree
@theme terracotta
@typography default
@size square
@show-node-numbers false
@output-dir output/tutorial_demo
```

Accepted styles:

```text
@layout tree
@layout: tree
```

### Available metadata keys

Current supported metadata keys:

- `@layout`
- `@theme`
- `@typography`
- `@size`
- `@page-size`
- `@output-dir`
- `@output_dir`
- `@show-node-numbers`
- `@show_node_numbers`
- `@node-numbers`
- `@node_numbers`

### Metadata precedence

Render options are resolved in this order:

1. explicit CLI flag
2. metadata from the document
3. built-in default

This means metadata is good for self-contained demo files, but the CLI can still override it.

### Disabling node numbers

By default Koala shows node numbers in the final map, such as `1`, `1.1`, and `1.2`.

You can disable them in metadata:

```text
@show-node-numbers false
```

Accepted false-like values:

- `false`
- `no`
- `off`
- `hide`
- `hidden`
- `0`

Accepted true-like values:

- `true`
- `yes`
- `on`
- `show`
- `shown`
- `1`

## 7. Available layouts

Current layouts:

- `tree`
- `synoptic`
- `synoptic_boxes`
- `radial`

### `tree`

Best for:

- classic hierarchies
- explanatory maps
- concept decomposition

Characteristics:

- top-down
- adaptive parent widths
- strong page-aware fitting

### `synoptic`

Best for:

- category trees
- grouped outlines
- compact classification charts

Characteristics:

- left-to-right
- bracket connectors
- no relation labels

### `synoptic_boxes`

Best for:

- left-to-right teaching diagrams
- structured breakdowns
- content where each sibling group is conceptually parallel

Characteristics:

- left-to-right
- boxed nodes
- relation labels preserved

### `radial`

Best for:

- mind maps
- central topic plus balanced branches
- star-like concept structures

Characteristics:

- root in the center
- branch distribution by angular span
- overlap-aware radial separation

## 8. Available themes

Current built-in themes:

- `default`
- `terracotta`
- `jungle`

### `default`

Best when:

- you want a neutral technical look
- readability is the priority
- you want the least opinionated color palette

### `terracotta`

Best when:

- you want a warmer editorial tone
- the document should feel more didactic or presentation-oriented

### `jungle`

Best when:

- you want a fresher, greener palette
- the content benefits from a lighter organic tone

## 9. Available typographies

Current built-in typography presets:

- `default`
- `radial`

### `default`

Used by:

- `tree`
- `synoptic`
- `synoptic_boxes`

Characteristics:

- stronger title presence
- balanced body size for boxed layouts
- good all-purpose readability

### `radial`

Used by default in:

- `radial`

Characteristics:

- slightly smaller type
- tuned for denser circular compositions

## 10. Available page sizes

Current page presets:

- `a4`
- `a4_landscape`
- `square`

### `a4`

Size:

- `210 x 297 mm`

Best when:

- the structure is taller
- the tree is deep
- you want stronger vertical reading rhythm

### `a4_landscape`

Size:

- `297 x 210 mm`

Best when:

- you want the safest general-purpose page
- you are using `synoptic` or `synoptic_boxes`
- the tree has medium horizontal spread

Current default page size:

- `a4_landscape`

### `square`

Size:

- `210 x 210 mm`

Best when:

- you want denser, centered compositions
- you are using `radial`
- a `tree` would otherwise spread too wide

## 11. Suggestions for better visual results

These are practical writing heuristics for the current engines.

### General suggestions

- Keep titles short and concept-oriented
- Move explanation into body text
- Avoid extremely long paragraphs
- Use relation labels only when they add meaning
- Prefer balanced sibling groups over very uneven branching
- Use metadata when a file is intended for a specific render style

### Suggestions for `tree`

- Use it for classic hierarchies and explanatory branching
- Keep child titles compact when a node has many children
- `a4_landscape` is the safest default
- `square` often improves shallow but wide trees
- `a4` works well for deeper trees

### Suggestions for `synoptic`

- Use it for category refinement and outline-like content
- Keep titles short
- Keep body text light
- `a4_landscape` is currently the safest size
- Use this layout when grouping matters more than relation labels

### Suggestions for `synoptic_boxes`

- Use it for structured left-to-right explanation
- Keep sibling groups parallel in meaning
- Prefer short-to-medium body text
- `a4_landscape` is currently the safest size
- `square` is supported, but content should stay tighter

### Suggestions for `radial`

- Use it when a central concept has several balanced branches
- Keep first-level branches relatively even in size
- Avoid one giant branch plus many tiny branches
- `square` and `a4_landscape` usually give the cleanest balance

## 12. Example tutorial document

```text
@layout tree
@theme terracotta
@size square
@show-node-numbers false

1 DSL Platform
Coordinates parser, layout, and render.

organizes -> 1.1 Core
Contains parsing, models, and validation.

renders -> 1.2 Render
Produces the final SVG output.

hl:: includes -> 1.2.1 Viewport
Fits the scene into the selected page size.
```

## 13. Recommended files to inspect

- [mocks/concepts.txt](/home/yaldapika/dev/koala/mocks/concepts.txt)
- [mocks/metadata_demo.txt](/home/yaldapika/dev/koala/mocks/metadata_demo.txt)
- [docs/syntax.md](/home/yaldapika/dev/koala/docs/syntax.md)
- [docs/layouts.md](/home/yaldapika/dev/koala/docs/layouts.md)
- [docs/architecture.md](/home/yaldapika/dev/koala/docs/architecture.md)
