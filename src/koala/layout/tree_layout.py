"""Motor de layout tipo árbol (top-down).

Retorna un `LayoutScene` con:
- `boxes`: nodos medidos y posicionados en jerarquía vertical.
- `edges`: aristas ortogonales (vertical-horizontal-vertical) con label.

Cómo funciona:
1. Mide nodos con utilidades compartidas.
2. Prueba variantes compactas o expandidas del árbol para acercarse a la hoja.
3. Calcula ancho de subárbol por nodo.
4. Asigna posiciones y devuelve la escena con mejor uso del espacio.
"""

from dataclasses import replace
from typing import Dict, List, Tuple

from koala.core.models import ConceptNode
from koala.layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig
from koala.layout.shared import (
    build_scene,
    get_content_min_width,
    get_h_gap_for_depth,
    get_preferred_content_width,
    get_v_gap_for_depth,
    iter_nodes,
    measure_node_box,
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


def _build_tree_scene_with_config(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_nodes(root_nodes, config, typography)

    for root in root_nodes:
        compute_tree_subtree_widths(root, boxes, config, typography)

    assign_tree_positions(root_nodes, boxes, config)
    edges = build_tree_edges(root_nodes, boxes, config)

    return build_scene(boxes, edges)


def _remeasure_box(
    node: ConceptNode,
    boxes: Dict[str, LayoutBox],
    width: float,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> None:
    current_box = boxes[node.number]
    measured = measure_node_box(node, current_box.depth, width, config, typography)
    measured.x = current_box.x
    measured.y = current_box.y
    measured.subtree_width = width
    boxes[node.number] = measured


def _scaled_tree_config(
    config: LayoutConfig,
    width_scale: float,
    h_gap_scale: float,
    v_gap_scale: float,
) -> LayoutConfig:
    root_width_delta = config.root_width_factor - 1.0
    scaled_root_width_factor = 1.0 + (root_width_delta * max(0.55, width_scale))

    return replace(
        config,
        node_width_base=config.node_width_base * width_scale,
        min_node_width=max(config.min_node_width * 0.72, config.min_node_width * width_scale),
        root_width_factor=max(1.0, scaled_root_width_factor),
        h_gap_base=max(10.0, config.h_gap_base * h_gap_scale),
        v_gap_base=max(10.0, config.v_gap_base * v_gap_scale),
    )


def _choose_parent_width(
    node: ConceptNode,
    box: LayoutBox,
    total_children_width: float,
    child_count: int,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    min_width = get_content_min_width(node, config, typography)
    width_factor = 1.0 if child_count == 1 else 0.90
    max_width = max(min_width, total_children_width * width_factor)
    preferred_width = max(min_width, get_preferred_content_width(node, config, typography))
    return min(preferred_width, max_width)


def _tree_scene_score(scene: LayoutScene, config: LayoutConfig) -> Tuple[float, float, float]:
    usable_w = max(1.0, config.page_width - (2 * config.margin_x))
    usable_h = max(1.0, config.page_height - (2 * config.margin_y))
    content_w = max(1.0, scene.content_right - scene.content_left)
    content_h = max(1.0, scene.content_bottom - scene.content_top)

    scale = min(usable_w / content_w, usable_h / content_h)
    fill_ratio = min(1.0, (content_w * scale) / usable_w) * min(1.0, (content_h * scale) / usable_h)
    return (scale * (0.65 + (0.35 * fill_ratio)), fill_ratio, scale)


def _choose_tree_scene(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    candidate_profiles = [
        (0.26, 0.40, 2.6),
        (0.34, 0.48, 2.1),
        (0.44, 0.56, 1.7),
        (0.58, 0.68, 1.4),
        (0.72, 0.80, 1.18),
        (0.86, 0.90, 1.06),
        (1.00, 1.00, 1.00),
        (1.08, 1.06, 0.95),
        (1.16, 1.12, 0.90),
    ]

    best_scene: LayoutScene | None = None
    best_score: Tuple[float, float, float] | None = None

    for width_scale, h_gap_scale, v_gap_scale in candidate_profiles:
        candidate_config = _scaled_tree_config(
            config,
            width_scale=width_scale,
            h_gap_scale=h_gap_scale,
            v_gap_scale=v_gap_scale,
        )
        candidate_scene = _build_tree_scene_with_config(root_nodes, candidate_config, typography)
        candidate_score = _tree_scene_score(candidate_scene, config)

        if best_scene is None or candidate_score > best_score:
            best_scene = candidate_scene
            best_score = candidate_score

    if best_scene is None:
        raise RuntimeError("No se pudo construir una escena para el layout tree.")

    return best_scene


def compute_tree_subtree_widths(
    node: ConceptNode,
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    box = boxes[node.number]

    if not node.children:
        box.subtree_width = box.width
        return box.subtree_width

    child_widths = [compute_tree_subtree_widths(child, boxes, config, typography) for child in node.children]
    h_gap = get_h_gap_for_depth(box.depth + 1, config)
    total_children_width = sum(child_widths) + (h_gap * (len(child_widths) - 1))

    target_width = _choose_parent_width(
        node,
        box,
        total_children_width,
        len(node.children),
        config,
        typography,
    )
    if abs(target_width - box.width) > 0.5:
        _remeasure_box(node, boxes, target_width, config, typography)
        box = boxes[node.number]

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
    return _choose_tree_scene(root_nodes, config, typography)
