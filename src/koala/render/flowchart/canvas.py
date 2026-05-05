"""Canvas SVG para diagramas de flujo `flowchart`.

Formas por kind:
- start / end  → cápsula (elipse alargada, esquinas muy redondeadas)
- process      → rectángulo con bordes redondeados (corner_radius del config)
- decision     → rombo (path con 4 vértices en los centros de cada lado)
- note         → rectángulo con esquina superior derecha doblada

Los colores vienen del sistema de paleta de Koala:
- start/end  → kind "main"
- process    → kind "default"
- decision   → kind "focus"
- note       → kind "note"
"""

from __future__ import annotations

from koala.render.shared.models import NodeStyle, RenderContext, SvgTextBlockSpec, SvgTextStyle
from koala.render.shared.svg.text import SvgTextRenderer

ARROW_SIZE = 5.0
EDGE_STROKE_WIDTH = 1.4
LABEL_FONT_SIZE = 8.5
NOTE_FOLD = 8.0

_KIND_TO_SLOT = {
    "start": "main",
    "end": "main",
    "process": "default",
    "decision": "focus",
    "note": "note",
}


class FlowchartSvgCanvasRenderer:
    """Dibuja nodos con forma semantica y aristas con punta de flecha."""

    def __init__(self, context: RenderContext) -> None:
        self._ctx = context

    def render(self, dwg: svgwrite.Drawing) -> None:
        defs = dwg.defs
        _define_arrowhead(dwg, defs, self._ctx.settings.theme.edge_color)

        root = dwg.g(transform=self._ctx.viewport.svg_transform())
        dwg.add(root)

        text_renderer = SvgTextRenderer(dwg, root)

        for edge in self._ctx.scene.edges:
            self._draw_edge(dwg, root, edge)

        for node_id, box in self._ctx.scene.boxes.items():
            raw_node = box.node
            kind = getattr(raw_node, "kind", "process")
            slot = _KIND_TO_SLOT.get(kind, "default")
            style = self._ctx.settings.theme.style_for(slot)
            self._draw_node(dwg, root, text_renderer, box, kind, style)

    def _draw_node(
        self,
        dwg: svgwrite.Drawing,
        root,
        text_renderer: SvgTextRenderer,
        box,
        kind: str,
        style: NodeStyle,
    ) -> None:
        draw_fn = {
            "start": _draw_capsule,
            "end": _draw_capsule,
            "decision": _draw_diamond,
            "note": _draw_note,
        }.get(kind, _draw_rect)

        draw_fn(dwg, root, box, style, self._ctx.settings.layout_config)
        self._draw_node_text(text_renderer, box, style)

    def _draw_node_text(self, text_renderer: SvgTextRenderer, box, style: NodeStyle) -> None:
        typography = self._ctx.settings.typography
        kind = getattr(box.node, "kind", "process")

        text_w = max(1.0, box.width - 12.0)
        line_step = box.title_font_size + 3.2
        text_block_h = len(box.title_lines) * line_step
        start_y = box.y + (box.height - text_block_h) / 2 + box.title_font_size

        if kind == "decision":
            text_w = max(1.0, box.width * 0.62)
            center_x = box.x + box.width / 2
            text_x = center_x - text_w / 2
        else:
            text_x = box.x + 6.0

        font_weight = "600" if kind in {"start", "end"} else None

        text_renderer.draw_block(
            SvgTextBlockSpec(
                lines=box.title_lines,
                x=text_x,
                start_y=start_y,
                line_step=line_step,
                max_width=text_w,
                style=SvgTextStyle(
                    font_size=box.title_font_size,
                    font_family=typography.title_font,
                    fill=style.title,
                    text_align="center" if kind in {"start", "end", "decision"} else "left",
                    font_weight=font_weight,
                ),
            )
        )

    def _draw_edge(self, dwg: svgwrite.Drawing, root, edge) -> None:
        theme = self._ctx.settings.theme
        points = edge.points
        if len(points) < 2:
            return

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            is_last = i == len(points) - 2
            line = dwg.line(
                start=(x1, y1),
                end=(x2, y2),
                stroke=theme.edge_color,
                stroke_width=EDGE_STROKE_WIDTH,
            )
            if is_last:
                line["marker-end"] = "url(#koala-arrow)"
            root.add(line)

        if edge.relation_label:
            lx, ly = edge.label_pos
            root.add(
                dwg.text(
                    edge.relation_label,
                    insert=(lx, ly),
                    font_size=LABEL_FONT_SIZE,
                    font_family=self._ctx.settings.typography.body_font,
                    fill=theme.relation_color,
                    text_anchor="middle",
                )
            )


def _define_arrowhead(dwg: svgwrite.Drawing, defs, color: str) -> None:
    marker = dwg.marker(
        id="koala-arrow",
        insert=(ARROW_SIZE, ARROW_SIZE / 2),
        size=(ARROW_SIZE, ARROW_SIZE),
        orient="auto",
        markerUnits="strokeWidth",
    )
    marker.add(
        dwg.path(
            d=f"M0,0 L0,{ARROW_SIZE} L{ARROW_SIZE},{ARROW_SIZE / 2} z",
            fill=color,
        )
    )
    defs.add(marker)


def _draw_rect(dwg, root, box, style: NodeStyle, config) -> None:
    root.add(
        dwg.rect(
            insert=(box.x, box.y),
            size=(box.width, box.height),
            rx=config.corner_radius,
            ry=config.corner_radius,
            fill=style.fill,
            stroke=style.stroke,
            stroke_width=1.6,
        )
    )


def _draw_capsule(dwg, root, box, style: NodeStyle, config) -> None:
    r = box.height / 2
    root.add(
        dwg.rect(
            insert=(box.x, box.y),
            size=(box.width, box.height),
            rx=r,
            ry=r,
            fill=style.fill,
            stroke=style.stroke,
            stroke_width=1.8,
        )
    )


def _draw_diamond(dwg, root, box, style: NodeStyle, config) -> None:
    cx = box.x + box.width / 2
    cy = box.y + box.height / 2
    pts = [
        (cx, box.y),
        (box.x + box.width, cy),
        (cx, box.y + box.height),
        (box.x, cy),
    ]
    root.add(
        dwg.polygon(
            points=pts,
            fill=style.fill,
            stroke=style.stroke,
            stroke_width=1.6,
        )
    )


def _draw_note(dwg, root, box, style: NodeStyle, config) -> None:
    f = NOTE_FOLD
    x, y, w, h = box.x, box.y, box.width, box.height
    d = (
        f"M{x},{y} L{x + w - f},{y} L{x + w},{y + f} "
        f"L{x + w},{y + h} L{x},{y + h} Z"
    )
    root.add(dwg.path(d=d, fill=style.fill, stroke=style.stroke, stroke_width=1.4))
    root.add(
        dwg.path(
            d=f"M{x + w - f},{y} L{x + w - f},{y + f} L{x + w},{y + f}",
            fill="none",
            stroke=style.stroke,
            stroke_width=1.0,
            opacity=0.6,
        )
    )
