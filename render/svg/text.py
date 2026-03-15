"""Renderizado de texto SVG.

Este modulo concentra la logica tipografica de bajo nivel:
- justificacion por palabras
- dibujo de lineas sueltas
- dibujo de bloques alineados a izquierda o centrados

El resto del backend solo arma specs y delega aqui el detalle tipografico.
"""

import svgwrite

from layout.shared import measure_text_width
from render.models import SvgTextBlockSpec, SvgTextLineSpec


class SvgTextRenderer:
    """Renderer especializado en bloques y lineas de texto SVG."""

    def __init__(self, dwg: svgwrite.Drawing, root_group: svgwrite.container.Group):
        self._dwg = dwg
        self._root_group = root_group

    def draw_block(self, spec: SvgTextBlockSpec) -> None:
        for index, line in enumerate(spec.lines):
            self.draw_line(spec.line_spec(index, line))

    def draw_centered_block(self, spec: SvgTextBlockSpec) -> None:
        for index, line in enumerate(spec.lines):
            text_kwargs: dict[str, object] = {
                "insert": (spec.x, spec.start_y + (index * spec.line_step)),
                "text_anchor": "middle",
                "font_size": spec.style.font_size,
                "fill": spec.style.fill,
                "font_family": spec.style.font_family,
            }
            if spec.style.font_weight is not None:
                text_kwargs["font_weight"] = spec.style.font_weight

            self._root_group.add(self._dwg.text(line, **text_kwargs))

    def draw_line(self, spec: SvgTextLineSpec) -> None:
        if self._should_justify_line(spec):
            if self._draw_justified_line(spec):
                return

        self._root_group.add(self._dwg.text(spec.line, **self._text_kwargs(spec)))

    @staticmethod
    def _should_justify_line(spec: SvgTextLineSpec) -> bool:
        return (
            spec.style.text_align == "justify"
            and not spec.is_last_line
            and len(spec.line.split()) > 1
        )

    def _draw_justified_line(self, spec: SvgTextLineSpec) -> bool:
        words = spec.line.split()
        word_widths = [
            measure_text_width(word, spec.style.font_family, spec.style.font_size)
            for word in words
        ]
        words_total_width = sum(word_widths)
        available_gap_width = spec.max_width - words_total_width

        if available_gap_width <= 0:
            return False

        gap_width = available_gap_width / (len(words) - 1)
        current_x = spec.x
        base_kwargs = self._text_kwargs(spec)

        for word, word_width in zip(words, word_widths):
            word_kwargs = dict(base_kwargs)
            word_kwargs["insert"] = (current_x, spec.y)
            self._root_group.add(self._dwg.text(word, **word_kwargs))
            current_x += word_width + gap_width
        return True

    @staticmethod
    def _text_kwargs(spec: SvgTextLineSpec) -> dict[str, object]:
        text_kwargs: dict[str, object] = {
            "insert": (spec.x, spec.y),
            "font_size": spec.style.font_size,
            "fill": spec.style.fill,
            "font_family": spec.style.font_family,
        }
        if spec.style.font_weight is not None:
            text_kwargs["font_weight"] = spec.style.font_weight
        return text_kwargs
