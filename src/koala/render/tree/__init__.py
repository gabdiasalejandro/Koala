"""Render SVG exclusivo del tipo de documento `tree`."""

# Importar `profiles` registra los `RenderProfile` de tree en el catalogo
# compartido. Debe ejecutarse antes de cualquier resolucion de settings.
from koala.render.tree import profiles as _profiles  # noqa: F401
from koala.render.tree.svg_render import TreeSvgRenderPipeline, render_svg, render_tree_svg

__all__ = ["TreeSvgRenderPipeline", "render_svg", "render_tree_svg"]
