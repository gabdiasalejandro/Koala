"""Presets de render exclusivos del tipo de documento `tree`.

Importar este modulo registra automaticamente los profiles de `tree` en el
`RenderProfileCatalog` compartido. `render/tree/__init__.py` lo importa para
garantizar la registracion temprana.

Aqui viven:
- `LAYOUT_CONFIGS`: variantes de geometria por layout (default, radial, synoptic)
- `TYPOGRAPHIES`: variantes tipograficas usadas por `tree`
- registro de un `RenderProfile` por cada layout soportado por `tree`
"""

from dataclasses import replace
from typing import Dict

from koala.layout.shared.models import LayoutConfig, TypographyConfig
from koala.render.shared.settings import (
    A4_HEIGHT,
    A4_WIDTH,
    MM,
    RenderProfile,
    RenderProfileCatalog,
)
from koala.render.shared.themes import DEFAULT_THEME_NAME


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
LAYOUT_CONFIGS["tree"] = replace(
    LAYOUT_CONFIGS["default"],
    depth_width_reduction=0.0,
    max_depth_reduction=0.0,
)
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
        max_title_lines=5,
        title_line_extra=1.2,
    ),
}
TYPOGRAPHIES["academic"] = replace(
    TYPOGRAPHIES["default"],
    title_font="Georgia",
    body_font="Times New Roman",
    title_size_base=18.2,
    title_size_min=16.4,
    body_size=11.2,
    relation_size=9.8,
    body_leading=14.4,
    title_line_extra=1.1,
)
TYPOGRAPHIES["formal"] = replace(
    TYPOGRAPHIES["default"],
    title_font="Times New Roman",
    body_font="Arial",
    title_size_base=18.4,
    title_size_min=16.5,
    body_size=11.0,
    relation_size=9.8,
    body_leading=13.8,
    title_line_extra=1.0,
)
TYPOGRAPHIES["casual"] = replace(
    TYPOGRAPHIES["default"],
    title_font="Trebuchet MS",
    body_font="Verdana",
    title_size_base=17.2,
    title_size_min=15.4,
    body_size=10.9,
    relation_size=9.8,
    body_leading=13.8,
)
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


def _register_tree_profiles() -> None:
    for typography_name, typography in TYPOGRAPHIES.items():
        RenderProfileCatalog.register_typography("tree", typography_name, typography)

    profiles_by_layout = {
        "tree": ("tree", "default"),
        "synoptic": ("synoptic", "default"),
        "synoptic_boxes": ("synoptic", "default"),
        "radial": ("radial", "radial"),
    }
    for layout_kind, (layout_config_name, typography_name) in profiles_by_layout.items():
        profile = RenderProfile(
            layout_config=LAYOUT_CONFIGS[layout_config_name],
            typography=TYPOGRAPHIES[typography_name],
            typography_name=typography_name,
            theme_name=DEFAULT_THEME_NAME,
        )
        RenderProfileCatalog.register_profile("tree", layout_kind, profile)


_register_tree_profiles()
