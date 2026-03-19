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

result = koala.compile(
    "docs/examples/radial.txt",
    layout="radial",
    theme="academic",
    size="square",
)

print(result.output_svg)
```

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
- SVG output

## Multiple Layouts

Tree, radial, and synoptic layouts from the same source.

![Radial example](https://raw.githubusercontent.com/gabdiasalejandro/Koala/main/docs/assets/example.radial.png)

## Philosophy

Koala is built around a simple idea:

The same source file should be able to drive multiple layouts and visual styles without rewriting the content.

## License

MIT
