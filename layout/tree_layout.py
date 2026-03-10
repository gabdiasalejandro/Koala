"""Motor de layout tipo árbol (top-down).

Retorna un `LayoutScene` con:
- `boxes`: nodos medidos y posicionados en jerarquía vertical.
- `edges`: aristas ortogonales (vertical-horizontal-vertical) con label.

Cómo funciona:
1. Mide nodos con utilidades compartidas.
2. Calcula ancho de subárbol por nodo.
3. Asigna posiciones de izquierda a derecha por raíces.
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


def build_tree_edges(
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

        x1 = parent.x + (parent.width / 2)
        y1 = parent.y + parent.height
        x2 = child.x + (child.width / 2)
        y2 = child.y
        y_mid = y1 + (get_v_gap_for_depth(child.depth, config) / 2)

        edges.append(
            LayoutEdge(
                parent_number=node.parent.number,
                child_number=node.number,
                points=[(x1, y1), (x1, y_mid), (x2, y_mid), (x2, y2)],
                relation_label=node.relation_from_parent,
                label_pos=((x1 + x2) / 2, y_mid - 3),
                label_max_width=max(70.0, abs(x2 - x1) + 30.0),
            )
        )

    return edges


def compute_tree_subtree_widths(
    node: ConceptNode,
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> float:
    box = boxes[node.number]

    if not node.children:
        box.subtree_width = box.width
        return box.subtree_width

    child_widths = [compute_tree_subtree_widths(child, boxes, config) for child in node.children]
    h_gap = get_h_gap_for_depth(box.depth + 1, config)
    total_children_width = sum(child_widths) + (h_gap * (len(child_widths) - 1))

    box.subtree_width = max(box.width, total_children_width)
    return box.subtree_width


def assign_tree_positions(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> None:
    current_x = config.margin_x

    def place(node: ConceptNode, left: float, top: float) -> None:
        box = boxes[node.number]

        box.x = left + ((box.subtree_width - box.width) / 2)
        box.y = top

        if not node.children:
            return

        h_gap = get_h_gap_for_depth(box.depth + 1, config)
        v_gap = get_v_gap_for_depth(box.depth + 1, config)

        total_children_width = sum(boxes[child.number].subtree_width for child in node.children)
        total_children_width += h_gap * (len(node.children) - 1)

        child_left = left + ((box.subtree_width - total_children_width) / 2)
        next_top = box.y + box.height + v_gap

        for child in node.children:
            child_box = boxes[child.number]
            place(child, child_left, next_top)
            child_left += child_box.subtree_width + h_gap

    for root in root_nodes:
        place(root, current_x, config.margin_y)
        current_x += boxes[root.number].subtree_width + config.h_gap_base


def build_tree_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_nodes(root_nodes, config, typography)

    for root in root_nodes:
        compute_tree_subtree_widths(root, boxes, config)

    assign_tree_positions(root_nodes, boxes, config)
    edges = build_tree_edges(root_nodes, boxes, config)

    return build_scene(boxes, edges)
