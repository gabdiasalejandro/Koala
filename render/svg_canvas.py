"""Dibujo SVG de la escena.

Recibe un `RenderContext` ya resuelto y se concentra solo en:
- aristas y etiquetas de relaciones
- nodos y su contenido tipografico
- adornos opcionales como numeracion y avisos
"""

import svgwrite

from layout.shared import measure_text_width, sort_node_key, wrap_text_lines
from render.defaults import SHOW_NODE_NUMBERS, SHOW_WARNINGS_FOOTER
from render.geometry import arrow_wing_points
from render.models import RenderContext


def draw_scene(dwg: svgwrite.Drawing, context: RenderContext) -> None:
    root_group = dwg.g(transform=context.viewport.svg_transform())
    dwg.add(root_group)

    _draw_edges(dwg, root_group, context)
    if context.settings.layout_kind == "synoptic":
        _draw_text_only_nodes(dwg, root_group, context)
    else:
        _draw_nodes(dwg, root_group, context)

    if SHOW_WARNINGS_FOOTER and context.parsed.warnings:
        _draw_warnings_footer(dwg, context)


def _draw_edges(dwg: svgwrite.Drawing, root_group: svgwrite.container.Group, context: RenderContext) -> None:
    typography = context.settings.typography
    theme = context.settings.theme
    use_brackets_only = context.settings.layout_kind == "synoptic"

    for edge in context.scene.edges:
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

        if not use_brackets_only:
            prev_point = edge.points[-2]
            tip_point = edge.points[-1]
            wing_a, wing_b = arrow_wing_points(prev_point, tip_point)
            root_group.add(dwg.line(tip_point, wing_a, stroke=theme.edge_color, stroke_width=1.0))
            root_group.add(dwg.line(tip_point, wing_b, stroke=theme.edge_color, stroke_width=1.0))

        if edge.relation_label and not use_brackets_only:
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


def _draw_nodes(dwg: svgwrite.Drawing, root_group: svgwrite.container.Group, context: RenderContext) -> None:
    config = context.settings.layout_config
    typography = context.settings.typography
    theme = context.settings.theme

    for number in sorted(context.scene.boxes.keys(), key=sort_node_key):
        box = context.scene.boxes[number]
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
            _draw_node_number(dwg, root_group, box, typography, theme)


def _draw_text_only_nodes(dwg: svgwrite.Drawing, root_group: svgwrite.container.Group, context: RenderContext) -> None:
    config = context.settings.layout_config
    typography = context.settings.typography
    theme = context.settings.theme

    for number in sorted(context.scene.boxes.keys(), key=sort_node_key):
        box = context.scene.boxes[number]
        style = theme.style_for(box.node.kind)

        title_y = box.y + config.inner_pad_y + box.title_font_size
        for line in box.title_lines or [box.node.title]:
            root_group.add(
                dwg.text(
                    line,
                    insert=(box.x + config.inner_pad_x, title_y),
                    font_size=box.title_font_size,
                    fill=style.title,
                    font_family=typography.title_font,
                    font_weight="600",
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


def _draw_node_number(
    dwg: svgwrite.Drawing,
    root_group: svgwrite.container.Group,
    box,
    typography,
    theme,
) -> None:
    num_text = box.node.number
    num_w = measure_text_width(num_text, typography.body_font, 6.5) + 6
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


def _draw_warnings_footer(dwg: svgwrite.Drawing, context: RenderContext) -> None:
    config = context.settings.layout_config
    typography = context.settings.typography
    preview = " | ".join(warning.message for warning in context.parsed.warnings[:3])
    dwg.add(
        dwg.text(
            f"Avisos: {preview[:140]}",
            insert=(config.margin_x, config.page_height - 16.0),
            font_size=7,
            fill="#7A4F01",
            font_family=typography.body_font,
        )
    )
