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

- `models.py`: `TreeLayoutKind` (the closed set of layouts supported by `tree`)
- `registry.py`: tree layout dispatch
- `tree.py`: top-down hierarchy
- `synoptic.py`: bracket-based synoptic layout
- `synoptic_boxes.py`: boxed synoptic layout
- `radial.py`: center-out radial layout

`src/koala/layout/matrix/` and `src/koala/layout/flowchart/` are placeholders
for future geometry engines.

### Layout kinds are scoped per document type

There is no global `LayoutKind` enum. Each document type defines its own in
`koala.layout.<type>.models` (e.g. `TreeLayoutKind`, future `MatrixLayoutKind`,
`FlowchartLayoutKind`). The shared layout/render layers treat layout
identifiers as opaque `str` and delegate validation to the registry of the
owning type. This keeps layout names from one type out of another type's
surface area.

## Render layer

`src/koala/render/shared/` owns cross-type render infrastructure:

- `models.py`: `RenderResult`, `ExportResult`, `RenderContext`, styles, SVG specs
- `settings.py`: page sizes, `RenderProfile`, `RenderProfileCatalog`, settings resolution
- `themes.py`: built-in themes and universal style slots
- `context.py`: shared metadata/settings resolution and generic `RenderContext` assembly
- `viewport.py`: fit a layout scene into a page
- `output.py`: SVG output-path resolution and persistence
- `export.py`: SVG/PNG/PDF conversion from a canonical SVG
- `geometry.py`: small geometry helpers used by SVG renderers
- `svg/document.py`: shared SVG document factory
- `svg/text.py`: shared SVG text renderer

`src/koala/render/tree/` owns tree-only SVG rendering:

- `profiles.py`: registers tree's `RenderProfile`s and typographies on import
- `context.py`: tree render context construction
- `svg_render.py`: tree SVG pipeline
- `canvas.py`: tree canvas orchestration
- `nodes.py`: tree node drawing
- `edges.py`: tree edge drawing

`src/koala/render/matrix/` and `src/koala/render/flowchart/` are placeholders
for future renderers.

### Profile registration

`render/shared/settings.py` does not enumerate any layout names or typography
names. Each document type registers its presets in `render/<type>/profiles.py`
through `RenderProfileCatalog.register_profile(...)` and
`register_typography(...)`. The package's `__init__.py` imports `profiles` so
the registration happens automatically on first import of the type's render
package.

This means `RenderSettingsCatalog.resolve(layout_kind, document_type=...)`
works without shared code knowing anything about tree, matrix, or flowchart
layouts.

## Themes, palette slots, and node roles

Themes define colors at three levels. The vocabulary is stable across document
types so a single theme produces a coherent identity in trees, matrices, and
flowcharts.

### Universal palette slots

`render/shared/themes.py` exposes a small set of universal style slots that
every theme must support. Today these are exposed via `UNIVERSAL_KIND_STYLES`
and the per-theme `kind_overrides`:

- `note`, `warn`, `soft` — universal annotation slots
- `main`, `hl`, `focus` — universal emphasis slots

A theme is responsible for picking concrete fill/stroke/title/body colors for
each slot. Renderers ask the theme for a slot (`theme.style_for("focus")`) and
get a fully resolved `NodeStyle`. Slots are the cross-type contract.

### Document-type kinds (current, tree-only)

In the current `tree` parser, the DSL accepts a `kind::` prefix (`focus::`,
`main::`, `note::`, …) that maps 1:1 to a palette slot. So in `tree`, a "kind"
is just a direct user-facing name for a slot.

### Roles (target model for non-tree types)

`flowchart` and other graph-like types will introduce **node roles**: semantic
labels driven by the DSL or topology, not by author intent on a single node.
Examples:

- `flowchart`: `start`, `end`, `process`, `decision`, `data`
- `matrix`: `header`, `cell`, `footer`

Each type defines its own role enum and a **role-to-slot mapping**. The
mapping is the only place a type couples its semantics to the shared palette:

```
flowchart role "decision"  →  palette slot "focus"
flowchart role "process"   →  palette slot (default node)
flowchart role "data"      →  palette slot "soft"
```

Why this split:

- **Slots stay shared.** A user who picks `terracotta` gets the same five-color
  identity in every type. Themes don't need to know which roles exist.
- **Roles stay local.** A flowchart's "decision" doesn't pollute the tree
  parser; a matrix's "header" doesn't need a slot of its own.
- **Re-skinning is free.** Changing the role-to-slot map for flowchart only
  changes which existing palette tone applies to decisions; no new color
  picking required.

### Where this lives in code

- Slots: `render/shared/themes.py` (`UNIVERSAL_KIND_STYLES`,
  `ThemeDefinition.kind_overrides`, `ThemeConfig.style_for(slot)`).
