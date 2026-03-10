"""Motor de layout tipo cuadro sinóptico.

Retorna un `LayoutScene` con:
- `boxes`: nodos medidos y posicionados en columnas (izquierda a derecha).
- `edges`: aristas ortogonales (horizontal-vertical-horizontal) con label.

Cómo funciona:
1. Mide nodos con utilidades compartidas.
2. Calcula altura de subárbol para cada nodo.
3. Posiciona nodos por columnas respetando la altura total de cada rama.
4. Construye aristas y devuelve escena final.
"""

from typing import Dict, List

from core.models import ConceptNode
from layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig
from layout.shared import (
    build_scene,
    get_h_gap_for_depth,
    get_v_gap_for_depth,
    iter_nodes,
    measure_nodes,
)


def build_synoptic_edges(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> List[LayoutEdge]:
    edges: List[LayoutEdge] = []

    for node in iter_nodes(root_nodes):
        if node.parent is None:
            continue

        parent = boxes[node.parent.number]
        child = boxes[node.number]

        x1 = parent.x + parent.width
        y1 = parent.y + (parent.height / 2)
        x2 = child.x
        y2 = child.y + (child.height / 2)
        x_mid = x1 + (get_h_gap_for_depth(child.depth, config) / 2)

        edges.append(
            LayoutEdge(
                parent_number=node.parent.number,
                child_number=node.number,
                points=[(x1, y1), (x_mid, y1), (x_mid, y2), (x2, y2)],
                relation_label=node.relation_from_parent,
                label_pos=(x_mid, ((y1 + y2) / 2) - 2),
                label_max_width=max(70.0, abs(y2 - y1) + 30.0),
            )
        )

    return edges


def compute_synoptic_subtree_heights(
    node: ConceptNode,
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
    subtree_heights: Dict[str, float],
) -> float:
    box = boxes[node.number]

    if not node.children:
        subtree_heights[node.number] = box.height
        return box.height

    child_heights = [compute_synoptic_subtree_heights(child, boxes, config, subtree_heights) for child in node.children]
    v_gap = get_v_gap_for_depth(box.depth + 1, config)
    children_total = sum(child_heights) + (v_gap * (len(child_heights) - 1))

    subtree_height = max(box.height, children_total)
    subtree_heights[node.number] = subtree_height
    return subtree_height


def assign_synoptic_positions(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
    subtree_heights: Dict[str, float],
) -> None:
    current_top = config.margin_y

    def place(node: ConceptNode, left: float, top: float, subtree_height: float) -> None:
        box = boxes[node.number]

        box.x = left
        box.y = top + ((subtree_height - box.height) / 2)

        if not node.children:
            return

        h_gap = get_h_gap_for_depth(box.depth + 1, config)
        v_gap = get_v_gap_for_depth(box.depth + 1, config)

        children_total = sum(subtree_heights[child.number] for child in node.children)
        children_total += v_gap * (len(node.children) - 1)

        child_top = top + ((subtree_height - children_total) / 2)
        next_left = box.x + box.width + h_gap

        for child in node.children:
            child_subtree_height = subtree_heights[child.number]
            place(child, next_left, child_top, child_subtree_height)
            child_top += child_subtree_height + v_gap

    for root in root_nodes:
        root_subtree_height = subtree_heights[root.number]
        place(root, config.margin_x, current_top, root_subtree_height)
        current_top += root_subtree_height + config.v_gap_base


def build_synoptic_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_nodes(root_nodes, config, typography)

    subtree_heights: Dict[str, float] = {}
    for root in root_nodes:
        compute_synoptic_subtree_heights(root, boxes, config, subtree_heights)

    assign_synoptic_positions(root_nodes, boxes, config, subtree_heights)
    edges = build_synoptic_edges(root_nodes, boxes, config)

    return build_scene(boxes, edges)
