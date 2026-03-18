# Tutorial

This tutorial is a practical guide to writing Koala documents and choosing good render settings.

It covers:

- installation
- CLI usage
- library usage
- in-memory APIs such as `compile_text(...)`, `inspect_text(...)`, and `validate_text(...)`
- user config
- core DSL syntax
- optional metadata with `@...`
- available themes
- available typography presets
- semantic kinds with `kind::`
- available page sizes
- practical suggestions for getting better visuals

## 1. Install and choose your interface

Koala can be used in two ways:

- from the CLI through the installed `koala` command
- from Python through `import koala`

Install from PyPI:

```bash
pip install koala-diagrams==1.0.0
```

If you mainly want the CLI as an isolated user tool:

```bash
pipx install koala-diagrams==1.0.0
```

If you are developing from the repository:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e . --no-build-isolation
PYTHONPATH=src ./.venv/bin/python -m koala themes
```

## 2. CLI quickstart

The installed command is `koala`.

Common commands:

```bash
koala themes
koala layouts
koala typographies
koala compile docs/examples/tree.txt --layout tree --theme academic
koala compile docs/examples/radial.txt --layout radial --theme frutal --size square
koala inspect docs/examples/tree.txt
koala validate docs/examples/radial.txt --strict
koala config-path
```

Current CLI subcommands:

- `compile`: render a source file to SVG
- `inspect`: resolve metadata and settings without writing output
- `validate`: validate parsing and settings; `--strict` fails on warnings
- `themes`: list available themes
- `layouts`: list available layouts
- `typographies`: list typography presets
- `config-path`: print the expected user config path

Output behavior from the CLI:

- by default, output goes next to the input file as `<input_stem>.<layout>.svg`
- `--output` writes to an explicit SVG path
- `--output-dir` writes to a specific folder
- `--desktop` writes to `~/Desktop` when available and otherwise falls back to the input folder

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

## 3. Library quickstart

Use the library API when you want to render from another Python program.

### Render from a source file

```python
import koala

result = koala.compile(
    "docs/examples/radial.txt",
    layout="radial",
    theme="academic",
    size="square",
    text_align="left",
)

print(result.output_svg)
print(result.context.settings.layout_kind)
print(len(result.context.parsed.node_index))
```

### Render from raw text in memory

```python
import koala

result = koala.compile_text(
    """
    1 Central Topic
    Main explanation.

    1.1 First Branch
    Supporting detail.
    """,
    layout="tree",
    theme="frutal",
    base_dir="docs/examples",
    output_name="inline_demo",
)

print(result.output_svg)
```

Current output behavior for `compile_text(...)`:

- relative output paths are resolved against `base_dir` when provided
- if `base_dir` is omitted, Koala uses `Path.cwd()`
- if you do not pass `output` or `output_dir`, the default file is `concept_map.<layout>.svg`
- if you pass `output_name="demo"`, the default file becomes `demo.<layout>.svg`

### Inspect and validate text without writing files

```python
import koala

context = koala.inspect_text(
    "1 Root\nBody.\n",
    layout="tree",
    theme="academic",
)

validated = koala.validate_text(
    "1 Root\nBody.\n",
    layout="tree",
    theme="academic",
    strict=True,
)

print(len(context.parsed.node_index))
print(len(validated.parsed.warnings))
```

If `strict=True` and the parser emits warnings, `validate_text(...)` raises `koala.ValidationError`.

### Current in-memory API surface

- `koala.compile(path, **config)`: render from `.txt` or `.docx`
- `koala.compile_text(text, **config)`: render from raw Koala DSL text
- `koala.inspect_text(text, **config)`: resolve `RenderContext` without writing SVG
- `koala.validate_text(text, **config)`: resolve `RenderContext` and optionally fail on warnings

## 4. Smallest useful document

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

## 5. Hierarchy syntax

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

## 6. Body text

Any non-empty line after a valid node header becomes body text for that node until a new node header appears.

Example:

```text
1 Cell
The cell is the basic unit of life.
All living organisms are composed of one or more cells.
```

That produces one node with two body lines.

## 7. Relations

Relations are optional and appear before the node number:

```text
contains -> 1.1 Nucleus
depends on -> 1.2 Membrane
```

Both `->` and `→` are accepted.

If you do not include a relation, the parent-child connector still exists, but is treated as implicit.

## 8. Semantic kinds with `kind::`

`kind::` lets you mark a node semantically so themes can style it differently.

Example:

```text
main:: 1 Main Topic
hl:: contains -> 1.1 Highlighted Child
note:: 1.2 Supporting Note
warn:: 1.2.1 Caution
soft:: 1.2.2 Secondary Detail
focus:: 1.3 Central Idea
```

Current behavior:

- kinds are normalized to lowercase
- if omitted, the kind becomes `default`
- built-in universal kinds are `note`, `warn`, and `soft`
- built-in theme-owned kinds are `main`, `hl`, and `focus`

### What each built-in kind is for

- `note`: supporting context that should read as useful but not dominant
- `warn`: caution, constraint, tradeoff, or risk
- `soft`: lower-priority supporting detail
- `main`: the primary root concept; built-in themes reserve it for the top-level anchor
- `hl`: a highlighted concept the active theme wants to emphasize strongly
- `focus`: the key thesis, core idea, or primary anchor of a branch

### Universal vs theme-owned kinds

Koala currently ships with two semantic groups:

- universal kinds: `note`, `warn`, `soft`
- theme-owned kinds: `main`, `hl`, `focus`

Universal kinds are defined once and then recolored by the active theme.
Theme-owned kinds also exist in every built-in theme, but each theme defines their specific treatment directly.

### Full example using all built-in kinds

```text
main:: 1 Render Pipeline
Coordinates the full SVG export process.

