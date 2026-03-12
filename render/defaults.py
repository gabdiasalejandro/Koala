"""Presets visuales y de pagina del render.

La idea es poder crecer por registro y no por `if` dispersos:
- tipografias registradas por nombre
- temas registrados por nombre
- perfiles por layout que componen esos presets
"""

from dataclasses import dataclass, replace
from typing import Dict, Literal, Optional

from layout.models import LayoutConfig, LayoutKind, NodeStyle, ThemeConfig, TypographyConfig
from render.models import RenderSettings


MM = 72.0 / 25.4
A4_WIDTH = 210 * MM
A4_HEIGHT = 297 * MM

DEFAULT_SHOW_NODE_NUMBERS = True
SHOW_WARNINGS_FOOTER = False
DEFAULT_LAYOUT_KIND: LayoutKind = "tree"
DEFAULT_THEME_NAME = "default"
PageSizeName = Literal["a4", "a4_landscape", "square"]
DEFAULT_PAGE_SIZE: PageSizeName = "a4_landscape"


@dataclass(frozen=True)
class RenderProfile:
    layout_config_name: str
    typography_name: str
    theme_name: str = DEFAULT_THEME_NAME


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

THEMES: Dict[str, ThemeConfig] = {
    "default": ThemeConfig(
        default_node=NodeStyle(
            fill="#F8FAFC",
            stroke="#4A647D",
            title="#1A3044",
            body="#314252",
        ),
        node_by_kind={
            "hl": NodeStyle(
                fill="#FFF4D8",
                stroke="#D39A2C",
                title="#6B4D00",
                body="#624E21",
            ),
        },
        edge_color="#93A7B8",
        implicit_edge_color="#5C7286",
        relation_color="#A14F1A",
        number_pill_bg="#E6EDF3",
        number_pill_text="#5A6E7D",
    ),
    "terracotta": ThemeConfig(
        default_node=NodeStyle(
            fill="#FFF7F1",
            stroke="#8F5D4A",
            title="#48281E",
            body="#66483F",
        ),
        node_by_kind={
            "hl": NodeStyle(
                fill="#FFE0D1",
                stroke="#C35A34",
                title="#6A2817",
                body="#7A4332",
            ),
        },
        edge_color="#B48B7A",
        implicit_edge_color="#7A6258",
        relation_color="#8C2F46",
        number_pill_bg="#F4E0D6",
        number_pill_text="#8B6557",
    ),
    "jungle": ThemeConfig(
        default_node=NodeStyle(
            fill="#F2FBF8",
            stroke="#4C8C78",
            title="#184A44",
            body="#2D5F68",
        ),
        node_by_kind={
            "hl": NodeStyle(
                fill="#DDF6F0",
                stroke="#2F9B8F",
                title="#0F5A63",
                body="#2C6670",
            ),
        },
        edge_color="#86B8AD",
        implicit_edge_color="#4E7F86",
        relation_color="#146B8C",
        number_pill_bg="#DDEFEA",
        number_pill_text="#5A8E95",
    ),
}

LAYOUT_RENDER_PROFILES: Dict[LayoutKind, RenderProfile] = {
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


def available_theme_names() -> tuple[str, ...]:
    return tuple(sorted(THEMES.keys()))


def available_typography_names() -> tuple[str, ...]:
    return tuple(sorted(TYPOGRAPHIES.keys()))


def available_page_size_names() -> tuple[str, ...]:
    return tuple(PAGE_SIZES.keys())


def resolve_render_settings(
    layout_kind: LayoutKind,
    theme_name: Optional[str] = None,
    typography_name: Optional[str] = None,
    page_size_name: Optional[PageSizeName] = None,
    show_node_numbers: Optional[bool] = None,
) -> RenderSettings:
    profile = LAYOUT_RENDER_PROFILES[layout_kind]
    resolved_theme_name = theme_name or profile.theme_name
    resolved_typography_name = typography_name or profile.typography_name
    resolved_page_size_name = page_size_name or DEFAULT_PAGE_SIZE

    layout_config = _require_named_preset(
        LAYOUT_CONFIGS,
        profile.layout_config_name,
        preset_type="layout config",
    )
    typography = _require_named_preset(
        TYPOGRAPHIES,
        resolved_typography_name,
        preset_type="typography",
    )
    theme = _require_named_preset(
        THEMES,
        resolved_theme_name,
        preset_type="theme",
    )
    page_width, page_height = _require_named_preset(
        PAGE_SIZES,
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
        layout_config=layout_config,
        typography=typography,
        theme=theme,
        show_node_numbers=DEFAULT_SHOW_NODE_NUMBERS if show_node_numbers is None else show_node_numbers,
    )


def _require_named_preset(presets: Dict[str, object], name: str, preset_type: str):
    preset = presets.get(name)
    if preset is None:
        available = ", ".join(sorted(presets.keys()))
        raise ValueError(f"{preset_type} '{name}' no existe. Disponibles: {available}.")
    return preset
