"""Entry point unico del pipeline de render SVG.

Este archivo define la secuencia completa del render:
- recibir un `SvgRenderRequest` ya agrupado
- construir el contexto visual y geometrico
- resolver la ruta final del archivo de salida
- crear el documento SVG
- delegar el dibujo al backend especializado
- guardar el resultado

La intencion es que `render_svg(...)` sea la unica puerta de entrada y que
cada paso interno tenga una responsabilidad facil de leer y probar.
"""

from pathlib import Path

from render.context import RenderContextBuilder
from render.models import RenderContext, RenderResult, SvgRenderRequest
from render.output import RenderOutputResolver
from render.svg.canvas import SvgCanvasRenderer
from render.svg.document import SvgDocumentFactory


class SvgRenderPipeline:
    """Pipeline orientado a pasos para producir un SVG final."""

    def __init__(self, request: SvgRenderRequest):
        self._request = request

    def run(self) -> RenderResult:
        """Ejecuta el pipeline completo y retorna el resultado persistido."""

        context = self._build_context()
        output_svg = self._resolve_output_svg(context)
        drawing = self._build_document(output_svg, context)
        self._draw_scene(drawing, context)
        drawing.save()
        return RenderResult(output_svg=output_svg, context=context)

    def _build_context(self) -> RenderContext:
        """Construye el contexto final de render desde el documento parseado."""

        return RenderContextBuilder.build(
            self._request.parsed,
            layout_kind=self._request.layout_kind,
            theme_name=self._request.theme_name,
            typography_name=self._request.typography_name,
            page_size_name=self._request.page_size_name,
            text_align=self._request.text_align,
            show_node_numbers=self._request.show_node_numbers,
            default_layout_kind=self._request.default_layout_kind,
            default_theme_name=self._request.default_theme_name,
            default_typography_name=self._request.default_typography_name,
            default_page_size_name=self._request.default_page_size_name,
            default_text_align=self._request.default_text_align,
            default_show_node_numbers=self._request.default_show_node_numbers,
        )

    def _resolve_output_svg(self, context: RenderContext) -> Path:
        """Resuelve y crea la ruta final del SVG de salida."""

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
    def _build_document(output_svg: Path, context: RenderContext):
        """Crea el objeto `svgwrite.Drawing` con el viewport correcto."""

        return SvgDocumentFactory.create(output_svg, context)

    @staticmethod
    def _draw_scene(drawing, context: RenderContext) -> None:
        """Delega el dibujo del contenido al backend SVG."""

        SvgCanvasRenderer(context).render(drawing)


def render_svg(request: SvgRenderRequest) -> RenderResult:
    """Ejecuta el render SVG completo.

    `render_svg(...)` es la API publica de alto nivel.
    Recibe un `SvgRenderRequest` para evitar firmas largas y delega la
    ejecucion a `SvgRenderPipeline`.
    """

    return SvgRenderPipeline(request).run()