hl:: orchestrates -> 1.1 Render Context
Combines layout selection, theme resolution, and viewport fitting.

note:: includes -> 1.1.1 Metadata
Allows the source file to carry render preferences.

warn:: constrains -> 1.1.2 Viewport
Very dense scenes may still require scale reduction.

soft:: documents -> 1.1.3 Defaults
Presets keep the CLI small and predictable.
```

If the root node uses `main::` in a boxed layout such as `tree`, `synoptic_boxes`, or `radial`, Koala also draws it with a thicker border to make the visual hierarchy more explicit.

Use `kind::` when a concept should visually stand out, not on every node.

## 9. Metadata with `@`

Koala supports optional document-level metadata using lines that start with `@`.

Example:

```text
@layout tree
@theme terracotta
@typography default
@text-align justify
@size square
@show-node-numbers false
@output-dir exports/tutorial_demo
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
- `@text-align`
- `@size`
- `@page-size`
- `@output-dir`
- `@output_dir`
- `@text_align`
- `@show-node-numbers`
- `@show_node_numbers`
- `@node-numbers`
- `@node_numbers`

For text alignment, supported values are `left` and `justify`. The default is `left`.

### Metadata precedence

Render options are resolved in this order:

1. explicit CLI flag or explicit library kwarg
2. metadata from the document
3. user config default
4. built-in default

This means metadata is good for self-contained demo files, but the CLI and the library API can still override it.

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

## 10. Available layouts

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

## 11. Available themes

Current built-in themes:

- `default`
- `terracotta`
- `jungle`
- `frutal`
- `academic`

All built-in themes currently support:

- universal kinds: `note`, `warn`, `soft`
- theme-owned kinds: `main`, `hl`, `focus`

### `default`

Best when:

- you want a neutral technical look
- readability is the priority
- you want the least opinionated color palette

Kind tone:

- `main` reads as the strongest root-level accent
- `hl` reads as a warm highlight against a neutral base
- `focus` reads as a cooler, primary emphasis

### `terracotta`

Best when:

- you want a warmer editorial tone
- the document should feel more didactic or presentation-oriented

Kind tone:

- `main` reads as the strongest terracotta root accent
- `hl` reads as a strong terracotta-accent highlight
- `focus` reads as a softer clay emphasis

### `jungle`

Best when:

- you want a fresher, greener palette
- the content benefits from a lighter organic tone

Kind tone:

- `main` reads as the strongest green root accent
- `hl` reads as an aqua-highlighted concept
- `focus` reads as a greener structural emphasis

### `frutal`

Best when:

- you want a brighter and more playful palette
- the diagram should feel more energetic or more didactic

Kind tone:

- `main` reads as the strongest fruit-like accent
- `hl` reads as the most vivid emphasis
- `focus` reads as a softer but still warm accent

### `academic`

Best when:

- you want the most sober built-in presentation
- black text and restrained contrast matter more than colorful accents

Kind tone:

- `main` reads as the strongest sober anchor
- `hl` reads as a restrained emphasis instead of a loud accent
- `focus` reads as a neutral structural highlight

### Theme demo files

The repository currently includes usage examples and test fixtures instead of root-level theme mocks:

- [docs/examples/tree.txt](/home/yaldapika/dev/koala/docs/examples/tree.txt)
- [docs/examples/radial.txt](/home/yaldapika/dev/koala/docs/examples/radial.txt)
- [tests/end_to_end/mocks/alignment_left.txt](/home/yaldapika/dev/koala/tests/end_to_end/mocks/alignment_left.txt)
- [tests/end_to_end/mocks/alignment_justify.txt](/home/yaldapika/dev/koala/tests/end_to_end/mocks/alignment_justify.txt)

## 12. Available typographies

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

## 13. Available page sizes

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

## 14. Suggestions for better visual results

These are practical writing heuristics for the current engines.

Main suggestion:

- avoid having more than 8 children in the deepest ring of a branch

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

## 15. Example tutorial document

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

## 16. Recommended files to inspect

- [docs/examples/tree.txt](/home/yaldapika/dev/koala/docs/examples/tree.txt)
- [docs/examples/radial.txt](/home/yaldapika/dev/koala/docs/examples/radial.txt)
- [tests/end_to_end/mocks/alignment_left.txt](/home/yaldapika/dev/koala/tests/end_to_end/mocks/alignment_left.txt)
- [tests/end_to_end/mocks/alignment_justify.txt](/home/yaldapika/dev/koala/tests/end_to_end/mocks/alignment_justify.txt)
- [docs/syntax.md](/home/yaldapika/dev/koala/docs/syntax.md)
- [docs/layouts.md](/home/yaldapika/dev/koala/docs/layouts.md)
- [docs/architecture.md](/home/yaldapika/dev/koala/docs/architecture.md)
