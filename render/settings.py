"""Resolucion de presets no semanticos del render.

Este archivo mantiene separados de los themes:
- perfiles por layout
- configuraciones de layout
- tipografias
- tamaños de pagina

El objetivo es que cambiar color, tipografia o geometria no mezcle registros
con responsabilidades distintas.
"""

from dataclasses import dataclass, replace
from typing import Dict, Literal, Optional

from layout.models import LayoutConfig, LayoutKind, TypographyConfig
from render.models import RenderSettings
from render.themes import DEFAULT_THEME_NAME, ThemeCatalog


MM = 72.0 / 25.4
A4_WIDTH = 210 * MM
A4_HEIGHT = 297 * MM

DEFAULT_SHOW_NODE_NUMBERS = True
DEFAULT_LAYOUT_KIND: LayoutKind = "tree"
PageSizeName = Literal["a4", "a4_landscape", "square"]
DEFAULT_PAGE_SIZE: PageSizeName = "a4_landscape"


@dataclass(frozen=True)
class RenderProfile:
    """Preset por layout que compone geometria, tipografia y theme default."""

    layout_config_name: str
    typography_name: str
    theme_name: str = DEFAULT_THEME_NAME


class RenderSettingsCatalog:
    """Registro y resolucion central de settings de render."""

    LAYOUT_CONFIGS: Dict[str, LayoutConfig] = {
        "default": LayoutConfig(
            page_width=A4_HEIGHT,
            page_height=A4_WIDTH,
            margin_x=12 * MM,
            margin_y=12 * MM,
            node_width_base=100 * MM,
            min_node_width=34 * MM,
            root_width_factor=1.5,
            depth_width_reduction=0.10,
            max_depth_reduction=0.35,
            h_gap_base=9 * MM,
            v_gap_base=10 * MM,
            inner_pad_x=3.5 * MM,
            inner_pad_y=2.8 * MM,
            corner_radius=4.0,
            title_body_gap=1.8 * MM,
        ),
    }
    LAYOUT_CONFIGS["radial"] = replace(
        LAYOUT_CONFIGS["default"],
        node_width_base=58 * MM,
        min_node_width=22 * MM,
        root_width_factor=1.15,
        depth_width_reduction=0,
        max_depth_reduction=0.55,
        h_gap_base=6 * MM,
        v_gap_base=6 * MM,
        inner_pad_x=2.6 * MM,
        inner_pad_y=2.2 * MM,
        title_body_gap=1.0 * MM,
    )
    LAYOUT_CONFIGS["synoptic"] = replace(
        LAYOUT_CONFIGS["default"],
        root_width_factor=1.0,
    )

    TYPOGRAPHIES: Dict[str, TypographyConfig] = {
        "default": TypographyConfig(
            title_font="Georgia",
            body_font="Arial",
            title_size_base=18.0,
            title_size_min=16.5,
            body_size=11.4,
            relation_size=10.0,
            body_leading=14.2,
            max_title_lines=3,
            title_line_extra=1.2,
        ),
    }
    TYPOGRAPHIES["radial"] = replace(
        TYPOGRAPHIES["default"],
        title_font="Trebuchet MS",
        body_font="Verdana",
        title_size_base=16.8,
        title_size_min=15.0,
        body_size=10.8,
        relation_size=9.8,
        body_leading=13.4,
    )

    PROFILES: Dict[LayoutKind, RenderProfile] = {
        "tree": RenderProfile(layout_config_name="default", typography_name="default"),
        "synoptic": RenderProfile(layout_config_name="synoptic", typography_name="default"),
        "synoptic_boxes": RenderProfile(layout_config_name="synoptic", typography_name="default"),
        "radial": RenderProfile(layout_config_name="radial", typography_name="radial"),
    }

    PAGE_SIZES: Dict[PageSizeName, tuple[float, float]] = {
        "a4": (A4_WIDTH, A4_HEIGHT),
        "a4_landscape": (A4_HEIGHT, A4_WIDTH),
        "square": (A4_WIDTH, A4_WIDTH),
    }

    @classmethod
    def available_page_size_names(cls) -> tuple[str, ...]:
        return tuple(cls.PAGE_SIZES.keys())

    @classmethod
    def available_typography_names(cls) -> tuple[str, ...]:
        return tuple(sorted(cls.TYPOGRAPHIES.keys()))

    @classmethod
    def resolve(
        cls,
        layout_kind: LayoutKind,
        theme_name: Optional[str] = None,
        typography_name: Optional[str] = None,
        page_size_name: Optional[PageSizeName] = None,
        show_node_numbers: Optional[bool] = None,
    ) -> RenderSettings:
        profile = cls.PROFILES[layout_kind]
        resolved_theme_name = theme_name or profile.theme_name
        resolved_typography_name = typography_name or profile.typography_name
        resolved_page_size_name = page_size_name or DEFAULT_PAGE_SIZE

        layout_config = cls._require_named_preset(
            cls.LAYOUT_CONFIGS,
            profile.layout_config_name,
            preset_type="layout config",
        )
        typography = cls._require_named_preset(
            cls.TYPOGRAPHIES,
            resolved_typography_name,
            preset_type="typography",
        )
        theme = ThemeCatalog.resolve(resolved_theme_name)
        page_width, page_height = cls._require_named_preset(
            cls.PAGE_SIZES,
            resolved_page_size_name,
            preset_type="page size",
        )
        layout_config = replace(
            layout_config,
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
            raise ValueError(f"{preset_type} '{name}' no existe. Disponibles: {available}.")
        return preset


def available_page_size_names() -> tuple[str, ...]:
    return RenderSettingsCatalog.available_page_size_names()


def available_typography_names() -> tuple[str, ...]:
    return RenderSettingsCatalog.available_typography_names()
