# Architecture

This document explains the current architecture of Koala as implemented in the codebase.
It is intentionally code-oriented: the goal is to describe what the system does now, not an aspirational design.

## High-level pipeline

Koala transforms structured text into an SVG in five steps:

1. `core/io.py` loads source text from `.txt` or `.docx`.
2. `core/parser.py` converts raw text into a `ParsedDocument`.
3. `layout/` turns the parsed node tree into a geometric `LayoutScene`.
4. `render/context.py` combines metadata, presets, layout, and viewport fitting into a `RenderContext`.
5. `render/svg_render.py` runs the SVG pipeline and delegates drawing to `render/svg/`.

The strict separation is:

- `core` understands the DSL and builds the semantic tree.
- `layout` computes geometry only.
- `render` applies presentation, page fitting, and SVG output.

## Main data structures

### `ConceptNode`

Defined in `core/models.py`.

Represents one DSL node and stores:

- hierarchical number such as `1.2.3`
- title
- relation from parent
- semantic kind
- body paragraphs
- children
- parent reference

This is the semantic tree used by all layout engines.

### `ParsedDocument`

Also defined in `core/models.py`.

Contains:

- `root_nodes`
- `node_index`
- `warnings`

The parser normalizes syntax and reconstructs the tree before any layout code runs.

### `LayoutBox`, `LayoutEdge`, `LayoutScene`

Defined in `layout/models.py`.

These are the contract between layout and render:

- `LayoutBox`: a measured and positioned node
- `LayoutEdge`: an explicit connector polyline or line, with optional label geometry
- `LayoutScene`: the full positioned scene plus bounds

Render code never needs to know which layout engine produced the scene.

### `RenderSettings`, `ViewportTransform`, `RenderContext`

Defined in `render/models.py`.

These complete the pipeline:

- `RenderSettings` resolves layout config, typography, and theme
- `ViewportTransform` scales/translates the scene into the final page
- `RenderContext` packages parsed content, scene, settings, and viewport

The same module also holds render-side style dataclasses such as:

- `NodeStyle` and `NodeStyleOverride`
- `ThemeDefinition` and `ThemeConfig`
- `RenderResult`
- `SvgRenderRequest`
- SVG drawing specs used by `render/svg/`

## Folder responsibilities

### `core/`

`core` is responsible for input normalization and parsing:

- `io.py`: load `.txt` and `.docx`
- `models.py`: parser-side data structures
- `parser.py`: line parsing, parent reconstruction, warnings

Important property: no layout geometry is computed here.

### `layout/`

`layout` is the geometry layer:

- `models.py`: layout-side structures and shared configuration for geometry/text measurement
- `shared.py`: text measurement, wrapping, common gap rules, scene bounds
- `tree_layout.py`: vertical hierarchy layout
- `synoptic_boxes_layout.py`: column layout with boxed nodes
- `synoptic_layout.py`: bracket-based synoptic layout
- `radial_layout.py`: center-out radial layout
- `registry.py`: layout engine dispatch

Important property: layout code measures text and computes node/edge coordinates, but does not draw SVG.

Internal flow inside `layout/` is:

1. `registry.py` picks the engine by layout kind.
2. `shared.py` measures nodes and provides reusable spacing/bounds helpers.
3. the concrete engine computes box positions and connector geometry.
4. the engine returns a generic `LayoutScene`.

### `render/`

`render` translates the scene into the final document:

- `themes.py`: universal kinds and theme definitions
- `settings.py`: typographies, page presets, layout profiles, and resolved `RenderSettings`
- `models.py`: render-side style models, resolved settings, viewport, and SVG draw specs
- `context.py`: orchestration from parsed document metadata to `RenderContext`
- `output.py`: output-path resolution from explicit args, metadata, and external defaults
- `viewport.py`: fit scene to page size
- `geometry.py`: small geometry helpers for rendering
- `svg_render.py`: public render entrypoint and pipeline execution
- `svg/`: SVG backend split by document, canvas, text, nodes, and edges

Important property: render code consumes `LayoutScene` as a generic scene, independent of layout internals.

## Current render flow

The current render orchestration is:

1. `render.svg_render.render_svg(SvgRenderRequest(...))`
2. `render.context.RenderContextBuilder.build(...)`
3. `render.settings.RenderSettingsCatalog.resolve(...)`
4. `layout.registry.build_layout(...)`
5. `render.viewport.ViewportFitter.fit(...)`
6. `render.output.RenderOutputResolver.resolve_svg_path(...)`
7. `render.svg.canvas.SvgCanvasRenderer.render(...)`

This means the order is:

- select presets
- build geometry
- fit geometry to paper
- draw SVG

## Shared measurement model

The common text and box measurement lives in `layout/shared.py`.

Current behavior:

- text width is approximated with a deterministic internal heuristic
- node width depends on depth, but can grow to fit content
- nodes never allow a single word to overflow horizontally
- titles are wrapped with font-size fallback between `title_size_base` and `title_size_min`
- body text uses the body font and body leading directly

For `tree`, parent nodes can be remeasured after child widths are known, so the final text layout for those boxes is based on the final visible width, not the initial width.

## Viewport fitting

`render/viewport.py` fits scene bounds into the usable page area through `ViewportFitter`.

Current behavior:

- all layouts can scale down to fit
- `tree` and `radial` can also scale up if the scene is smaller than the page
- `tree` and `radial` are centered on leftover free space
- `synoptic` and `synoptic_boxes` keep the more traditional fixed-to-page-origin behavior

## Typography and alignment

Typography is currently defined in `TypographyConfig` and resolved from `render/settings.py`.

Theme composition now happens in `render/themes.py`:

- universal kind styles are defined once
- current universal kinds are `note`, `warn`, and `soft`
- each theme contributes a base `default_node`
- each built-in theme defines three theme-owned kinds: `main`, `hl`, and `focus`
- theme-specific kind overrides are merged on top of the universal ones

The result is a resolved `ThemeConfig` consumed by the SVG renderer.

`main` is intended mainly for the root node. In boxed layouts, when the root uses `main::`, the SVG node renderer applies a thicker border to reinforce the hierarchy visually.

Current text alignment behavior:

- default node text alignment is `left`
- `justify` remains available through document metadata such as `@text-align justify`
- justified lines in SVG are implemented by distributing space between words, not by stretching characters
- the last line of a text block remains left-aligned

Alignment can be overridden from document metadata and is applied before layout measurement, so wrapping stays consistent with the final render.

## Why the architecture is structured this way

The practical benefits of the current split are:

- the parser can evolve without touching rendering math
- new layouts can reuse shared measurement code
- the SVG layer can change appearance without changing geometry engines
- presets can be swapped without modifying the core pipeline

This is the main architectural idea in Koala: semantic parsing, geometric layout, and visual rendering stay independent enough to evolve separately.
