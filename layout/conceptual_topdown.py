from typing import Dict, List, Tuple

from reportlab.pdfbase.pdfmetrics import stringWidth

from core.models import ConceptNode
from layout.models import LayoutBox, LayoutConfig, LayoutScene, TypographyConfig


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


def measure_tree(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> Dict[str, LayoutBox]:
    boxes: Dict[str, LayoutBox] = {}

    def measure(node: ConceptNode) -> LayoutBox:
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

        box = LayoutBox(
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

        if node.children:
            child_boxes = [measure(child) for child in node.children]
            h_gap = get_h_gap_for_depth(depth + 1, config)
            total_children_width = sum(child_box.subtree_width for child_box in child_boxes)
            total_children_width += h_gap * (len(child_boxes) - 1)
            box.subtree_width = max(box.width, total_children_width)

        boxes[node.number] = box
        return box

    for root in root_nodes:
        measure(root)

    return boxes


def assign_positions(
    root_nodes: List[ConceptNode],
    boxes: Dict[str, LayoutBox],
    config: LayoutConfig,
) -> Tuple[float, float]:
    current_x = config.margin_x
    max_bottom = 0.0
    max_right = 0.0

    def place(node: ConceptNode, left: float, top: float) -> None:
        nonlocal max_bottom, max_right

        box = boxes[node.number]
        box.x = left + (box.subtree_width - box.width) / 2
        box.y = top

        max_bottom = max(max_bottom, box.y + box.height)
        max_right = max(max_right, box.x + box.width)

        if not node.children:
            return

        h_gap = get_h_gap_for_depth(box.depth + 1, config)
        v_gap = get_v_gap_for_depth(box.depth + 1, config)

        total_children_width = sum(boxes[child.number].subtree_width for child in node.children)
        total_children_width += h_gap * (len(node.children) - 1)

        child_left = left + (box.subtree_width - total_children_width) / 2
        next_top = box.y + box.height + v_gap

        for child in node.children:
            child_box = boxes[child.number]
            place(child, child_left, next_top)
            child_left += child_box.subtree_width + h_gap

    for root in root_nodes:
        place(root, current_x, config.margin_y)
        current_x += boxes[root.number].subtree_width + config.h_gap_base

    return max_bottom, max_right


def build_topdown_layout(
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes = measure_tree(root_nodes, config, typography)
    content_bottom, content_right = assign_positions(root_nodes, boxes, config)
    return LayoutScene(boxes=boxes, content_bottom=content_bottom, content_right=content_right)


def sort_node_key(number: str) -> List[int]:
    return [int(part) for part in number.split(".")]
