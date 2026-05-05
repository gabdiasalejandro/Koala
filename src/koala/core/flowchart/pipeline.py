"""Pipeline para documentos de flujo tipo `flowchart`."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from koala.config import KoalaUserConfig
from koala.core.flowchart.models import ParsedFlowchartDocument
from koala.core.flowchart.parser import parse_flowchart_text
from koala.core.shared.errors import DocumentTypeMismatchError
from koala.layout.flowchart.registry import FLOWCHART_LAYOUTS
from koala.render.flowchart.context import FlowchartRenderContextBuilder, FLOWCHART_TYPOGRAPHIES
from koala.render.flowchart.svg_render import render_flowchart_svg
from koala.render.shared.context import MetadataValueResolver
from koala.render.shared.models import RenderContext, RenderResult, SvgRenderRequest


FlowchartDocumentType = Literal["flowchart"]


class FlowchartDocumentPipeline:
    """Implementacion del flujo para diagramas de tipo flowchart."""

    type_name: FlowchartDocumentType = "flowchart"
    supported_layouts: tuple[str, ...] = FLOWCHART_LAYOUTS

    def parse(self, source_text: str) -> ParsedFlowchartDocument:
        self._raise_if_known_non_flowchart_syntax(source_text)
        parsed = parse_flowchart_text(source_text)
        if not parsed.nodes:
            raise DocumentTypeMismatchError(
                expected_type=self.type_name,
                line_no=None,
                line="",
                reason="se esperaba al menos un nodo como 'step:: id :: Etiqueta'",
            )
        return parsed

    def resolve_output_file_name(
        self,
        parsed: ParsedFlowchartDocument,
        *,
        stem: str,
        layout,
        user_config: KoalaUserConfig,
    ) -> str:
        sanitized_stem = stem.strip() or "flowchart"
        if sanitized_stem.lower().endswith(".svg"):
            return sanitized_stem
        resolved_layout = (
            layout
            or MetadataValueResolver.resolve_value(parsed.metadata, "layout")
            or "flowchart"
        )
        return f"{sanitized_stem}.{resolved_layout}.svg"

    def render_text(
        self,
        source_text: str,
        *,
        base_dir: Path,
        persist_output: bool,
        output_svg_path,
        output_dir_name,
        output_file_name,
        default_output_dir_name,
        layout,
        theme_name,
        typography_name,
        page_size_name,
        text_align,
        show_node_numbers,
        background_color,
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
        parsed: ParsedFlowchartDocument,
        *,
        base_dir: Path,
        persist_output: bool,
        output_svg_path,
        output_dir_name,
        output_file_name,
        default_output_dir_name,
        layout,
        theme_name,
        typography_name,
        page_size_name,
        text_align,
        show_node_numbers,
        background_color,
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
        return render_flowchart_svg(request)

    def inspect_text(
        self,
        source_text: str,
        *,
        layout,
        theme_name,
        typography_name,
        page_size_name,
        text_align,
        show_node_numbers,
        background_color,
        user_config: KoalaUserConfig,
    ) -> RenderContext:
        parsed = self.parse(source_text)
        return FlowchartRenderContextBuilder.build(
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
        return layout if layout in FLOWCHART_LAYOUTS else None

    @staticmethod
    def _valid_default_typography(typography: str | None) -> str | None:
        return typography if typography in FLOWCHART_TYPOGRAPHIES else None

    @staticmethod
    def _raise_if_known_non_flowchart_syntax(source_text: str) -> None:
        matrix_markers = ("matrix::", "columns::", "row::", "footer::")
        for line_no, raw_line in enumerate(source_text.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("@"):
                continue
            lowered = stripped.lower()
            if lowered.startswith(matrix_markers):
                raise DocumentTypeMismatchError(
                    expected_type="flowchart",
                    line_no=line_no,
                    line=stripped,
                    reason="parece sintaxis de matrix, no de flowchart",
                )
