from pathlib import Path

import svgwrite
from reportlab.pdfbase.pdfmetrics import stringWidth

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
)


def render_svg(parsed: ParsedDocument, output_svg: Path) -> None:
    config = DEFAULT_LAYOUT_CONFIG
    typography = DEFAULT_TYPOGRAPHY
    theme = DEFAULT_THEME

    scene = build_layout(DEFAULT_LAYOUT_KIND, parsed.root_nodes, config, typography)
    boxes = scene.boxes

    dwg = svgwrite.Drawing(
        str(output_svg),
        size=(config.page_width, config.page_height),
        viewBox=f"0 0 {config.page_width} {config.page_height}",
    )

    scale_x = (config.page_width - (2 * config.margin_x)) / max(1, scene.content_right - config.margin_x)
    scale_y = (config.page_height - (2 * config.margin_y)) / max(1, scene.content_bottom - config.margin_y)
    scale = min(1.0, scale_x, scale_y)

    root_group = dwg.g(transform=f"scale({scale})")
    dwg.add(root_group)

    for node in parsed.node_index.values():
        if node.parent is None:
            continue

        parent = boxes[node.parent.number]
        child = boxes[node.number]

        x1 = parent.x + (parent.width / 2)
        y1 = parent.y + parent.height
        x2 = child.x + (child.width / 2)
        y2 = child.y

        y_mid = y1 + (get_v_gap_for_depth(child.depth, config) / 2)

        root_group.add(dwg.line((x1, y1), (x1, y_mid), stroke=theme.edge_color, stroke_width=1.2))
        root_group.add(dwg.line((x1, y_mid), (x2, y_mid), stroke=theme.edge_color, stroke_width=1.2))
        root_group.add(dwg.line((x2, y_mid), (x2, y2), stroke=theme.edge_color, stroke_width=1.2))

        root_group.add(dwg.line((x2, y2), (x2 - 3, y2 + 5), stroke=theme.edge_color, stroke_width=1.0))
        root_group.add(dwg.line((x2, y2), (x2 + 3, y2 + 5), stroke=theme.edge_color, stroke_width=1.0))

        if node.relation_from_parent:
            max_width = max(70.0, abs(x2 - x1) + 30.0)
            lines = wrap_text_lines(
                node.relation_from_parent,
                typography.body_font,
                typography.relation_size,
                max_width,
            )
            line_height = typography.relation_size + 1
            first_line_y = y_mid - 3

            for line_index, line in enumerate(lines):
                root_group.add(
                    dwg.text(
                        line,
                        insert=((x1 + x2) / 2, first_line_y + (line_index * line_height)),
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
