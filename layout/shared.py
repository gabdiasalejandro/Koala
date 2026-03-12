"""Utilidades compartidas de layout.

Retorna primitivas reutilizables para cualquier motor de layout:
- Medición de nodos (`measure_nodes`) con tipografía y espaciados.
- Helpers geométricos (`get_*_gap_for_depth`, `collect_bounds`, etc.).
- Utilidades de texto para render (`wrap_text_lines`, `sort_node_key`).

Cómo funciona:
1. Recibe `root_nodes`, `LayoutConfig` y `TypographyConfig`.
2. Calcula cajas base (`LayoutBox`) con tamaño y contenido tipográfico.
3. Entrega helpers para que cada layout específico asigne posiciones y aristas.
"""

from typing import Dict, Iterable, List, Tuple

from core.models import ConceptNode
from layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig


_NARROW_CHARS = set(" !'`,.:;|ijlIt")
_MEDIUM_CHARS = set('()[]{}"*/\\-')
_WIDE_CHARS = set("mwMW@%#&QGOD")
_DIGITS = set("0123456789")


def sort_node_key(number: str) -> List[int]:
    return [int(part) for part in number.split(".")]


def iter_nodes(root_nodes: List[ConceptNode]) -> Iterable[ConceptNode]:
    stack: List[ConceptNode] = list(reversed(root_nodes))
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children))


def get_depth(node: ConceptNode) -> int:
    depth = 0
    current = node.parent
    while current is not None:
        depth += 1
        current = current.parent
    return depth


def get_node_width_for_depth(depth: int, config: LayoutConfig) -> float:
    if depth == 0:
        return config.node_width_base * config.root_width_factor

    reduction = min(config.max_depth_reduction, depth * config.depth_width_reduction)
    return max(config.min_node_width, config.node_width_base * (1.0 - reduction))


def get_h_gap_for_depth(depth: int, config: LayoutConfig) -> float:
    return max(4.0, config.h_gap_base * (1.0 - min(0.35, depth * 0.08)))


def get_v_gap_for_depth(depth: int, config: LayoutConfig) -> float:
    return max(5.0, config.v_gap_base * (1.0 - min(0.30, depth * 0.06)))


def measure_text_width(text: str, font_name: str, font_size: float) -> float:
    """Aproxima el ancho de texto sin depender de motores externos.

    El objetivo no es precision tipografica absoluta sino mantener una
    medicion estable para layout y render usando fuentes Helvetica-like.
    """

    font_factor = 1.04 if "bold" in font_name.lower() else 1.0
    total = 0.0

    for char in text:
        if char in _NARROW_CHARS:
            total += 0.34
        elif char in _MEDIUM_CHARS:
            total += 0.42
        elif char in _WIDE_CHARS:
            total += 0.82
        elif char in _DIGITS:
            total += 0.56
        elif char.isupper():
            total += 0.68
        else:
            total += 0.54

    return total * font_size * font_factor


def wrap_text_lines(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    words = text.split()
    if not words:
        return []

    lines: List[str] = []
    current = ""

    for word in words:
        trial = f"{current} {word}".strip()
        if measure_text_width(trial, font_name, font_size) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def measure_longest_word_width(text: str, font_name: str, font_size: float) -> float:
    words = text.split()
    if not words:
        return 0.0

    return max(measure_text_width(word, font_name, font_size) for word in words)


def get_content_min_width(
    node: ConceptNode,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    title_width = measure_longest_word_width(node.title, typography.title_font, typography.title_size_base)
    body_width = measure_longest_word_width(node.body_text(), typography.body_font, typography.body_size)
    content_width = max(title_width, body_width)

    if content_width <= 0.0:
        return 2 * config.inner_pad_x

    return content_width + (2 * config.inner_pad_x)


def get_preferred_title_width(
    node: ConceptNode,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    title_width = measure_text_width(node.title, typography.title_font, typography.title_size_base)
    if title_width <= 0.0:
        return 2 * config.inner_pad_x
    return title_width + (2 * config.inner_pad_x) + 3.0


def get_preferred_content_width(
    node: ConceptNode,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    title_width = measure_text_width(node.title, typography.title_font, typography.title_size_base)
    body_width = measure_text_width(node.body_text(), typography.body_font, typography.body_size)
    preferred_width = max(title_width, body_width)

    if preferred_width <= 0.0:
        return 2 * config.inner_pad_x

    return preferred_width + (2 * config.inner_pad_x) + 3.0


def get_required_node_width(
    node: ConceptNode,
    depth: int,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    base_width = get_node_width_for_depth(depth, config)
    padded_width = get_content_min_width(node, config, typography)
    return max(base_width, padded_width)


def measure_node_box(
    node: ConceptNode,
    depth: int,
    width: float,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutBox:
    content_width = width - (2 * config.inner_pad_x)
    title_lines, title_font_size, title_height = choose_title_layout(node.title, content_width, typography)
    body_lines = wrap_text_lines(node.body_text(), typography.body_font, typography.body_size, content_width)
    body_height = len(body_lines) * typography.body_leading

    height = (
        config.inner_pad_y
        + title_height
        + (config.title_body_gap if body_lines else 0.0)
        + body_height
        + config.inner_pad_y
    )

    return LayoutBox(
        node=node,
        depth=depth,
        width=width,
        height=height,
        subtree_width=width,
        x=0.0,
        y=0.0,
        title_lines=title_lines,
        title_font_size=title_font_size,
        title_height=title_height,
        body_lines=body_lines,
    )


def choose_title_layout(
    title: str,
    content_width: float,
    typography: TypographyConfig,
) -> Tuple[List[str], float, float]:
    font_size = typography.title_size_base

    while font_size >= typography.title_size_min:
        lines = wrap_text_lines(title, typography.title_font, font_size, content_width)
        if len(lines) <= typography.max_title_lines:
            title_height = len(lines) * (font_size + typography.title_line_extra)
            return lines, font_size, title_height
        font_size -= 0.5

    lines = wrap_text_lines(title, typography.title_font, typography.title_size_min, content_width)
    lines = lines[: typography.max_title_lines]

    if lines:
        last = lines[-1]
        while last and measure_text_width(last + "...", typography.title_font, typography.title_size_min) > content_width:
            last = last[:-1]
        lines[-1] = (last + "...") if last else "..."

    title_height = len(lines) * (typography.title_size_min + typography.title_line_extra)
    return lines, typography.title_size_min, title_height


def measure_nodes(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> Dict[str, LayoutBox]:
    boxes: Dict[str, LayoutBox] = {}

    def visit(node: ConceptNode) -> None:
        depth = get_depth(node)
        width = get_required_node_width(node, depth, config, typography)
        boxes[node.number] = measure_node_box(node, depth, width, config, typography)

        for child in node.children:
            visit(child)

    for root in root_nodes:
        visit(root)

    return boxes


def collect_bounds(boxes: Dict[str, LayoutBox]) -> Tuple[float, float, float, float]:
    if not boxes:
        return 0.0, 0.0, 0.0, 0.0

    left = min(box.x for box in boxes.values())
    top = min(box.y for box in boxes.values())
    right = max(box.x + box.width for box in boxes.values())
    bottom = max(box.y + box.height for box in boxes.values())
    return left, top, right, bottom


def build_scene(boxes: Dict[str, LayoutBox], edges: List[LayoutEdge]) -> LayoutScene:
    left, top, right, bottom = collect_bounds(boxes)
    return LayoutScene(
        boxes=boxes,
        edges=edges,
        content_left=left,
        content_top=top,
        content_right=right,
        content_bottom=bottom,
    )
