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

from reportlab.pdfbase.pdfmetrics import stringWidth

from core.models import ConceptNode
from layout.models import LayoutBox, LayoutConfig, LayoutEdge, LayoutScene, TypographyConfig


def sort_node_key(number: str) -> List[int]:
    return [int(part) for part in number.split(".")]


def iter_nodes(root_nodes: List[ConceptNode]) -> Iterable[ConceptNode]:
    stack: List[ConceptNode] = list(reversed(root_nodes))
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children))


def get_depth(number: str) -> int:
    return len(number.split(".")) - 1


def get_node_width_for_depth(depth: int, config: LayoutConfig) -> float:
    if depth == 0:
        return config.node_width_base * config.root_width_factor

    reduction = min(config.max_depth_reduction, depth * config.depth_width_reduction)
    return max(config.min_node_width, config.node_width_base * (1.0 - reduction))


def get_h_gap_for_depth(depth: int, config: LayoutConfig) -> float:
    return max(4.0, config.h_gap_base * (1.0 - min(0.35, depth * 0.08)))


def get_v_gap_for_depth(depth: int, config: LayoutConfig) -> float:
    return max(5.0, config.v_gap_base * (1.0 - min(0.30, depth * 0.06)))


def wrap_text_lines(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    words = text.split()
    if not words:
        return []

    lines: List[str] = []
    current = ""

    for word in words:
        trial = f"{current} {word}".strip()
        if stringWidth(trial, font_name, font_size) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


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
        while last and stringWidth(last + "...", typography.title_font, typography.title_size_min) > content_width:
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
        depth = get_depth(node.number)
        width = get_node_width_for_depth(depth, config)
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

        boxes[node.number] = LayoutBox(
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
