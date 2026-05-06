"""Utilidades compartidas del core de Koala."""

from koala.core.shared.errors import (
    DocumentTypeMismatchError,
    InputLimitExceededError,
    InvalidRenderConfigError,
    KoalaError,
    KoalaInputError,
    UnknownDocumentTypeError,
)
from koala.core.shared.types import DEFAULT_DOCUMENT_TYPE, DocumentType

__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "DocumentType",
    "DocumentTypeMismatchError",
    "InputLimitExceededError",
    "InvalidRenderConfigError",
    "KoalaError",
    "KoalaInputError",
    "UnknownDocumentTypeError",
]
