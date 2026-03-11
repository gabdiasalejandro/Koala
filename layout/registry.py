"""Registro de motores de layout.

Retorna una `LayoutScene` a través de `build_layout(layout_kind, ...)`.

Cómo funciona:
1. Mapea cada `LayoutKind` a una función constructora.
2. Valida si el layout solicitado existe.
3. Ejecuta el motor y devuelve la escena genérica para render.
"""

from typing import Callable, Dict, List

from core.models import ConceptNode
from layout.radial_layout import build_radial_layout
from layout.models import LayoutConfig, LayoutKind, LayoutScene, TypographyConfig
from layout.synoptic_layout import build_synoptic_layout
from layout.synoptic_boxes_layout import build_synoptic_boxes_layout
from layout.tree_layout import build_tree_layout


LayoutEngine = Callable[[List[ConceptNode], LayoutConfig, TypographyConfig], LayoutScene]


LAYOUT_ENGINES: Dict[LayoutKind, LayoutEngine] = {
    "tree": build_tree_layout,
    "synoptic": build_synoptic_layout,
    "synoptic_boxes": build_synoptic_boxes_layout,
    "radial": build_radial_layout,
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
