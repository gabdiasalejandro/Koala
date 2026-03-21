"""Renderizado SVG de aristas y labels de relacion.

Este modulo dibuja conectores sobre una escena ya resuelta:
- lineas o polilineas
- puntas de flecha cuando corresponde
- labels de relacion en layouts que las muestran
"""

import math

import svgwrite

from koala.layout.shared import wrap_text_lines
from koala.render.geometry import arrow_wing_points, synoptic_brace_path_data
from koala.render.models import RenderContext, SvgTextBlockSpec, SvgTextStyle
from koala.render.svg.text import SvgTextRenderer


class SvgEdgeRenderer:
    """Renderer de aristas a partir del `RenderContext` actual."""

    def __init__(
        self,
        dwg: svgwrite.Drawing,
        root_group: svgwrite.container.Group,
        context: RenderContext,
        text_renderer: SvgTextRenderer,
    ):
        self._dwg = dwg
        self._root_group = root_group
        self._context = context
        self._text_renderer = text_renderer

    def render(
        self,
        *,
        include_lines: bool = True,
        include_label_backgrounds: bool = True,
        include_label_text: bool = True,
    ) -> None:
        typography = self._context.settings.typography
        theme = self._context.settings.theme
        use_brackets_only = self._context.settings.layout_kind == "synoptic"

        for edge in self._context.scene.edges:
            if len(edge.points) < 2:
                continue

            has_explicit_relation = bool(edge.relation_label)
            stroke_color = theme.edge_color if has_explicit_relation else theme.implicit_edge_color
            stroke_width = 1.2 if has_explicit_relation else 1.75

            if include_lines and use_brackets_only and self._draw_synoptic_brace(edge.points, stroke_color):
                continue

            if include_lines:
                if len(edge.points) == 2:
                    self._draw_segmented_line(
                        edge.points[0],
                        edge.points[1],
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        gap_bounds=(
                            edge.label_bounds
                            if self._context.settings.layout_kind == "radial" and edge.relation_label
                            else None
                        ),
                    )
                else:
                    self._root_group.add(
                        self._dwg.polyline(
                            points=edge.points,
                            fill="none",
                            stroke=stroke_color,
                            stroke_width=stroke_width,
                        )
                    )

                if not use_brackets_only:
                    self._draw_arrow(edge.points[-2], edge.points[-1], theme.edge_color)

            if edge.relation_label and not use_brackets_only:
                is_radial = self._context.settings.layout_kind == "radial"
                background_fill = None
                background_opacity = 1.0
                background_padding_x = 0.0
                background_padding_y = 0.0
                background_corner_radius = 0.0

                if is_radial:
                    background_fill = None

                label_spec = SvgTextBlockSpec(
                    lines=wrap_text_lines(
                        edge.relation_label,
                        typography.body_font,
                        typography.relation_size,
                        edge.label_max_width,
                    ),
                    x=edge.label_pos[0],
                    start_y=edge.label_pos[1],
                    line_step=typography.relation_size + 1,
                    max_width=edge.label_max_width,
                    style=SvgTextStyle(
                        font_size=typography.relation_size,
                        font_family=typography.body_font,
                        fill=theme.relation_color,
                        text_align="left",
                    ),
                    rotation_degrees=edge.label_angle,
                    rotation_center=(
                        None
                        if edge.label_bounds is None
                        else (
                            (edge.label_bounds[0] + edge.label_bounds[2]) / 2,
                            (edge.label_bounds[1] + edge.label_bounds[3]) / 2,
                        )
                    ),
                    background_fill=background_fill,
                    background_opacity=background_opacity,
                    background_padding_x=background_padding_x,
                    background_padding_y=background_padding_y,
                    background_corner_radius=background_corner_radius,
                )
                if include_label_backgrounds and background_fill:
                    background_only_spec = SvgTextBlockSpec(
                        lines=label_spec.lines,
                        x=label_spec.x,
                        start_y=label_spec.start_y,
                        line_step=label_spec.line_step,
                        max_width=label_spec.max_width,
                        style=SvgTextStyle(
                            font_size=label_spec.style.font_size,
                            font_family=label_spec.style.font_family,
                            fill="none",
                            text_align=label_spec.style.text_align,
                            font_weight=label_spec.style.font_weight,
                        ),
                        rotation_degrees=label_spec.rotation_degrees,
                        rotation_center=label_spec.rotation_center,
                        background_fill=label_spec.background_fill,
                        background_opacity=label_spec.background_opacity,
                        background_padding_x=label_spec.background_padding_x,
                        background_padding_y=label_spec.background_padding_y,
                        background_corner_radius=label_spec.background_corner_radius,
                    )
                    self._text_renderer.draw_centered_block(background_only_spec)
                if include_label_text:
                    text_only_spec = SvgTextBlockSpec(
                        lines=label_spec.lines,
                        x=label_spec.x,
                        start_y=label_spec.start_y,
                        line_step=label_spec.line_step,
                        max_width=label_spec.max_width,
                        style=label_spec.style,
                        rotation_degrees=label_spec.rotation_degrees,
                        rotation_center=label_spec.rotation_center,
                    )
                    self._text_renderer.draw_centered_block(text_only_spec)

    def _draw_synoptic_brace(self, points, stroke_color: str) -> bool:
        path_data = synoptic_brace_path_data(points)
        if path_data is None:
            return False

        self._root_group.add(
            self._dwg.path(
                d=path_data,
                fill="none",
                stroke=stroke_color,
                stroke_width=2.1,
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=0.96,
            )
        )
        return True

    def _draw_arrow(self, start, tip, stroke_color: str) -> None:
        wing_a, wing_b = arrow_wing_points(start, tip)
        self._root_group.add(self._dwg.line(tip, wing_a, stroke=stroke_color, stroke_width=1.0))
        self._root_group.add(self._dwg.line(tip, wing_b, stroke=stroke_color, stroke_width=1.0))

    def _draw_segmented_line(
        self,
        start,
        end,
        *,
        stroke_color: str,
        stroke_width: float,
        gap_bounds,
    ) -> None:
        if gap_bounds is None:
            self._root_group.add(
                self._dwg.line(
                    start,
                    end,
                    stroke=stroke_color,
                    stroke_width=stroke_width,
                )
            )
            return

        clipped_interval = self._line_gap_interval(start, end, gap_bounds, padding=3.0)
        if clipped_interval is None:
            self._root_group.add(
                self._dwg.line(
                    start,
                    end,
                    stroke=stroke_color,
                    stroke_width=stroke_width,
                )
            )
            return

        t_start, t_end = clipped_interval
        if t_start > 1e-4:
            seg_end = self._point_on_segment(start, end, t_start)
            self._root_group.add(
                self._dwg.line(
                    start,
                    seg_end,
                    stroke=stroke_color,
                    stroke_width=stroke_width,
                )
            )

        if t_end < 1.0 - 1e-4:
            seg_start = self._point_on_segment(start, end, t_end)
            self._root_group.add(
                self._dwg.line(
                    seg_start,
                    end,
                    stroke=stroke_color,
                    stroke_width=stroke_width,
                )
            )

    @staticmethod
    def _point_on_segment(start, end, t: float):
        return (
            start[0] + ((end[0] - start[0]) * t),
            start[1] + ((end[1] - start[1]) * t),
        )

    @staticmethod
    def _line_gap_interval(start, end, bounds, padding: float):
        left, top, right, bottom = bounds
        left -= padding
        top -= padding
        right += padding
        bottom += padding

        dx = end[0] - start[0]
        dy = end[1] - start[1]
        t0 = 0.0
        t1 = 1.0

        for p, q in (
            (-dx, start[0] - left),
            (dx, right - start[0]),
            (-dy, start[1] - top),
            (dy, bottom - start[1]),
        ):
            if abs(p) < 1e-8:
                if q < 0:
                    return None
                continue

            ratio = q / p
            if p < 0:
                t0 = max(t0, ratio)
            else:
                t1 = min(t1, ratio)

            if t0 > t1:
                return None

        if math.isclose(t0, 0.0) and math.isclose(t1, 1.0):
            return 0.0, 1.0
        if t1 <= 0.0 or t0 >= 1.0:
            return None

        return max(0.0, t0), min(1.0, t1)
