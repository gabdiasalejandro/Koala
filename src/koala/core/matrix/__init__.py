"""Placeholder para el tipo de documento `matrix`.

Para implementarlo, este paquete debe contener:
- `models.py`: modelos de dominio (analogo de `ConceptNode`/`ParsedDocument`).
- `parser.py`: parser del DSL de matrix.
- `pipeline.py`: `MatrixDocumentPipeline` que cumpla el protocolo descrito
  en `docs/architecture.md` ("Adding a new document type") y se registre en
  `koala.core.shared.registry`.
"""
"""Core del doctype `matrix`."""

from koala.core.matrix.models import MatrixCell, MatrixFooter, MatrixRow, ParsedMatrixDocument
from koala.core.matrix.parser import parse_matrix_text

__all__ = [
    "MatrixCell",
    "MatrixFooter",
    "MatrixRow",
    "ParsedMatrixDocument",
    "parse_matrix_text",
]
