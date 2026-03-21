# DSL Syntax

This document describes the current syntax accepted by Koala and how the parser interprets it.

## Supported input files

Koala currently accepts:

- `.txt`
- `.docx`

The loader lives in `src/koala/core/io.py`.

After loading, both formats become plain text and are parsed the same way.

## Conceptual model

Each node in the DSL has:

- a hierarchical number
- a title
- an optional relation from its parent
- an optional semantic kind
- optional body text lines

The parser turns that into a `ConceptNode`.

## Node line syntax

The current parser accepts node headers with this structure:

```text
[kind::] [relation ->] number title
```

Examples:

```text
1 Main Concept
contains -> 1.1 Child Node
hl:: 1.2 Highlighted Node
hl:: organizes -> 1.3 Semantic Child
```

Important details:

- `kind::` is optional
- relation is optional
- both `->` and `→` are accepted
- `number` must be hierarchical numeric notation such as `1`, `1.2`, or `3.4.5`
- everything after the number is treated as the node title

## Hierarchical numbering rules

The current numbering rules are:

- `1`, `2`, `3` are top-level roots
- `1.1` is a child of `1`
- `1.1.1` is a child of `1.1`
- `0` can be used as an optional super-root

If `0` exists:

- first-level numbered nodes such as `1`, `2`, `3` become children of `0`

If `0` does not exist:

- first-level numbered nodes remain independent roots

## Body text syntax

Any non-empty line after a node header is treated as body text for the current node until another valid node header appears.

Example:

```text
1 Cell
The cell is the basic unit of life.
It can be prokaryotic or eukaryotic.

1.1 Membrane
Defines the boundary of the cell.
```

This produces:

- node `1` with two body lines
- node `1.1` with one body line

Internally, body lines are stored as paragraphs and later joined with spaces for layout measurement and rendering.

## Semantic kinds

Kinds are declared with the `kind::` prefix:

```text
main:: 1 Root Topic
hl:: 1 Important Concept
note:: 1 Supporting Note
focus:: 1.1 Main Takeaway
```

Current behavior:

- kinds are normalized to lowercase
- if no kind is present, the parser stores `default`
- themes can style nodes by kind at render time

Current built-in kinds are:

- universal kinds: `note`, `warn`, `soft`
- theme-owned kinds: `main`, `hl`, `focus`

Universal kinds are declared once and then recolored by the active theme.
Theme-owned kinds are also supported across built-in themes, but each theme defines their visual treatment explicitly.

`main` is intended primarily for the diagram root. In boxed layouts, if the root node uses `main::`, the renderer also draws it with a thicker border.

## Relations

Relation text appears before the node number:

```text
depends on -> 1.2 Dependency
```

Current behavior:

- the relation is stored as `relation_from_parent`
- relation labels are rendered in layouts that support them
- `synoptic` intentionally suppresses relation labels even if they exist

If no relation is declared:

- the parent-child link still exists
- the connector is considered implicit

## Metadata syntax

Koala now supports optional document metadata using lines that start with `@`.

Current accepted forms are:

```text
@layout tree
@theme terracotta
@typography default
@text-align justify
@size square
@background #F7F4ED
@show-node-numbers false
```

or:

```text
@layout: tree
@theme: terracotta
```

Current behavior:

- metadata keys are normalized to lowercase
- metadata lines can appear in the document without breaking node parsing
- duplicate metadata keys overwrite the previous value and generate a warning
- metadata is optional

### Current metadata keys

The parser currently accepts metadata for the CLI-related render options:

- `@layout`
- `@theme`
- `@typography`
- `@size`
- `@page-size`
- `@background`
- `@text-align`
- `@show-node-numbers`

`@text_align`, `@show_node_numbers`, `@node-numbers`, `@node_numbers`, `@background-color`, and `@background_color` are also accepted as aliases.

For text alignment, accepted values are:

- `left` (default)
- `justify`

For background, pass a hex color such as `#F7F4ED`. If omitted, Koala keeps the current default behavior and does not add an explicit page background.

### Precedence

Current resolution order is:

1. explicit CLI flag or explicit library kwarg
2. document metadata
3. user config default
4. built-in default

This means metadata is useful for shipping self-describing visual examples, while still allowing the CLI or the library call to override them when needed.

Output location is not resolved from metadata anymore. Use explicit CLI or library output options, or user config defaults.

### Controlling node numbers

By default Koala hides node-number pills in the final map.

You can enable or disable them in metadata when a document really needs that behavior embedded:

```text
@show-node-numbers true
```

Accepted false-like values include:

- `false`
- `no`
- `off`
- `hide`
- `hidden`
- `0`

## Parsing order and tree reconstruction

The parser works in two main phases:

### Phase 1: create nodes

For every valid node header line:

- extract `kind`
- extract optional relation
- extract number
- extract title
- create or replace a `ConceptNode`

### Phase 2: rebuild the hierarchy

