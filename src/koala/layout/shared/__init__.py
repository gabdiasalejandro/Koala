"""Contratos y helpers compartidos por layouts."""

from koala.layout.shared.models import (
    LayoutBox,
    LayoutConfig,
    LayoutEdge,
    LayoutKind,
    LayoutScene,
    TypographyConfig,
)
from koala.layout.shared.measurement import (
    build_scene,
    get_h_gap_for_depth,
    get_v_gap_for_depth,
    measure_nodes,
    measure_text_width,
    sort_node_key,
    wrap_text_lines,
)

__all__ = [
    "LayoutBox",
    "LayoutConfig",
    "LayoutEdge",
    "LayoutKind",
    "LayoutScene",
    "TypographyConfig",
    "build_scene",
    "get_h_gap_for_depth",
    "get_v_gap_for_depth",
    "measure_nodes",
    "measure_text_width",
    "sort_node_key",
    "wrap_text_lines",
]
