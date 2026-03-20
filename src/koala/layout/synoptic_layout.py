"""Motor de layout tipo cuadro sinoptico con corchetes.

Retorna un `LayoutScene` con:
- `boxes`: nodos posicionados por columnas igual que el sinoptico clasico.
- `edges`: conectores con forma de corchete para agrupar hijos.

Como funciona:
1. Reutiliza la medicion y posicionamiento del layout sinoptico.
2. Construye un corchete por grupo de hijos en lugar de una arista por hijo.
3. Omite labels de relacion porque este layout prioriza agrupacion visual.
"""

from typing import Dict, List

from koala.core.models import ConceptNode
from koala.layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig
from koala.layout.shared import build_scene, get_h_gap_for_depth, measure_nodes, sort_node_key
from koala.layout.synoptic_boxes_layout import assign_synoptic_box_positions, compute_synoptic_box_subtree_heights


def build_synoptic_edges(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> List[LayoutEdge]:
    edges: List[LayoutEdge] = []

    for root in sorted(root_nodes, key=lambda node: sort_node_key(node.number)):
        for node in _iter_nodes_in_order(root):
            if not node.children:
                continue

            parent = boxes[node.number]
            ordered_children = sorted(node.children, key=lambda child: sort_node_key(child.number))
            child_boxes = [boxes[child.number] for child in ordered_children]

            group_top = min(child.y for child in child_boxes)
            group_bottom = max(child.y + child.height for child in child_boxes)

            parent_anchor_x = parent.x + parent.width
            parent_anchor_y = parent.y + (parent.height / 2)
            h_gap = get_h_gap_for_depth(parent.depth + 1, config)
            bracket_x = parent_anchor_x + max(14.0, h_gap * 0.55)
            hook = max(8.0, h_gap * 0.22)

            edges.append(
                LayoutEdge(
                    parent_number=node.number,
                    child_number=ordered_children[0].number,
                    points=[
                        (parent_anchor_x, parent_anchor_y),
                        (bracket_x, group_top),
                        (bracket_x + hook, group_top),
                        (bracket_x, group_bottom),
                        (bracket_x + hook, group_bottom),
                    ],
                    relation_label="",
                    label_pos=(0.0, 0.0),
                    label_max_width=0.0,
                )
            )

    return edges


def build_synoptic_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_nodes(root_nodes, config, typography)

    subtree_heights: Dict[str, float] = {}
    for root in root_nodes:
        compute_synoptic_box_subtree_heights(root, boxes, config, subtree_heights)

    assign_synoptic_box_positions(root_nodes, boxes, config, subtree_heights)
    edges = build_synoptic_edges(root_nodes, boxes, config)

    return build_scene(boxes, edges)


def _iter_nodes_in_order(node: ConceptNode):
    yield node
    for child in sorted(node.children, key=lambda item: sort_node_key(item.number)):
        yield from _iter_nodes_in_order(child)
