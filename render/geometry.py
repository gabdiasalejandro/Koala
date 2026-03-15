"""Helpers geometricos usados por el renderizador.

Mantiene la logica vectorial fuera del codigo de dibujo para que sea
facil reutilizarla en futuros formatos de salida.
"""

from typing import Sequence, Tuple


def arrow_wing_points(
    start: Tuple[float, float],
    tip: Tuple[float, float],
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    dx = tip[0] - start[0]
    dy = tip[1] - start[1]
    length = (dx * dx + dy * dy) ** 0.5

    if length < 1e-6:
        return tip, tip

    ux = dx / length
    uy = dy / length

    arrow_len = 6.0
    arrow_w = 3.2

    wing_a = (
        tip[0] - (ux * arrow_len) - (uy * arrow_w),
        tip[1] - (uy * arrow_len) + (ux * arrow_w),
    )
    wing_b = (
        tip[0] - (ux * arrow_len) + (uy * arrow_w),
        tip[1] - (uy * arrow_len) - (ux * arrow_w),
    )

    return wing_a, wing_b


def synoptic_brace_path_data(points: Sequence[Tuple[float, float]]) -> str | None:
    """Construye un brace curvo para el layout `synoptic`.

    Espera la secuencia de puntos producida por `layout/synoptic_layout.py`.
    Si la geometria no coincide con ese contrato, retorna `None` para que el
    renderer pueda usar el fallback polilineal.
    """

    if len(points) < 10:
        return None

    parent_x, parent_y = points[0]
    elbow_x = points[1][0]
    brace_x, mid_y = points[3]
    hook_x = points[4][0]
    top_y = points[6][1]
    bottom_y = points[9][1]
    span_y = max(1.0, bottom_y - top_y)
    curve_y = max(2.0, min(14.0, span_y * 0.18))
    if span_y < curve_y * 2.4:
        curve_y = max(1.5, span_y / 3)

    return (
        f"M {parent_x:.2f} {parent_y:.2f} "
        f"C {elbow_x:.2f} {parent_y:.2f} {elbow_x:.2f} {mid_y:.2f} {brace_x:.2f} {mid_y:.2f} "
        f"M {hook_x:.2f} {top_y:.2f} "
        f"Q {brace_x:.2f} {top_y:.2f} {brace_x:.2f} {top_y + curve_y:.2f} "
        f"L {brace_x:.2f} {mid_y:.2f} "
        f"L {brace_x:.2f} {bottom_y - curve_y:.2f} "
        f"Q {brace_x:.2f} {bottom_y:.2f} {hook_x:.2f} {bottom_y:.2f}"
    )
