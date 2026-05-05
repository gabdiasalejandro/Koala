"""Canvas SVG para cuadros comparativos `matrix`."""

from __future__ import annotations

from koala.core.matrix.models import MatrixCell
from koala.render.shared.models import RenderContext, SvgTextBlockSpec, SvgTextStyle
from koala.render.shared.svg.text import SvgTextRenderer


class MatrixSvgCanvasRenderer:
    """Dibuja una matriz formal con header, cuerpo y cierre."""

    BORDER_OPACITY = 0.82
    BODY_FILL_OPACITY = 0.36
    FOOTER_FILL_OPACITY = 0.62

    def __init__(self, context: RenderContext):
        self._context = context

    def render(self, dwg: svgwrite.Drawing) -> None:
        root_group = dwg.g(transform=self._context.viewport.svg_transform())
        dwg.add(root_group)
        text_renderer = SvgTextRenderer(dwg, root_group)

        self._draw_table_backdrop(dwg, root_group)
        self._draw_title(dwg, root_group, text_renderer)
        self._draw_cells(dwg, root_group, text_renderer)

    def _draw_table_backdrop(self, dwg: svgwrite.Drawing, root_group) -> None:
        boxes = self._context.scene.boxes
        body_boxes = [box for key, box in boxes.items() if key != "title"]
        if not body_boxes:
            return
        left = min(box.x for box in body_boxes)
        top = min(box.y for box in body_boxes)
        right = max(box.x + box.width for box in body_boxes)
        bottom = max(box.y + box.height for box in body_boxes)
        theme = self._context.settings.theme
        root_group.add(
            dwg.rect(
                insert=(left, top),
                size=(right - left, bottom - top),
                rx=0,
                ry=0,
                fill=theme.default_node.fill,
                stroke=theme.edge_color,
                stroke_width=1.4,
            )
        )

    def _draw_title(self, dwg: svgwrite.Drawing, root_group, text_renderer: SvgTextRenderer) -> None:
        box = self._context.scene.boxes.get("title")
        if box is None:
            return
        typography = self._context.settings.typography
        style = self._context.settings.theme.style_for("main")
        accent_y = box.y + box.height - 2.0
        root_group.add(
            dwg.line(
                start=(box.x, accent_y),
                end=(box.x + box.width, accent_y),
                stroke=style.stroke,
                stroke_width=2.0,
                opacity=0.72,
            )
        )
        text_renderer.draw_block(
            SvgTextBlockSpec(
                lines=box.title_lines,
                x=box.x,
                start_y=box.y + self._context.settings.layout_config.inner_pad_y + box.title_font_size,
                line_step=box.title_font_size + typography.title_line_extra,
                max_width=box.width,
                style=SvgTextStyle(
                    font_size=box.title_font_size,
                    font_family=typography.title_font,
                    fill=style.title,
                    text_align="left",
                    font_weight="600",
                ),
            )
        )

    def _draw_cells(self, dwg: svgwrite.Drawing, root_group, text_renderer: SvgTextRenderer) -> None:
        for key in self._ordered_cell_keys():
            box = self._context.scene.boxes[key]
            node = box.node
            role = getattr(node, "role", "cell")
            style = self._style_for_role(role)
            fill_opacity = self._fill_opacity(role)
            root_group.add(
                dwg.rect(
                    insert=(box.x, box.y),
                    size=(box.width, box.height),
                    rx=0,
                    ry=0,
                    fill=style.fill,
                    fill_opacity=fill_opacity,
                    stroke=style.stroke if role != "cell" else self._context.settings.theme.edge_color,
                    stroke_width=1.0 if role != "footer" else 1.2,
                    stroke_opacity=self.BORDER_OPACITY,
                )
            )
            self._draw_cell_text(text_renderer, box, node, style)

    def _draw_cell_text(self, text_renderer: SvgTextRenderer, box, node: MatrixCell, style) -> None:
        config = self._context.settings.layout_config
        typography = self._context.settings.typography
        role = getattr(node, "role", "cell")
        text_x = box.x + config.inner_pad_x
        text_width = max(1.0, box.width - (2 * config.inner_pad_x))
        font_family = typography.title_font if role in {"header", "row_header"} else typography.body_font
        font_weight = "600" if role in {"header", "row_header", "footer"} else None
        fill = style.title if role in {"header", "row_header"} else style.body
        line_step = self._line_step(box.title_font_size)
        text_height = len(box.title_lines) * line_step
        start_y = box.y + max(
            config.inner_pad_y + box.title_font_size,
            ((box.height - text_height) / 2) + box.title_font_size - 1.0,
        )
        text_align = typography.text_align if role == "cell" else "left"
        text_renderer.draw_block(
            SvgTextBlockSpec(
                lines=box.title_lines,
                x=text_x,
                start_y=start_y,
                line_step=line_step,
                max_width=text_width,
                style=SvgTextStyle(
                    font_size=box.title_font_size,
                    font_family=font_family,
                    fill=fill,
                    text_align=text_align,
                    font_weight=font_weight,
                ),
            )
        )

    def _ordered_cell_keys(self) -> list[str]:
        keys = [key for key in self._context.scene.boxes if key != "title"]

        def sort_key(key: str) -> tuple[int, int, str]:
            node = self._context.scene.boxes[key].node
            return (getattr(node, "row", 0), getattr(node, "col", 0), key)

        return sorted(keys, key=sort_key)

    def _style_for_role(self, role: str):
        slot = {
            "header": "main",
            "row_header": "hl",
            "footer": "soft",
        }.get(role, "default")
        return self._context.settings.theme.style_for(slot)

    def _fill_opacity(self, role: str) -> float:
        if role in {"header", "row_header"}:
            return 1.0
        if role == "footer":
            return self.FOOTER_FILL_OPACITY
        return self.BODY_FILL_OPACITY

    @staticmethod
    def _line_step(font_size: float) -> float:
        return font_size + 2.2
