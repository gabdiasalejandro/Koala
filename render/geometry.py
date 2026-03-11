"""Helpers geometricos usados por el renderizador.

Mantiene la logica vectorial fuera del codigo de dibujo para que sea
facil reutilizarla en futuros formatos de salida.
"""

from typing import Tuple


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
