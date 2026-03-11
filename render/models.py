"""Modelos internos del pipeline de render.

Separa dos responsabilidades:
- `RenderSettings`: configuracion visual y de pagina ya resuelta.
- `RenderContext`/`ViewportTransform`: escena lista para dibujar en SVG.
"""

from dataclasses import dataclass

from core.models import ParsedDocument
from layout.models import LayoutConfig, LayoutKind, LayoutScene, ThemeConfig, TypographyConfig


@dataclass(frozen=True)
class RenderSettings:
    layout_kind: LayoutKind
    layout_config: LayoutConfig
    typography: TypographyConfig
    theme: ThemeConfig


@dataclass(frozen=True)
class ViewportTransform:
    scale: float
    translate_x: float
    translate_y: float

    def svg_transform(self) -> str:
        return f"translate({self.translate_x},{self.translate_y}) scale({self.scale})"


@dataclass(frozen=True)
class RenderContext:
    parsed: ParsedDocument
    scene: LayoutScene
    settings: RenderSettings
    viewport: ViewportTransform
