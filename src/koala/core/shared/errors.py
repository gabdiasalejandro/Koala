"""Errores comunes para pipelines de documentos."""

from __future__ import annotations

from dataclasses import dataclass


class KoalaError(Exception):
    """Base comun para errores publicos de Koala."""


class KoalaInputError(KoalaError, ValueError):
    """Base para errores causados por input/configuracion del usuario."""


@dataclass(frozen=True)
class InvalidRenderConfigError(KoalaInputError):
    """Una opcion de render recibio un valor invalido."""

    key: str
    value: object
    expected: str

    def __str__(self) -> str:
        return (
            f"Config de render invalida para '{self.key}': {self.value!r}. "
            f"Esperado: {self.expected}."
        )


@dataclass(frozen=True)
class InputLimitExceededError(KoalaInputError):
    """El input excede un limite defensivo definido por el llamador."""

    limit_name: str
    actual: int
    maximum: int

    def __str__(self) -> str:
        return (
            f"Input excede '{self.limit_name}': {self.actual} > {self.maximum}."
        )


@dataclass(frozen=True)
class UnknownDocumentTypeError(KoalaInputError):
    """Se pidio un tipo de documento que Koala no conoce."""

    document_type: str
    available_types: tuple[str, ...]

    def __str__(self) -> str:
        available = ", ".join(self.available_types)
        return f"Tipo de documento '{self.document_type}' no existe. Disponibles: {available}."


@dataclass(frozen=True)
class DocumentTypeMismatchError(KoalaInputError):
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
