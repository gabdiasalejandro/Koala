"""Construccion del `RenderContext`.

Este archivo toma decisiones de orquestacion:
- aplica precedencia entre argumentos explicitos, metadata y defaults
- resuelve settings visuales
- construye la escena de layout
- ajusta el viewport final

La salida es un `RenderContext` listo para que el backend SVG lo dibuje.
"""

import re
from dataclasses import replace
from typing import Optional

from koala.core.models import ParsedDocument
from koala.layout.models import LayoutKind
from koala.layout.registry import build_layout
from koala.render.models import RenderContext
from koala.render.settings import DEFAULT_LAYOUT_KIND, PageSizeName, RenderSettingsCatalog
from koala.render.viewport import ViewportFitter


class MetadataValueResolver:
    """Helpers para leer metadata tolerante a aliases y valores flexibles."""

    BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "on", "show", "shown"}
    BOOLEAN_FALSE_VALUES = {"0", "false", "no", "off", "hide", "hidden"}
    TEXT_ALIGN_VALUES = {"left", "justify"}
    HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

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

            normalized = cls.normalize_text_align(raw_value)
            if normalized is not None:
                return normalized
        return None

    @classmethod
    def normalize_text_align(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip().lower()
        if normalized in cls.TEXT_ALIGN_VALUES:
            return normalized
        return None

    @classmethod
    def resolve_hex_color(cls, metadata: dict[str, str], *keys: str) -> str | None:
        for key in keys:
            raw_value = metadata.get(key)
            if raw_value is None:
                continue

            normalized = cls.normalize_hex_color(raw_value)
            if normalized is None:
                raise ValueError(
                    f"Metadata '{key}' invalida: '{raw_value}'. Usa un color hex como #F7F4ED."
                )
            return normalized
        return None

    @classmethod
    def normalize_hex_color(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if cls.HEX_COLOR_RE.match(normalized):
            return normalized.upper()
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
        selected_layout = layout_kind or cls._resolve_layout(parsed, default_layout_kind)
        resolved_theme_name = theme_name or cls._resolve_theme(parsed, default_theme_name)
        resolved_typography_name = typography_name or cls._resolve_typography(
            parsed,
            default_typography_name,
        )
        resolved_page_size_name = page_size_name or cls._resolve_page_size(
            parsed,
            default_page_size_name,
        )
        resolved_show_node_numbers = (
            show_node_numbers
            if show_node_numbers is not None
            else MetadataValueResolver.resolve_bool(
                parsed.metadata,
                "show-node-numbers",
                "show_node_numbers",
                "node-numbers",
                "node_numbers",
            )
        )
        if resolved_show_node_numbers is None:
            resolved_show_node_numbers = default_show_node_numbers

        settings = RenderSettingsCatalog.resolve(
            selected_layout,
            theme_name=resolved_theme_name,
            typography_name=resolved_typography_name,
            page_size_name=resolved_page_size_name,
            show_node_numbers=resolved_show_node_numbers,
        )
        resolved_text_align = (
            MetadataValueResolver.normalize_text_align(text_align)
            or MetadataValueResolver.resolve_text_align(
                parsed.metadata,
                "text-align",
                "text_align",
            )
            or MetadataValueResolver.normalize_text_align(default_text_align)
        )
        if resolved_text_align is not None:
            settings = replace(
                settings,
                typography=replace(settings.typography, text_align=resolved_text_align),
            )
        resolved_background_color = cls._resolve_background_color(parsed, background_color)
        if resolved_background_color is not None:
            settings = replace(settings, background_color=resolved_background_color)

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
    def _resolve_layout(
        parsed: ParsedDocument,
        default_layout_kind: LayoutKind | None = None,
    ) -> LayoutKind:
        return (
            MetadataValueResolver.resolve_value(parsed.metadata, "layout")
            or default_layout_kind
            or DEFAULT_LAYOUT_KIND
        )

    @staticmethod
    def _resolve_theme(parsed: ParsedDocument, default_theme_name: str | None = None) -> str | None:
        return MetadataValueResolver.resolve_value(parsed.metadata, "theme") or default_theme_name

    @staticmethod
    def _resolve_typography(
        parsed: ParsedDocument,
        default_typography_name: str | None = None,
    ) -> str | None:
        return (
            MetadataValueResolver.resolve_value(parsed.metadata, "typography")
            or default_typography_name
        )

    @staticmethod
    def _resolve_page_size(
        parsed: ParsedDocument,
        default_page_size_name: str | None = None,
    ) -> str | None:
        return (
            MetadataValueResolver.resolve_value(parsed.metadata, "size", "page-size")
            or default_page_size_name
        )

    @staticmethod
    def _resolve_background_color(
        parsed: ParsedDocument,
        explicit_background_color: str | None = None,
    ) -> str | None:
        if explicit_background_color is not None:
            normalized = MetadataValueResolver.normalize_hex_color(explicit_background_color)
            if normalized is None:
                raise ValueError(
                    "Background invalido. Usa un color hex como #F7F4ED."
                )
            return normalized

        return MetadataValueResolver.resolve_hex_color(
            parsed.metadata,
            "background",
            "background-color",
            "background_color",
        )
