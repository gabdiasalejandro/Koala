"""Construccion del `RenderContext`.

Este archivo toma decisiones de orquestacion:
- aplica precedencia entre argumentos explicitos, metadata y defaults
- resuelve settings visuales
- construye la escena de layout
- ajusta el viewport final

La salida es un `RenderContext` listo para que el backend SVG lo dibuje.
"""

from dataclasses import replace
from typing import Optional

from core.models import ParsedDocument
from layout.models import LayoutKind
from layout.registry import build_layout
from render.models import RenderContext
from render.settings import DEFAULT_LAYOUT_KIND, PageSizeName, RenderSettingsCatalog
from render.viewport import ViewportFitter


class MetadataValueResolver:
    """Helpers para leer metadata tolerante a aliases y valores flexibles."""

    BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "on", "show", "shown"}
    BOOLEAN_FALSE_VALUES = {"0", "false", "no", "off", "hide", "hidden"}
    TEXT_ALIGN_VALUES = {"left", "justify"}

    @classmethod
    def resolve_value(cls, metadata: dict[str, str], *keys: str) -> str | None:
        for key in keys:
            value = metadata.get(key)
            if value:
                return value
        return None

    @classmethod
    def resolve_bool(cls, metadata: dict[str, str], *keys: str) -> bool | None:
        for key in keys:
            raw_value = metadata.get(key)
            if raw_value is None:
                continue

            normalized = raw_value.strip().lower()
            if normalized in cls.BOOLEAN_TRUE_VALUES:
                return True
            if normalized in cls.BOOLEAN_FALSE_VALUES:
                return False
        return None

    @classmethod
    def resolve_text_align(cls, metadata: dict[str, str], *keys: str) -> str | None:
        for key in keys:
            raw_value = metadata.get(key)
            if raw_value is None:
                continue

            normalized = raw_value.strip().lower()
            if normalized in cls.TEXT_ALIGN_VALUES:
                return normalized
        return None


class RenderContextBuilder:
    """Orquestador del pipeline previo al backend SVG."""

    @classmethod
    def build(
        cls,
        parsed: ParsedDocument,
        layout_kind: Optional[LayoutKind] = None,
        theme_name: Optional[str] = None,
        typography_name: Optional[str] = None,
        page_size_name: Optional[PageSizeName] = None,
    ) -> RenderContext:
        selected_layout = layout_kind or cls._resolve_layout(parsed)
        resolved_theme_name = theme_name or cls._resolve_theme(parsed)
        resolved_typography_name = typography_name or cls._resolve_typography(parsed)
        resolved_page_size_name = page_size_name or cls._resolve_page_size(parsed)

        settings = RenderSettingsCatalog.resolve(
            selected_layout,
            theme_name=resolved_theme_name,
            typography_name=resolved_typography_name,
            page_size_name=resolved_page_size_name,
            show_node_numbers=MetadataValueResolver.resolve_bool(
                parsed.metadata,
                "show-node-numbers",
                "show_node_numbers",
                "node-numbers",
                "node_numbers",
            ),
        )
        text_align = MetadataValueResolver.resolve_text_align(
            parsed.metadata,
            "text-align",
            "text_align",
        )
        if text_align is not None:
            settings = replace(
                settings,
                typography=replace(settings.typography, text_align=text_align),
            )

        scene = build_layout(
            selected_layout,
            parsed.root_nodes,
            settings.layout_config,
            settings.typography,
        )
        viewport = ViewportFitter.fit(scene, selected_layout, settings.layout_config)

        return RenderContext(
            parsed=parsed,
            scene=scene,
            settings=settings,
            viewport=viewport,
        )

    @staticmethod
    def _resolve_layout(parsed: ParsedDocument) -> LayoutKind:
        return (
            MetadataValueResolver.resolve_value(parsed.metadata, "layout")
            or DEFAULT_LAYOUT_KIND
        )

    @staticmethod
    def _resolve_theme(parsed: ParsedDocument) -> str | None:
        return MetadataValueResolver.resolve_value(parsed.metadata, "theme")

    @staticmethod
    def _resolve_typography(parsed: ParsedDocument) -> str | None:
        return MetadataValueResolver.resolve_value(parsed.metadata, "typography")

    @staticmethod
    def _resolve_page_size(parsed: ParsedDocument) -> str | None:
        return MetadataValueResolver.resolve_value(parsed.metadata, "size", "page-size")
