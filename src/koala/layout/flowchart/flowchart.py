"""Motor de layout para diagramas de flujo tipo `flowchart`.

Estrategia: top-down en columnas.
- Se calcula la profundidad de cada nodo usando BFS desde los nodos de inicio.
- Los nodos de la misma profundidad se distribuyen horizontalmente centrados.
- Las aristas son rectas con un quiebre ortogonal cuando source y target
  no están alineados verticalmente.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Tuple

from koala.core.flowchart.models import FlowchartEdge, FlowchartNode, ParsedFlowchartDocument
from koala.layout.shared.measurement import build_scene, wrap_text_lines
from koala.layout.shared.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig


# Factores de tamaño por kind, relativos al nodo base.
_KIND_WIDTH_FACTOR: Dict[str, float] = {
    "start": 0.72,
    "end": 0.72,
    "process": 1.0,
    "decision": 1.12,
    "note": 0.90,
}
_KIND_HEIGHT_EXTRA: Dict[str, float] = {
    "start": 4.0,
    "end": 4.0,
    "process": 0.0,
    "decision": 8.0,
    "note": 0.0,
}

NODE_W = 100.0
NODE_H_MIN = 34.0
H_GAP = 20.0
V_GAP = 28.0


def build_flowchart_layout(
    parsed: ParsedFlowchartDocument,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    if not parsed.nodes:
        return build_scene({}, [])

    depth_map = _assign_depths(parsed)
    levels: Dict[int, List[str]] = defaultdict(list)
    for node_id, depth in depth_map.items():
        levels[depth].append(node_id)

    for depth in levels:
        levels[depth].sort(key=lambda nid: parsed.ordered_node_ids.index(nid))

    node_sizes = _measure_node_sizes(parsed.nodes, typography)
    positions = _assign_positions(levels, node_sizes, config)
    boxes = _build_boxes(parsed.nodes, positions, node_sizes, typography, config)
    edges = _build_edges(parsed.edges, boxes)

    return build_scene(boxes, edges)


def _assign_depths(parsed: ParsedFlowchartDocument) -> Dict[str, int]:
    start_ids = [n.node_id for n in parsed.nodes.values() if n.kind == "start"]
    if not start_ids:
        start_ids = parsed.ordered_node_ids[:1]

    depth: Dict[str, int] = {}
    queue: deque[str] = deque()

    for sid in start_ids:
        depth[sid] = 0
        queue.append(sid)

    successors: Dict[str, List[str]] = defaultdict(list)
    for edge in parsed.edges:
        successors[edge.source_id].append(edge.target_id)

    visited_edges: set[Tuple[str, str]] = set()

    while queue:
        current = queue.popleft()
        current_depth = depth[current]
        for nxt in successors[current]:
            if nxt not in parsed.nodes:
                continue
            edge_key = (current, nxt)
            if edge_key in visited_edges:
                continue
            visited_edges.add(edge_key)
            new_depth = current_depth + 1
            if nxt not in depth or depth[nxt] < new_depth:
                depth[nxt] = new_depth
                queue.append(nxt)

    for node_id in parsed.ordered_node_ids:
        if node_id not in depth:
            depth[node_id] = 0

    return depth


def _measure_node_sizes(
    nodes: Dict[str, FlowchartNode],
    typography: TypographyConfig,
) -> Dict[str, Tuple[float, float]]:
    sizes: Dict[str, Tuple[float, float]] = {}
    for node_id, node in nodes.items():
        w_factor = _KIND_WIDTH_FACTOR.get(node.kind, 1.0)
        h_extra = _KIND_HEIGHT_EXTRA.get(node.kind, 0.0)
        w = NODE_W * w_factor
        content_w = max(1.0, w - 12.0)
        lines = wrap_text_lines(node.label, typography.title_font, typography.body_size, content_w)
        line_count = max(1, len(lines))
        text_h = line_count * (typography.body_size + 3.2)
        h = max(NODE_H_MIN + h_extra, text_h + 16.0 + h_extra)
        sizes[node_id] = (w, h)
    return sizes


def _assign_positions(
    levels: Dict[int, List[str]],
    node_sizes: Dict[str, Tuple[float, float]],
    config: LayoutConfig,
) -> Dict[str, Tuple[float, float]]:
    max_depth = max(levels.keys(), default=0)

    level_widths: Dict[int, float] = {}
    for depth, node_ids in levels.items():
        total_w = sum(node_sizes[nid][0] for nid in node_ids)
        total_gaps = H_GAP * (len(node_ids) - 1)
        level_widths[depth] = total_w + total_gaps

    canvas_width = max(level_widths.values(), default=NODE_W)

    positions: Dict[str, Tuple[float, float]] = {}
    current_y = 0.0

    for depth in range(max_depth + 1):
        node_ids = levels.get(depth, [])
        if not node_ids:
            current_y += NODE_H_MIN + V_GAP
            continue

        row_width = level_widths[depth]
        start_x = (canvas_width - row_width) / 2.0
        level_h = max(node_sizes[nid][1] for nid in node_ids)

        x = start_x
        for nid in node_ids:
            w, _ = node_sizes[nid]
            positions[nid] = (x, current_y)
            x += w + H_GAP

        current_y += level_h + V_GAP

    return positions


def _build_boxes(
    nodes: Dict[str, FlowchartNode],
    positions: Dict[str, Tuple[float, float]],
    node_sizes: Dict[str, Tuple[float, float]],
    typography: TypographyConfig,
    config: LayoutConfig,
) -> Dict[str, LayoutBox]:
    boxes: Dict[str, LayoutBox] = {}
    for node_id, node in nodes.items():
        if node_id not in positions:
            continue
        x, y = positions[node_id]
        w, h = node_sizes[node_id]
        content_w = max(1.0, w - 12.0)
        lines = wrap_text_lines(node.label, typography.title_font, typography.body_size, content_w)
        if not lines:
            lines = [node.label]

        dummy_node = _DummyConceptNode(node)

        boxes[node_id] = LayoutBox(
            node=dummy_node,  # type: ignore[arg-type]
            depth=0,
            width=w,
            height=h,
            subtree_width=w,
            x=x,
            y=y,
            title_lines=lines,
            title_font_size=typography.body_size,
            title_height=len(lines) * (typography.body_size + 3.2),
            body_lines=[],
        )
    return boxes


def _build_edges(
    edges: List[FlowchartEdge],
    boxes: Dict[str, LayoutBox],
) -> List[LayoutEdge]:
    layout_edges: List[LayoutEdge] = []
    for edge in edges:
        if edge.source_id not in boxes or edge.target_id not in boxes:
            continue

        src = boxes[edge.source_id]
        tgt = boxes[edge.target_id]

        src_cx = src.x + src.width / 2
        src_bottom = src.y + src.height
        tgt_cx = tgt.x + tgt.width / 2
        tgt_top = tgt.y

        if abs(src_cx - tgt_cx) < 2.0:
            points = [(src_cx, src_bottom), (tgt_cx, tgt_top)]
        else:
            mid_y = (src_bottom + tgt_top) / 2
            points = [
                (src_cx, src_bottom),
                (src_cx, mid_y),
                (tgt_cx, mid_y),
                (tgt_cx, tgt_top),
            ]

        label_x = (src_cx + tgt_cx) / 2
        label_y = (src_bottom + tgt_top) / 2

        layout_edges.append(
            LayoutEdge(
                parent_number=edge.source_id,
                child_number=edge.target_id,
                points=points,
                relation_label=edge.label,
                label_pos=(label_x, label_y),
                label_max_width=60.0,
            )
        )

    return layout_edges


class _DummyConceptNode:
    """Shim que adapta FlowchartNode a la interfaz que espera LayoutBox."""

    def __init__(self, node: FlowchartNode) -> None:
        self._node = node
        self.number = node.node_id
        self.title = node.label
        self.kind = node.kind
        self.role = node.kind
        self.children: list = []
        self.parent = None

    def body_text(self) -> str:
        return self._node.body
