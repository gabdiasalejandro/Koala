"""API publica del subsistema de render.

Expone el entrypoint SVG y mantiene el paquete con una superficie chica:
- `render_svg(...)` como punto de entrada.
- El resto de modulos separan configuracion, viewport y dibujo.
"""

from render.svg_render import render_svg

__all__ = ["render_svg"]
