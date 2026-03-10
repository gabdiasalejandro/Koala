"""Motor de layout radial.

Retorna un `LayoutScene` con:
- `boxes`: raíz centrada y nodos distribuidos en anillos sin solaparse.
- `edges`: aristas lineales entre nodos con flecha hacia el hijo y label.

Cómo funciona:
1. Mide nodos con utilidades compartidas.
2. Reparte ángulos por subárbol (tipo estrella/copo) usando hojas.
3. Calcula radios por profundidad para evitar solapes radial y tangencial.
4. La rama más profunda fija el radio externo final del diagrama.
5. Construye aristas y devuelve escena final.
"""

import math
from typing import Dict, List, Tuple

from core.models import ConceptNode
from layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig
from layout.shared import build_scene, iter_nodes, measure_nodes, sort_node_key


def ordered_children(node: ConceptNode) -> List[ConceptNode]:
    return sorted(node.children, key=lambda item: sort_node_key(item.number))


def box_footprint(box: LayoutBox) -> float:
    return math.hypot(box.width, box.height)


def max_box_dim(boxes: List[LayoutBox]) -> float:
    if not boxes:
        return 0.0
    return max(max(box.width, box.height) for box in boxes)


def radial_half_extent(box: LayoutBox, angle: float) -> float:
    return abs(math.cos(angle)) * (box.width / 2) + abs(math.sin(angle)) * (box.height / 2)


def tangential_half_extent(box: LayoutBox, angle: float) -> float:
    return abs(math.sin(angle)) * (box.width / 2) + abs(math.cos(angle)) * (box.height / 2)


def angle_diff_positive(a_from: float, a_to: float) -> float:
    return (a_to - a_from) % (2 * math.pi)


def rect_anchor_towards(box: LayoutBox, target_x: float, target_y: float) -> Tuple[float, float]:
    cx = box.x + (box.width / 2)
    cy = box.y + (box.height / 2)

    dx = target_x - cx
    dy = target_y - cy

    if abs(dx) < 1e-8 and abs(dy) < 1e-8:
        return cx, cy

    half_w = box.width / 2
    half_h = box.height / 2

    tx = float("inf") if abs(dx) < 1e-8 else half_w / abs(dx)
    ty = float("inf") if abs(dy) < 1e-8 else half_h / abs(dy)
    t = min(tx, ty)

    return cx + (dx * t), cy + (dy * t)


def build_radial_edges(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
) -> List[LayoutEdge]:
    edges: List[LayoutEdge] = []

    for node in iter_nodes(root_nodes):
        if node.parent is None:
            continue

        parent = boxes[node.parent.number]
        child = boxes[node.number]

        parent_center = (parent.x + (parent.width / 2), parent.y + (parent.height / 2))
        child_center = (child.x + (child.width / 2), child.y + (child.height / 2))

        start = rect_anchor_towards(parent, child_center[0], child_center[1])
        end = rect_anchor_towards(child, parent_center[0], parent_center[1])

        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        distance = math.hypot(end[0] - start[0], end[1] - start[1])

        edges.append(
            LayoutEdge(
                parent_number=node.parent.number,
                child_number=node.number,
                points=[start, end],
                relation_label=node.relation_from_parent,
                label_pos=(mid_x, mid_y - 2),
                label_max_width=max(70.0, distance * 0.8),
            )
        )

    return edges


def count_leaves(node: ConceptNode, leaf_counts: Dict[str, int]) -> int:
    children = ordered_children(node)
    if not children:
        leaf_counts[node.number] = 1
        return 1

    total = sum(count_leaves(child, leaf_counts) for child in children)
    leaf_counts[node.number] = total
    return total


def assign_angles(
    node: ConceptNode,
    start_angle: float,
    end_angle: float,
    leaf_counts: Dict[str, int],
    angles: Dict[str, float],
) -> None:
    angles[node.number] = (start_angle + end_angle) / 2

    children = ordered_children(node)
    if not children:
        return

    children_leaves = sum(leaf_counts[child.number] for child in children)
    if children_leaves <= 0:
        return

    cursor = start_angle
    angle_span = end_angle - start_angle

    for child in children:
        portion = leaf_counts[child.number] / children_leaves
        child_span = angle_span * portion
        assign_angles(child, cursor, cursor + child_span, leaf_counts, angles)
        cursor += child_span


def min_radial_step(
    prev_level_boxes: List[LayoutBox],
    current_level_boxes: List[LayoutBox],
    angles: Dict[str, float],
    config: LayoutConfig,
) -> float:
    if not prev_level_boxes or not current_level_boxes:
        return max(config.v_gap_base, config.h_gap_base) * 0.4

    prev_extent = 0.0
    for box in prev_level_boxes:
        if box.depth == 0:
            extent = max(box.width, box.height) / 2
        else:
            extent = radial_half_extent(box, angles.get(box.node.number, 0.0))
        prev_extent = max(prev_extent, extent)

    curr_extent = 0.0
    for box in current_level_boxes:
        extent = radial_half_extent(box, angles.get(box.node.number, 0.0))
        curr_extent = max(curr_extent, extent)

    base_gap = max(config.v_gap_base, config.h_gap_base) * 0.45
    return prev_extent + curr_extent + base_gap


