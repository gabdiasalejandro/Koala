"""Entry point del pipeline SVG para documentos `flowchart`."""

from __future__ import annotations

import io
from pathlib import Path

from koala.core.flowchart.models import ParsedFlowchartDocument
from koala.render.flowchart.canvas import FlowchartSvgCanvasRenderer
from koala.render.flowchart.context import FlowchartRenderContextBuilder
from koala.render.shared.models import RenderContext, RenderResult, SvgRenderRequest
from koala.render.shared.output import RenderOutputResolver, RenderOutputWriter
from koala.render.shared.svg.document import SvgDocumentFactory


class FlowchartSvgRenderPipeline:
    """Pipeline orientado a pasos para producir un SVG de flowchart."""

    def __init__(self, request: SvgRenderRequest) -> None:
        self._request = request

    def run(self) -> RenderResult:
        context = self._build_context()
        drawing = SvgDocumentFactory.create(context)
        FlowchartSvgCanvasRenderer(context).render(drawing)
        svg = self._serialize(drawing)
        output_svg = self._persist_if_needed(context, svg)
        return RenderResult(
            svg=svg,
            output_svg=output_svg,
            context=context,
            document_type=self._request.document_type,
            title=self._resolve_title(context),
        )

    def _build_context(self) -> RenderContext:
        return FlowchartRenderContextBuilder.build(
            self._request.parsed,  # type: ignore[arg-type]
            layout_kind=self._request.layout_kind,
            theme_name=self._request.theme_name,
            typography_name=self._request.typography_name,
            page_size_name=self._request.page_size_name,
            text_align=self._request.text_align,
            show_node_numbers=self._request.show_node_numbers,
            background_color=self._request.background_color,
            default_layout_kind=self._request.default_layout_kind,
            default_theme_name=self._request.default_theme_name,
            default_typography_name=self._request.default_typography_name,
            default_page_size_name=self._request.default_page_size_name,
            default_text_align=self._request.default_text_align,
            default_show_node_numbers=self._request.default_show_node_numbers,
        )

    def _resolve_output_svg(self, context: RenderContext) -> Path:
        return RenderOutputResolver.resolve_svg_path(
            base_dir=self._request.base_dir,
            parsed=self._request.parsed,
            layout_kind=context.settings.layout_kind,
            output_svg_path=self._request.output_svg_path,
            output_dir_name=self._request.output_dir_name,
            output_file_name=self._request.output_file_name,
            default_output_dir_name=self._request.default_output_dir_name,
        )

    @staticmethod
    def _serialize(drawing) -> str:
        buf = io.StringIO()
        drawing.write(buf)
        return buf.getvalue()

    def _persist_if_needed(self, context: RenderContext, svg: str) -> Path | None:
        if not self._request.persist_output:
            return None
        return RenderOutputWriter.write_svg(self._resolve_output_svg(context), svg)

    @staticmethod
    def _resolve_title(context: RenderContext) -> str:
        parsed = context.parsed
        if isinstance(parsed, ParsedFlowchartDocument):
            return parsed.title
        return "Koala flowchart"


def render_flowchart_svg(request: SvgRenderRequest) -> RenderResult:
    return FlowchartSvgRenderPipeline(request).run()
