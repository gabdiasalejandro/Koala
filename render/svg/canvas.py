"""Canvas SVG de alto nivel.

Este archivo coordina el backend SVG:
- crea el grupo raiz con el viewport ya resuelto
- delega texto, nodos y aristas a renderers especializados
- añade adornos globales como el footer de avisos
"""

import svgwrite

from render.models import RenderContext
from render.svg.edges import SvgEdgeRenderer
from render.svg.nodes import SvgNodeRenderer
from render.svg.text import SvgTextRenderer


class SvgCanvasRenderer:
    """Orquestador del dibujo SVG de una escena completa."""

    SHOW_WARNINGS_FOOTER = False

    def __init__(self, context: RenderContext):
        self._context = context

    def render(self, dwg: svgwrite.Drawing) -> None:
        root_group = dwg.g(transform=self._context.viewport.svg_transform())
        dwg.add(root_group)

        text_renderer = SvgTextRenderer(dwg, root_group)
        SvgEdgeRenderer(dwg, root_group, self._context, text_renderer).render()
        node_renderer = SvgNodeRenderer(dwg, root_group, self._context, text_renderer)

        if self._context.settings.layout_kind == "synoptic":
            node_renderer.render_text_only_nodes()
        else:
            node_renderer.render_boxed_nodes()

        if self._should_draw_warnings_footer():
            self._draw_warnings_footer(dwg)

    def _should_draw_warnings_footer(self) -> bool:
        return self.SHOW_WARNINGS_FOOTER and bool(self._context.parsed.warnings)

    def _draw_warnings_footer(self, dwg: svgwrite.Drawing) -> None:
        config = self._context.settings.layout_config
        typography = self._context.settings.typography
        preview = " | ".join(warning.message for warning in self._context.parsed.warnings[:3])
        dwg.add(
            dwg.text(
                f"Avisos: {preview[:140]}",
                insert=(config.margin_x, config.page_height - 16.0),
                font_size=7,
                fill="#7A4F01",
                font_family=typography.body_font,
            )
        )
