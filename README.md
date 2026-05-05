# Koala

Koala is a DSL for generating diagrams from structured text.

Write once, render as trees, radial maps, synoptic layouts, or formal comparison matrices.

[GitHub Repository](https://github.com/gabdiasalejandro/Koala)
[Español](https://github.com/gabdiasalejandro/Koala/blob/main/README.es.md)

## Quick Example

Write this:

```text
@theme jungle

main:: 1 Biology
Study of life.

hl:: contains -> 1.1 Cell
Basic unit of life.

1.2 Genetics
Study of heredity.
```

Then run:

```bash
koala compile example.txt --layout tree
```

## Result

![Koala diagram example](https://raw.githubusercontent.com/gabdiasalejandro/Koala/main/docs/assets/example.tree.png)

## Installation

Install from PyPI:

```bash
pip install koala-diagrams
```

Or with `pipx`:

```bash
pipx install koala-diagrams
```

## Usage

### CLI

```bash
koala types
koala compile docs/examples/tree.txt --type tree --layout tree
koala compile docs/examples/radial.txt --type tree --layout radial --theme jungle --size square
koala compile comparison.txt --type matrix --layout matrix --typography formal
koala export docs/examples/tree.txt --format png --quality high
koala export comparison.txt --type matrix --layout matrix --format png --quality medium
koala export docs/examples/tree.txt --format pdf --quality high
koala inspect docs/examples/tree.txt
koala validate docs/examples/radial.txt --strict
```

### Python

```python
import koala

file_result = koala.compile(
    "docs/examples/radial.txt",
    type="tree",
    layout="radial",
    theme="academic",
    size="square",
)

svg_result = koala.render_text(
    """
    1 Central Topic
    Main explanation.

    1.1 First Branch
    Supporting detail.
    """,
    type="tree",
    layout="tree",
    theme="frutal",
)

source_path = koala.save_text(
    "1 Root\nBody.\n",
    "docs/examples/inline_demo",
)

print(file_result.output_svg)
print(svg_result.svg)
print(source_path)

png_result = koala.export_text(
    "main:: 1 Central Topic\nMain explanation.\n",
    type="tree",
    format="png",
    quality="high",
    layout="tree",
    theme="frutal",
)

pdf_result = koala.export_text(
    "main:: 1 Central Topic\nMain explanation.\n",
    type="tree",
    format="pdf",
    quality="high",
    layout="tree",
    theme="frutal",
)

print(png_result.media_type, len(png_result.content))
print(pdf_result.media_type, len(pdf_result.content))
```

Matrix documents use an explicit comparative-table syntax:

```text
matrix:: Format Comparison
columns:: Criterion | Tree | Matrix
row:: Best for | Hierarchical concept maps | Side-by-side evaluation
row:: Reading path | From parent to children | Across consistent criteria
footer:: Recommendation | Use matrix when the decision depends on comparing options.
```

Render it with:

```bash
koala compile comparison.txt --type matrix --layout matrix --theme academic --typography formal
koala export comparison.txt --type matrix --layout matrix --format pdf --quality high
```

Library API summary:

- `koala.compile(path, **config)` or `koala.compile_file(path, **config)`: source file to `.svg`
- `koala.render_text(text, **config)`: Koala DSL text to in-memory SVG via `result.svg`
- `koala.export_text(text, format="svg"|"png"|"pdf", **config)`: Koala DSL text to in-memory export bytes via `result.content`
- `koala.export_file(path, format="svg"|"png"|"pdf", **config)`: source file to in-memory export bytes
- `koala.save_text(text, output, **config)`: raw Koala DSL text to `.txt`
- `koala.compile_text(text, **config)`: legacy helper that still writes `.svg` to disk

`RenderResult` now always includes the serialized SVG in `result.svg`. `result.output_svg` is only populated when the operation writes a file.
`ExportResult` includes final bytes in `result.content`, the HTTP media type in `result.media_type`, and `result.output_path` when an explicit output is written.
PNG export uses direct SVG conversion at `medium` or `high` quality. PDF export is vector-based and adds a professional frame with margins, a title resolved from the first `main::` node, and theme-aware colors.
All render/export APIs accept `type="tree"` or `type="matrix"`; it defaults to `tree`. Tree layouts are `tree`, `radial`, `synoptic`, and `synoptic_boxes`. Matrix uses `layout="matrix"`. If DSL syntax does not match the requested type, Koala raises `DocumentTypeMismatchError`.

In general, avoid embedding `@show-node-numbers` in document metadata. Prefer CLI flags, library arguments, or user config defaults unless a file really needs to be self-descriptive about numbering.

## DSL Syntax

Koala uses a simple line-based DSL:

```text
[kind::] [relation ->] number title
```

Example:

```text
1 Main Concept
contains -> 1.1 Child Node
hl:: 1.2 Highlighted Node
```

- [Full syntax guide](https://github.com/gabdiasalejandro/Koala/blob/main/docs/syntax.md)
- [Authoring tutorial](https://github.com/gabdiasalejandro/Koala/blob/main/docs/tutorial.md)
- [How to add a typography](https://github.com/gabdiasalejandro/Koala/blob/main/docs/how-to-add-a-typography.md)
- [Examples](https://github.com/gabdiasalejandro/Koala/tree/main/docs/examples)
- [LLM prompts](https://github.com/gabdiasalejandro/Koala/tree/main/docs/prompts)

## Features

- Simple hierarchical DSL
- Multiple tree layouts (`tree`, `radial`, `synoptic`, `synoptic_boxes`)
- Formal comparative matrices with `type="matrix"`
- Theme system
- CLI and Python API
- SVG output to disk or in memory
- In-memory SVG, PNG, and decorated PDF export

## Multiple Layouts

Tree, radial, and synoptic layouts from the same hierarchical source. Matrix documents use a separate table-oriented source and the same theme/export system.

![Radial example](https://raw.githubusercontent.com/gabdiasalejandro/Koala/main/docs/assets/example.radial.png)

## Philosophy

Koala is built around a simple idea:

The same source file should be able to drive multiple layouts and visual styles without rewriting the content.

## License

MIT
