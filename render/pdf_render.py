from pathlib import Path
from typing import Optional, Tuple

from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from core.models import ParsedDocument
from layout.models import ThemeConfig, TypographyConfig
from layout.models import LayoutKind
from layout.registry import build_layout
from layout.shared import sort_node_key, wrap_text_lines
from render.defaults import (
    DEFAULT_LAYOUT_KIND,
    DEFAULT_THEME,
    SHOW_NODE_NUMBERS,
    SHOW_WARNINGS_FOOTER,
    layout_config_for,
    typography_for,
)


def to_pdf_y(y_top: float, page_height: float) -> float:
    return page_height - y_top


def arrow_wing_points(start: Tuple[float, float], tip: Tuple[float, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    dx = tip[0] - start[0]
    dy = tip[1] - start[1]
    length = (dx * dx + dy * dy) ** 0.5

    if length < 1e-6:
        return tip, tip

    ux = dx / length
    uy = dy / length

    arrow_len = 6.0
    arrow_w = 3.2

    wing_a = (
        tip[0] - (ux * arrow_len) - (uy * arrow_w),
        tip[1] - (uy * arrow_len) + (ux * arrow_w),
    )
    wing_b = (
        tip[0] - (ux * arrow_len) + (uy * arrow_w),
        tip[1] - (uy * arrow_len) - (ux * arrow_w),
    )

    return wing_a, wing_b


def draw_round_rect(
    pdf_canvas: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    corner_radius: float,
    page_height: float,
) -> None:
    y = page_height - y_top - height
    pdf_canvas.roundRect(x, y, width, height, corner_radius, stroke=1, fill=1)


def draw_polyline(pdf_canvas: canvas.Canvas, points: list[Tuple[float, float]], page_height: float) -> None:
    for index in range(len(points) - 1):
        x1, y1 = points[index]
        x2, y2 = points[index + 1]
        pdf_canvas.line(x1, to_pdf_y(y1, page_height), x2, to_pdf_y(y2, page_height))


def draw_wrapped_label(
    pdf_canvas: canvas.Canvas,
    text: str,
    x_center: float,
    y_top: float,
    max_width: float,
    page_height: float,
    typography: TypographyConfig,
    theme: ThemeConfig,
) -> None:
    lines = wrap_text_lines(text, typography.body_font, typography.relation_size, max(20.0, max_width))
    if not lines:
        return

    box_w = max(stringWidth(line, typography.body_font, typography.relation_size) for line in lines) + 6
    box_h = len(lines) * (typography.relation_size + 1) + 4

    x = x_center - (box_w / 2)
    y = page_height - y_top - (box_h / 2)

    pdf_canvas.setFillColor(colors.white)
    pdf_canvas.roundRect(x, y, box_w, box_h, 2, stroke=0, fill=1)

    pdf_canvas.setFillColor(colors.HexColor(theme.relation_color))
    text_y = y + box_h - typography.relation_size - 1
    for line in lines:
        pdf_canvas.drawCentredString(x_center, text_y, line)
        text_y -= typography.relation_size + 1


def render_pdf(parsed: ParsedDocument, output_pdf: Path, layout_kind: Optional[LayoutKind] = None) -> None:
    selected_layout = layout_kind or DEFAULT_LAYOUT_KIND
    config = layout_config_for(selected_layout)
    typography = typography_for(selected_layout)
    theme = DEFAULT_THEME

    scene = build_layout(selected_layout, parsed.root_nodes, config, typography)
    boxes = scene.boxes

    page_size = (config.page_width, config.page_height)
    pdf_canvas = canvas.Canvas(str(output_pdf), pagesize=page_size)
    pdf_canvas.setTitle("Prototype Concept Map")

    content_w = max(1.0, scene.content_right - scene.content_left)
    content_h = max(1.0, scene.content_bottom - scene.content_top)
    usable_w = config.page_width - (2 * config.margin_x)
    usable_h = config.page_height - (2 * config.margin_y)

    scale_x = usable_w / content_w if content_w > usable_w else 1.0
    scale_y = usable_h / content_h if content_h > usable_h else 1.0
    scale = min(1.0, scale_x, scale_y)

    extra_x = 0.0
    extra_y = 0.0
    if selected_layout == "radial":
        extra_x = max(0.0, (usable_w - (content_w * scale)) / 2)
        extra_y = max(0.0, (usable_h - (content_h * scale)) / 2)

    tx = config.margin_x + extra_x - (scale * scene.content_left)
    ty = config.page_height - config.margin_y - extra_y + (scale * scene.content_top)

    pdf_canvas.saveState()
    pdf_canvas.translate(tx, ty)
    pdf_canvas.scale(scale, scale)
    pdf_canvas.translate(0, -config.page_height)

    pdf_canvas.setStrokeColor(colors.HexColor(theme.edge_color))
    pdf_canvas.setLineWidth(0.9)

    for edge in scene.edges:
        if len(edge.points) < 2:
            continue

        draw_polyline(pdf_canvas, edge.points, config.page_height)

        prev_point = edge.points[-2]
        tip_point = edge.points[-1]
        wing_a, wing_b = arrow_wing_points(prev_point, tip_point)

        pdf_canvas.line(
            tip_point[0],
            to_pdf_y(tip_point[1], config.page_height),
            wing_a[0],
            to_pdf_y(wing_a[1], config.page_height),
        )
        pdf_canvas.line(
            tip_point[0],
            to_pdf_y(tip_point[1], config.page_height),
            wing_b[0],
            to_pdf_y(wing_b[1], config.page_height),
        )

        if edge.relation_label:
            draw_wrapped_label(
                pdf_canvas,
                edge.relation_label,
                edge.label_pos[0],
                edge.label_pos[1],
                edge.label_max_width,
                config.page_height,
                typography,
                theme,
            )

    for number in sorted(boxes.keys(), key=sort_node_key):
        box = boxes[number]
        style = theme.style_for(box.node.kind)

        pdf_canvas.setFillColor(colors.HexColor(style.fill))
        pdf_canvas.setStrokeColor(colors.HexColor(style.stroke))
        draw_round_rect(
            pdf_canvas,
            box.x,
            box.y,
            box.width,
            box.height,
            config.corner_radius,
            config.page_height,
        )

        pdf_canvas.setFillColor(colors.HexColor(style.title))
        pdf_canvas.setFont(typography.title_font, box.title_font_size)

        title_y_cursor = config.page_height - box.y - config.inner_pad_y - box.title_font_size
        for line in box.title_lines or [box.node.title]:
            pdf_canvas.drawString(box.x + config.inner_pad_x, title_y_cursor, line)
            title_y_cursor -= box.title_font_size + typography.title_line_extra

        if box.body_lines:
            pdf_canvas.setFillColor(colors.HexColor(style.body))
            pdf_canvas.setFont(typography.body_font, typography.body_size)

            body_y_cursor = (
                config.page_height
                - box.y
                - config.inner_pad_y
                - box.title_height
                - config.title_body_gap
                - typography.body_size
            )

            for line in box.body_lines:
                pdf_canvas.drawString(box.x + config.inner_pad_x, body_y_cursor, line)
                body_y_cursor -= typography.body_leading

        if SHOW_NODE_NUMBERS:
            num_text = box.node.number
            num_w = stringWidth(num_text, typography.body_font, 6.5) + 6
            num_h = 9
            num_x = box.x + box.width - num_w - 3
            num_y = config.page_height - box.y - num_h - 3

            pdf_canvas.setFillColor(colors.HexColor(theme.number_pill_bg))
            pdf_canvas.roundRect(num_x, num_y, num_w, num_h, 3, stroke=0, fill=1)

            pdf_canvas.setFillColor(colors.HexColor(theme.relation_color))
            pdf_canvas.setFont(typography.body_font, 6.5)
            pdf_canvas.drawCentredString(num_x + (num_w / 2), num_y + 2.2, num_text)

    pdf_canvas.restoreState()

    if SHOW_WARNINGS_FOOTER and parsed.warnings:
        pdf_canvas.setFillColor(colors.HexColor("#7A4F01"))
        pdf_canvas.setFont(typography.body_font, 7)
        preview = " | ".join(warning.message for warning in parsed.warnings[:3])
        pdf_canvas.drawString(config.margin_x, 28.0, f"Avisos: {preview[:140]}")

    pdf_canvas.save()
