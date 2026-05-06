"""Resolucion de presets no semanticos del render compartidos por todos los tipos.

Este archivo solo aloja:
- presets de pagina (`PAGE_SIZES`)
- nombres por defecto reutilizables
- el `RenderProfile` y la funcion de resolucion `resolve(...)`

Los catalogos especificos de cada tipo de documento (layout configs,
tipografias, profiles por layout) viven en `render/<tipo>/profiles.py`. Cada
tipo registra su catalogo via `RenderProfileCatalog.register(...)` durante el
import del paquete `render.<tipo>`.

Esto evita que `shared` tenga que enumerar layouts de tipos concretos.
"""

from dataclasses import dataclass, replace
from typing import Dict, Literal, Optional

from koala.layout.shared.models import LayoutConfig, TypographyConfig
from koala.core.shared.errors import InvalidRenderConfigError
from koala.render.shared.models import RenderSettings
from koala.render.shared.themes import DEFAULT_THEME_NAME, ThemeCatalog


MM = 72.0 / 25.4
A4_WIDTH = 210 * MM
A4_HEIGHT = 297 * MM

DEFAULT_SHOW_NODE_NUMBERS = False
PageSizeName = Literal["a4", "a4_landscape", "square"]
DEFAULT_PAGE_SIZE: PageSizeName = "a4_landscape"

# Default conservador, util para fallback. El default real lo aporta cada
# tipo de documento desde su pipeline.
DEFAULT_LAYOUT_KIND: str = "tree"


@dataclass(frozen=True)
class RenderProfile:
    """Preset por layout que compone geometria, tipografia y theme default.

    `typography_name` es el nombre canonico de la tipografia asociada al
    profile, util para reportar settings ya resueltos sin invertir el lookup.
    """

    layout_config: LayoutConfig
    typography: TypographyConfig
    typography_name: str
    theme_name: str = DEFAULT_THEME_NAME


class RenderProfileCatalog:
    """Registro central de profiles y tipografias por tipo de documento.

    Cada tipo de documento llama a `register_profile(...)` y
    `register_typography(...)` desde su `render/<tipo>/profiles.py`. La capa
    shared solo orquesta lookup; no conoce los nombres de tipografia ni de
    layout especificos.
    """

    _PROFILES: Dict[tuple[str, str], RenderProfile] = {}
    _TYPOGRAPHIES: Dict[tuple[str, str], TypographyConfig] = {}

    @classmethod
    def register_profile(
        cls, document_type: str, layout_kind: str, profile: RenderProfile
    ) -> None:
        cls._PROFILES[(document_type, layout_kind)] = profile

    @classmethod
    def register_typography(
        cls, document_type: str, name: str, typography: TypographyConfig
    ) -> None:
        cls._TYPOGRAPHIES[(document_type, name)] = typography

    @classmethod
    def get_profile(cls, document_type: str, layout_kind: str) -> RenderProfile:
        key = (document_type, layout_kind)
        profile = cls._PROFILES.get(key)
        if profile is None:
            available = ", ".join(
                sorted(f"{dt}/{lk}" for dt, lk in cls._PROFILES.keys())
            )
            raise InvalidRenderConfigError(
                key="layout",
                value=layout_kind,
                expected=f"layout registrado para document_type='{document_type}'. Disponibles: {available or '(ninguno)'}",
            )
        return profile

    @classmethod
    def get_typography(
        cls, document_type: str, name: str
    ) -> TypographyConfig:
        typography = cls._TYPOGRAPHIES.get((document_type, name))
        if typography is None:
            available = ", ".join(
                sorted(n for dt, n in cls._TYPOGRAPHIES.keys() if dt == document_type)
            )
            raise InvalidRenderConfigError(
                key="typography",
                value=name,
                expected=f"typography para document_type='{document_type}'. Disponibles: {available or '(ninguno)'}",
            )
        return typography

    @classmethod
    def available_layouts_for(cls, document_type: str) -> tuple[str, ...]:
        return tuple(
            sorted(layout for dt, layout in cls._PROFILES.keys() if dt == document_type)
        )

    @classmethod
    def available_typography_names(cls) -> tuple[str, ...]:
        return tuple(sorted({name for _dt, name in cls._TYPOGRAPHIES.keys()}))

    @classmethod
    def available_typography_names_for(cls, document_type: str) -> tuple[str, ...]:
        return tuple(
            sorted(name for dt, name in cls._TYPOGRAPHIES.keys() if dt == document_type)
        )


class RenderSettingsCatalog:
    """Resolucion central de settings de render compartidos."""

    PAGE_SIZES: Dict[PageSizeName, tuple[float, float]] = {
        "a4": (A4_WIDTH, A4_HEIGHT),
        "a4_landscape": (A4_HEIGHT, A4_WIDTH),
        "square": (A4_WIDTH, A4_WIDTH),
    }

    @classmethod
    def available_page_size_names(cls) -> tuple[str, ...]:
        return tuple(cls.PAGE_SIZES.keys())

    @classmethod
    def resolve(
        cls,
        layout_kind: str,
        document_type: str = "tree",
        theme_name: Optional[str] = None,
        typography_name: Optional[str] = None,
        page_size_name: Optional[PageSizeName] = None,
        show_node_numbers: Optional[bool] = None,
    ) -> RenderSettings:
        profile = RenderProfileCatalog.get_profile(document_type, layout_kind)
        resolved_theme_name = theme_name or profile.theme_name
        resolved_page_size_name = page_size_name or DEFAULT_PAGE_SIZE

        if typography_name is not None:
            typography = RenderProfileCatalog.get_typography(document_type, typography_name)
            resolved_typography_name = typography_name
        else:
            typography = profile.typography
            resolved_typography_name = profile.typography_name

        theme = ThemeCatalog.resolve(resolved_theme_name)
        page_width, page_height = cls._require_named_preset(
            cls.PAGE_SIZES,
            resolved_page_size_name,
            preset_type="page size",
        )
        layout_config = replace(
            profile.layout_config,
            page_width=page_width,
            page_height=page_height,
        )

        return RenderSettings(
            layout_kind=layout_kind,
            theme_name=resolved_theme_name,
            typography_name=resolved_typography_name,
            page_size_name=resolved_page_size_name,
            layout_config=layout_config,
            typography=typography,
            theme=theme,
            show_node_numbers=(
                DEFAULT_SHOW_NODE_NUMBERS if show_node_numbers is None else show_node_numbers
            ),
        )

    @staticmethod
    def _require_named_preset(presets: Dict[str, object], name: str, preset_type: str):
        preset = presets.get(name)
        if preset is None:
            available = ", ".join(sorted(presets.keys()))
            raise InvalidRenderConfigError(
                key=preset_type,
                value=name,
                expected=f"uno de: {available}",
            )
        return preset


def available_page_size_names() -> tuple[str, ...]:
    return RenderSettingsCatalog.available_page_size_names()


def available_typography_names() -> tuple[str, ...]:
    return RenderProfileCatalog.available_typography_names()


def available_typography_names_for(document_type: str) -> tuple[str, ...]:
    return RenderProfileCatalog.available_typography_names_for(document_type)
