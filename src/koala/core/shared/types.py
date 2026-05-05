"""Tipos de documento soportados por Koala."""

from typing import Literal


DocumentType = Literal["tree", "matrix", "flowchart"]
DEFAULT_DOCUMENT_TYPE: DocumentType = "tree"
