# Architecture

This document explains the current architecture of Koala as implemented in the codebase.
It is intentionally code-oriented: the goal is to describe what the system does now, not an aspirational design.

## Public entry points

Koala now exposes two top-level usage surfaces:

1. the installed CLI through `koala`
2. the library API through `import koala`, `koala.compile(path, **config)`, `koala.compile_file(path, **config)`, `koala.render_text(text, **config)`, `koala.save_text(text, output, **config)`, `koala.compile_text(text, **config)`, `koala.inspect_text(text, **config)`, and `koala.validate_text(text, **config)`

The public package entry files live in:

- `src/koala/__init__.py`
- `src/koala/__main__.py`
- `src/koala/api.py`
- `src/koala/cli.py`
- `src/koala/config.py`

## High-level pipeline

Koala transforms structured text into an SVG in seven steps:

1. `src/koala/api.py` or `src/koala/cli.py` collects explicit user inputs.
2. `src/koala/core/io.py` loads source text from `.txt` or `.docx`.
3. `src/koala/core/parser.py` converts raw text into a `ParsedDocument`.
4. `src/koala/layout/` turns the parsed node tree into a geometric `LayoutScene`.
5. `src/koala/render/context.py` combines metadata, user defaults, presets, layout, and viewport fitting into a `RenderContext`.
6. `src/koala/render/svg_render.py` builds an in-memory SVG document and delegates drawing to `src/koala/render/svg/`.
7. `src/koala/render/output.py` optionally resolves a filesystem target and persists the serialized SVG.

The strict separation is:

- `koala.core` understands the DSL and builds the semantic tree.
- `koala.layout` computes geometry only.
- `koala.render` applies presentation, page fitting, and SVG output.

## Main data structures

### `ConceptNode`

Defined in `src/koala/core/models.py`.

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

Also defined in `src/koala/core/models.py`.

Contains:

- `root_nodes`
- `node_index`
- `warnings`

The parser normalizes syntax and reconstructs the tree before any layout code runs.

### `LayoutBox`, `LayoutEdge`, `LayoutScene`

Defined in `src/koala/layout/models.py`.

These are the contract between layout and render:

- `LayoutBox`: a measured and positioned node
- `LayoutEdge`: an explicit connector polyline or line, with optional label geometry
- `LayoutScene`: the full positioned scene plus bounds

Render code never needs to know which layout engine produced the scene.

### `RenderSettings`, `ViewportTransform`, `RenderContext`

Defined in `src/koala/render/models.py`.

These complete the pipeline:

- `RenderSettings` resolves layout config, typography, and theme
- `ViewportTransform` scales/translates the scene into the final page
- `RenderContext` packages parsed content, scene, settings, and viewport

The same module also holds render-side style dataclasses such as:

- `NodeStyle` and `NodeStyleOverride`
- `ThemeDefinition` and `ThemeConfig`
- `RenderResult`
- `SvgRenderRequest`
- SVG drawing specs used by `src/koala/render/svg/`

## Folder responsibilities

### `src/koala/core/`

`koala.core` is responsible for input normalization and parsing:

- `io.py`: load `.txt` and `.docx`
- `models.py`: parser-side data structures
- `parser.py`: line parsing, parent reconstruction, warnings

Important property: no layout geometry is computed here.

### `src/koala/layout/`

`koala.layout` is the geometry layer:

- `models.py`: layout-side structures and shared configuration for geometry/text measurement
- `shared.py`: text measurement, wrapping, common gap rules, scene bounds
- `tree_layout.py`: vertical hierarchy layout
- `synoptic_boxes_layout.py`: column layout with boxed nodes
- `synoptic_layout.py`: bracket-based synoptic layout
- `radial_layout.py`: center-out radial layout
- `registry.py`: layout engine dispatch

Important property: layout code measures text and computes node/edge coordinates, but does not draw SVG.

Internal flow inside `koala.layout` is:

1. `registry.py` picks the engine by layout kind.
2. `shared.py` measures nodes and provides reusable spacing/bounds helpers.
3. the concrete engine computes box positions and connector geometry.
4. the engine returns a generic `LayoutScene`.

### `src/koala/render/`

`koala.render` translates the scene into the final document:

- `themes.py`: universal kinds and theme definitions
- `settings.py`: typographies, page presets, layout profiles, and resolved `RenderSettings`
- `models.py`: render-side style models, resolved settings, viewport, and SVG draw specs
- `context.py`: orchestration from parsed document metadata to `RenderContext`
- `output.py`: output-path resolution and optional persistence for serialized SVG output
- `viewport.py`: fit scene to page size
- `geometry.py`: small geometry helpers for rendering
- `svg_render.py`: public render entrypoint and pipeline execution
- `svg/`: SVG backend split by document, canvas, text, nodes, and edges

