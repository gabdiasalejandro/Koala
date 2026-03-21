"""Motor de layout radial.

Retorna un `LayoutScene` con:
- `boxes`: raíz centrada y nodos distribuidos radialmente con compactación local.
- `edges`: aristas lineales entre nodos con flecha hacia el hijo y label.

Cómo funciona:
1. Mide nodos con utilidades compartidas.
2. Reparte ángulos usando una mezcla de peso estructural y huella visual.
3. Calcula radios base por profundidad para evitar solapes radial y tangencial.
4. Prueba varias rotaciones y elige la que mejor aprovecha la hoja.
5. Acerca nodos individualmente hacia el centro mientras sigan sin colisionar.
6. Construye aristas y devuelve escena final.
"""

import math
from typing import Dict, List, Tuple

from koala.core.models import ConceptNode
from koala.layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig
from koala.layout.shared import (
    build_scene,
    iter_nodes,
    measure_nodes,
    measure_text_width,
    sort_node_key,
    wrap_text_lines,
)


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


def box_center(box: LayoutBox) -> Tuple[float, float]:
    return box.x + (box.width / 2), box.y + (box.height / 2)


def rect_anchor_towards(box: LayoutBox, target_x: float, target_y: float) -> Tuple[float, float]:
    cx, cy = box_center(box)

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


def normalize_label_angle(angle: float) -> float:
    while angle <= -math.pi:
        angle += 2 * math.pi
    while angle > math.pi:
        angle -= 2 * math.pi

    if angle > math.pi / 2:
        angle -= math.pi
    elif angle < -math.pi / 2:
        angle += math.pi

    return angle


def rects_overlap(
    rect_a: Tuple[float, float, float, float],
    rect_b: Tuple[float, float, float, float],
    clearance: float,
) -> bool:
    return not (
        (rect_a[2] + clearance) <= rect_b[0]
        or (rect_b[2] + clearance) <= rect_a[0]
        or (rect_a[3] + clearance) <= rect_b[1]
        or (rect_b[3] + clearance) <= rect_a[1]
    )


def box_bounds(box: LayoutBox) -> Tuple[float, float, float, float]:
    return box.x, box.y, box.x + box.width, box.y + box.height


def edge_label_metrics(
    label: str,
    max_width: float,
    typography: TypographyConfig,
) -> Tuple[List[str], float, float]:
    lines = wrap_text_lines(
        label,
        typography.body_font,
        typography.relation_size,
        max_width,
    )
    measured_width = max(
        (measure_text_width(line, typography.body_font, typography.relation_size) for line in lines),
        default=0.0,
    )
    measured_height = typography.relation_size + max(0.0, (len(lines) - 1) * (typography.relation_size + 1))
    return lines, measured_width, measured_height


def rotated_text_bounds(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    angle: float,
) -> Tuple[float, float, float, float]:
    projected_half_width = (abs(math.cos(angle)) * width + abs(math.sin(angle)) * height) / 2
    projected_half_height = (abs(math.sin(angle)) * width + abs(math.cos(angle)) * height) / 2
    return (
        center_x - projected_half_width,
        center_y - projected_half_height,
        center_x + projected_half_width,
        center_y + projected_half_height,
    )


