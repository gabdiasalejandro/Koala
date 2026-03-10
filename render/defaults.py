from dataclasses import replace

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

from layout.models import LayoutConfig, LayoutKind, NodeStyle, ThemeConfig, TypographyConfig


PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

SHOW_NODE_NUMBERS = True
SHOW_WARNINGS_FOOTER = False
DEFAULT_LAYOUT_KIND: LayoutKind = "tree"

DEFAULT_LAYOUT_CONFIG = LayoutConfig(
    page_width=PAGE_WIDTH,
    page_height=PAGE_HEIGHT,
    margin_x=12 * mm,
    margin_y=12 * mm,
    node_width_base=100 * mm,
    min_node_width=34 * mm,
    root_width_factor=1.5,
    depth_width_reduction=0.10,
    max_depth_reduction=0.35,
    h_gap_base=9 * mm,
    v_gap_base=10 * mm,
    inner_pad_x=3.5 * mm,
    inner_pad_y=2.8 * mm,
    corner_radius=4.0,
    title_body_gap=1.8 * mm,
)

RADIAL_LAYOUT_CONFIG = replace(
    DEFAULT_LAYOUT_CONFIG,
    node_width_base=58 * mm,
    min_node_width=22 * mm,
    root_width_factor=1.15,
    depth_width_reduction=0,
    max_depth_reduction=0.55,
    h_gap_base=6 * mm,
    v_gap_base=6 * mm,
    inner_pad_x=2.6 * mm,
    inner_pad_y=2.2 * mm,
    title_body_gap=1.0 * mm,
)

DEFAULT_TYPOGRAPHY = TypographyConfig(
    title_font="Helvetica-Bold",
    body_font="Helvetica",
    title_size_base=20.0,
    title_size_min=20.0,
    body_size=12.0,
    relation_size=11.0,
    body_leading=15.0,
    max_title_lines=3,
    title_line_extra=1.8,
)

RADIAL_TYPOGRAPHY = replace(
    DEFAULT_TYPOGRAPHY,
    title_size_base=21.0,
    title_size_min=19.0,
    body_size=13.0,
    relation_size=11.5,
    body_leading=15.5,
)

DEFAULT_THEME = ThemeConfig(
    default_node=NodeStyle(
        fill="#F9FBFD",
        stroke="#52728A",
        title="#16324A",
        body="#25313C",
    ),
    node_by_kind={
        "fr": NodeStyle(
            fill="#EFF7FF",
            stroke="#2F6FA3",
            title="#123B5A",
            body="#1A2E3D",
        ),
    },
    edge_color="#8AA3B7",
    relation_color="#4E6472",
    number_pill_bg="#E3EDF5",
)


def layout_config_for(layout_kind: LayoutKind) -> LayoutConfig:
    if layout_kind == "radial":
        return RADIAL_LAYOUT_CONFIG
    return DEFAULT_LAYOUT_CONFIG


def typography_for(layout_kind: LayoutKind) -> TypographyConfig:
    if layout_kind == "radial":
        return RADIAL_TYPOGRAPHY
    return DEFAULT_TYPOGRAPHY
