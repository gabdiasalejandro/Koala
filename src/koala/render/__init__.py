"""API publica del subsistema de render.

La superficie publica sigue siendo pequena:
- `render_svg(...)` como entrypoint de ejecucion
- el resto del paquete solo organiza contexto, presets y backend SVG
"""

from koala.render.svg_render import render_svg

__all__ = ["render_svg"]
