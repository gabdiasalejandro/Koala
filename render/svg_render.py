"""Entry point del render basado en SVG.

La responsabilidad de este archivo es minima:
- construir el contexto completo del render
- crear el documento SVG
- delegar el dibujo a `svg_canvas`
"""

from pathlib import Path
from typing import Optional

import svgwrite

from core.models import ParsedDocument
from layout.models import LayoutKind
from render.scene import build_render_context
from render.svg_canvas import draw_scene


def render_svg(
    parsed: ParsedDocument,
    output_svg: Path,
    layout_kind: Optional[LayoutKind] = None,
    theme_name: Optional[str] = None,
    typography_name: Optional[str] = None,
) -> None:
    context = build_render_context(
        parsed,
        layout_kind=layout_kind,
        theme_name=theme_name,
        typography_name=typography_name,
    )
    config = context.settings.layout_config

    dwg = svgwrite.Drawing(
        str(output_svg),
        size=(config.page_width, config.page_height),
        viewBox=f"0 0 {config.page_width} {config.page_height}",
    )
    draw_scene(dwg, context)
    dwg.save()
