"""Registro de layouts exclusivos del tipo de documento `tree`."""

from typing import Callable, Dict, List

from koala.layout.shared.models import (
    LayoutConfig,
    LayoutKind,
    LayoutScene,
    TypographyConfig,
)
from koala.layout.tree.radial import build_radial_layout
from koala.layout.tree.synoptic import build_synoptic_layout
from koala.layout.tree.synoptic_boxes import build_synoptic_boxes_layout
from koala.layout.tree.tree import build_tree_layout
from koala.core.tree.models import ConceptNode


TreeLayoutEngine = Callable[[List[ConceptNode], LayoutConfig, TypographyConfig], LayoutScene]


TREE_LAYOUT_ENGINES: Dict[LayoutKind, TreeLayoutEngine] = {
    "tree": build_tree_layout,
    "synoptic": build_synoptic_layout,
    "synoptic_boxes": build_synoptic_boxes_layout,
    "radial": build_radial_layout,
}
TREE_LAYOUTS: tuple[LayoutKind, ...] = tuple(TREE_LAYOUT_ENGINES.keys())


def build_tree_layout_scene(
    layout_kind: LayoutKind,
    root_nodes: List[ConceptNode],
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    engine = TREE_LAYOUT_ENGINES.get(layout_kind)
    if engine is None:
        available = ", ".join(sorted(TREE_LAYOUT_ENGINES.keys()))
        raise NotImplementedError(
            f"Layout tree '{layout_kind}' aun no esta implementado. Disponibles: {available}."
        )

    return engine(root_nodes, config, typography)