Important property: render code consumes `LayoutScene` as a generic scene, independent of layout internals.

### `src/koala/api.py` and `src/koala/config.py`

The high-level library surface lives in `src/koala/api.py`.

Current behavior:

- `koala.compile(path, **config)` and `koala.compile_file(path, **config)` are the file-to-SVG entrypoints
- `koala.render_text(text, **config)` renders raw Koala DSL to SVG in memory
- `koala.save_text(text, output, **config)` writes raw Koala DSL to a `.txt` file
- `koala.compile_text(text, **config)` is kept as a legacy helper that still writes SVG to disk
- `koala.inspect_text(text, **config)` resolves a `RenderContext` without writing output
- `koala.validate_text(text, **config)` also resolves a `RenderContext` and can raise `ValidationError` in strict mode
- it validates accepted config keys before rendering
- it can load user defaults through `src/koala/config.py`
- all render entrypoints now produce the final SVG string in memory first
- they return a `RenderResult` with `svg`, optional `output_svg`, and the resolved `RenderContext`
- `compile_text(...)` resolves relative outputs against `base_dir` when provided, otherwise against `Path.cwd()`
- explicit relative outputs for `compile_text(...)` are also resolved against `base_dir`
- output location is now controlled only by explicit args and external defaults, not by document metadata

`src/koala/config.py` is responsible for user-level defaults:

- default path: `~/.config/koala/config.toml`
- fallback path: `~/.koala.toml`
- supported defaults include layout, theme, typography, page size, text alignment, node numbers, and output policy

## Current render flow

The current render orchestration is:

1. `koala.compile(path, **config)`, `koala.render_text(text, **config)`, or `koala compile ...`
2. `koala.render.svg_render.render_svg(SvgRenderRequest(...))`
3. `koala.render.context.RenderContextBuilder.build(...)`
4. `koala.render.settings.RenderSettingsCatalog.resolve(...)`
5. `koala.layout.registry.build_layout(...)`
6. `koala.render.viewport.ViewportFitter.fit(...)`
7. `koala.render.svg.canvas.SvgCanvasRenderer.render(...)`
8. `svgwrite.Drawing.tostring()` serializes the SVG document in memory
9. when `persist_output=True`, `koala.render.output.RenderOutputResolver.resolve_svg_path(...)`
10. when `persist_output=True`, `koala.render.output.RenderOutputWriter.write_svg(...)`

This means the order is:

- resolve explicit inputs, metadata, and user defaults
- select presets
- build geometry
- fit geometry to paper
- draw SVG
- serialize SVG in memory
- optionally persist it to disk

Current precedence for render settings is:

1. explicit CLI flag or explicit library kwarg
2. document metadata
3. user config default
4. built-in default

## Shared measurement model

The common text and box measurement lives in `src/koala/layout/shared.py`.

Current behavior:

- text width is approximated with a deterministic internal heuristic
- node width depends on depth, but can grow to fit content
- nodes never allow a single word to overflow horizontally
- titles are wrapped with font-size fallback between `title_size_base` and `title_size_min`
- body text uses the body font and body leading directly

For `tree`, parent nodes can be remeasured after child widths are known, so the final text layout for those boxes is based on the final visible width, not the initial width.

## Viewport fitting

`src/koala/render/viewport.py` fits scene bounds into the usable page area through `ViewportFitter`.

Current behavior:

- all layouts can scale down to fit
- `tree` and `radial` can also scale up if the scene is smaller than the page
- `tree` and `radial` are centered on leftover free space
- `synoptic` and `synoptic_boxes` keep the more traditional fixed-to-page-origin behavior

## Typography and alignment

Typography is currently defined in `TypographyConfig` and resolved from `src/koala/render/settings.py`.

Theme composition now happens in `src/koala/render/themes.py`:

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

Current text measurement behavior:

- `src/koala/layout/shared.py` uses a heuristic width estimator instead of a native font engine
- the estimator now applies small per-font width factors for known fonts such as `Georgia`, `Trebuchet MS`, and `Verdana`
- wrapping also uses a small font-dependent safety padding, so the effective line width is slightly narrower than the box width
- this is especially important for the radial typography profile, where `Trebuchet MS` and `Verdana` can render slightly wider than the generic Helvetica-like approximation

The goal of those adjustments is not typographic exactness, but reducing right-edge overflow cases while keeping layout measurement deterministic and dependency-free.

## Why the architecture is structured this way

The practical benefits of the current split are:

- the parser can evolve without touching rendering math
- new layouts can reuse shared measurement code
- the SVG layer can change appearance without changing geometry engines
- presets can be swapped without modifying the core pipeline

This is the main architectural idea in Koala: semantic parsing, geometric layout, and visual rendering stay independent enough to evolve separately.
