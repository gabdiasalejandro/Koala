"""Placeholder para el render de `matrix`.

Para implementarlo, este paquete debe contener:
- `profiles.py`: registra `RenderProfile` por layout y tipografias propias en
  `RenderProfileCatalog` (ver `render/tree/profiles.py` como ejemplo).
- `svg_render.py`: pipeline SVG que reciba un `SvgRenderRequest` y retorne
  `RenderResult(document_type="matrix", ...)`.

`__init__.py` debe importar `profiles` para que la registracion ocurra al
cargar el paquete.
"""
"""Render SVG exclusivo del tipo de documento `matrix`."""

from koala.render.matrix import profiles as _profiles  # noqa: F401
from koala.render.matrix.svg_render import MatrixSvgRenderPipeline, render_matrix_svg, render_svg

__all__ = ["MatrixSvgRenderPipeline", "render_matrix_svg", "render_svg"]
