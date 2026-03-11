"""Orquestacion del pipeline de render.

Este modulo une layout y render:
1. Resuelve presets visuales.
2. Construye la `LayoutScene`.
3. Calcula el viewport final para SVG.
"""

from typing import Optional

from core.models import ParsedDocument
from layout.models import LayoutKind
from layout.registry import build_layout
from render.defaults import DEFAULT_LAYOUT_KIND, resolve_render_settings
from render.models import RenderContext
from render.viewport import fit_scene_to_page


def build_render_context(
    parsed: ParsedDocument,
    layout_kind: Optional[LayoutKind] = None,
    theme_name: Optional[str] = None,
    typography_name: Optional[str] = None,
) -> RenderContext:
    selected_layout = layout_kind or DEFAULT_LAYOUT_KIND
    settings = resolve_render_settings(
        selected_layout,
        theme_name=theme_name,
        typography_name=typography_name,
    )
    scene = build_layout(
        selected_layout,
        parsed.root_nodes,
        settings.layout_config,
        settings.typography,
    )
    viewport = fit_scene_to_page(scene, selected_layout, settings.layout_config)
    return RenderContext(
        parsed=parsed,
        scene=scene,
        settings=settings,
        viewport=viewport,
    )
