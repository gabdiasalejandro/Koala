"""Calculo del viewport SVG.

Este archivo encapsula el ajuste final de la escena a pagina:
- mide el contenido real
- calcula escala util
- decide si un layout puede expandirse
- devuelve una sola transformacion reutilizable por el backend SVG
"""

from koala.layout.models import LayoutConfig, LayoutKind, LayoutScene
from koala.render.models import ViewportTransform


class ViewportFitter:
    """Servicio puro para ajustar una `LayoutScene` al tamaño de pagina."""

    EXPANDABLE_LAYOUTS = {"tree", "radial"}

    @classmethod
    def fit(
        cls,
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

        if layout_kind not in cls.EXPANDABLE_LAYOUTS:
            scale = min(1.0, scale)

        extra_x, extra_y = cls._resolve_extra_offsets(
            layout_kind,
            usable_w,
            usable_h,
            content_w,
            content_h,
            scale,
        )

        return ViewportTransform(
            scale=scale,
            translate_x=config.margin_x + extra_x - (scene.content_left * scale),
            translate_y=config.margin_y + extra_y - (scene.content_top * scale),
        )

    @classmethod
    def _resolve_extra_offsets(
        cls,
        layout_kind: LayoutKind,
        usable_w: float,
        usable_h: float,
        content_w: float,
        content_h: float,
        scale: float,
    ) -> tuple[float, float]:
        if layout_kind not in cls.EXPANDABLE_LAYOUTS:
            return 0.0, 0.0

        return (
            max(0.0, (usable_w - (content_w * scale)) / 2),
            max(0.0, (usable_h - (content_h * scale)) / 2),
        )