After all nodes are read:

- parent numbers are inferred from the hierarchical number
- if `0` exists, first-level nodes attach to `0`
- children are appended to their resolved parent
- unresolved parents generate warnings and the node becomes a root

## Current warnings

The parser emits warnings for the following situations:

- duplicate node number
- text found before the first node
- missing parent
- missing intermediate levels such as `1.2` missing before `1.2.1`
- long title: more than 10 words
- long body: more than 100 words
- many children: more than 7 children

Warnings do not stop rendering; they are advisory.

## Current limitations of the syntax

The current grammar is intentionally simple.

Important limitations:

- there is no inline attribute syntax beyond `kind::`
- there is no explicit multi-relation graph syntax outside tree numbering
- body text is plain text, not rich Markdown
- node titles and bodies are inferred from line positions rather than explicit blocks

## Minimal valid example

```text
1 Platform
Defines the main idea.

organizes -> 1.1 Core
Contains parser, models, and validation.

renders -> 1.2 Render
Produces the final SVG output.
```

## Example with optional super-root

```text
0 Biology
The global topic.

1 Cell
The basic unit of life.

2 Genetics
Study of heredity.
```

Current interpretation:

- `0` is the only root
- `1` and `2` become its children

## Example with metadata

```text
@layout tree
@theme terracotta
@size square
@show-node-numbers false

1 DSL Platform
Coordinates parser, layout, and render.
```

## CLI-related syntax knobs

The DSL itself is independent from the CLI, but the parser/output flow is normally exercised through:

```bash
./.venv/bin/koala compile docs/examples/tree.txt --layout tree
./.venv/bin/koala compile docs/examples/tree.txt --layout synoptic
./.venv/bin/koala compile docs/examples/tree.txt --layout synoptic_boxes
./.venv/bin/koala compile docs/examples/radial.txt --layout radial
./.venv/bin/koala compile docs/examples/tree.txt --layout tree --size a4
./.venv/bin/koala compile docs/examples/tree.txt --layout tree --size a4_landscape
./.venv/bin/koala compile docs/examples/tree.txt --layout tree --size square
```

Useful parser-related flags:

- `--input`: choose `.txt` or `.docx`
- `--layout`: choose how the parsed tree is converted into geometry
- `--size`: choose the target page geometry used by layout fitting and SVG output

### Current page size options

The current CLI supports three page presets:

- `a4`: portrait A4, `210 x 297 mm`
- `a4_landscape`: landscape A4, `297 x 210 mm`
- `square`: square page, currently `210 x 210 mm`

Current behavior:

- `a4_landscape` is the default
- the page preset does not change DSL parsing
- it changes the page dimensions seen by the layout engine and by the viewport
- `tree` and `radial` currently take the most advantage of the new aspect ratio
- `synoptic` and `synoptic_boxes` already render on the selected page size, but do not yet have dedicated geometry heuristics for portrait or square layouts

## Authoring tips for better visuals

These are writing suggestions for the current engines, not hard syntax rules.

### General

- Keep titles short and move explanation into body text
- Prefer compact paragraphs over long prose blocks
- Use relations only when they add real semantic value
- Use metadata when the file is intended for a specific layout, theme, or page size

### `tree`

- Works best with classic hierarchies and explanatory branches
- Keep sibling titles compact when a parent has many children
- `a4_landscape` is the safest default
- `square` often improves shallow but wide trees
- `a4` is useful for deeper trees with more vertical rhythm

### `synoptic`

- Works best for category refinement and outline-like structures
- Prefer short titles and very light body text
- `a4_landscape` is currently the safest page size
- `square` and `a4` are already supported, but there is no dedicated aspect-ratio optimization yet

### `synoptic_boxes`

- Works best with parallel sibling groups and moderate text density
- Prefer short or medium bodies, not large paragraphs
- `a4_landscape` is currently the safest page size
- `square` already works, but content should stay tighter because there is no special compaction pass yet

### `radial`

- Works best when first-level branches are relatively balanced
- A short root title plus balanced branches usually gives the cleanest result
- `square` and `a4_landscape` usually give the best radial balance
- Relation labels now work best when they stay sparse and short; the renderer cuts the edge around the label instead of letting the line pass underneath

### Page-size-specific suggestions

- `a4`: better for taller structures and deeper trees
- `a4_landscape`: best general-purpose option and current default
- `square`: best when you want a denser, more centered composition

If page size is not specified explicitly:

- Koala does not auto-pick a page size from layout shape or content density
- precedence is CLI/library argument, then metadata, then user config, then the internal default
- the internal fallback remains `a4_landscape`

## Summary

The current DSL is line-based, hierarchical, and intentionally small:

- numbering defines structure
- optional relation text defines connector labels
- optional `kind::` defines semantic styling
- following lines become node body text

That simplicity is what allows the same input to be rendered by multiple layout engines without changing the source file.
