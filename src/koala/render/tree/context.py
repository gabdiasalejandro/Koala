"""Construccion de `RenderContext` para documentos `tree`."""

from __future__ import annotations

from typing import Optional

from koala.layout.shared.models import LayoutKind
from koala.layout.tree.registry import build_tree_layout_scene
from koala.core.tree.models import ParsedDocument
from koala.render.shared.context import RenderContextBuilder, RenderSettingsResolver
from koala.render.shared.models import RenderContext
from koala.render.shared.settings import PageSizeName


class TreeRenderContextBuilder:
    """Orquesta settings compartidos + layout exclusivo de `tree`."""

    @classmethod
    def build(
        cls,
        parsed: ParsedDocument,
        layout_kind: Optional[LayoutKind] = None,
        theme_name: Optional[str] = None,
        typography_name: Optional[str] = None,
        page_size_name: Optional[PageSizeName] = None,
        text_align: Optional[str] = None,
        show_node_numbers: Optional[bool] = None,
        background_color: Optional[str] = None,
        default_layout_kind: Optional[LayoutKind] = None,
        default_theme_name: Optional[str] = None,
        default_typography_name: Optional[str] = None,
        default_page_size_name: Optional[PageSizeName] = None,
        default_text_align: Optional[str] = None,
        default_show_node_numbers: Optional[bool] = None,
    ) -> RenderContext:
        settings = RenderSettingsResolver.resolve(
            parsed,
            layout_kind=layout_kind,
            theme_name=theme_name,
            typography_name=typography_name,
            page_size_name=page_size_name,
            text_align=text_align,
            show_node_numbers=show_node_numbers,
            background_color=background_color,
            default_layout_kind=default_layout_kind,
            default_theme_name=default_theme_name,
            default_typography_name=default_typography_name,
            default_page_size_name=default_page_size_name,
            default_text_align=default_text_align,
            default_show_node_numbers=default_show_node_numbers,
        )
        scene = build_tree_layout_scene(
            settings.layout_kind,
            parsed.root_nodes,
            settings.layout_config,
            settings.typography,
        )
        return RenderContextBuilder.build(
            parsed=parsed,
            scene=scene,
            settings=settings,
        )
