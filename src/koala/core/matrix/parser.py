"""Parser para cuadros comparativos `matrix`."""

from __future__ import annotations

import re
from typing import Dict, List

from koala.core.matrix.models import (
    MatrixCell,
    MatrixFooter,
    MatrixRow,
    ParseWarning,
    ParsedMatrixDocument,
)


METADATA_LINE_RE = re.compile(r"^\s*@(?P<key>[A-Za-z][\w-]*)\s*(?::|\s)\s*(?P<value>.+?)\s*$")
MATRIX_LINE_RE = re.compile(r"^\s*matrix::\s*(?P<title>.+?)\s*$", re.IGNORECASE)
COLUMNS_LINE_RE = re.compile(r"^\s*columns::\s*(?P<columns>.+?)\s*$", re.IGNORECASE)
ROW_LINE_RE = re.compile(r"^\s*row::\s*(?P<cells>.+?)\s*$", re.IGNORECASE)
FOOTER_LINE_RE = re.compile(r"^\s*footer::\s*(?P<footer>.+?)\s*$", re.IGNORECASE)


ROLE_TO_KIND = {
    "title": "main",
    "header": "main",
    "row_header": "hl",
    "cell": "default",
    "footer": "soft",
}


def parse_matrix_text(text: str) -> ParsedMatrixDocument:
    metadata: Dict[str, str] = {}
    warnings: List[ParseWarning] = []
    title = ""
    columns: List[str] = []
    rows: List[MatrixRow] = []
    footer: MatrixFooter | None = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        metadata_match = METADATA_LINE_RE.match(line)
        if metadata_match:
            key = metadata_match.group("key").strip().lower()
            if key in metadata:
                warnings.append(ParseWarning(line_no, f"Metadata duplicada '{key}'. Se sobrescribira."))
            metadata[key] = metadata_match.group("value").strip()
            continue

        matrix_match = MATRIX_LINE_RE.match(line)
        if matrix_match:
            title = matrix_match.group("title").strip()
            continue

        columns_match = COLUMNS_LINE_RE.match(line)
        if columns_match:
            columns = _split_cells(columns_match.group("columns"))
            continue

        row_match = ROW_LINE_RE.match(line)
        if row_match:
            rows.append(MatrixRow(cells=_split_cells(row_match.group("cells"))))
            continue

        footer_match = FOOTER_LINE_RE.match(line)
        if footer_match:
            footer = _parse_footer(footer_match.group("footer"))
            continue

        warnings.append(ParseWarning(line_no, "Linea no reconocida para matrix. Se ignora."))

    node_index = _build_node_index(title, columns, rows, footer, warnings)
    root_nodes = [node_index["title"]] if "title" in node_index else []
    return ParsedMatrixDocument(
        title=title,
        columns=columns,
        rows=rows,
        footer=footer,
        root_nodes=root_nodes,
        node_index=node_index,
        metadata=metadata,
        warnings=warnings,
    )


def _split_cells(raw: str) -> List[str]:
    return [cell.strip() for cell in raw.split("|")]


def _parse_footer(raw: str) -> MatrixFooter:
    parts = _split_cells(raw)
    if len(parts) >= 2:
        return MatrixFooter(title=parts[0], text=" | ".join(parts[1:]))
    return MatrixFooter(title="Conclusion", text=raw.strip())


def _build_node_index(
    title: str,
    columns: List[str],
    rows: List[MatrixRow],
    footer: MatrixFooter | None,
    warnings: List[ParseWarning],
) -> Dict[str, MatrixCell]:
    node_index: Dict[str, MatrixCell] = {}
    if title:
        node_index["title"] = _cell("title", title, -2, 0, "title")

    for col_index, column in enumerate(columns):
        node_index[f"h{col_index}"] = _cell(f"h{col_index}", column, -1, col_index, "header")

    expected_columns = len(columns)
    for row_index, row in enumerate(rows):
        cells = _normalize_row_cells(row.cells, expected_columns, row_index, warnings)
        for col_index, value in enumerate(cells):
            role = "row_header" if col_index == 0 else "cell"
            cell_id = f"r{row_index}c{col_index}"
            node_index[cell_id] = _cell(cell_id, value, row_index, col_index, role)

    if footer is not None:
        node_index["footer"] = _cell("footer", f"{footer.title}: {footer.text}", len(rows), 0, "footer")

    return node_index


def _normalize_row_cells(
    cells: List[str],
    expected_columns: int,
    row_index: int,
    warnings: List[ParseWarning],
) -> List[str]:
    if expected_columns <= 0:
        return cells

    normalized = list(cells)
    if len(normalized) < expected_columns:
        warnings.append(
            ParseWarning(0, f"La fila {row_index + 1} tiene menos celdas que columnas; se rellenara.")
        )
        normalized.extend([""] * (expected_columns - len(normalized)))
    if len(normalized) > expected_columns:
        warnings.append(
            ParseWarning(0, f"La fila {row_index + 1} tiene mas celdas que columnas; se recortara.")
        )
        normalized = normalized[:expected_columns]
    return normalized


def _cell(cell_id: str, title: str, row: int, col: int, role: str) -> MatrixCell:
    return MatrixCell(
        number=cell_id,
        title=title,
        row=row,
        col=col,
        role=role,
        kind=ROLE_TO_KIND.get(role, "default"),
    )
