"""Entry point del pipeline SVG para documentos `matrix`."""

from __future__ import annotations

import io
from pathlib import Path

from koala.core.matrix.models import ParsedMatrixDocument
from koala.render.matrix.canvas import MatrixSvgCanvasRenderer
from koala.render.matrix.context import MatrixRenderContextBuilder
from koala.render.shared.models import RenderContext, RenderResult, SvgRenderRequest
from koala.render.shared.output import RenderOutputResolver, RenderOutputWriter
from koala.render.shared.svg.document import SvgDocumentFactory


class MatrixSvgRenderPipeline:
    """Pipeline orientado a pasos para producir un SVG de matriz."""

    def __init__(self, request: SvgRenderRequest):
        self._request = request

    def run(self) -> RenderResult:
        context = self._build_context()
        drawing = SvgDocumentFactory.create(context)
        MatrixSvgCanvasRenderer(context).render(drawing)
        svg = self._serialize_document(drawing)
        output_svg = self._persist_svg_if_needed(context, svg)
        return RenderResult(
            svg=svg,
            output_svg=output_svg,
            context=context,
            document_type=self._request.document_type,
            title=self._resolve_title(context),
        )

    def _build_context(self) -> RenderContext:
        return MatrixRenderContextBuilder.build(
            self._request.parsed,  # type: ignore[arg-type]
            layout_kind=self._request.layout_kind,  # type: ignore[arg-type]
            theme_name=self._request.theme_name,
            typography_name=self._request.typography_name,
            page_size_name=self._request.page_size_name,
            text_align=self._request.text_align,
            show_node_numbers=self._request.show_node_numbers,
            background_color=self._request.background_color,
            default_layout_kind=self._request.default_layout_kind,  # type: ignore[arg-type]
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
    def _serialize_document(drawing) -> str:
        buffer = io.StringIO()
        drawing.write(buffer)
        return buffer.getvalue()

    def _persist_svg_if_needed(self, context: RenderContext, svg: str) -> Path | None:
        if not self._request.persist_output:
            return None
        return RenderOutputWriter.write_svg(self._resolve_output_svg(context), svg)

    @staticmethod
    def _resolve_title(context: RenderContext) -> str:
        parsed = context.parsed
        if isinstance(parsed, ParsedMatrixDocument):
            return parsed.title
        return "Koala matrix"


def render_matrix_svg(request: SvgRenderRequest) -> RenderResult:
    return MatrixSvgRenderPipeline(request).run()


def render_svg(request: SvgRenderRequest) -> RenderResult:
    return render_matrix_svg(request)
