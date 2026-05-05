"""Pipeline para documentos comparativos tipo `matrix`."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from koala.config import KoalaUserConfig
from koala.core.matrix.models import ParsedMatrixDocument
from koala.core.matrix.parser import parse_matrix_text
from koala.core.shared.errors import DocumentTypeMismatchError
from koala.layout.matrix.registry import MATRIX_LAYOUTS
from koala.render.matrix.context import MATRIX_TYPOGRAPHIES
from koala.render.matrix.context import MatrixRenderContextBuilder
from koala.render.matrix.svg_render import render_matrix_svg
from koala.render.shared.context import MetadataValueResolver
from koala.render.shared.models import RenderContext, RenderResult, SvgRenderRequest


MatrixDocumentType = Literal["matrix"]


class MatrixDocumentPipeline:
    """Implementacion del flujo para cuadros comparativos."""

    type_name: MatrixDocumentType = "matrix"
    supported_layouts = MATRIX_LAYOUTS

    def parse(self, source_text: str) -> ParsedMatrixDocument:
        self._raise_if_known_tree_syntax(source_text)
        parsed = parse_matrix_text(source_text)
        if not parsed.title:
            raise DocumentTypeMismatchError(
                expected_type=self.type_name,
                line_no=None,
                line="",
                reason="se esperaba una linea inicial como 'matrix:: Titulo'",
            )
        if len(parsed.columns) < 2:
            raise DocumentTypeMismatchError(
                expected_type=self.type_name,
                line_no=None,
                line="",
                reason="se esperaban al menos dos columnas con 'columns:: A | B'",
            )
        if not parsed.rows:
            raise DocumentTypeMismatchError(
                expected_type=self.type_name,
                line_no=None,
                line="",
                reason="se esperaba al menos una fila con 'row:: ... | ...'",
            )
        return parsed

    def resolve_output_file_name(
        self,
        parsed: ParsedMatrixDocument,
        *,
        stem: str,
        layout,
        user_config: KoalaUserConfig,
    ) -> str:
        sanitized_stem = stem.strip() or "comparison_matrix"
        if sanitized_stem.lower().endswith(".svg"):
            return sanitized_stem
        resolved_layout = (
            layout
            or MetadataValueResolver.resolve_value(parsed.metadata, "layout")
            or self._valid_default_layout(user_config.default_layout)
            or "matrix"
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
        layout,
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
        parsed: ParsedMatrixDocument,
        *,
        base_dir: Path,
        persist_output: bool,
        output_svg_path: Path | None,
        output_dir_name: str | None,
        output_file_name: str | None,
        default_output_dir_name: str | None,
        layout,
        theme_name: str | None,
        typography_name: str | None,
        page_size_name: str | None,
        text_align: str | None,
        show_node_numbers: bool | None,
        background_color: str | None,
        user_config: KoalaUserConfig,
    ) -> RenderResult:
        request = SvgRenderRequest(
            parsed=parsed,  # type: ignore[arg-type]
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
            default_layout_kind=self._valid_default_layout(user_config.default_layout),
            default_theme_name=user_config.default_theme,
            default_typography_name=self._valid_default_typography(user_config.default_typography),
            default_page_size_name=user_config.default_size,
            default_text_align=user_config.default_text_align,
            default_show_node_numbers=False,
            document_type=self.type_name,
        )
        return render_matrix_svg(request)

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
        user_config: KoalaUserConfig,
    ) -> RenderContext:
        parsed = self.parse(source_text)
        return MatrixRenderContextBuilder.build(
            parsed,
            layout_kind=layout,
            theme_name=theme_name,
            typography_name=typography_name,
            page_size_name=page_size_name,
            text_align=text_align,
            show_node_numbers=show_node_numbers,
            background_color=background_color,
            default_layout_kind=self._valid_default_layout(user_config.default_layout),
            default_theme_name=user_config.default_theme,
            default_typography_name=self._valid_default_typography(user_config.default_typography),
            default_page_size_name=user_config.default_size,
            default_text_align=user_config.default_text_align,
            default_show_node_numbers=False,
        )

    @staticmethod
    def _valid_default_layout(layout: str | None) -> str | None:
        return layout if layout in MATRIX_LAYOUTS else None

    @staticmethod
    def _valid_default_typography(typography: str | None) -> str | None:
        return typography if typography in MATRIX_TYPOGRAPHIES else None

    @staticmethod
    def _raise_if_known_tree_syntax(source_text: str) -> None:
        for line_no, raw_line in enumerate(source_text.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("@"):
                continue
            lowered = stripped.lower()
            if lowered.startswith(("matrix::", "columns::", "row::", "footer::")):
                return
            if stripped[0].isdigit() or "::" in stripped and any(ch.isdigit() for ch in stripped):
                raise DocumentTypeMismatchError(
                    expected_type="matrix",
                    line_no=line_no,
                    line=stripped,
                    reason="parece sintaxis jerarquica de tree, no de matrix",
                )