def resolve_radial_label_geometry(
    label: str,
    start: Tuple[float, float],
    end: Tuple[float, float],
    boxes: Dict[str, LayoutBox],
    typography: TypographyConfig,
    config: LayoutConfig,
    occupied_bounds: List[Tuple[float, float, float, float]],
) -> Tuple[Tuple[float, float], float, float, Tuple[float, float, float, float]]:
    def overlap_area(
        rect_a: Tuple[float, float, float, float],
        rect_b: Tuple[float, float, float, float],
    ) -> float:
        overlap_w = min(rect_a[2], rect_b[2]) - max(rect_a[0], rect_b[0])
        overlap_h = min(rect_a[3], rect_b[3]) - max(rect_a[1], rect_b[1])
        if overlap_w <= 0 or overlap_h <= 0:
            return 0.0
        return overlap_w * overlap_h

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = max(1e-6, math.hypot(dx, dy))
    tangent_x = dx / distance
    tangent_y = dy / distance
    normal_x = -tangent_y
    normal_y = tangent_x
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2
    center_x = config.page_width / 2
    center_y = config.page_height / 2
    radial_x = mid_x - center_x
    radial_y = mid_y - center_y

    if (normal_x * radial_x) + (normal_y * radial_y) < 0:
        normal_x *= -1
        normal_y *= -1

    preferred_width = min(
        max(70.0, measure_text_width(label, typography.body_font, typography.relation_size) + 10.0),
        max(70.0, distance * 1.25),
    )
    lines, label_width, label_height = edge_label_metrics(label, preferred_width, typography)
    if not lines:
        zero_bounds = (mid_x, mid_y, mid_x, mid_y)
        return (mid_x, mid_y - 2), preferred_width, 0.0, zero_bounds

    angle_aligned = normalize_label_angle(math.atan2(dy, dx))
    angle_candidates = [angle_aligned]
    if abs(angle_aligned) > math.radians(12):
        angle_candidates.append(0.0)
    else:
        angle_candidates.extend([0.0, math.radians(90.0)])

    offset_candidates = [12.0, 20.0, 30.0, 42.0, 56.0, 72.0]
    tangent_shift_candidates = [0.0, 12.0, -12.0, 24.0, -24.0]
    normal_sides = [1.0, -1.0]
    box_bounds_list = [box_bounds(box) for box in boxes.values()]
    best_choice: Tuple[Tuple[float, float], float, Tuple[float, float, float, float], Tuple[int, float, float]] | None = None

    for angle in angle_candidates:
        for normal_side in normal_sides:
            for offset in offset_candidates:
                for tangent_shift in tangent_shift_candidates:
                    candidate_center_x = (
                        mid_x
                        + (normal_x * offset * normal_side)
                        + (tangent_x * tangent_shift)
                    )
                    candidate_center_y = (
                        mid_y
                        + (normal_y * offset * normal_side)
                        + (tangent_y * tangent_shift)
                    )
                    candidate_bounds = rotated_text_bounds(
                        candidate_center_x,
                        candidate_center_y,
                        label_width,
                        label_height,
                        angle,
                    )

                    collision_count = 0
                    total_overlap_area = 0.0

                    for candidate_box_bounds in box_bounds_list:
                        if not rects_overlap(candidate_bounds, candidate_box_bounds, 4.0):
                            continue
                        collision_count += 1
                        total_overlap_area += overlap_area(candidate_bounds, candidate_box_bounds)

                    for other_bounds in occupied_bounds:
                        if not rects_overlap(candidate_bounds, other_bounds, 3.0):
                            continue
                        collision_count += 1
                        total_overlap_area += overlap_area(candidate_bounds, other_bounds)

                    score = (
                        collision_count,
                        total_overlap_area,
                        offset + abs(tangent_shift) + (abs(angle) * 10.0) + (0.5 if normal_side < 0 else 0.0),
                    )
                    if best_choice is None or score < best_choice[3]:
                        best_choice = (
                            (candidate_center_x, candidate_center_y),
                            angle,
                            candidate_bounds,
                            score,
                        )

                    if collision_count == 0:
                        break
                if best_choice is not None and best_choice[3][0] == 0:
                    break
            if best_choice is not None and best_choice[3][0] == 0:
                break
        if best_choice is not None and best_choice[3][0] == 0:
            break

    assert best_choice is not None
    chosen_center, chosen_angle, chosen_bounds, _ = best_choice
    start_y = chosen_center[1] - (label_height / 2) + typography.relation_size
    return (chosen_center[0], start_y), preferred_width, math.degrees(chosen_angle), chosen_bounds


