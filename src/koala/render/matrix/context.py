"""Construccion de `RenderContext` para documentos `matrix`."""

from __future__ import annotations

from typing import Optional

from koala.core.matrix.models import ParsedMatrixDocument
from koala.layout.matrix.models import MatrixLayoutKind
from koala.layout.matrix.registry import build_matrix_layout_scene
from koala.render.matrix.profiles import TYPOGRAPHIES
from koala.render.shared.context import RenderContextBuilder, RenderSettingsResolver
from koala.render.shared.models import RenderContext
from koala.render.shared.settings import PageSizeName


MATRIX_TYPOGRAPHIES = tuple(TYPOGRAPHIES.keys())


class MatrixRenderContextBuilder:
    """Orquesta settings compartidos + layout exclusivo de `matrix`."""

    @classmethod
    def build(
        cls,
        parsed: ParsedMatrixDocument,
        layout_kind: Optional[MatrixLayoutKind] = None,
        theme_name: Optional[str] = None,
        typography_name: Optional[str] = None,
        page_size_name: Optional[PageSizeName] = None,
        text_align: Optional[str] = None,
        show_node_numbers: Optional[bool] = None,
        background_color: Optional[str] = None,
        default_layout_kind: Optional[MatrixLayoutKind] = None,
        default_theme_name: Optional[str] = None,
        default_typography_name: Optional[str] = None,
        default_page_size_name: Optional[PageSizeName] = None,
        default_text_align: Optional[str] = None,
        default_show_node_numbers: Optional[bool] = None,
    ) -> RenderContext:
        settings = RenderSettingsResolver.resolve(
            parsed,  # type: ignore[arg-type]
            document_type="matrix",
            layout_kind=layout_kind,
            theme_name=theme_name,
            typography_name=typography_name,
            page_size_name=page_size_name,
            text_align=text_align,
            show_node_numbers=show_node_numbers,
            background_color=background_color,
            default_layout_kind=default_layout_kind or "matrix",
            default_theme_name=default_theme_name,
            default_typography_name=default_typography_name,
            default_page_size_name=default_page_size_name,
            default_text_align=default_text_align,
            default_show_node_numbers=default_show_node_numbers,
        )
        scene = build_matrix_layout_scene(
            settings.layout_kind,
            parsed,
            settings.layout_config,
            settings.typography,
        )
        return RenderContextBuilder.build(
            parsed=parsed,  # type: ignore[arg-type]
            scene=scene,
            settings=settings,
        )
