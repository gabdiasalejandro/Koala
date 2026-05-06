# Tutorial

This tutorial is a practical guide to writing Koala documents and choosing render settings that match the current Python API and CLI.

Koala currently supports three document types:

- `tree`: numbered hierarchical concept maps
- `matrix`: comparative tables
- `flowchart`: process diagrams with steps, decisions, and directed edges

The default document type is `tree`.

## 1. Install

Install from PyPI:

```bash
pip install koala-diagrams==1.3.6
```

Or install the CLI as an isolated user tool:

```bash
pipx install koala-diagrams==1.3.6
```

For local development from this repository:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e . --no-build-isolation
PYTHONPATH=src ./.venv/bin/python -m koala themes
```

## 2. CLI Quickstart

The installed command is `koala`.

Useful discovery commands:

```bash
koala types
koala layouts
koala themes
koala typographies
koala typographies --type tree
koala typographies --type matrix
koala typographies --type flowchart
koala config-path
```

Render and inspect commands:

```bash
koala compile map.txt --type tree --layout tree --theme academic
koala compile map.txt --type tree --layout radial --theme frutal --size square
koala compile comparison.txt --type matrix --layout matrix --theme academic --typography formal
koala compile process.txt --type flowchart --layout flowchart --theme ocean

koala export map.txt --type tree --layout tree --format png --quality high
koala export comparison.txt --type matrix --layout matrix --format pdf --quality high
koala export process.txt --type flowchart --layout flowchart --format pdf --quality high

koala inspect map.txt --type tree --layout tree
koala validate map.txt --type tree --layout tree --strict
```

Current CLI subcommands:

- `compile`: render a `.txt` or `.docx` source file to SVG
- `export`: export a source file to SVG, PNG, or PDF
- `inspect`: resolve parsing, metadata, layout, theme, typography, and page settings without writing output
- `validate`: validate parsing and settings; `--strict` exits with failure on parser warnings
- `themes`: list available themes
- `types`: list available document types
- `layouts`: list available layouts
- `typographies`: list typography presets, optionally filtered with `--type`
- `config-path`: print the expected user config path

CLI output behavior:

- by default, `compile` writes next to the input file
- default SVG names use `<input_stem>.<layout>.svg`
- `--output` writes to an explicit SVG path
- `--output-dir` writes to a specific folder
- `--desktop` writes to `~/Desktop` when available and otherwise falls back to the input folder
- `export -o` writes the requested SVG, PNG, or PDF path

## 3. Python API Quickstart

Use the Python API when another program needs Koala as a library.

### Render SVG In Memory

`render_text(...)` is the clearest API for in-memory SVG rendering. It does not write files.

```python
import koala

result = koala.render_text(
    """
    main:: 1 Central Topic
    Main explanation.

    supports -> 1.1 First Branch
    Supporting detail.
    """,
    type="tree",
    layout="tree",
    theme="frutal",
)

print(result.svg)
print(result.output_svg)  # None
print(result.context.settings.layout_kind)
```

### Compile A File To SVG

`compile(...)` reads a `.txt` or `.docx` file and writes an SVG.

```python
import koala

result = koala.compile(
    "map.txt",
    type="tree",
    layout="radial",
    theme="academic",
    size="square",
    text_align="left",
)

print(result.output_svg)
print(result.svg)
```

`compile_file(...)` is an explicit alias for `compile(...)`.

### Legacy Text Compile

`compile_text(...)` writes an SVG from raw text. It is kept for compatibility, while `render_text(...)` is preferred for pure in-memory rendering.

```python
import koala

result = koala.compile_text(
    "1 Root\nBody.\n",
    type="tree",
    layout="tree",
    theme="academic",
    base_dir=".",
    output_name="inline_demo",
)

print(result.output_svg)  # inline_demo.tree.svg
```

For `compile_text(...)`:

- relative output paths are resolved against `base_dir` when provided
- if `base_dir` is omitted, Koala uses `Path.cwd()`
- if neither `output` nor `output_dir` is provided, the default file is `concept_map.<layout>.svg`
- if `output_name="demo"` is provided, the default file is `demo.<layout>.svg`

### Export Bytes

`export_text(...)` and `export_file(...)` return bytes suitable for web responses or storage.

```python
import koala

