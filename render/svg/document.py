"""Creacion del documento SVG.

Este archivo encapsula la configuracion fisica del archivo de salida:
- tamaño de pagina
- viewBox
- inicializacion del objeto `svgwrite.Drawing`
"""

from pathlib import Path

import svgwrite

from render.models import RenderContext


class SvgDocumentFactory:
    """Fabrica del documento SVG final."""

    @classmethod
    def create(cls, output_svg: Path, context: RenderContext) -> svgwrite.Drawing:
        config = context.settings.layout_config
        return svgwrite.Drawing(
            str(output_svg),
            size=(config.page_width, config.page_height),
            viewBox=f"0 0 {config.page_width} {config.page_height}",
        )
