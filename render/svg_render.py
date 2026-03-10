from pathlib import Path
from typing import Optional, Tuple

import svgwrite
from reportlab.pdfbase.pdfmetrics import stringWidth

from core.models import ParsedDocument
from layout.models import LayoutKind
from layout.registry import build_layout
from layout.shared import sort_node_key, wrap_text_lines
from render.defaults import (
    DEFAULT_LAYOUT_KIND,
    DEFAULT_THEME,
    SHOW_NODE_NUMBERS,
    layout_config_for,
    typography_for,
)


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


def render_svg(parsed: ParsedDocument, output_svg: Path, layout_kind: Optional[LayoutKind] = None) -> None:
    selected_layout = layout_kind or DEFAULT_LAYOUT_KIND
    config = layout_config_for(selected_layout)
    typography = typography_for(selected_layout)
    theme = DEFAULT_THEME

    scene = build_layout(selected_layout, parsed.root_nodes, config, typography)
    boxes = scene.boxes

    dwg = svgwrite.Drawing(
        str(output_svg),
        size=(config.page_width, config.page_height),
        viewBox=f"0 0 {config.page_width} {config.page_height}",
    )

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

    tx = config.margin_x + extra_x - (scene.content_left * scale)
    ty = config.margin_y + extra_y - (scene.content_top * scale)

    root_group = dwg.g(transform=f"translate({tx},{ty}) scale({scale})")
    dwg.add(root_group)

    for edge in scene.edges:
        if len(edge.points) < 2:
            continue

        if len(edge.points) == 2:
            root_group.add(
                dwg.line(
                    edge.points[0],
                    edge.points[1],
                    stroke=theme.edge_color,
                    stroke_width=1.2,
                )
            )
        else:
            root_group.add(
                dwg.polyline(
                    points=edge.points,
                    fill="none",
                    stroke=theme.edge_color,
                    stroke_width=1.2,
                )
            )

        prev_point = edge.points[-2]
        tip_point = edge.points[-1]
        wing_a, wing_b = arrow_wing_points(prev_point, tip_point)

        root_group.add(dwg.line(tip_point, wing_a, stroke=theme.edge_color, stroke_width=1.0))
        root_group.add(dwg.line(tip_point, wing_b, stroke=theme.edge_color, stroke_width=1.0))

        if edge.relation_label:
            lines = wrap_text_lines(
                edge.relation_label,
                typography.body_font,
                typography.relation_size,
                edge.label_max_width,
            )

            line_height = typography.relation_size + 1
            for line_index, line in enumerate(lines):
                root_group.add(
                    dwg.text(
                        line,
                        insert=(edge.label_pos[0], edge.label_pos[1] + (line_index * line_height)),
                        text_anchor="middle",
                        font_size=typography.relation_size,
                        fill=theme.relation_color,
                        font_family=typography.body_font,
                    )
                )

    for number in sorted(boxes.keys(), key=sort_node_key):
        box = boxes[number]
        style = theme.style_for(box.node.kind)

        root_group.add(
            dwg.rect(
                insert=(box.x, box.y),
                size=(box.width, box.height),
                rx=config.corner_radius,
                ry=config.corner_radius,
                fill=style.fill,
                stroke=style.stroke,
                stroke_width=1.2,
            )
        )

        title_y = box.y + config.inner_pad_y + box.title_font_size
        for line in box.title_lines or [box.node.title]:
            root_group.add(
                dwg.text(
                    line,
                    insert=(box.x + config.inner_pad_x, title_y),
                    font_size=box.title_font_size,
                    fill=style.title,
                    font_family=typography.title_font,
                )
            )
            title_y += box.title_font_size + typography.title_line_extra

        if box.body_lines:
            body_y = box.y + config.inner_pad_y + box.title_height + config.title_body_gap + typography.body_size
            for line in box.body_lines:
                root_group.add(
                    dwg.text(
                        line,
                        insert=(box.x + config.inner_pad_x, body_y),
                        font_size=typography.body_size,
                        fill=style.body,
                        font_family=typography.body_font,
                    )
                )
                body_y += typography.body_leading

        if SHOW_NODE_NUMBERS:
            num_text = box.node.number
            num_w = stringWidth(num_text, typography.body_font, 6.5) + 6
            num_h = 9
            num_x = box.x + box.width - num_w - 3
            num_y = box.y + 3

            root_group.add(
                dwg.rect(
                    insert=(num_x, num_y),
                    size=(num_w, num_h),
                    rx=3,
                    ry=3,
                    fill=theme.number_pill_bg,
                )
            )
            root_group.add(
                dwg.text(
                    num_text,
                    insert=(num_x + (num_w / 2), num_y + 7),
                    text_anchor="middle",
                    font_size=6.5,
                    fill=theme.relation_color,
                    font_family=typography.body_font,
                )
            )

    dwg.save()