- Tree's "kind" today: parsed in `core/tree/parser.py`, used directly as a
  slot name.
- Future role-to-slot mapping: each type owns a small dict (e.g.
  `render/flowchart/roles.py`) and consults `ThemeConfig.style_for(slot)`.

Until a non-tree type lands, no code-level role layer is implemented; tree
keeps using its `kind::` syntax.

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

## Adding a new document type

Use this contract when adding `matrix`, `flowchart`, or any future type. Fill
the placeholders; do not modify tree internals.

```text
src/koala/core/<type>/
src/koala/layout/<type>/
src/koala/render/<type>/
```

### Required modules

- `core/<type>/models.py` — domain models (analogue of `ConceptNode`,
  `ParsedDocument`).
- `core/<type>/parser.py` — DSL parser producing those models.
- `core/<type>/pipeline.py` — implementation of the document pipeline
  protocol expected by `koala.core.shared.registry.DocumentPipelineRegistry`.
  Today, `tree` exposes:
  - `type_name: str`
  - `supported_layouts: tuple[str, ...]`
  - `parse(source_text) -> ParsedDocument`
  - `resolve_output_file_name(parsed, *, stem, layout, user_config) -> str`
  - `render_text(...) -> RenderResult`
  - `render_parsed(...) -> RenderResult`
  - `inspect_text(...) -> RenderContext`
- `layout/<type>/models.py` — type-scoped `<Type>LayoutKind` literal.
- `layout/<type>/registry.py` — exports `<TYPE>_LAYOUTS: tuple[str, ...]` and
  a builder `build_<type>_layout_scene(layout_kind, parsed, config, typography) -> LayoutScene`.
- `render/<type>/profiles.py` — registers a `RenderProfile` per layout via
  `RenderProfileCatalog.register_profile("<type>", layout_kind, profile)` and
  any type-specific typographies via `register_typography(...)`. Imported
  eagerly from `render/<type>/__init__.py`.
- `render/<type>/svg_render.py` — entry point that builds the SVG given an
  `SvgRenderRequest` and returns a `RenderResult`.

### Wiring

1. register the pipeline in `core/shared/registry.py`.
2. add `"<type>"` to `core/shared/types.py`.
3. import `koala.render.<type>` from somewhere reachable so its profiles get
   registered (currently `koala.render.__init__.py` does this transitively
   for tree).
4. make the pipeline reject incompatible DSL through `DocumentTypeMismatchError`.
5. return `RenderResult(document_type="<type>", title=...)`.
6. reuse `render/shared/export.py` for SVG, PNG, and PDF — the export layer is
   type-agnostic.

### Roles and palette

Define a role enum in `core/<type>/models.py` (or wherever the parser produces
nodes) and a role-to-slot mapping in `render/<type>/`. Look up `NodeStyle`s
through `ThemeConfig.style_for(slot)` so themes work without modification.

## Known shared-layer leaks (audit notes)

Several `shared/` modules still encode tree-specific assumptions. They work
because `tree` is the only type today; before a second type lands, each item
must be reviewed and either generalized or moved into `<type>/`.

- `layout/shared/measurement.py`: imports `ConceptNode` directly and walks
  `node.parent`/`node.children`/`node.body_text()`. The text/wrapping helpers
  are reusable; the node traversal is tree-specific. Likely refactor: split
  into a generic `text/` measurement module and a tree-specific
  `measure_nodes` that lives under `layout/tree/`.
- `layout/shared/models.py`: `LayoutBox.node: ConceptNode` and
  `LayoutBox.subtree_width` couple the shared model to tree. Likely refactor:
  parameterize `LayoutBox` over a generic node type, or store an opaque payload
  per box.
- `layout/shared/models.py`: `LayoutEdge.parent_number`/`child_number`/
  `relation_label` are hierarchical; flowcharts will want endpoint ids and
  optional labels without parent/child semantics. Likely refactor: rename to
  `source`/`target` and treat the relation as opaque metadata.
- `render/shared/context.py`: `RenderSettingsResolver.resolve` accepts a
  `ParsedDocument` whose type is the tree variant. The metadata-resolution
  logic itself is generic; the type is too narrow.
- `render/shared/viewport.py`: `EXPANDABLE_LAYOUTS = {"tree", "radial"}` is a
  hardcoded list of tree layout names. Likely refactor: let each type
  register layout traits at profile-registration time.
- `render/shared/models.py`: `SvgNodeRenderSpec.node: ConceptNode` and
  `RenderContext.parsed: ParsedDocument` are tree-specific. Same refactor
  options as `LayoutBox`.

These items are tracked as "known leaks": the architecture is intentionally
not abstracted further until a second type forces the abstraction to be
real instead of speculative.
