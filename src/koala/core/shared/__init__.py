"""Utilidades compartidas del core de Koala."""

from koala.core.shared.errors import DocumentTypeMismatchError, UnknownDocumentTypeError
from koala.core.shared.types import DEFAULT_DOCUMENT_TYPE, DocumentType

__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "DocumentType",
    "DocumentTypeMismatchError",
    "UnknownDocumentTypeError",
]
