"""Registro de layouts exclusivos del tipo de documento `flowchart`."""

from __future__ import annotations

from typing import Callable, Dict

from koala.core.flowchart.models import ParsedFlowchartDocument
from koala.layout.flowchart.flowchart import build_flowchart_layout
from koala.layout.flowchart.models import FlowchartLayoutKind
from koala.layout.shared.models import LayoutConfig, LayoutScene, TypographyConfig


FlowchartLayoutEngine = Callable[[ParsedFlowchartDocument, LayoutConfig, TypographyConfig], LayoutScene]

FLOWCHART_LAYOUT_ENGINES: Dict[str, FlowchartLayoutEngine] = {
    "flowchart": build_flowchart_layout,
}
FLOWCHART_LAYOUTS: tuple[str, ...] = tuple(FLOWCHART_LAYOUT_ENGINES.keys())


def build_flowchart_layout_scene(
    layout_kind: str,
    parsed: ParsedFlowchartDocument,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    engine = FLOWCHART_LAYOUT_ENGINES.get(layout_kind)
    if engine is None:
        available = ", ".join(sorted(FLOWCHART_LAYOUT_ENGINES.keys()))
        raise NotImplementedError(
            f"Layout flowchart '{layout_kind}' no esta implementado. Disponibles: {available}."
        )
    return engine(parsed, config, typography)
