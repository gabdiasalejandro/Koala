# Koala

🇺🇸 English | 🇪🇸 [Español](README.es.md)

Koala is a DSL for generating diagrams from structured text.

The project is designed around a simple idea: the same source file should be able to drive multiple layouts and visual styles without rewriting the content itself.

## Current capabilities

- Parse hierarchical concept trees from `.txt` and `.docx`
- Render the same document as `tree`, `synoptic`, `synoptic_boxes`, or `radial`
- Apply themes and typography presets
- Select page size from the CLI
- Read optional render metadata directly from the source file with `@...`
- Fit the final scene into SVG output

## Syntax overview

Nodes use hierarchical numbering:

- `1`, `2`, `3` are roots
- `1.1`, `1.2` are children of `1`
- `1.1.1` is a child of `1.1`
- `0` is an optional super-root

Example:

```text
1 DSL Platform
Defines the main concept.

organizes -> 1.1 Core
Contains parser, models, and validations.

renders -> 1.2 Render
Generates SVG output.
```

Optional semantic kind:

```text
hl:: 1.2 Users Table
hl:: contains -> 1.2.1 Foreign Key
note:: 1.3 Note
focus:: 1.4 Main Insight
```

Built-in kinds currently available:

- universal: `note`, `warn`, `soft`
- theme-owned: `hl`, `focus`

Built-in themes currently available:

- `default`
- `terracotta`
- `jungle`

Optional metadata:

```text
@layout tree
@theme terracotta
@typography default
@text-align justify
@size square
@show-node-numbers false
@output-dir output/metadata_demo
```

Metadata is optional and follows this precedence:

1. explicit CLI flag
2. metadata in the source file
3. built-in defaults

Node text alignment is now `left` by default. If you want justified text, use `@text-align justify`.

For the full syntax, see [docs/syntax.md](/home/yaldapika/dev/koala/docs/syntax.md).

## Usage

Main entry point:

- [main.py](/home/yaldapika/dev/koala/main.py)

Examples:

```bash
./.venv/bin/python main.py --layout tree
./.venv/bin/python main.py --layout synoptic
./.venv/bin/python main.py --layout synoptic_boxes
./.venv/bin/python main.py --layout radial
./.venv/bin/python main.py --input mocks/metadata_demo.txt
./.venv/bin/python main.py --layout tree --theme terracotta --size square
```

Current CLI options:

- `--layout`: `tree`, `synoptic`, `synoptic_boxes`, `radial`
- `--input`: input `.txt` or `.docx`
- `--output-dir`: output folder
- `--theme`: theme preset
- `--typography`: typography preset
- `--size`: page preset, currently `a4`, `a4_landscape`, `square`

Current page presets:

- `a4`: `210 x 297 mm`
- `a4_landscape`: `297 x 210 mm`
- `square`: `210 x 210 mm`

Output:

- `output/concept_map_<layout>.svg`

## Layouts

Current supported layouts:

- `tree`: top-down hierarchy with adaptive parent widths and page-aware fitting
- `synoptic`: synoptic chart with brackets and no relation labels
- `synoptic_boxes`: synoptic chart with boxes and relation labels
- `radial`: center-out mind-map style layout

For implementation details, see [docs/layouts.md](/home/yaldapika/dev/koala/docs/layouts.md).

## Architecture

The project is split into three layers:

- `core/`: parsing, DSL models, input loading
- `layout/`: shared measurement plus one geometry engine per layout
- `render/`: theme resolution, render context, viewport fitting, and SVG backend

The separation of concerns is:

- `core` understands the language
- `layout` computes geometry and connector paths
- `render` resolves presentation and draws the scene

For the full architecture, see [docs/architecture.md](/home/yaldapika/dev/koala/docs/architecture.md).

## Authoring tips for better visuals

These suggestions are practical heuristics for getting cleaner diagrams with the current engines.

### General

- Keep titles short and concept-oriented; move explanation into body text
- Use relations only when they add value; too many relation labels create noise
- Prefer balanced sibling groups over very uneven branching when possible
- Split very long paragraphs into tighter prose; box measurement is line-based and compact prose produces better wrapping
- Use metadata for layout/theme/size when a file is meant to be rendered in a specific way

### `tree`

- Best for classic hierarchies and explanatory maps
- Works especially well when upper levels are conceptual and lower levels carry detail
- Good fit for `a4_landscape` and `square`
- If a parent has many children, keep child titles compact so the tree can stay readable at larger sizes
- If the map is shallow and very wide, `square` often helps force a denser composition

### `synoptic`

- Best for grouped classifications and outline-like content
- Prefer short titles and very light body text
- Works best when each level behaves like a category refinement
- `a4_landscape` is currently the safest page size because the internal geometry is still column-oriented
- Use fewer relation labels in the source; they are intentionally suppressed in this layout

### `synoptic_boxes`

- Best for left-to-right teaching diagrams or process decompositions
- Keep each sibling set conceptually parallel
- Use short-to-medium body text, not large paragraphs
- `a4_landscape` is currently the safest page size
- `square` is already supported, but there is no dedicated compaction pass yet, so content should be tighter

### `radial`

- Best for central topics with several balanced branches
- Try to keep first-level branches similar in importance and size
- Avoid one giant branch plus many tiny ones if you want a clean circular composition
- `square` and `a4_landscape` usually give the best radial balance
- If the root concept is very short and children are rich, radial can use the page very efficiently

### Page-size-specific advice

#### `a4`

- Better for taller trees or vertically deep hierarchies
- Good when you want more stacked reading rhythm
- Less ideal for wide synoptic structures unless the content is compact

#### `a4_landscape`

- Current default
- Best general-purpose preset
- Safest choice for `synoptic` and `synoptic_boxes`
- Also strong for medium-width `tree` documents

#### `square`

- Best when you want a denser, more centered composition
- Strong option for `radial`
- Useful for `tree` when the content would otherwise spread too far horizontally
- Requires tighter writing for `synoptic` and `synoptic_boxes` until those engines get aspect-ratio-specific optimization

## Recommended examples

- [mocks/concepts.txt](/home/yaldapika/dev/koala/mocks/concepts.txt)
- [mocks/theme_default_tree.txt](/home/yaldapika/dev/koala/mocks/theme_default_tree.txt)
- [mocks/theme_terracotta_synoptic_boxes.txt](/home/yaldapika/dev/koala/mocks/theme_terracotta_synoptic_boxes.txt)
- [mocks/theme_jungle_radial.txt](/home/yaldapika/dev/koala/mocks/theme_jungle_radial.txt)

## Current status

The project is already useful for:

- rapid concept-map prototyping
- trying multiple layouts from the same content
- testing visual semantics with `kind::`
- shipping self-describing demo files through metadata

There is still room to improve:

- layout-specific adaptation for `synoptic` and `synoptic_boxes` under portrait and square pages
- richer DSL syntax
- stronger validations
- automated visual regression checks
