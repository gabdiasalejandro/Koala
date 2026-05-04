# Architecture

Koala is organized by layers first and document types second.

The project has three main implementation layers:

- `core/`: source loading, document type registry, parser models, parsers, and pipelines
- `layout/`: layout contracts, measurement helpers, and geometry engines
- `render/`: render settings, themes, viewport fitting, SVG drawing, output writing, and export conversion

Inside each layer, type-specific code lives in a folder named after the document
type. Shared code lives in `shared/`.

## Public entry points

The public package entry files are:

- `src/koala/__init__.py`
- `src/koala/__main__.py`
- `src/koala/api.py`
- `src/koala/cli.py`
- `src/koala/config.py`

The main library entrypoints are:

- `koala.compile(path, **config)` / `koala.compile_file(path, **config)`
- `koala.render_text(text, **config)`
- `koala.export_text(text, **config)` / `koala.export_file(path, **config)`
- `koala.save_text(text, output, **config)`
- `koala.compile_text(text, **config)`
- `koala.inspect_text(text, **config)`
- `koala.validate_text(text, **config)`

## Document type policy

The caller chooses the document type explicitly through the API or CLI:

- Python: `koala.render_text(text, type="tree")`
- CLI: `koala compile input.txt --type tree`

Koala does not infer document type from metadata. If the caller requests
`type="tree"` and sends matrix-like syntax, the selected pipeline raises
`DocumentTypeMismatchError`.

Current supported type:

- `tree`

Prepared future types:

- `matrix`
- `flowchart`

## Target folder shape

The intended scalable shape is:

```text
src/koala/
├── core/
│   ├── shared/
│   ├── tree/
│   ├── matrix/
│   └── flowchart/
├── layout/
│   ├── shared/
│   ├── tree/
│   ├── matrix/
│   └── flowchart/
└── render/
    ├── shared/
    ├── tree/
    ├── matrix/
    └── flowchart/
```

## Core layer

`src/koala/core/shared/` owns cross-type core services:

- `io.py`: load `.txt` and `.docx`
- `types.py`: `DocumentType` and the default document type
- `errors.py`: document-type errors
- `registry.py`: `DocumentPipelineRegistry`

`src/koala/core/tree/` owns tree semantics:

- `models.py`: `ConceptNode`, `ParsedDocument`, parser warnings, metadata
- `parser.py`: numbered tree DSL parser
- `pipeline.py`: `TreeDocumentPipeline`

`src/koala/core/matrix/` and `src/koala/core/flowchart/` are intentionally
present as placeholders. Their future parsers, models, and pipelines should be
added there.

## Layout layer

`src/koala/layout/shared/` owns layout contracts and deterministic measurement:

- `models.py`: `LayoutBox`, `LayoutEdge`, `LayoutScene`, `LayoutConfig`, `TypographyConfig`
- `measurement.py`: text measurement, wrapping, spacing helpers, scene bounds

`src/koala/layout/tree/` owns tree-only geometry engines:

- `registry.py`: tree layout dispatch
- `tree.py`: top-down hierarchy
- `synoptic.py`: bracket-based synoptic layout
- `synoptic_boxes.py`: boxed synoptic layout
- `radial.py`: center-out radial layout

`src/koala/layout/matrix/` and `src/koala/layout/flowchart/` are placeholders
for future geometry engines.

## Render layer

`src/koala/render/shared/` owns cross-type render infrastructure:

- `models.py`: `RenderResult`, `ExportResult`, `RenderContext`, styles, SVG specs
- `settings.py`: page sizes, typography presets, layout profiles
- `themes.py`: built-in themes and universal style kinds
- `context.py`: shared metadata/settings resolution and generic `RenderContext` assembly
- `viewport.py`: fit a layout scene into a page
- `output.py`: SVG output-path resolution and persistence
- `export.py`: SVG/PNG/PDF conversion from a canonical SVG
- `geometry.py`: small geometry helpers used by SVG renderers
- `svg/document.py`: shared SVG document factory
- `svg/text.py`: shared SVG text renderer

`src/koala/render/tree/` owns tree-only SVG rendering:

- `context.py`: tree render context construction
- `svg_render.py`: tree SVG pipeline
- `canvas.py`: tree canvas orchestration
- `nodes.py`: tree node drawing
- `edges.py`: tree edge drawing

`src/koala/render/matrix/` and `src/koala/render/flowchart/` are placeholders
for future renderers.

## Tree render flow

For the current `tree` type, the concrete flow is:

1. `koala.api` or `koala.cli` receives explicit inputs.
2. `koala.core.shared.io.load_input_text(...)` loads source text.
3. `koala.core.shared.registry.DocumentPipelineRegistry.require(...)` selects the pipeline.
4. `koala.core.tree.pipeline.TreeDocumentPipeline.parse(...)` validates and parses tree DSL.
5. `koala.render.tree.svg_render.render_tree_svg(...)` starts the tree SVG pipeline.
6. `koala.render.tree.context.TreeRenderContextBuilder.build(...)` resolves settings and tree layout.
7. `koala.render.shared.context.RenderSettingsResolver.resolve(...)` applies config precedence.
8. `koala.layout.tree.registry.build_tree_layout_scene(...)` builds tree geometry.
9. `koala.render.shared.context.RenderContextBuilder.build(...)` fits the viewport.
10. `koala.render.tree.canvas.SvgCanvasRenderer.render(...)` draws the tree SVG.
11. `svgwrite.Drawing.tostring()` serializes SVG in memory.
12. `koala.render.shared.output.RenderOutputWriter.write_svg(...)` persists only when requested.

`RenderResult` contains:

- `svg`: final canonical SVG string
- `output_svg`: optional path when the SVG was persisted
- `context`: resolved render context
- `document_type`: currently `"tree"`
- `title`: generic title used by shared surfaces such as PDF export

## Export flow

Export starts after the canonical SVG exists:

1. `koala.export_text(...)`, `koala.export_file(...)`, or `koala export ...`
2. render with `persist_output=False`
3. `koala.render.shared.export.ExportConverter.convert(...)`
4. for `svg`, return UTF-8 SVG bytes
5. for `png`, call CairoSVG against the canonical SVG at medium or high quality
6. for `pdf`, build a decorated outer SVG using shared theme/settings metadata,
   then call CairoSVG PDF conversion

PNG export is intentionally plain: it reflects the canonical SVG exactly.

PDF export is intentionally decorated: it adds margins, a title, a subtle
header, and a theme-aware page frame suitable for sending to a client.

## Configuration precedence

Current precedence for render settings is:

1. explicit CLI flag or explicit library kwarg
2. document metadata
3. user config default
4. built-in default

Document type is different: it is controlled by explicit API/CLI `type` and
defaults to `tree`; metadata does not select document type.

## Adding `matrix`

To add `matrix`, fill the placeholders instead of modifying tree internals:

```text
src/koala/core/matrix/
src/koala/layout/matrix/
src/koala/render/matrix/
```

Then:

1. add matrix models/parser/pipeline in `core/matrix/`
2. add matrix layout contracts/engines in `layout/matrix/`
3. add matrix SVG rendering in `render/matrix/`
4. register the pipeline in `core/shared/registry.py`
5. add `"matrix"` to `core/shared/types.py`
6. make the pipeline reject incompatible DSL through `DocumentTypeMismatchError`
7. return `RenderResult(document_type="matrix", title=...)`
8. reuse `render/shared/export.py` for SVG, PNG, and PDF

`flowchart` should follow the same pattern.
