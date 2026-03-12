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
from render.defaults import DEFAULT_LAYOUT_KIND, PageSizeName, resolve_render_settings
from render.models import RenderContext
from render.viewport import fit_scene_to_page


_BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "on", "show", "shown"}
_BOOLEAN_FALSE_VALUES = {"0", "false", "no", "off", "hide", "hidden"}


def _resolve_bool_metadata(metadata: dict[str, str], *keys: str) -> bool | None:
    for key in keys:
        raw_value = metadata.get(key)
        if raw_value is None:
            continue

        normalized = raw_value.strip().lower()
        if normalized in _BOOLEAN_TRUE_VALUES:
            return True
        if normalized in _BOOLEAN_FALSE_VALUES:
            return False

    return None


def build_render_context(
    parsed: ParsedDocument,
    layout_kind: Optional[LayoutKind] = None,
    theme_name: Optional[str] = None,
    typography_name: Optional[str] = None,
    page_size_name: Optional[PageSizeName] = None,
) -> RenderContext:
    selected_layout = layout_kind or DEFAULT_LAYOUT_KIND
    settings = resolve_render_settings(
        selected_layout,
        theme_name=theme_name,
        typography_name=typography_name,
        page_size_name=page_size_name,
        show_node_numbers=_resolve_bool_metadata(
            parsed.metadata,
            "show-node-numbers",
            "show_node_numbers",
            "node-numbers",
            "node_numbers",
        ),
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
