"""Calculo del viewport SVG.

Traduce una `LayoutScene` al espacio final de pagina:
- escala si el contenido excede el area util.
- permite ampliar `tree` y `radial` cuando sobra espacio.
- centra esos layouts si queda aire en algun eje.
"""

from layout.models import LayoutConfig, LayoutKind, LayoutScene
from render.models import ViewportTransform


def fit_scene_to_page(
    scene: LayoutScene,
    layout_kind: LayoutKind,
    config: LayoutConfig,
) -> ViewportTransform:
    content_w = max(1.0, scene.content_right - scene.content_left)
    content_h = max(1.0, scene.content_bottom - scene.content_top)
    usable_w = config.page_width - (2 * config.margin_x)
    usable_h = config.page_height - (2 * config.margin_y)

    scale_x = usable_w / content_w
    scale_y = usable_h / content_h
    scale = min(scale_x, scale_y)

    if layout_kind not in {"tree", "radial"}:
        scale = min(1.0, scale)

    extra_x = 0.0
    extra_y = 0.0
    if layout_kind in {"tree", "radial"}:
        extra_x = max(0.0, (usable_w - (content_w * scale)) / 2)
        extra_y = max(0.0, (usable_h - (content_h * scale)) / 2)

    return ViewportTransform(
        scale=scale,
        translate_x=config.margin_x + extra_x - (scene.content_left * scale),
        translate_y=config.margin_y + extra_y - (scene.content_top * scale),
    )