source = """
main:: 1 Product Map
Direction and scope.

supports -> 1.1 API
In-memory export results.
"""

png = koala.export_text(
    source,
    type="tree",
    layout="tree",
    format="png",
    quality="high",
    theme="jungle",
)

pdf = koala.export_text(
    source,
    type="tree",
    layout="tree",
    format="pdf",
    quality="high",
    theme="jungle",
)

print(png.media_type, len(png.content))
print(pdf.media_type, len(pdf.content))
```

Supported export formats:

- `svg`
- `png`
- `pdf`

PNG quality values:

- `medium`: 200 DPI
- `high`: 450 DPI

PDF export is vector based and adds a framed page, title, margins, and theme-aware accent colors. If `title` is omitted, Koala resolves it from the first `main::` node, then from the first root.

### Inspect And Validate

Use `inspect_text(...)` to resolve a `RenderContext` without writing files.

Use `validate_text(...)` when you want the same resolution step plus optional strict failure on parser warnings.

```python
import koala

context = koala.inspect_text(
    "1 Root\nBody.\n",
    type="tree",
    layout="tree",
    theme="academic",
)

validated = koala.validate_text(
    "1 Root\nBody.\n",
    type="tree",
    layout="tree",
    theme="academic",
    strict=True,
)

print(len(context.parsed.node_index))
print(len(validated.parsed.warnings))
```

If `strict=True` and the parser emits warnings, `validate_text(...)` raises `koala.ValidationError`.

### API Surface

Current public API:

- `koala.compile(path, **config)`: render `.txt` or `.docx` to SVG on disk
- `koala.compile_file(path, **config)`: explicit alias for `compile(...)`
- `koala.render_text(text, **config)`: render raw DSL to in-memory SVG
- `koala.safe_render_text(text, **config)`: render raw DSL with server-oriented limits
- `koala.compile_text(text, **config)`: legacy helper that renders raw DSL and writes SVG to disk
- `koala.export_text(text, format="svg"|"png"|"pdf", **config)`: export raw DSL to bytes
- `koala.safe_export_text(text, format="svg"|"png"|"pdf", **config)`: export raw DSL with server-oriented limits and no file writes
- `koala.export_file(path, format="svg"|"png"|"pdf", **config)`: export a source file to bytes
- `koala.save_text(text, output, **config)`: save raw DSL text as `.txt`
- `koala.inspect_text(text, **config)`: resolve `RenderContext` without writing output
- `koala.validate_text(text, **config)`: inspect and optionally fail on parser warnings
- `koala.available_document_types()`: return available document types
- `koala.available_typographies(type=None)`: return typography presets globally or by document type

All render, compile, inspect, validate, and export APIs accept:

- `type="tree"`
- `type="matrix"`
- `type="flowchart"`

The Python type alias `koala.DocumentType` also reflects those three values. If the DSL syntax does not match the requested type, Koala raises `koala.DocumentTypeMismatchError`. If the type is unknown, Koala raises `koala.UnknownDocumentTypeError`.

Common config kwargs:

- `type`
- `layout`
- `theme`
- `typography`
- `size`
- `text_align`
- `show_node_numbers`
- `background`
- `use_user_config`
- `user_config`

File-writing APIs also accept output controls such as `output`, `output_dir`, `desktop`, `base_dir`, and `output_name`, depending on the function.

### Safe Rendering For Servers

Use `safe_render_text(...)` or `safe_export_text(...)` when the source text comes from an LLM, user input, or an HTTP request.

Safe rendering currently accepts only:

- `type="tree"`
- `type="matrix"`

It deliberately rejects `flowchart` for now.

Default limits:

- `max_input_bytes=80000`
- `max_input_lines=800`
- `max_nodes=250`
- `max_warnings=0`

You can override those limits per call.

```python
import koala

try:
    export = koala.safe_export_text(
        generated_dsl,
        type="tree",
        layout="tree",
        format="svg",
        max_nodes=180,
    )
except koala.KoalaInputError as exc:
    # In FastAPI this is usually a 422 response.
    raise ValueError(str(exc))

