"""Modelos del doctype `matrix`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MatrixCell:
    """Celda semantica de un cuadro comparativo."""

    number: str
    title: str
    row: int
    col: int
    role: str = "cell"
    kind: str = "default"
    attributes: Dict[str, str] = field(default_factory=dict)
    paragraphs: List[str] = field(default_factory=list)
    children: List["MatrixCell"] = field(default_factory=list)
    parent: "MatrixCell | None" = None

    def body_text(self) -> str:
        return " ".join(self.paragraphs).strip()


@dataclass
class MatrixRow:
    cells: List[str]


@dataclass
class MatrixFooter:
    title: str
    text: str


@dataclass
class ParseWarning:
    line_no: int
    message: str


@dataclass
class ParsedMatrixDocument:
    title: str
    columns: List[str]
    rows: List[MatrixRow]
    footer: MatrixFooter | None
    root_nodes: List[MatrixCell]
    node_index: Dict[str, MatrixCell]
    metadata: Dict[str, str]
    warnings: List[ParseWarning]
