# Koala

Koala is a DSL for generating diagrams from structured text.

Write once, render in multiple layouts.

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
pip install koala-diagrams==1.2.1
```

Or with `pipx`:

```bash
pipx install koala-diagrams==1.2.1
```

## Usage

### CLI

```bash
koala compile docs/examples/tree.txt --layout tree
koala compile docs/examples/radial.txt --layout radial --theme jungle --size square
koala inspect docs/examples/tree.txt
koala validate docs/examples/radial.txt --strict
```

### Python

```python
import koala

file_result = koala.compile(
    "docs/examples/radial.txt",
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
```

Library API summary:

- `koala.compile(path, **config)` or `koala.compile_file(path, **config)`: source file to `.svg`
- `koala.render_text(text, **config)`: Koala DSL text to in-memory SVG via `result.svg`
- `koala.save_text(text, output, **config)`: raw Koala DSL text to `.txt`
- `koala.compile_text(text, **config)`: legacy helper that still writes `.svg` to disk

`RenderResult` now always includes the serialized SVG in `result.svg`. `result.output_svg` is only populated when the operation writes a file.

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
- [Examples](https://github.com/gabdiasalejandro/Koala/tree/main/docs/examples)

## Features

- Simple hierarchical DSL
- Multiple layouts (`tree`, `radial`, `synoptic`)
- Theme system
- CLI and Python API
- SVG output to disk or in memory

## Multiple Layouts

Tree, radial, and synoptic layouts from the same source.

![Radial example](https://raw.githubusercontent.com/gabdiasalejandro/Koala/main/docs/assets/example.radial.png)

## Philosophy

Koala is built around a simple idea:

The same source file should be able to drive multiple layouts and visual styles without rewriting the content.

## License

MIT
