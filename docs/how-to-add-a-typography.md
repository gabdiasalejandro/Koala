# How to Add a Typography

Koala typographies are render presets. They choose font families and text metrics
for a document type, then the SVG renderer writes those values into the final
SVG as `font-family`, `font-size`, and related attributes.

The important thing to remember: `svgwrite` only serializes the SVG attributes.
The real visual result depends on the renderer that opens the SVG:

- browsers use installed fonts or web/CSS fonts if available
- CairoSVG uses fonts available through the system font stack when exporting PNG/PDF
- if a font is missing, the renderer falls back to another font
- fallback fonts can change text width, wrapping, and perceived formality

## Where Typographies Live

Each document type registers its own typographies in:

```text
src/koala/render/<type>/profiles.py
```

Current files:

- `src/koala/render/tree/profiles.py`
- `src/koala/render/matrix/profiles.py`

The shared registry is `RenderProfileCatalog` in:

```text
src/koala/render/shared/settings.py
```

Do not add document-specific typography names to shared settings. Add them to
the owning document type.

## Add a Matrix Typography

Open:

```text
src/koala/render/matrix/profiles.py
```

Add a new entry to `TYPOGRAPHIES`:

```python
TYPOGRAPHIES: Dict[str, TypographyConfig] = {
    "default": TypographyConfig(...),
    "formal": TypographyConfig(...),
    "academic": TypographyConfig(
        title_font="Georgia",
        body_font="Times New Roman",
        title_size_base=19.2,
        title_size_min=17.0,
        body_size=10.3,
        relation_size=9.4,
        body_leading=13.2,
        max_title_lines=3,
        title_line_extra=1.0,
    ),
}
```

That is enough for explicit use:

```bash
koala compile comparison.txt --type matrix --layout matrix --typography academic
```

If you want the layout to use this typography by default, update the profile:

```python
RenderProfile(
    layout_config=MATRIX_LAYOUT_CONFIG,
    typography=TYPOGRAPHIES["academic"],
    typography_name="academic",
    theme_name=DEFAULT_THEME_NAME,
)
```

## Add a Tree Typography

Open:

```text
src/koala/render/tree/profiles.py
```

Add a new entry to `TYPOGRAPHIES`. For one-off variants, prefer `replace(...)`
from an existing preset:

```python
TYPOGRAPHIES["classic"] = replace(
    TYPOGRAPHIES["default"],
    title_font="Georgia",
    body_font="Times New Roman",
    body_size=11.0,
    body_leading=13.8,
)
```

Then decide whether a layout should use it by default in `profiles_by_layout`:

```python
profiles_by_layout = {
    "tree": ("default", "classic"),
    "synoptic": ("synoptic", "default"),
    "synoptic_boxes": ("synoptic", "default"),
    "radial": ("radial", "radial"),
}
```

If you only want the typography available as an option, do not change
`profiles_by_layout`.

## Choosing Font Families

Prefer fonts that are likely to exist in browsers and in CairoSVG export
environments:

- `Georgia`
- `Times New Roman`
- `Arial`
- `Helvetica`
- `Verdana`
- `Trebuchet MS`

Good formal/academic combinations:

- title `Georgia`, body `Times New Roman`
- title `Georgia`, body `Arial`
- title `Times New Roman`, body `Arial`
- title `Helvetica`, body `Arial`

Use serif title fonts when you want a more editorial or academic tone. Use a
sans-serif body when cells are dense and need scanability. Full serif body text
can look formal, but it may require slightly more line height.

## Tuning Metrics

`TypographyConfig` fields:

- `title_font`: font family for titles, headers, and emphasized labels
- `body_font`: font family for body text and ordinary cells
- `text_align`: default text alignment, usually `left`
- `title_size_base`: preferred title size
- `title_size_min`: smallest title size before truncation/wrap fallback
- `body_size`: body text size
- `relation_size`: relation label size for tree edges
- `body_leading`: line height for body text
- `max_title_lines`: maximum title lines before shrinking/truncation
- `title_line_extra`: extra spacing between title lines

Practical tips:

- If text feels cramped, increase `body_leading` before reducing `body_size`.
- If table cells become too tall, reduce `body_size` by `0.2` to `0.4`.
- If titles wrap too aggressively, reduce `title_size_base` or increase the layout width.
- For serif body fonts, add a little more leading.
- For dense matrix exports, keep `body_size` around `10.0` to `10.8`.
- For tree nodes, keep `body_size` around `10.8` to `11.6`.

## Why Measurement Matters

Koala measures text with a deterministic heuristic in:

```text
src/koala/layout/shared/measurement.py
```

That means Koala does not ask the operating system for exact font metrics during
layout. This keeps layout stable and fast, but it also means unusual fonts can
render wider or narrower than expected.

If a new font is consistently wider, add a small adjustment in
`_FONT_WIDTH_FACTORS` and possibly `_FONT_WRAP_PADDING_EM`:

```python
_FONT_WIDTH_FACTORS = {
    "georgia": 1.01,
    "trebuchet ms": 1.03,
    "verdana": 1.04,
}
```

Only do this after seeing text overflow or poor wrapping in SVG/PNG/PDF.

## Test Checklist

Run fast tests first:

```bash
.venv/bin/python -m unittest discover tests/unit/code
.venv/bin/python -m compileall src tests/end_to_end/code tests/unit/code
```

Check that the CLI lists the new typography:

```bash
.venv/bin/koala typographies
```

Render a focused sample:

```bash
.venv/bin/koala compile tests/end_to_end/mocks/comparative_matrix.txt \
  --type matrix \
  --layout matrix \
  --typography academic \
  --output /tmp/matrix-academic.svg
```

Export PNG and PDF:

```bash
.venv/bin/koala export tests/end_to_end/mocks/comparative_matrix.txt \
  --type matrix \
  --layout matrix \
  --typography academic \
  --format png \
  --quality high \
  --output /tmp/matrix-academic.png

.venv/bin/koala export tests/end_to_end/mocks/comparative_matrix.txt \
  --type matrix \
  --layout matrix \
  --typography academic \
  --format pdf \
  --quality high \
  --output /tmp/matrix-academic.pdf
```

Run the full e2e gallery when the change should be part of regression coverage:

```bash
.venv/bin/python -m unittest tests.end_to_end.code.test_render_e2e.RenderEndToEndTest.test_render_gallery
```

## Visual Review Checklist

Review at least one SVG, one medium/high PNG, and one PDF.

Look for:

- text not overflowing cell or node bounds
- line breaks that still read naturally
- headers and body text clearly distinct
- sufficient leading in multi-line cells
- no unexpected font fallback
- high PNG large enough for inspection
- PDF title and frame still matching the document tone

For formal or academic presets:

- prefer restrained size differences
- avoid playful display fonts
- use serif titles carefully
- keep body text readable over decorative personality
- make matrix row labels concise and parallel

## Common Pitfalls

- Adding a typography to `tree` and expecting it to exist for `matrix`.
  Typographies are registered per document type.
- Picking a font that looks good locally but is missing in CI or user systems.
- Making title text too large for matrix headers.
- Forgetting to update docs when the new typography is user-facing.
- Assuming PNG quality changes vector quality. PNG quality changes raster
  resolution; the SVG remains the canonical vector source.