print(export.media_type)
print(export.content)
```

`safe_export_text(...)` always returns bytes in memory. It does not accept `output`, so the server owns all storage and response handling.

## 4. User Config

Default config path:

```text
~/.config/koala/config.toml
```

Legacy fallback path:

```text
~/.koala.toml
```

Example:

```toml
[tool.koala]
default_layout = "tree"
default_theme = "academic"
default_typography = "default"
default_size = "a4_landscape"
default_text_align = "left"
default_show_node_numbers = false
default_output_mode = "next_to_input"
```

Config precedence for render settings:

1. explicit CLI flag or explicit Python kwarg
2. document metadata
3. user config default
4. built-in default

Output location is controlled by CLI flags, Python output kwargs, or user config. It is not controlled by document metadata.

## 5. Tree Documents

Use `type="tree"` for numbered hierarchical concept maps.

Smallest useful tree document:

```text
1 DSL Platform
Defines the main concept.

organizes -> 1.1 Core
Contains parser, models, and validation.

renders -> 1.2 Render
Generates SVG output.
```

Tree syntax:

- `1`, `2`, `3` are root nodes
- `1.1`, `1.2` are children of `1`
- `1.1.1` is a child of `1.1`
- body text is any non-empty line after a node header until the next node header
- relation labels are optional and appear before the node number as `label -> 1.1 Child`
- both `->` and `→` are accepted
- `0` can be used as an optional super-root

Example with relation labels:

```text
main:: 1 Biology
Study of life.

contains -> 1.1 Cell
Basic unit of life.

depends on -> 1.2 Genetics
Study of heredity.
```

Tree layouts:

- `tree`
- `synoptic`
- `synoptic_boxes`
- `radial`

## 6. Matrix Documents

Use `type="matrix"` for formal comparisons.

Smallest useful matrix document:

```text
matrix:: Format Comparison
columns:: Criterion | Tree | Matrix
row:: Best for | Hierarchical concept maps | Side-by-side evaluation
row:: Reading path | From parent to children | Across consistent criteria
footer:: Recommendation | Use matrix when the decision depends on comparing options.
```

Render it:

```bash
koala compile comparison.txt --type matrix --layout matrix --theme academic --typography formal
```

Matrix syntax:

- `matrix::` defines the title and is required
- `columns::` defines the header row and is required
- `row::` defines one comparison row; at least one row is required
- cells are separated with `|`
- `footer::` is optional and renders as a full-width conclusion row
- `@theme`, `@typography`, `@text-align`, `@size`, and `@background` work as document metadata

Matrix layout:

- `matrix`

## 7. Flowchart Documents

Use `type="flowchart"` for process diagrams, decision paths, and branching workflows.

Smallest useful flowchart document:

```text
flowchart:: Content publishing process

start:: draft :: Draft ready
decision:: review :: Approved?
step:: corrections :: Apply corrections
step:: design :: Design and layout
end:: published :: Published

