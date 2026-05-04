"""Placeholder para los layouts de `matrix`.

Para implementarlo, este paquete debe contener:
- `models.py`: `MatrixLayoutKind` (Literal con los layouts soportados).
- `registry.py`: `MATRIX_LAYOUTS: tuple[str, ...]` y un builder
  `build_matrix_layout_scene(layout_kind, parsed, config, typography) -> LayoutScene`.
- un modulo por engine de layout (grid, swimlane, etc.).
"""
