# Koala

🇺🇸 English | 🇪🇸 [Español](README.es.md)

Koala is a DSL for generating diagrams from structured text.

The project is designed around a simple idea: the same source file should be able to drive multiple layouts and visual styles without rewriting the content itself.

## Quick Start

Main entry point:

- [cli.py](/home/yaldapika/dev/koala/cli.py)
- installed command: `koala`

Install locally in a virtual environment:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e . --no-build-isolation
```

If you prefer a user-facing install instead of a repo-local venv:

```bash
pipx install .
```

Basic commands:

```bash
koala themes
koala layouts
koala typographies
koala compile docs/examples/tree.txt --layout tree
koala compile docs/examples/radial.txt --layout radial --theme jungle --size square
koala inspect docs/examples/tree.txt
koala validate docs/examples/radial.txt --strict
koala config-path
```

Available subcommands:

- `compile`: render a source file to SVG
- `inspect`: show metadata, warnings, and resolved settings
- `validate`: validate parsing and resolved settings; with `--strict` it fails on warnings
- `themes`: list available themes
- `layouts`: list available layouts
- `typographies`: list available typography presets
- `config-path`: show the expected user config path

User config:

- default path: `~/.config/koala/config.toml`
- fallback path: `~/.koala.toml`

Example:

```toml
[tool.koala]
default_layout = "tree"
default_theme = "academic"
default_typography = "default"
default_size = "a4_landscape"
default_text_align = "left"
default_show_node_numbers = true
default_output_mode = "next_to_input"
```

Supported config keys:

- `default_layout`
- `default_theme`
- `default_typography`
- `default_size`
- `default_text_align`
- `default_show_node_numbers`
- `default_output_mode`: `next_to_input`, `desktop`, `cwd`
- `default_output_dir`

Output behavior:

- by default, output goes next to the source file and is named `<input_stem>.<layout>.svg`
- `--output` writes to an explicit SVG path
- `--output-dir` writes to a specific folder
- `--desktop` writes to `~/Desktop` when present, otherwise falls back to the input folder

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
main:: 1 DSL Platform
hl:: 1.2 Users Table
hl:: contains -> 1.2.1 Foreign Key
note:: 1.3 Note
focus:: 1.4 Main Insight
```

Built-in kinds currently available:

- universal: `note`, `warn`, `soft`
- theme-owned: `main`, `hl`, `focus`

`main` is intended mainly for the diagram root. When the root node uses `main::`, built-in themes give it a more prominent color treatment and a thicker border.

Built-in themes currently available:

- `default`
- `terracotta`
- `jungle`
- `frutal`
- `academic`

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

## CLI Reference

Current page presets:

- `a4`: `210 x 297 mm`
- `a4_landscape`: `297 x 210 mm`
- `square`: `210 x 210 mm`

Output:

- by default, next to the source file, named `<input_stem>.<layout>.svg`
- it can also go to `Desktop`, another folder, or an explicit file path via `--output`

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

- [docs/examples/tree.txt](/home/yaldapika/dev/koala/docs/examples/tree.txt)
- [docs/examples/radial.txt](/home/yaldapika/dev/koala/docs/examples/radial.txt)

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