def build_radial_edges(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> List[LayoutEdge]:
    edges: List[LayoutEdge] = []
    occupied_label_bounds: List[Tuple[float, float, float, float]] = []

    for node in iter_nodes(root_nodes):
        if node.parent is None:
            continue

        parent = boxes[node.parent.number]
        child = boxes[node.number]

        parent_center = box_center(parent)
        child_center = box_center(child)

        start = rect_anchor_towards(parent, child_center[0], child_center[1])
        end = rect_anchor_towards(child, parent_center[0], parent_center[1])

        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        distance = math.hypot(end[0] - start[0], end[1] - start[1])
        label_pos = (mid_x, mid_y - 2)
        label_max_width = max(70.0, distance * 0.8)
        label_angle = 0.0
        label_bounds = None

        if node.relation_from_parent:
            label_pos, label_max_width, label_angle, label_bounds = resolve_radial_label_geometry(
                node.relation_from_parent,
                start,
                end,
                boxes,
                typography,
                config,
                occupied_label_bounds,
            )
            occupied_label_bounds.append(label_bounds)

        edges.append(
            LayoutEdge(
                parent_number=node.parent.number,
                child_number=node.number,
                points=[start, end],
                relation_label=node.relation_from_parent,
                label_pos=label_pos,
                label_max_width=label_max_width,
                label_angle=label_angle,
                label_bounds=label_bounds,
            )
        )

    return edges


def compute_subtree_weights(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    footprint_reference = max(config.min_node_width, config.node_width_base * 0.9)

    def visit(node: ConceptNode) -> float:
        box = boxes[node.number]
        self_weight = max(1.0, box_footprint(box) / footprint_reference)
        children = ordered_children(node)

        if not children:
            weights[node.number] = self_weight
            return self_weight

        child_weight = sum(visit(child) for child in children)
        weights[node.number] = max(child_weight, self_weight * 0.9)
        return weights[node.number]

    for root in root_nodes:
        visit(root)

    return weights


def assign_angles(
    node: ConceptNode,
    start_angle: float,
    end_angle: float,
    weights: Dict[str, float],
    angles: Dict[str, float],
) -> None:
    angles[node.number] = (start_angle + end_angle) / 2

    children = ordered_children(node)
    if not children:
        return

    children_weight = sum(weights.get(child.number, 0.0) for child in children)
    if children_weight <= 0:
        return

    cursor = start_angle
    angle_span = end_angle - start_angle

    for child in children:
        portion = weights.get(child.number, 0.0) / children_weight
        child_span = angle_span * portion
        assign_angles(child, cursor, cursor + child_span, weights, angles)
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


def assign_node_angles(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
    rotation_offset: float,
) -> Dict[str, float]:
    roots = sorted(root_nodes, key=lambda node: sort_node_key(node.number))
    weights = compute_subtree_weights(roots, boxes, config)
    angles: Dict[str, float] = {}
    start_angle = -math.pi / 2 + rotation_offset

    if len(roots) == 1:
        root = roots[0]
        children = ordered_children(root)

        if children:
            total = sum(weights.get(child.number, 0.0) for child in children)
            cursor = start_angle
            for child in children:
                child_span = (2 * math.pi) * (weights.get(child.number, 0.0) / total)
                assign_angles(child, cursor, cursor + child_span, weights, angles)
                cursor += child_span
    else:
        total = sum(weights.get(root.number, 0.0) for root in roots)
        cursor = start_angle
        for root in roots:
            root_span = (2 * math.pi) * (weights.get(root.number, 0.0) / total)
            assign_angles(root, cursor, cursor + root_span, weights, angles)
            cursor += root_span

    return angles


def compute_depth_radii(
    depth_groups: Dict[int, List[LayoutBox]],
    angles: Dict[str, float],
    config: LayoutConfig,
) -> Dict[int, float]:
    max_depth = max(depth_groups.keys(), default=0)
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

    return radii


def resolve_node_angle(node: ConceptNode, angles: Dict[str, float]) -> float:
    angle = angles.get(node.number)
    if angle is not None:
        return angle

    if node.parent is not None:
        return angles.get(node.parent.number, -math.pi / 2)

    return -math.pi / 2


def root_ring_radius(depth_groups: Dict[int, List[LayoutBox]], config: LayoutConfig) -> float:
    return max(max_box_dim(depth_groups.get(0, [])), config.h_gap_base * 1.5)


def build_node_radii(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    depth_groups: Dict[int, List[LayoutBox]],
    depth_radii: Dict[int, float],
    config: LayoutConfig,
) -> Dict[str, float]:
    roots = sorted(root_nodes, key=lambda node: sort_node_key(node.number))
    node_radii: Dict[str, float] = {}
    root_radius = root_ring_radius(depth_groups, config)

    for node in iter_nodes(roots):
        box = boxes[node.number]
        if len(roots) == 1 and box.depth == 0:
            node_radii[node.number] = 0.0
            continue

        if box.depth == 0:
            node_radii[node.number] = root_radius
            continue

        node_radii[node.number] = depth_radii.get(box.depth, 0.0)

    return node_radii


def place_box_on_ray(
    box: LayoutBox,
    center_x: float,
    center_y: float,
    angle: float,
    radius: float,
) -> None:
    x = center_x + (radius * math.cos(angle))
    y = center_y + (radius * math.sin(angle))
    box.x = x - (box.width / 2)
    box.y = y - (box.height / 2)


def place_radial_boxes(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    node_radii: Dict[str, float],
    angles: Dict[str, float],
    config: LayoutConfig,
) -> None:
    roots = sorted(root_nodes, key=lambda node: sort_node_key(node.number))
    center_x = config.page_width / 2
    center_y = config.page_height / 2

    if len(roots) == 1 and roots:
        root = roots[0]
        root_box = boxes[root.number]
        root_box.x = center_x - (root_box.width / 2)
        root_box.y = center_y - (root_box.height / 2)

    for node in iter_nodes(roots):
        box = boxes[node.number]

        if len(roots) == 1 and box.depth == 0:
            continue

        angle = resolve_node_angle(node, angles)
        radius = node_radii.get(node.number, 0.0)
        place_box_on_ray(box, center_x, center_y, angle, radius)


def boxes_overlap(a: LayoutBox, b: LayoutBox, clearance: float) -> bool:
    return not (
        (a.x + a.width + clearance) <= b.x
        or (b.x + b.width + clearance) <= a.x
        or (a.y + a.height + clearance) <= b.y
        or (b.y + b.height + clearance) <= a.y
    )


def collides_with_any(
    candidate: LayoutBox,
    boxes: Dict[str, LayoutBox],
    clearance: float,
) -> bool:
    for other in boxes.values():
        if other.node.number == candidate.node.number:
            continue
        if boxes_overlap(candidate, other, clearance):
            return True
    return False


def minimum_node_radius(
    node: ConceptNode,
    boxes: Dict[str, LayoutBox],
    node_radii: Dict[str, float],
    angle: float,
    config: LayoutConfig,
) -> float:
    if node.parent is None:
        return node_radii.get(node.number, 0.0)

    parent_box = boxes[node.parent.number]
    child_box = boxes[node.number]
    parent_radius = node_radii.get(node.parent.number, 0.0)
    parent_extent = max(parent_box.width, parent_box.height) / 2 if parent_radius <= 1e-6 else radial_half_extent(parent_box, angle)
    child_extent = radial_half_extent(child_box, angle)
    gap = max(4.0, max(config.h_gap_base, config.v_gap_base) * 0.28)
    return parent_radius + parent_extent + child_extent + gap


def compact_node_radii(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    node_radii: Dict[str, float],
    angles: Dict[str, float],
    config: LayoutConfig,
) -> None:
    center_x = config.page_width / 2
    center_y = config.page_height / 2
    clearance = max(2.0, min(config.h_gap_base, config.v_gap_base) * 0.16)

    movable_nodes = [
        node
        for node in iter_nodes(root_nodes)
        if node.parent is not None
    ]
    movable_nodes.sort(key=lambda node: (boxes[node.number].depth, angles.get(node.number, -math.pi / 2)))

    for node in movable_nodes:
        box = boxes[node.number]
        angle = resolve_node_angle(node, angles)
        current_radius = node_radii.get(node.number, 0.0)
        minimum_radius = minimum_node_radius(node, boxes, node_radii, angle, config)

        if current_radius - minimum_radius <= 1.0:
            continue

        best_radius = current_radius
        low = minimum_radius
        high = current_radius

        for _ in range(18):
            trial_radius = (low + high) / 2
            place_box_on_ray(box, center_x, center_y, angle, trial_radius)
            if collides_with_any(box, boxes, clearance):
                low = trial_radius
            else:
                best_radius = trial_radius
                high = trial_radius

        node_radii[node.number] = best_radius
        place_box_on_ray(box, center_x, center_y, angle, best_radius)


def layout_score(scene: LayoutScene, config: LayoutConfig) -> Tuple[float, float, float]:
    usable_w = config.page_width - (2 * config.margin_x)
    usable_h = config.page_height - (2 * config.margin_y)
    content_w = max(1.0, scene.content_right - scene.content_left)
    content_h = max(1.0, scene.content_bottom - scene.content_top)
    scale = min(usable_w / content_w, usable_h / content_h)
    scaled_fill = ((content_w * scale) * (content_h * scale)) / max(1.0, usable_w * usable_h)
    aspect_delta = abs((content_w / content_h) - (usable_w / usable_h))
    return scale, scaled_fill, -aspect_delta


def assign_radial_positions(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> None:
    if not boxes:
        return

    depth_groups: Dict[int, List[LayoutBox]] = {}
    for box in boxes.values():
        depth_groups.setdefault(box.depth, []).append(box)

    rotation_steps = 12
    best_rotation = 0.0
    best_score: Tuple[float, float, float] | None = None

    for step in range(rotation_steps):
        rotation_offset = (2 * math.pi * step) / rotation_steps
        angles = assign_node_angles(root_nodes, boxes, config, rotation_offset)
        depth_radii = compute_depth_radii(depth_groups, angles, config)
        node_radii = build_node_radii(root_nodes, boxes, depth_groups, depth_radii, config)
        place_radial_boxes(root_nodes, boxes, node_radii, angles, config)
        compact_node_radii(root_nodes, boxes, node_radii, angles, config)
        score = layout_score(build_scene(boxes, []), config)

        if best_score is None or score > best_score:
            best_score = score
            best_rotation = rotation_offset

    angles = assign_node_angles(root_nodes, boxes, config, best_rotation)
    depth_radii = compute_depth_radii(depth_groups, angles, config)
    node_radii = build_node_radii(root_nodes, boxes, depth_groups, depth_radii, config)
    place_radial_boxes(root_nodes, boxes, node_radii, angles, config)
    compact_node_radii(root_nodes, boxes, node_radii, angles, config)


def build_radial_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_nodes(root_nodes, config, typography)

    assign_radial_positions(root_nodes, boxes, config)
    edges = build_radial_edges(root_nodes, boxes, config, typography)

    return build_scene(boxes, edges)
