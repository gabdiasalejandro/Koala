from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.io import load_input_text
from core.models import ParsedDocument
from core.parser import parse_concept_text
from layout.conceptual_topdown import (
    get_v_gap_for_depth,
    sort_node_key,
    wrap_text_lines,
)
from layout.registry import build_layout
from render.defaults import (
    DEFAULT_LAYOUT_KIND,
    DEFAULT_LAYOUT_CONFIG,
    DEFAULT_THEME,
    DEFAULT_TYPOGRAPHY,
    SHOW_NODE_NUMBERS,
    SHOW_WARNINGS_FOOTER,
)


def to_pdf_y(y_top: float, page_height: float) -> float:
    return page_height - y_top


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


def draw_wrapped_label(
    pdf_canvas: canvas.Canvas,
    text: str,
    x_center: float,
    y_top: float,
    max_width: float,
    page_height: float,
) -> None:
    typography = DEFAULT_TYPOGRAPHY
    theme = DEFAULT_THEME

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


def draw_arrow_head(pdf_canvas: canvas.Canvas, x: float, y_top: float, page_height: float) -> None:
    y = to_pdf_y(y_top, page_height)
    pdf_canvas.line(x, y, x - 2.2, y + 4.2)
    pdf_canvas.line(x, y, x + 2.2, y + 4.2)


def render_pdf(parsed: ParsedDocument, output_pdf: Path) -> None:
    config = DEFAULT_LAYOUT_CONFIG
    typography = DEFAULT_TYPOGRAPHY
    theme = DEFAULT_THEME

    scene = build_layout(DEFAULT_LAYOUT_KIND, parsed.root_nodes, config, typography)
    boxes = scene.boxes

    page_size = (config.page_width, config.page_height)
    pdf_canvas = canvas.Canvas(str(output_pdf), pagesize=page_size)
    pdf_canvas.setTitle("Prototype Concept Map")

    usable_w = config.page_width - (2 * config.margin_x)
    usable_h = config.page_height - (2 * config.margin_y)
    content_w = max(1.0, scene.content_right - config.margin_x)
    content_h = max(1.0, scene.content_bottom - config.margin_y)

    scale_x = usable_w / content_w if content_w > usable_w else 1.0
    scale_y = usable_h / content_h if content_h > usable_h else 1.0
    scale = min(1.0, scale_x, scale_y)

    pdf_canvas.saveState()
    pdf_canvas.translate(config.margin_x * (1 - scale), config.page_height - config.margin_y * (1 - scale))
    pdf_canvas.scale(scale, scale)
    pdf_canvas.translate(0, -config.page_height)

    pdf_canvas.setStrokeColor(colors.HexColor(theme.edge_color))
    pdf_canvas.setLineWidth(0.9)

    for node in parsed.node_index.values():
        if node.parent is None:
            continue

        parent = boxes[node.parent.number]
        child = boxes[node.number]

        x1 = parent.x + (parent.width / 2)
        y1_top = parent.y + parent.height
        x2 = child.x + (child.width / 2)
        y2_top = child.y
        y_mid_top = y1_top + (get_v_gap_for_depth(child.depth, config) / 2)

        pdf_canvas.line(x1, to_pdf_y(y1_top, config.page_height), x1, to_pdf_y(y_mid_top, config.page_height))
        pdf_canvas.line(x1, to_pdf_y(y_mid_top, config.page_height), x2, to_pdf_y(y_mid_top, config.page_height))
        pdf_canvas.line(x2, to_pdf_y(y_mid_top, config.page_height), x2, to_pdf_y(y2_top + 3, config.page_height))
        draw_arrow_head(pdf_canvas, x2, y2_top + 3, config.page_height)

        if node.relation_from_parent:
            draw_wrapped_label(
                pdf_canvas,
                node.relation_from_parent,
                (x1 + x2) / 2,
                y_mid_top,
                max(18.0, abs(x2 - x1) + 18.0),
                config.page_height,
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
