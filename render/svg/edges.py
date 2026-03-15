"""Renderizado SVG de aristas y labels de relacion.

Este modulo dibuja conectores sobre una escena ya resuelta:
- lineas o polilineas
- puntas de flecha cuando corresponde
- labels de relacion en layouts que las muestran
"""

import svgwrite

from layout.shared import wrap_text_lines
from render.geometry import arrow_wing_points
from render.models import RenderContext, SvgTextBlockSpec, SvgTextStyle
from render.svg.text import SvgTextRenderer


class SvgEdgeRenderer:
    """Renderer de aristas a partir del `RenderContext` actual."""

    def __init__(
        self,
        dwg: svgwrite.Drawing,
        root_group: svgwrite.container.Group,
        context: RenderContext,
        text_renderer: SvgTextRenderer,
    ):
        self._dwg = dwg
        self._root_group = root_group
        self._context = context
        self._text_renderer = text_renderer

    def render(self) -> None:
        typography = self._context.settings.typography
        theme = self._context.settings.theme
        use_brackets_only = self._context.settings.layout_kind == "synoptic"

        for edge in self._context.scene.edges:
            if len(edge.points) < 2:
                continue

            has_explicit_relation = bool(edge.relation_label)
            stroke_color = theme.edge_color if has_explicit_relation else theme.implicit_edge_color
            stroke_width = 1.2 if has_explicit_relation else 1.75

            if len(edge.points) == 2:
                self._root_group.add(
                    self._dwg.line(
                        edge.points[0],
                        edge.points[1],
                        stroke=stroke_color,
                        stroke_width=stroke_width,
                    )
                )
            else:
                self._root_group.add(
                    self._dwg.polyline(
                        points=edge.points,
                        fill="none",
                        stroke=stroke_color,
                        stroke_width=stroke_width,
                    )
                )

            if not use_brackets_only:
                self._draw_arrow(edge.points[-2], edge.points[-1], theme.edge_color)

            if edge.relation_label and not use_brackets_only:
                label_spec = SvgTextBlockSpec(
                    lines=wrap_text_lines(
                        edge.relation_label,
                        typography.body_font,
                        typography.relation_size,
                        edge.label_max_width,
                    ),
                    x=edge.label_pos[0],
                    start_y=edge.label_pos[1],
                    line_step=typography.relation_size + 1,
                    max_width=edge.label_max_width,
                    style=SvgTextStyle(
                        font_size=typography.relation_size,
                        font_family=typography.body_font,
                        fill=theme.relation_color,
                        text_align="left",
                    ),
                )
                self._text_renderer.draw_centered_block(label_spec)

    def _draw_arrow(self, start, tip, stroke_color: str) -> None:
        wing_a, wing_b = arrow_wing_points(start, tip)
        self._root_group.add(self._dwg.line(tip, wing_a, stroke=stroke_color, stroke_width=1.0))
        self._root_group.add(self._dwg.line(tip, wing_b, stroke=stroke_color, stroke_width=1.0))
