"""Pipeline para documentos jerarquicos tipo `tree`.

Este pipeline encapsula la semantica historica de Koala: parsear nodos
jerarquicos, aplicar un layout exclusivo de arbol y producir el SVG canonico.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from koala.config import KoalaUserConfig
from koala.core.tree.models import ParsedDocument
from koala.core.tree.parser import parse_concept_text
from koala.core.shared.errors import DocumentTypeMismatchError
from koala.layout.tree.registry import TREE_LAYOUTS
from koala.layout.shared.models import LayoutKind
from koala.render.tree.context import TreeRenderContextBuilder
from koala.render.shared.context import MetadataValueResolver
from koala.render.shared.models import RenderContext, RenderResult, SvgRenderRequest
from koala.render.shared.settings import DEFAULT_LAYOUT_KIND
from koala.render.tree.svg_render import render_tree_svg


TreeDocumentType = Literal["tree"]


class TreeDocumentPipeline:
    """Implementacion del flujo para documentos jerarquicos."""

    type_name: TreeDocumentType = "tree"
    supported_layouts: tuple[LayoutKind, ...] = TREE_LAYOUTS

    def parse(self, source_text: str) -> ParsedDocument:
        self._raise_if_known_non_tree_syntax(source_text)
        parsed = parse_concept_text(source_text)
        if not parsed.root_nodes:
            raise DocumentTypeMismatchError(
                expected_type=self.type_name,
                line_no=None,
                line="",
                reason="se esperaba al menos una linea de nodo jerarquico como '1 Titulo'",
            )
        return parsed

    def resolve_output_file_name(
        self,
        parsed: ParsedDocument,
        *,
        stem: str,
        layout: LayoutKind | None,
        user_config: KoalaUserConfig,
    ) -> str:
        sanitized_stem = stem.strip() or "concept_map"
        if sanitized_stem.lower().endswith(".svg"):
            return sanitized_stem

        resolved_layout = (
            layout
            or MetadataValueResolver.resolve_value(parsed.metadata, "layout")
            or user_config.default_layout
            or DEFAULT_LAYOUT_KIND
        )
        return f"{sanitized_stem}.{resolved_layout}.svg"

    def render_text(
        self,
        source_text: str,
        *,
        base_dir: Path,
        persist_output: bool,
        output_svg_path: Path | None,
        output_dir_name: str | None,
        output_file_name: str | None,
        default_output_dir_name: str | None,
        layout: LayoutKind | None,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: KoalaUserConfig,
    ) -> RenderResult:
        parsed = self.parse(source_text)
        return self.render_parsed(
            parsed,
            base_dir=base_dir,
            persist_output=persist_output,
            output_svg_path=output_svg_path,
            output_dir_name=output_dir_name,
            output_file_name=output_file_name,
            default_output_dir_name=default_output_dir_name,
            layout=layout,
            theme_name=theme_name,
            typography_name=typography_name,
            page_size_name=page_size_name,
            text_align=text_align,
            show_node_numbers=show_node_numbers,
            background_color=background_color,
            user_config=user_config,
        )

    def render_parsed(
        self,
        parsed: ParsedDocument,
        *,
        base_dir: Path,
        persist_output: bool,
        output_svg_path: Path | None,
        output_dir_name: str | None,
        output_file_name: str | None,
        default_output_dir_name: str | None,
        layout: LayoutKind | None,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: KoalaUserConfig,
    ) -> RenderResult:
        request = SvgRenderRequest(
            parsed=parsed,
            base_dir=base_dir,
            persist_output=persist_output,
            output_svg_path=output_svg_path,
            output_dir_name=output_dir_name,
            output_file_name=output_file_name,
            default_output_dir_name=default_output_dir_name,
            layout_kind=layout,
            theme_name=theme_name,
            typography_name=typography_name,
            page_size_name=page_size_name,
            text_align=text_align,
            show_node_numbers=show_node_numbers,
            background_color=background_color,
            default_layout_kind=user_config.default_layout,
            default_theme_name=user_config.default_theme,
            default_typography_name=user_config.default_typography,
            default_page_size_name=user_config.default_size,
            default_text_align=user_config.default_text_align,
            default_show_node_numbers=user_config.default_show_node_numbers,
            document_type=self.type_name,
        )
        return render_tree_svg(request)

    def inspect_text(
        self,
        source_text: str,
        *,
        layout: LayoutKind | None,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: KoalaUserConfig,
    ) -> RenderContext:
        parsed = self.parse(source_text)
        return TreeRenderContextBuilder.build(
            parsed,
            layout_kind=layout,
            theme_name=theme_name,
            typography_name=typography_name,
            page_size_name=page_size_name,
            text_align=text_align,
            show_node_numbers=show_node_numbers,
            background_color=background_color,
            default_layout_kind=user_config.default_layout,
            default_theme_name=user_config.default_theme,
            default_typography_name=user_config.default_typography,
            default_page_size_name=user_config.default_size,
            default_text_align=user_config.default_text_align,
            default_show_node_numbers=user_config.default_show_node_numbers,
        )

    @staticmethod
    def _raise_if_known_non_tree_syntax(source_text: str) -> None:
        matrix_markers = ("matrix::", "columns::", "row::")
        flowchart_markers = ("flowchart::", "step::", "decision::")
        for line_no, raw_line in enumerate(source_text.splitlines(), start=1):
            stripped = raw_line.strip()
            lowered = stripped.lower()
            if lowered.startswith(matrix_markers):
                raise DocumentTypeMismatchError(
                    expected_type="tree",
                    line_no=line_no,
                    line=stripped,
                    reason="parece sintaxis de matrix, no de tree",
                )
            if lowered.startswith(flowchart_markers):
                raise DocumentTypeMismatchError(
                    expected_type="tree",
                    line_no=line_no,
                    line=stripped,
                    reason="parece sintaxis de flowchart, no de tree",
                )
