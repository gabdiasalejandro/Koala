"""Presets de render exclusivos del tipo de documento `flowchart`."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict

from koala.layout.shared.models import LayoutConfig, TypographyConfig
from koala.render.shared.settings import A4_HEIGHT, A4_WIDTH, MM, RenderProfile, RenderProfileCatalog
from koala.render.shared.themes import DEFAULT_THEME_NAME


FLOWCHART_LAYOUT_CONFIG = LayoutConfig(
    page_width=A4_HEIGHT,
    page_height=A4_WIDTH,
    margin_x=12 * MM,
    margin_y=12 * MM,
    node_width_base=100.0,
    min_node_width=40.0,
    root_width_factor=1.0,
    depth_width_reduction=0.0,
    max_depth_reduction=0.0,
    h_gap_base=20.0,
    v_gap_base=28.0,
    inner_pad_x=3.0 * MM,
    inner_pad_y=2.4 * MM,
    corner_radius=6.0,
    title_body_gap=1.0 * MM,
)

TYPOGRAPHIES: Dict[str, TypographyConfig] = {
    "default": TypographyConfig(
        title_font="Georgia",
        body_font="Arial",
        title_size_base=14.0,
        title_size_min=11.5,
        body_size=10.5,
        relation_size=9.0,
        body_leading=13.0,
        max_title_lines=5,
        title_line_extra=1.2,
    ),
    "formal": TypographyConfig(
        title_font="Times New Roman",
        body_font="Arial",
        title_size_base=13.8,
        title_size_min=11.2,
        body_size=10.3,
        relation_size=8.8,
        body_leading=12.8,
        max_title_lines=5,
        title_line_extra=1.0,
    ),
}
TYPOGRAPHIES["academic"] = replace(
    TYPOGRAPHIES["default"],
    title_font="Georgia",
    body_font="Times New Roman",
    title_size_base=13.6,
    title_size_min=11.0,
    body_size=10.2,
    body_leading=13.2,
    title_line_extra=1.0,
)
TYPOGRAPHIES["casual"] = replace(
    TYPOGRAPHIES["default"],
    title_font="Trebuchet MS",
    body_font="Verdana",
    title_size_base=13.0,
    title_size_min=10.8,
    body_size=9.8,
    body_leading=12.6,
    title_line_extra=1.0,
)


def _register_flowchart_profiles() -> None:
    for typography_name, typography in TYPOGRAPHIES.items():
        RenderProfileCatalog.register_typography("flowchart", typography_name, typography)

    RenderProfileCatalog.register_profile(
        "flowchart",
        "flowchart",
        RenderProfile(
            layout_config=FLOWCHART_LAYOUT_CONFIG,
            typography=TYPOGRAPHIES["default"],
            typography_name="default",
            theme_name=DEFAULT_THEME_NAME,
        ),
    )


_register_flowchart_profiles()
