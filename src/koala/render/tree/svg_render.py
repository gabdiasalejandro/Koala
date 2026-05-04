"""Entry point del pipeline SVG para documentos tree.

Este archivo define la secuencia completa del render:
- recibir un `SvgRenderRequest` ya agrupado
- construir el contexto visual y geometrico
- crear el documento SVG en memoria
- delegar el dibujo al backend especializado
- serializar el resultado
- persistirlo solo si hace falta

La intencion es que `render_tree_svg(...)` sea la unica puerta de entrada y que
cada paso interno tenga una responsabilidad facil de leer y probar.
"""

import io
from pathlib import Path

from koala.render.tree.context import TreeRenderContextBuilder
from koala.render.shared.models import RenderContext, RenderResult, SvgRenderRequest
from koala.render.shared.output import RenderOutputResolver, RenderOutputWriter
from koala.render.tree.canvas import SvgCanvasRenderer
from koala.layout.shared.measurement import sort_node_key
from koala.render.shared.svg.document import SvgDocumentFactory


class TreeSvgRenderPipeline:
    """Pipeline orientado a pasos para producir un SVG final."""

    def __init__(self, request: SvgRenderRequest):
        self._request = request

    def run(self) -> RenderResult:
        """Ejecuta el pipeline completo y retorna el resultado serializado."""

        context = self._build_context()
        drawing = self._build_document(context)
        self._draw_scene(drawing, context)
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
        """Construye el contexto final de render desde el documento parseado."""

        return TreeRenderContextBuilder.build(
            self._request.parsed,
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
        """Resuelve la ruta final del SVG de salida."""

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
    def _build_document(context: RenderContext):
        """Crea el objeto `svgwrite.Drawing` con el viewport correcto."""

        return SvgDocumentFactory.create(context)

    @staticmethod
    def _draw_scene(drawing, context: RenderContext) -> None:
        """Delega el dibujo del contenido al backend SVG."""

        SvgCanvasRenderer(context).render(drawing)

    @staticmethod
    def _serialize_document(drawing) -> str:
        """Serializa el documento SVG con el mismo formato del backend file-oriented."""

        buffer = io.StringIO()
        drawing.write(buffer)
        return buffer.getvalue()

    def _persist_svg_if_needed(self, context: RenderContext, svg: str) -> Path | None:
        if not self._request.persist_output:
            return None

        output_svg = self._resolve_output_svg(context)
        return RenderOutputWriter.write_svg(output_svg, svg)

    @staticmethod
    def _resolve_title(context: RenderContext) -> str:
        parsed = context.parsed
        main_nodes = [
            node for node in parsed.node_index.values() if node.kind.strip().lower() == "main"
        ]
        if main_nodes:
            return sorted(main_nodes, key=lambda node: sort_node_key(node.number))[0].title
        if parsed.root_nodes:
            return parsed.root_nodes[0].title
        return "Koala diagram"


def render_tree_svg(request: SvgRenderRequest) -> RenderResult:
    """Ejecuta el render SVG completo.

    `render_tree_svg(...)` es la API publica de alto nivel.
    Recibe un `SvgRenderRequest` para evitar firmas largas y delega la
    ejecucion a `TreeSvgRenderPipeline`.
    """

    return TreeSvgRenderPipeline(request).run()


def render_svg(request: SvgRenderRequest) -> RenderResult:
    """Alias de compatibilidad para el render SVG de `tree`."""

    return render_tree_svg(request)
