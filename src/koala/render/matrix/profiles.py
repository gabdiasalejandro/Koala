"""Presets de render exclusivos del tipo de documento `matrix`."""

from __future__ import annotations

from typing import Dict

from koala.layout.shared.models import LayoutConfig, TypographyConfig
from koala.render.shared.settings import A4_HEIGHT, A4_WIDTH, MM, RenderProfile, RenderProfileCatalog
from koala.render.shared.themes import DEFAULT_THEME_NAME


MATRIX_LAYOUT_CONFIG = LayoutConfig(
    page_width=A4_HEIGHT,
    page_height=A4_WIDTH,
    margin_x=14 * MM,
    margin_y=14 * MM,
    node_width_base=84 * MM,
    min_node_width=30 * MM,
    root_width_factor=1.0,
    depth_width_reduction=0.0,
    max_depth_reduction=0.0,
    h_gap_base=0.0,
    v_gap_base=0.0,
    inner_pad_x=3.4 * MM,
    inner_pad_y=2.6 * MM,
    corner_radius=0.0,
    title_body_gap=1.0 * MM,
)

TYPOGRAPHIES: Dict[str, TypographyConfig] = {
    "default": TypographyConfig(
        title_font="Georgia",
        body_font="Arial",
        title_size_base=19.0,
        title_size_min=17.0,
        body_size=10.6,
        relation_size=9.5,
        body_leading=13.2,
        max_title_lines=3,
        title_line_extra=1.2,
    ),
    "formal": TypographyConfig(
        title_font="Times New Roman",
        body_font="Arial",
        title_size_base=19.4,
        title_size_min=17.2,
        body_size=10.4,
        relation_size=9.4,
        body_leading=13.0,
        max_title_lines=3,
        title_line_extra=1.0,
    ),
}


def _register_matrix_profiles() -> None:
    for typography_name, typography in TYPOGRAPHIES.items():
        RenderProfileCatalog.register_typography("matrix", typography_name, typography)

    RenderProfileCatalog.register_profile(
        "matrix",
        "matrix",
        RenderProfile(
            layout_config=MATRIX_LAYOUT_CONFIG,
            typography=TYPOGRAPHIES["formal"],
            typography_name="formal",
            theme_name=DEFAULT_THEME_NAME,
        ),
    )


_register_matrix_profiles()
