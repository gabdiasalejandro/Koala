"""Motor de layout para cuadros comparativos formales."""

from __future__ import annotations

from typing import Dict, List

from koala.core.matrix.models import MatrixCell, ParsedMatrixDocument
from koala.layout.shared.measurement import build_scene, wrap_text_lines
from koala.layout.shared.models import LayoutBox, LayoutConfig, LayoutScene, TypographyConfig


TITLE_GAP = 14.0
HEADER_FACTOR = 1.08
BODY_FACTOR = 1.0
ROW_HEADER_FACTOR = 1.02
FOOTER_FACTOR = 0.98


def build_matrix_layout(
    parsed: ParsedMatrixDocument,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    boxes: Dict[str, LayoutBox] = {}
    table_width = max(1.0, config.page_width - (2 * config.margin_x))
    column_widths = _column_widths(len(parsed.columns), table_width)

    current_y = 0.0
    title_box = _title_box(parsed.node_index["title"], table_width, current_y, config, typography)
    boxes["title"] = title_box
    current_y += title_box.height + TITLE_GAP

    header_height = _row_height(
        [parsed.node_index[f"h{col}"] for col in range(len(parsed.columns))],
        column_widths,
        config,
        typography,
    )
    _place_row(
        boxes,
        [parsed.node_index[f"h{col}"] for col in range(len(parsed.columns))],
        column_widths,
        current_y,
        header_height,
        config,
        typography,
    )
    current_y += header_height

    for row_index in range(len(parsed.rows)):
        row_cells = [
            parsed.node_index[f"r{row_index}c{col}"] for col in range(len(parsed.columns))
        ]
        row_height = _row_height(row_cells, column_widths, config, typography)
        _place_row(boxes, row_cells, column_widths, current_y, row_height, config, typography)
        current_y += row_height

    if parsed.footer is not None and "footer" in parsed.node_index:
        footer_node = parsed.node_index["footer"]
        footer_box = _cell_box(
            footer_node,
            table_width,
            current_y,
            config,
            typography,
            font_size=typography.body_size * FOOTER_FACTOR,
            font_family=typography.body_font,
            min_height=34.0,
        )
        footer_box.width = table_width
        boxes["footer"] = footer_box

    return build_scene(boxes, [])


def _column_widths(column_count: int, table_width: float) -> List[float]:
    if column_count <= 0:
        return []
    if column_count == 1:
        return [table_width]

    first_col = min(table_width * 0.30, max(table_width * 0.22, 132.0))
    remaining = max(1.0, table_width - first_col)
    other_width = remaining / (column_count - 1)
    return [first_col] + [other_width] * (column_count - 1)


def _title_box(
    node: MatrixCell,
    width: float,
    y: float,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutBox:
    content_width = width - (2 * config.inner_pad_x)
    measure_font = _weighted_font_family(typography.title_font, "600")
    lines = wrap_text_lines(node.title, measure_font, typography.title_size_base + 2.0, content_width)
    if not lines:
        lines = [node.title]
    font_size = typography.title_size_base + 2.0
    title_height = len(lines) * (font_size + typography.title_line_extra)
    return LayoutBox(
        node=node,  # type: ignore[arg-type]
        depth=0,
        width=width,
        height=title_height + (2 * config.inner_pad_y),
        subtree_width=width,
        x=0.0,
        y=y,
        title_lines=lines,
        title_font_size=font_size,
        title_height=title_height,
        body_lines=[],
    )


def _row_height(
    cells: List[MatrixCell],
    column_widths: List[float],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> float:
    heights = []
    for cell, width in zip(cells, column_widths):
        font_size, font_family = _cell_typography(cell, typography)
        lines = wrap_text_lines(cell.title, font_family, font_size, width - (2 * config.inner_pad_x))
        line_step = _line_step(font_size, typography)
        heights.append((len(lines) * line_step) + (2 * config.inner_pad_y))
    return max(32.0, max(heights, default=32.0))


def _place_row(
    boxes: Dict[str, LayoutBox],
    cells: List[MatrixCell],
    column_widths: List[float],
    y: float,
    height: float,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> None:
    x = 0.0
    for cell, width in zip(cells, column_widths):
        font_size, font_family = _cell_typography(cell, typography)
        boxes[cell.number] = _cell_box(
            cell,
            width,
            y,
            config,
            typography,
            font_size=font_size,
            font_family=font_family,
            min_height=height,
            x=x,
        )
        x += width


def _cell_box(
    node: MatrixCell,
    width: float,
    y: float,
    config: LayoutConfig,
    typography: TypographyConfig,
    *,
    font_size: float,
    font_family: str,
    min_height: float,
    x: float = 0.0,
) -> LayoutBox:
    content_width = max(1.0, width - (2 * config.inner_pad_x))
    measure_font_family = _weighted_font_family(font_family, _cell_font_weight(node))
    lines = wrap_text_lines(node.title, measure_font_family, font_size, content_width)
    if not lines and node.title:
        lines = [node.title]
    line_step = _line_step(font_size, typography)
    title_height = len(lines) * line_step
    measured_height = title_height + (2 * config.inner_pad_y)
    return LayoutBox(
        node=node,  # type: ignore[arg-type]
        depth=0,
        width=width,
        height=max(min_height, measured_height),
        subtree_width=width,
        x=x,
        y=y,
        title_lines=lines,
        title_font_size=font_size,
        title_height=title_height,
        body_lines=[],
    )


def _cell_typography(cell: MatrixCell, typography: TypographyConfig) -> tuple[float, str]:
    if cell.role == "header":
        return typography.body_size * HEADER_FACTOR, typography.title_font
    if cell.role == "row_header":
        return typography.body_size * ROW_HEADER_FACTOR, typography.title_font
    return typography.body_size * BODY_FACTOR, typography.body_font


def _cell_font_weight(cell: MatrixCell) -> str | None:
    if cell.role in {"header", "row_header", "footer"}:
        return "600"
    return None


def _weighted_font_family(font_family: str, font_weight: str | None) -> str:
    if font_weight is None:
        return font_family
    if font_weight in {"600", "700", "bold"}:
        return f"{font_family} bold"
    return font_family


def _line_step(font_size: float, typography: TypographyConfig) -> float:
    return max(font_size + 2.2, typography.body_leading * (font_size / max(1.0, typography.body_size)))
