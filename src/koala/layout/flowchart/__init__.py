"""Placeholder para los layouts de `flowchart`.

Para implementarlo, este paquete debe contener:
- `models.py`: `FlowchartLayoutKind` (Literal con los layouts soportados).
- `registry.py`: `FLOWCHART_LAYOUTS: tuple[str, ...]` y un builder
  `build_flowchart_layout_scene(layout_kind, parsed, config, typography) -> LayoutScene`.
- un modulo por engine de layout (top-down, left-right, swim, etc.).
"""
