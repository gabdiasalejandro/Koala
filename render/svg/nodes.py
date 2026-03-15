"""Renderizado SVG de nodos.

Este modulo separa dos tareas:
- construir specs de nodos desde un `RenderContext`
- dibujar nodos normales o text-only segun el layout

La composicion de colores ya llega resuelta desde el theme activo.
"""

import svgwrite

from layout.shared import measure_text_width, sort_node_key
from render.models import RenderContext, SvgNodeRenderSpec, SvgTextBlockSpec, SvgTextStyle
from render.svg.text import SvgTextRenderer


class SvgNodeSpecFactory:
    """Convierte cajas del layout en specs aptos para el backend SVG."""

    @classmethod
    def build(cls, context: RenderContext, number: str, *, text_only: bool) -> SvgNodeRenderSpec:
        config = context.settings.layout_config
        typography = context.settings.typography
        theme = context.settings.theme

        box = context.scene.boxes[number]
        node_style = theme.style_for(box.node.kind)
        text_x = box.x + config.inner_pad_x
        text_width = box.width - (2 * config.inner_pad_x)
        title_y = box.y + config.inner_pad_y + box.title_font_size

        title_block = SvgTextBlockSpec(
            lines=box.title_lines or [box.node.title],
            x=text_x,
            start_y=title_y,
            line_step=box.title_font_size + typography.title_line_extra,
            max_width=text_width,
            style=SvgTextStyle(
                font_size=box.title_font_size,
                font_family=typography.title_font,
                fill=node_style.title,
                text_align=typography.text_align,
                font_weight="600" if text_only else None,
            ),
        )

        body_block = None
        if box.body_lines:
            body_y = box.y + config.inner_pad_y + box.title_height + config.title_body_gap + typography.body_size
            body_block = SvgTextBlockSpec(
                lines=box.body_lines,
                x=text_x,
                start_y=body_y,
                line_step=typography.body_leading,
                max_width=text_width,
                style=SvgTextStyle(
                    font_size=typography.body_size,
                    font_family=typography.body_font,
                    fill=node_style.body,
                    text_align=typography.text_align,
                ),
            )

        return SvgNodeRenderSpec(
            box=box,
            node=box.node,
            node_style=node_style,
            title_block=title_block,
            body_block=body_block,
        )


class SvgNodeRenderer:
    """Renderer de nodos y numeracion opcional."""

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

    def render_boxed_nodes(self) -> None:
        config = self._context.settings.layout_config
        typography = self._context.settings.typography

        for number in sorted(self._context.scene.boxes.keys(), key=sort_node_key):
            spec = SvgNodeSpecFactory.build(self._context, number, text_only=False)
            self._root_group.add(
                self._dwg.rect(
                    insert=(spec.box.x, spec.box.y),
                    size=(spec.box.width, spec.box.height),
                    rx=config.corner_radius,
                    ry=config.corner_radius,
                    fill=spec.node_style.fill,
                    stroke=spec.node_style.stroke,
                    stroke_width=1.2,
                )
            )
            self._text_renderer.draw_block(spec.title_block)
            if spec.body_block is not None:
                self._text_renderer.draw_block(spec.body_block)
            if self._context.settings.show_node_numbers:
                self._draw_node_number(spec, typography)

    def render_text_only_nodes(self) -> None:
        for number in sorted(self._context.scene.boxes.keys(), key=sort_node_key):
            spec = SvgNodeSpecFactory.build(self._context, number, text_only=True)
            self._text_renderer.draw_block(spec.title_block)
            if spec.body_block is not None:
                self._text_renderer.draw_block(spec.body_block)

    def _draw_node_number(self, spec: SvgNodeRenderSpec, typography) -> None:
        theme = self._context.settings.theme
        num_text = spec.node.number
        num_w = measure_text_width(num_text, typography.body_font, 6.5) + 6
        num_h = 9
        num_x = spec.box.x + spec.box.width - num_w - 3
        num_y = spec.box.y + 3

        self._root_group.add(
            self._dwg.rect(
                insert=(num_x, num_y),
                size=(num_w, num_h),
                rx=3,
                ry=3,
                fill=theme.number_pill_bg,
            )
        )
        self._root_group.add(
            self._dwg.text(
                num_text,
                insert=(num_x + (num_w / 2), num_y + 7),
                text_anchor="middle",
                font_size=6.5,
                fill=theme.number_pill_text,
                font_family=typography.body_font,
            )
        )
