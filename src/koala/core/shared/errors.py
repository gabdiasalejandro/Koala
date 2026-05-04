"""Errores comunes para pipelines de documentos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnknownDocumentTypeError(ValueError):
    """Se pidio un tipo de documento que Koala no conoce."""

    document_type: str
    available_types: tuple[str, ...]

    def __str__(self) -> str:
        available = ", ".join(self.available_types)
        return f"Tipo de documento '{self.document_type}' no existe. Disponibles: {available}."


@dataclass(frozen=True)
class DocumentTypeMismatchError(ValueError):
    """El DSL recibido no coincide con el tipo de documento solicitado."""

    expected_type: str
    line_no: int | None
    line: str
    reason: str

    def __str__(self) -> str:
        location = f"linea {self.line_no}" if self.line_no is not None else "documento"
        return (
            f"DSL incompatible con type='{self.expected_type}' en {location}: "
            f"{self.reason}. Texto: {self.line!r}."
        )
