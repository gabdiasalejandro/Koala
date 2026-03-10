from typing import Callable, Dict, List

from core.models import ConceptNode
from layout.conceptual_topdown import build_topdown_layout
from layout.models import LayoutConfig, LayoutKind, LayoutScene, TypographyConfig


LayoutEngine = Callable[[List[ConceptNode], LayoutConfig, TypographyConfig], LayoutScene]


LAYOUT_ENGINES: Dict[LayoutKind, LayoutEngine] = {
    "tree": build_topdown_layout,
}


def build_layout(
    layout_kind: LayoutKind,
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    engine = LAYOUT_ENGINES.get(layout_kind)
    if engine is None:
        available = ", ".join(sorted(LAYOUT_ENGINES.keys()))
        raise NotImplementedError(
            f"Layout '{layout_kind}' aun no esta implementado. Disponibles: {available}."
        )

    return engine(root_nodes, config, typography)