def required_radius_for_tangential_separation(
    level_boxes: List[LayoutBox],
    angles: Dict[str, float],
    current_radius: float,
    config: LayoutConfig,
) -> float:
    if len(level_boxes) < 2:
        return current_radius

    ordered = sorted(level_boxes, key=lambda box: angles.get(box.node.number, -math.pi / 2))
    tangential_gap = max(config.h_gap_base * 0.35, 4.0)

    required_radius = current_radius

    for index, box_a in enumerate(ordered):
        box_b = ordered[(index + 1) % len(ordered)]

        a1 = angles.get(box_a.node.number, -math.pi / 2)
        a2 = angles.get(box_b.node.number, -math.pi / 2)

        delta = angle_diff_positive(a1, a2)
        if delta < 1e-4:
            delta = 1e-4

        mid_angle = (a1 + (delta / 2)) % (2 * math.pi)
        required_chord = (
            tangential_half_extent(box_a, mid_angle)
            + tangential_half_extent(box_b, mid_angle)
            + tangential_gap
        )
        denom = 2 * math.sin(delta / 2)

        if abs(denom) < 1e-4:
            pair_radius = required_chord / 1e-4
        else:
            pair_radius = required_chord / denom

        required_radius = max(required_radius, pair_radius)

    return required_radius


def assign_radial_positions(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> None:
    if not boxes:
        return

    roots = sorted(root_nodes, key=lambda node: sort_node_key(node.number))

    leaf_counts: Dict[str, int] = {}
    for root in roots:
        count_leaves(root, leaf_counts)

    angles: Dict[str, float] = {}

    if len(roots) == 1:
        root = roots[0]
        children = ordered_children(root)

        if children:
            total = sum(leaf_counts[child.number] for child in children)
            cursor = -math.pi / 2
            for child in children:
                child_span = (2 * math.pi) * (leaf_counts[child.number] / total)
                assign_angles(child, cursor, cursor + child_span, leaf_counts, angles)
                cursor += child_span
    else:
        total = sum(leaf_counts[root.number] for root in roots)
        cursor = -math.pi / 2
        for root in roots:
            root_span = (2 * math.pi) * (leaf_counts[root.number] / total)
            assign_angles(root, cursor, cursor + root_span, leaf_counts, angles)
            cursor += root_span

    depth_groups: Dict[int, List[LayoutBox]] = {}
    for box in boxes.values():
        depth_groups.setdefault(box.depth, []).append(box)

    max_depth = max(depth_groups.keys())

    radii: Dict[int, float] = {0: 0.0}
    for depth in range(1, max_depth + 1):
        prev_level = depth_groups.get(depth - 1, [])
        current_level = depth_groups.get(depth, [])
        radii[depth] = radii[depth - 1] + min_radial_step(prev_level, current_level, angles, config)

    for depth in range(1, max_depth + 1):
        current_level = depth_groups.get(depth, [])
        radii[depth] = required_radius_for_tangential_separation(current_level, angles, radii[depth], config)

    for depth in range(1, max_depth + 1):
        prev_level = depth_groups.get(depth - 1, [])
        current_level = depth_groups.get(depth, [])
        radii[depth] = max(radii[depth], radii[depth - 1] + min_radial_step(prev_level, current_level, angles, config))

    center_x = config.page_width / 2
    center_y = config.page_height / 2

    if len(roots) == 1:
        root = roots[0]
        root_box = boxes[root.number]
        root_box.x = center_x - (root_box.width / 2)
        root_box.y = center_y - (root_box.height / 2)

    for node in iter_nodes(roots):
        box = boxes[node.number]

        if len(roots) == 1 and box.depth == 0:
            continue

        angle = angles.get(node.number)
        if angle is None:
            if node.parent is not None:
                angle = angles.get(node.parent.number, -math.pi / 2)
            else:
                angle = -math.pi / 2

        if box.depth == 0:
            root_radius = max_box_dim(depth_groups.get(0, []))
            radius = max(root_radius, config.h_gap_base * 1.5)
        else:
            radius = radii.get(box.depth, radii.get(max_depth, 0.0))

        x = center_x + (radius * math.cos(angle))
        y = center_y + (radius * math.sin(angle))

        box.x = x - (box.width / 2)
        box.y = y - (box.height / 2)


def build_radial_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_nodes(root_nodes, config, typography)

    assign_radial_positions(root_nodes, boxes, config)
    edges = build_radial_edges(root_nodes, boxes)

    return build_scene(boxes, edges)
