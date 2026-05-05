"""Registro de layouts exclusivos del tipo de documento `matrix`."""

from __future__ import annotations

from typing import Callable, Dict

from koala.core.matrix.models import ParsedMatrixDocument
from koala.layout.matrix.matrix import build_matrix_layout
from koala.layout.matrix.models import MatrixLayoutKind
from koala.layout.shared.models import LayoutConfig, LayoutScene, TypographyConfig


MatrixLayoutEngine = Callable[[ParsedMatrixDocument, LayoutConfig, TypographyConfig], LayoutScene]

MATRIX_LAYOUT_ENGINES: Dict[MatrixLayoutKind, MatrixLayoutEngine] = {
    "matrix": build_matrix_layout,  # type: ignore[dict-item]
}
MATRIX_LAYOUTS: tuple[MatrixLayoutKind, ...] = tuple(MATRIX_LAYOUT_ENGINES.keys())


def build_matrix_layout_scene(
    layout_kind: str,
    parsed: ParsedMatrixDocument,
    config: LayoutConfig,
    typography: TypographyConfig,
) -> LayoutScene:
    engine = MATRIX_LAYOUT_ENGINES.get(layout_kind)  # type: ignore[arg-type]
    if engine is None:
        available = ", ".join(sorted(MATRIX_LAYOUT_ENGINES.keys()))
        raise NotImplementedError(
            f"Layout matrix '{layout_kind}' aun no esta implementado. Disponibles: {available}."
        )
    return engine(parsed, config, typography)
