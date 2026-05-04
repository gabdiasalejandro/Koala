"""Registro de pipelines por tipo de documento."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from koala.core.shared.errors import UnknownDocumentTypeError
from koala.core.shared.types import DEFAULT_DOCUMENT_TYPE, DocumentType
from koala.render.shared.models import RenderContext, RenderResult

if TYPE_CHECKING:
    from koala.config import KoalaUserConfig


class DocumentPipeline(Protocol):
    """Contrato comun que implementa cada tipo de documento."""

    type_name: DocumentType
    supported_layouts: tuple[str, ...]

    def parse(self, source_text: str):
        ...

    def resolve_output_file_name(
        self,
        parsed,
        *,
        stem: str,
        layout,
        user_config: "KoalaUserConfig",
    ) -> str:
        ...

    def render_parsed(
        self,
        parsed,
        *,
        base_dir,
        persist_output: bool,
        output_svg_path,
        output_dir_name,
        output_file_name,
        default_output_dir_name,
        layout,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: "KoalaUserConfig",
    ) -> RenderResult:
        ...

    def render_text(
        self,
        source_text: str,
        *,
        base_dir,
        persist_output: bool,
        output_svg_path,
        output_dir_name,
        output_file_name,
        default_output_dir_name,
        layout,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: "KoalaUserConfig",
    ) -> RenderResult:
        ...

    def inspect_text(
        self,
        source_text: str,
        *,
        layout,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: "KoalaUserConfig",
    ) -> RenderContext:
        ...


class DocumentPipelineRegistry:
    """Resuelve pipelines sin que la API publica conozca cada implementacion."""

    _PIPELINES: dict[str, DocumentPipeline] = {}

    @classmethod
    def register(cls, pipeline: DocumentPipeline) -> None:
        cls._PIPELINES[pipeline.type_name] = pipeline

    @classmethod
    def require(cls, document_type: str | None) -> DocumentPipeline:
        normalized = cls.normalize_type(document_type)
        pipeline = cls._PIPELINES.get(normalized)
        if pipeline is None:
            raise UnknownDocumentTypeError(normalized, cls.available_types())
        return pipeline

    @classmethod
    def normalize_type(cls, document_type: str | None) -> str:
        if document_type is None:
            return DEFAULT_DOCUMENT_TYPE
        return document_type.strip().lower().replace("-", "_")

    @classmethod
    def available_types(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._PIPELINES.keys()))


from koala.core.tree.pipeline import TreeDocumentPipeline


DocumentPipelineRegistry.register(TreeDocumentPipeline())