draft -> review
review -> corrections :: no
review -> design :: yes
corrections -> draft
design -> published
```

Render it:

```bash
koala compile process.txt --type flowchart --layout flowchart --theme ocean
```

Flowchart syntax:

- `flowchart::` defines the title and is required
- nodes are declared with `<kind>:: <id>` or `<kind>:: <id> :: <label>`
- if `<label>` is omitted, the `<id>` is used as the label
- edges are declared with `<source_id> -> <target_id>` or `<source_id> -> <target_id> :: <label>`
- node ids are case-sensitive and must be unique
- `@theme`, `@typography`, `@text-align`, `@size`, and `@background` work as document metadata

Flowchart node kinds:

| Kind | Shape | Palette slot |
|---|---|---|
| `start` | rounded capsule | `main` |
| `end` | rounded capsule | `main` |
| `step` | rounded rectangle | `default` |
| `process` | rounded rectangle | `default` |
| `decision` | diamond | `focus` |
| `note` | rectangle with folded corner | `note` |

Flowchart layout:

- `flowchart`

## 8. Metadata

Koala supports optional document-level metadata with lines that start with `@`.

```text
@layout tree
@theme terracotta
@typography default
@text-align justify
@size square
@background #F7F4ED
@show-node-numbers false
```

Accepted metadata styles:

```text
@layout tree
@layout: tree
```

Supported metadata keys:

- `@layout`
- `@theme`
- `@typography`
- `@text-align`
- `@text_align`
- `@size`
- `@page-size`
- `@background`
- `@show-node-numbers`
- `@show_node_numbers`
- `@node-numbers`
- `@node_numbers`

Supported text alignment values:

- `left`
- `justify`

Accepted false-like values for node numbers:

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

## 9. Semantic Kinds

Tree nodes can use `kind::` before the node header:

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
- universal kinds are `note`, `warn`, and `soft`
- theme-owned kinds are `main`, `hl`, and `focus`

Universal kinds are defined once and then recolored by the active theme. Theme-owned kinds exist in every built-in theme, but each theme defines their exact treatment directly.

Flowchart node roles map to the same palette slots. For example, `decision` uses the `focus` tone, while `start` and `end` use `main`.

## 10. Layouts

Current layouts by document type:

| Document type | Layouts |
|---|---|
| `tree` | `tree`, `synoptic`, `synoptic_boxes`, `radial` |
| `matrix` | `matrix` |
| `flowchart` | `flowchart` |

### `tree`

Best for classic hierarchies, explanatory maps, and concept decomposition.

Characteristics:

- top-down
- adaptive parent widths
- relation labels preserved
- strong page-aware fitting

### `synoptic`

Best for category trees, grouped outlines, and compact classification charts.

Characteristics:

- left-to-right
- bracket connectors
- relation labels intentionally omitted

### `synoptic_boxes`

Best for left-to-right teaching diagrams and structured breakdowns.

Characteristics:

- left-to-right
- boxed nodes
- relation labels preserved

### `radial`

Best for mind maps and central-topic diagrams with balanced branches.

Characteristics:

- root in the center
- branch distribution by angular span
- overlap-aware radial separation

### `matrix`

Best for formal comparative tables, option evaluation, and executive summaries with consistent criteria.

Characteristics:

- table geometry
- theme-aware headers, row labels, body cells, and footer
- respects typography and `left` or `justify` alignment for body cells

### `flowchart`

Best for process diagrams, step-by-step workflows, and decision trees.

Characteristics:

- top-down layout with automatic depth assignment
- node shape reflects semantic role
- directed edges with arrowheads
- edge labels supported for branches

## 11. Themes

Themes apply to `tree`, `matrix`, and `flowchart` documents. All built-in themes support:

- universal kinds: `note`, `warn`, `soft`
- theme-owned kinds: `main`, `hl`, `focus`

Current built-in themes:

- `academic`
- `black`
- `colorblind`
- `default`
- `dusk`
- `frutal`
- `jungle`
- `minimal`
- `neon`
- `ocean`
- `pastel`
- `sepia`
- `terracotta`

Theme notes:

- `academic`: sober editorial palette for reports, notes, and formal teaching material
- `black`: grayscale, high-contrast output for print-friendly diagrams
- `colorblind`: accessible palette with strong color separation
- `default`: neutral technical look with warm highlights
- `dusk`: purple-toned palette for polished presentation material
- `frutal`: bright, playful, high-energy palette
- `jungle`: green and aqua palette for fresh, organic material
- `minimal`: restrained grayscale palette with a dark `focus` treatment
- `neon`: dark theme with electric cyan accents
- `ocean`: blue and teal palette for calm technical diagrams
- `pastel`: soft pink and muted presentation palette
- `sepia`: warm brown print-like palette
- `terracotta`: warm clay editorial palette

Inspect the live list from the CLI:

```bash
koala themes
```

Or from Python:

```python
from koala.render.shared.themes import available_theme_names

print(available_theme_names())
```

## 12. Typographies

Current typography presets:

- `default`
- `academic`
- `formal`
- `casual`
- `radial`

Preset availability by document type:

| Document type | Typographies |
|---|---|
| `tree` | `default`, `academic`, `formal`, `casual`, `radial` |
| `matrix` | `default`, `academic`, `formal`, `casual` |
| `flowchart` | `default`, `academic`, `formal`, `casual` |

Preset notes:

- `default`: general-purpose readable diagrams
- `academic`: serif body text for scholarly or editorial material
- `formal`: sober report-ready typography, default for `matrix`
- `casual`: friendlier workshop and draft style
- `radial`: compact typography tuned for the `radial` tree layout

Inspect typography lists:

```bash
koala typographies
koala typographies --type tree
koala typographies --type matrix
koala typographies --type flowchart
```

Python:

```python
import koala

