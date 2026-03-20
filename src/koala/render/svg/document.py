"""Creacion del documento SVG.

Este archivo encapsula la configuracion fisica del documento:
- tamaño de pagina
- viewBox
- inicializacion del objeto `svgwrite.Drawing`

El documento puede usarse solo en memoria o luego persistirse a disco.
"""

import svgwrite

from koala.render.models import RenderContext


class SvgDocumentFactory:
    """Fabrica del documento SVG final."""

    @classmethod
    def create(cls, context: RenderContext) -> svgwrite.Drawing:
        config = context.settings.layout_config
        drawing = svgwrite.Drawing(
            size=(config.page_width, config.page_height),
            viewBox=f"0 0 {config.page_width} {config.page_height}",
        )
        if context.settings.background_color:
            drawing.attribs["style"] = f"background-color:{context.settings.background_color}"
        return drawing
