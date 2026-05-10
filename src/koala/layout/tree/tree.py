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

from koala.core.tree.models import ConceptNode
from koala.layout.shared.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig
from koala.layout.shared.measurement import (
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


class _WalkerNode:
    """Nodo auxiliar para Walker/Buchheim layout linear."""

    __slots__ = (
        "node",
        "box",
        "children",
        "parent",
        "number",
        "prelim",
        "mod",
        "shift",
        "change",
        "thread",
        "ancestor",
    )

    def __init__(self, node: ConceptNode, box: LayoutBox) -> None:
        self.node = node
        self.box = box
        self.children: List["_WalkerNode"] = []
        self.parent: "_WalkerNode" | None = None
        self.number: int = 0
        self.prelim: float = 0.0
        self.mod: float = 0.0
        self.shift: float = 0.0
        self.change: float = 0.0
        self.thread: "_WalkerNode" | None = None
        self.ancestor: "_WalkerNode" = self


def _build_walker_tree(root: ConceptNode, boxes: Dict[str, LayoutBox]) -> _WalkerNode:
    walker_root = _WalkerNode(root, boxes[root.number])

    def build(parent_walker: _WalkerNode, parent_node: ConceptNode) -> None:
        for index, child in enumerate(parent_node.children):
            child_walker = _WalkerNode(child, boxes[child.number])
            child_walker.parent = parent_walker
            child_walker.number = index
            child_walker.ancestor = child_walker
            parent_walker.children.append(child_walker)
            build(child_walker, child)

    build(walker_root, root)
    return walker_root


def _walker_distance(a: _WalkerNode, b: _WalkerNode, config: LayoutConfig) -> float:
    h_gap = get_h_gap_for_depth(a.box.depth, config)
    return (a.box.width + b.box.width) / 2 + h_gap


def _next_left(v: _WalkerNode) -> _WalkerNode | None:
    if v.children:
        return v.children[0]
    return v.thread


def _next_right(v: _WalkerNode) -> _WalkerNode | None:
    if v.children:
        return v.children[-1]
    return v.thread


def _walker_ancestor(
    v_inner_right: _WalkerNode,
    v: _WalkerNode,
    default_ancestor: _WalkerNode,
) -> _WalkerNode:
    if v.parent is not None and v_inner_right.ancestor in v.parent.children:
        return v_inner_right.ancestor
    return default_ancestor


def _move_subtree(w_left: _WalkerNode, w_right: _WalkerNode, shift: float) -> None:
    subtrees = max(1, w_right.number - w_left.number)
    w_right.change -= shift / subtrees
    w_right.shift += shift
    w_left.change += shift / subtrees
    w_right.prelim += shift
    w_right.mod += shift


def _execute_shifts(v: _WalkerNode) -> None:
    shift = 0.0
    change = 0.0
    for child in reversed(v.children):
        child.prelim += shift
        child.mod += shift
        change += child.change
        shift += child.shift + change


def _apportion(
    v: _WalkerNode,
    default_ancestor: _WalkerNode,
    config: LayoutConfig,
) -> _WalkerNode:
    if v.number == 0 or v.parent is None:
        return default_ancestor

    left_sibling = v.parent.children[v.number - 1]

    v_inner_right = left_sibling
    v_inner_left = v
    v_outer_right = v.parent.children[0]
    v_outer_left = v

    s_inner_right = v_inner_right.mod
    s_inner_left = v_inner_left.mod
    s_outer_right = v_outer_right.mod
    s_outer_left = v_outer_left.mod

    next_right_inner = _next_right(v_inner_right)
    next_left_inner = _next_left(v_inner_left)

    while next_right_inner is not None and next_left_inner is not None:
        v_inner_right = next_right_inner
        v_inner_left = next_left_inner
        v_outer_right = _next_right(v_outer_right) or v_outer_right
        v_outer_left = _next_left(v_outer_left) or v_outer_left
        v_outer_left.ancestor = v

        # Walker resuelve el contorno con sibling_gap. El gap cross-subtree
        # (entre ramas distintas) lo aplica una pasada posterior porque el
        # smoothing de Buchheim distribuye el shift entre siblings
        # intermedios y absorberia parte del cross_gap si lo aplicaramos aca.
        gap = (v_inner_right.box.width + v_inner_left.box.width) / 2 + get_h_gap_for_depth(
            v_inner_right.box.depth, config
        )
        shift = (v_inner_right.prelim + s_inner_right) - (
            v_inner_left.prelim + s_inner_left
        ) + gap
        if shift > 0:
            ancestor = _walker_ancestor(v_inner_right, v, default_ancestor)
            _move_subtree(ancestor, v, shift)
            s_inner_left += shift
            s_outer_left += shift

        s_inner_right += v_inner_right.mod
        s_inner_left += v_inner_left.mod
        s_outer_right += v_outer_right.mod
        s_outer_left += v_outer_left.mod

        next_right_inner = _next_right(v_inner_right)
        next_left_inner = _next_left(v_inner_left)

    if next_right_inner is not None and _next_right(v_outer_left) is None:
        v_outer_left.thread = next_right_inner
        v_outer_left.mod += s_inner_right - s_outer_left
    if next_left_inner is not None and _next_left(v_outer_right) is None:
        v_outer_right.thread = next_left_inner
        v_outer_right.mod += s_inner_left - s_outer_right
        default_ancestor = v

    return default_ancestor


def _first_walk(v: _WalkerNode, config: LayoutConfig) -> None:
    if not v.children:
        if v.number > 0 and v.parent is not None:
            left_sibling = v.parent.children[v.number - 1]
            v.prelim = left_sibling.prelim + _walker_distance(left_sibling, v, config)
        else:
            v.prelim = 0.0
        return

    default_ancestor = v.children[0]
    for child in v.children:
        _first_walk(child, config)
        default_ancestor = _apportion(child, default_ancestor, config)

    _execute_shifts(v)

    midpoint = (v.children[0].prelim + v.children[-1].prelim) / 2
    if v.number > 0 and v.parent is not None:
        left_sibling = v.parent.children[v.number - 1]
        v.prelim = left_sibling.prelim + _walker_distance(left_sibling, v, config)
        v.mod = v.prelim - midpoint
    else:
        v.prelim = midpoint


def _second_walk(
    v: _WalkerNode,
    m: float,
    depth_y: Dict[int, float],
) -> None:
    center_x = v.prelim + m
    v.box.x = center_x - (v.box.width / 2)
    v.box.y = depth_y[v.box.depth]
    for child in v.children:
        _second_walk(child, m + v.mod, depth_y)


def _collect_walker_nodes(root: _WalkerNode) -> List[_WalkerNode]:
    out: List[_WalkerNode] = []

    def visit(node: _WalkerNode) -> None:
        out.append(node)
        for child in node.children:
            visit(child)

    visit(root)
    return out


def _depth_y_offsets(
    walker_nodes: List[_WalkerNode],
    config: LayoutConfig,
    base_y: float,
) -> Dict[int, float]:
    """Calcula la y de cada depth: max altura del depth + v_gap acumulado."""

    heights_per_depth: Dict[int, float] = {}
    for wn in walker_nodes:
        depth = wn.box.depth
        heights_per_depth[depth] = max(heights_per_depth.get(depth, 0.0), wn.box.height)

    if not heights_per_depth:
        return {}

    max_depth = max(heights_per_depth.keys())
    depth_y: Dict[int, float] = {}
    cursor = base_y
    for depth in range(max_depth + 1):
        depth_y[depth] = cursor
        v_gap = get_v_gap_for_depth(depth + 1, config)
        cursor += heights_per_depth.get(depth, 0.0) + v_gap
    return depth_y


def assign_tree_positions(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> None:
    """Coloca nodos usando Walker (Buchheim et al.) en lugar del packing por bandas.

    El algoritmo de Walker permite que subarboles vecinos interpenetren sus
    huecos manteniendo separacion entre nodos individuales: cuando un subarbol
    es ancho arriba y angosto abajo, el siguiente puede meterse en su hueco
    inferior sin colisionar. Eso recupera espacio que el packing clasico
    desperdiciaba al reservar bandas independientes por subarbol.

    Despues de Walker se ejecuta una pasada que enforce un gap mayor entre
    subarboles distintos (cousins o mas lejanos). Walker resuelve overlaps
    con sibling_gap, pero el smoothing de Buchheim absorbe el factor extra
    si se intenta aplicar dentro de _apportion. Por eso el ajuste cross-
    subtree se aplica como post-procesamiento explicito.
    """

    cursor_x = config.margin_x

    for root in root_nodes:
        walker_root = _build_walker_tree(root, boxes)
        _first_walk(walker_root, config)

        walker_nodes = _collect_walker_nodes(walker_root)
        depth_y = _depth_y_offsets(walker_nodes, config, base_y=config.margin_y)

        min_left_x = _walker_subtree_left_edge(walker_root)
        offset_x = cursor_x - min_left_x

        _second_walk(walker_root, offset_x, depth_y)
        _enforce_cross_subtree_gap(root, boxes, config)

        all_descendants = list(iter_nodes([root]))
        max_right = max(boxes[n.number].x + boxes[n.number].width for n in all_descendants)
        cursor_x = max_right + config.h_gap_base


def _enforce_cross_subtree_gap(
    root: ConceptNode,
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> None:
    """Pasa post-Walker que separa boxes de ramas distintas.

    Para cada par adyacente al mismo depth con padres distintos, si el gap
    actual es menor que el cross_gap requerido, desplaza el subarbol del
    box derecho y todos los siblings posteriores en su cadena de ancestros,
    hacia la derecha por la diferencia. Eso preserva el spacing relativo
    dentro de cada rama y solo abre espacio entre ramas distintas.

    Itera hasta que no haya conflictos (o hasta un limite defensivo) porque
    desplazar puede revelar conflictos en otros depths cuando los subarboles
    cruzan profundidades distintas.
    """

    factor = config.cross_subtree_gap_factor
    if factor <= 1.0 + 1e-6:
        return

    parent_index_cache: Dict[str, int] = {}
    for node in iter_nodes([root]):
        if node.parent is None:
            continue
        parent_index_cache[node.number] = node.parent.children.index(node)

    def shift_subtree(node: ConceptNode, dx: float) -> None:
        boxes[node.number].x += dx
        for child in node.children:
            shift_subtree(child, dx)

    def shift_node_and_followers(node: ConceptNode, dx: float) -> None:
        shift_subtree(node, dx)
        cur = node
        while cur.parent is not None:
            parent = cur.parent
            idx = parent_index_cache[cur.number]
            for sibling in parent.children[idx + 1:]:
                shift_subtree(sibling, dx)
            cur = parent

    by_depth: Dict[int, List[LayoutBox]] = {}
    for node in iter_nodes([root]):
        box = boxes[node.number]
        by_depth.setdefault(box.depth, []).append(box)

    for _ in range(6):
        any_shift = False
        for depth in sorted(by_depth.keys()):
            level = sorted(by_depth[depth], key=lambda b: b.x)
            i = 1
            while i < len(level):
                a = level[i - 1]
                b = level[i]
                same_parent = a.node.parent is b.node.parent
                if same_parent:
                    i += 1
                    continue
                base_gap = get_h_gap_for_depth(depth, config)
                required = base_gap * factor
                actual = b.x - (a.x + a.width)
                if actual + 0.5 >= required:
                    i += 1
                    continue
                deficit = required - actual
                shift_node_and_followers(b.node, deficit)
                level = sorted(by_depth[depth], key=lambda bx: bx.x)
                any_shift = True
                i = 1
        if not any_shift:
            break


def _walker_subtree_left_edge(walker_root: _WalkerNode) -> float:
    """Recorre el arbol respetando los modifiers para hallar el borde izquierdo."""

    stack: List[Tuple[_WalkerNode, float]] = [(walker_root, 0.0)]
    min_left = float("inf")
    while stack:
        node, accumulated = stack.pop()
        center_x = node.prelim + accumulated
        left_x = center_x - node.box.width / 2
        if left_x < min_left:
            min_left = left_x
        for child in node.children:
            stack.append((child, accumulated + node.mod))
    return min_left


def build_tree_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    return _choose_tree_scene(root_nodes, config, typography)