print(koala.available_typographies())
print(koala.available_typographies(type="tree"))
print(koala.available_typographies(type="matrix"))
print(koala.available_typographies(type="flowchart"))
```

## 13. Page Sizes

Current page presets:

- `a4`
- `a4_landscape`
- `square`

### `a4`

Portrait A4, `210 x 297 mm`.

Best for:

- deeper trees
- tall linear flowcharts
- vertical reading rhythm

### `a4_landscape`

Landscape A4, `297 x 210 mm`.

Best for:

- most general-purpose diagrams
- `tree`
- `synoptic`
- `synoptic_boxes`
- `matrix`
- medium-width flowcharts

Current default page size:

- `a4_landscape`

### `square`

Square page, `210 x 210 mm`.

Best for:

- radial maps
- compact flowcharts
- shallow but wide trees

## 14. Practical Suggestions

General:

- keep titles short and concept-oriented
- move explanation into body text
- avoid extremely long paragraphs
- use relation labels only when they add meaning
- prefer balanced sibling groups over very uneven branching
- use metadata when a file is meant to be self-contained

Tree:

- use `tree` for classic hierarchies and explanatory branching
- use `synoptic` for classification charts where grouping matters more than relation labels
- use `synoptic_boxes` for structured left-to-right explanations
- use `radial` when a central concept has several balanced branches
- avoid more than 8 children in the deepest ring of a branch

Matrix:

- keep row labels short and criteria parallel
- prefer concise cell text over long prose
- use `formal` typography for reports and PDFs
- use `justify` only when cells have enough words to benefit from it

Flowchart:

- keep node labels short
- use one concept per node
- use `decision` for conditional choices
- use edge labels on decision outputs, such as `yes`, `no`, or short phrases
- use `note` for supporting context that is not a step in the flow
- avoid more than two outputs from a single decision node

## 15. Complete Examples

### Tree

```text
@layout tree
@theme terracotta
@size square
@show-node-numbers false

main:: 1 DSL Platform
Coordinates parser, layout, and render.

organizes -> 1.1 Core
Contains parsing, models, and validation.

renders -> 1.2 Render
Produces the final SVG output.

hl:: includes -> 1.2.1 Viewport
Fits the scene into the selected page size.
```

### Matrix

```text
@theme academic
@typography formal
@text-align left

matrix:: Koala Format Comparison
columns:: Criterion | Tree | Matrix | Flowchart
row:: Purpose | Knowledge hierarchies | Side-by-side comparison | Processes and decisions
row:: Reading path | General to specific | Horizontal and comparative | Chronological or conditional
footer:: Recommendation | Choose the document type that matches the structure of the source material.
```

### Flowchart

```text
@theme ocean
@typography default
@size a4_landscape

flowchart:: Content publishing process

start:: start :: Start
step:: review :: Review draft
decision:: approved :: Approved?
step:: corrections :: Apply corrections
step:: design :: Design and layout
decision:: quality :: Passes QA?
step:: adjustments :: Final adjustments
step:: publish :: Publish
note:: note :: Notify the team by email
end:: end :: End

start -> review
review -> approved
approved -> corrections :: no
approved -> design :: yes
corrections -> review
design -> quality
quality -> adjustments :: no
quality -> publish :: yes
adjustments -> design
publish -> note
note -> end
```

## 16. Files To Inspect

Useful repository files:

- `tests/end_to_end/mocks/alignment_left.txt`
- `tests/end_to_end/mocks/alignment_justify.txt`
- `tests/end_to_end/mocks/comparative_matrix.txt`
- `tests/end_to_end/mocks/flowchart.txt`
- `docs/syntax.md`
- `docs/layouts.md`
- `docs/how-to-add-a-typography.md`

Run the end-to-end gallery to compare themes, typographies, SVG, PNG, and PDF output:

```bash
.venv/bin/python -m unittest tests.end_to_end.code.test_render_e2e.RenderEndToEndTest.test_render_gallery
```

Generated gallery output is written under:

```text
tests/end_to_end/output/
```
