"""Exportacion de SVG canonico a formatos finales.

El render principal de Koala sigue produciendo SVG. Este modulo vive despues de
ese paso y convierte el SVG serializado a bytes listos para HTTP o archivo.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from lxml import etree

from koala.render.shared.models import ExportFormat, ExportQuality, ExportResult, RenderResult


PNG_DPI_BY_QUALITY: dict[ExportQuality, int] = {
    "medium": 250,
    "high": 500,
}

PDF_QUALITY: ExportQuality = "high"
SVG_MEDIA_TYPE = "image/svg+xml"
PNG_MEDIA_TYPE = "image/png"
PDF_MEDIA_TYPE = "application/pdf"
SVG_NS = "http://www.w3.org/2000/svg"


class ExportConverter:
    """Convierte un `RenderResult` a bytes finales sin re-renderizar layout."""

    @classmethod
    def convert(
        cls,
        render: RenderResult,
        *,
        format: ExportFormat,
        quality: ExportQuality = "high",
        title: str | None = None,
    ) -> ExportResult:
        normalized_format = cls._normalize_format(format)
        normalized_quality = cls._normalize_quality(quality)

        if normalized_format == "svg":
            content = render.svg.encode("utf-8")
            return ExportResult(
                content=content,
                media_type=SVG_MEDIA_TYPE,
                extension="svg",
                format=normalized_format,
                quality=normalized_quality,
                render=render,
            )

        cls._ensure_cairosvg_available()

        if normalized_format == "png":
            content = cls._export_png(render, normalized_quality)
            return ExportResult(
                content=content,
                media_type=PNG_MEDIA_TYPE,
                extension="png",
                format=normalized_format,
                quality=normalized_quality,
                render=render,
            )

        if normalized_quality != PDF_QUALITY:
            raise ValueError("PDF solo soporta quality='high'.")

        content = cls._export_pdf(render, title=title)
        return ExportResult(
            content=content,
            media_type=PDF_MEDIA_TYPE,
            extension="pdf",
            format=normalized_format,
            quality=normalized_quality,
            render=render,
        )

    @classmethod
    def write(cls, export: ExportResult, path: str | Path) -> ExportResult:
        output_path = Path(path).expanduser()
        if output_path.suffix.lower() != f".{export.extension}":
            output_path = output_path.with_suffix(f".{export.extension}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(export.content)
        return ExportResult(
            content=export.content,
            media_type=export.media_type,
            extension=export.extension,
            format=export.format,
            quality=export.quality,
            render=export.render,
            output_path=output_path,
        )

    @staticmethod
    def _normalize_format(format: str) -> ExportFormat:
        normalized = format.strip().lower()
        if normalized not in {"svg", "png", "pdf"}:
            raise ValueError("Formato de exportacion invalido. Usa 'svg', 'png' o 'pdf'.")
        return normalized  # type: ignore[return-value]

    @staticmethod
    def _normalize_quality(quality: str) -> ExportQuality:
        normalized = quality.strip().lower()
        if normalized not in {"medium", "high"}:
            raise ValueError("Calidad de exportacion invalida. Usa 'medium' o 'high'.")
        return normalized  # type: ignore[return-value]

    @staticmethod
    def _ensure_cairosvg_available() -> None:
        try:
            import cairosvg  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depende del entorno de instalacion
            raise RuntimeError(
                "La exportacion PNG/PDF requiere cairosvg. "
                "Instala Koala con sus dependencias actualizadas o agrega cairosvg==2.7.1."
            ) from exc

    @classmethod
    def _export_png(cls, render: RenderResult, quality: ExportQuality) -> bytes:
        import cairosvg

        dpi = PNG_DPI_BY_QUALITY[quality]
        config = render.context.settings.layout_config
        output_width = round(config.page_width * dpi / 72.0)
        output_height = round(config.page_height * dpi / 72.0)
        return cairosvg.svg2png(
            bytestring=render.svg.encode("utf-8"),
            output_width=output_width,
            output_height=output_height,
        )

    @classmethod
    def _export_pdf(cls, render: RenderResult, *, title: str | None) -> bytes:
        import cairosvg

        decorated_svg = PdfFrameSvgBuilder.build(render, title=title)
        return cairosvg.svg2pdf(bytestring=decorated_svg.encode("utf-8"))


class PdfFrameSvgBuilder:
    """Construye un SVG de pagina profesional para la exportacion PDF."""

    HEADER_HEIGHT = 68.0
    MARGIN_X = 34.0
    MARGIN_BOTTOM = 28.0
    TITLE_SIZE = 20.0
    SUBTITLE_SIZE = 7.5
    ACCENT_HEIGHT = 2.0

    @classmethod
    def build(cls, render: RenderResult, *, title: str | None = None) -> str:
        context = render.context
        config = context.settings.layout_config
        theme = context.settings.theme
        typography = context.settings.typography
        page_width = config.page_width
        page_height = config.page_height
        resolved_title = title if title is not None else cls._resolve_main_title(render)
        main_style = theme.style_for("main")
        page_fill = context.settings.background_color or theme.default_node.fill

        outer = etree.Element(
            f"{{{SVG_NS}}}svg",
            nsmap={None: SVG_NS},
            width=f"{page_width}pt",
            height=f"{page_height}pt",
            viewBox=f"0 0 {page_width} {page_height}",
            version="1.1",
        )
        etree.SubElement(
            outer,
            f"{{{SVG_NS}}}rect",
            x="0",
            y="0",
            width=str(page_width),
            height=str(page_height),
            fill=page_fill,
        )
        cls._add_header(
            outer,
            title=resolved_title,
            theme_name=context.settings.theme_name,
            typography_family=typography.title_font,
            body_family=typography.body_font,
            title_color=main_style.title,
            accent_color=main_style.stroke,
            page_width=page_width,
        )
        cls._embed_inner_svg(outer, render)
        return etree.tostring(outer, encoding="unicode", xml_declaration=False)

    @classmethod
    def _add_header(
        cls,
        outer,
        *,
        title: str,
        theme_name: str,
        typography_family: str,
        body_family: str,
        title_color: str,
        accent_color: str,
        page_width: float,
    ) -> None:
        if title:
            text = etree.SubElement(
                outer,
                f"{{{SVG_NS}}}text",
                x=str(cls.MARGIN_X),
                y="35",
                fill=title_color,
                **{
                    "font-family": typography_family,
                    "font-size": str(cls.TITLE_SIZE),
                    "font-weight": "600",
                },
            )
            text.text = title

        subtitle = etree.SubElement(
            outer,
            f"{{{SVG_NS}}}text",
            x=str(cls.MARGIN_X),
            y="51",
            fill=accent_color,
            **{
                "font-family": body_family,
                "font-size": str(cls.SUBTITLE_SIZE),
                "letter-spacing": "0.4",
            },
        )
        subtitle.text = f"Koala diagram · {theme_name}"
        etree.SubElement(
            outer,
            f"{{{SVG_NS}}}rect",
            x=str(cls.MARGIN_X),
            y="59",
            width=str(max(24.0, page_width - (2 * cls.MARGIN_X))),
            height=str(cls.ACCENT_HEIGHT),
            fill=accent_color,
            opacity="0.72",
        )

    @classmethod
    def _embed_inner_svg(cls, outer, render: RenderResult) -> None:
        source_root = etree.fromstring(render.svg.encode("utf-8"))
        context = render.context
        config = context.settings.layout_config
        content_x = cls.MARGIN_X
        content_y = cls.HEADER_HEIGHT
        content_width = max(1.0, config.page_width - (2 * cls.MARGIN_X))
        content_height = max(1.0, config.page_height - cls.HEADER_HEIGHT - cls.MARGIN_BOTTOM)
        inner = etree.SubElement(
            outer,
            f"{{{SVG_NS}}}svg",
            x=str(content_x),
            y=str(content_y),
            width=str(content_width),
            height=str(content_height),
            viewBox=source_root.get("viewBox", f"0 0 {config.page_width} {config.page_height}"),
            preserveAspectRatio="xMidYMid meet",
        )
        for child in source_root:
            inner.append(deepcopy(child))

    @staticmethod
    def _resolve_main_title(render: RenderResult) -> str:
        return render.title or "Koala diagram"
