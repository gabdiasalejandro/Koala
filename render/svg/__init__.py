"""Backend SVG del subsistema de render.

Este subpaquete separa el dibujo por responsabilidad:
- documento SVG
- texto
- aristas
- nodos
- canvas final

El objetivo es que cada pieza conozca solo el estado minimo que necesita.
"""

from render.svg.canvas import SvgCanvasRenderer
from render.svg.document import SvgDocumentFactory

__all__ = ["SvgCanvasRenderer", "SvgDocumentFactory"]
