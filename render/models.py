"""Modelos del subsistema de render.

Este modulo define:
- estilos y temas resueltos
- settings y contexto del pipeline
- resultado final del render
- specs compactos consumidos por el backend SVG

La meta es mantener el paso de datos explicito sin depender de parametros sueltos.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

from core.models import ConceptNode, ParsedDocument
from layout.models import LayoutBox, LayoutConfig, LayoutKind, LayoutScene, TypographyConfig


@dataclass(frozen=True)
class NodeStyle:
    """Colores finales de un nodo ya listos para dibujar."""

    fill: str
    stroke: str
    title: str
    body: str

    def apply(self, override: "NodeStyleOverride") -> "NodeStyle":
        """Retorna una copia con los campos presentes en `override`."""

        return NodeStyle(
            fill=override.fill or self.fill,
            stroke=override.stroke or self.stroke,
            title=override.title or self.title,
            body=override.body or self.body,
        )


@dataclass(frozen=True)
class NodeStyleOverride:
    """Override parcial sobre un `NodeStyle`.

    Se usa para dos casos:
    - kinds universales que se aplican a todos los temas
    - kinds o ajustes especificos de un tema concreto
    """

    fill: Optional[str] = None
    stroke: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None


@dataclass(frozen=True)
class ThemeDefinition:
    """Preset declarativo de un tema antes de expandir sus kinds.

    `kind_overrides` puede definir:
    - un kind universal re-coloreado por este tema
    - un kind exclusivo de este tema
    """

    default_node: NodeStyle
    kind_overrides: Mapping[str, NodeStyleOverride] = field(default_factory=dict)
    edge_color: str = "#8AA3B7"
    implicit_edge_color: str = "#64798A"
    relation_color: str = "#4E6472"
    number_pill_bg: str = "#E3EDF5"
    number_pill_text: str = "#4E6472"


@dataclass(frozen=True)
class ThemeConfig:
    """Tema ya resuelto con todos los kinds disponibles materializados."""

    default_node: NodeStyle
    node_by_kind: Mapping[str, NodeStyle] = field(default_factory=dict)
    edge_color: str = "#8AA3B7"
    implicit_edge_color: str = "#64798A"
    relation_color: str = "#4E6472"
    number_pill_bg: str = "#E3EDF5"
    number_pill_text: str = "#4E6472"

    def style_for(self, kind: str) -> NodeStyle:
        normalized = kind.strip().lower() if kind else "default"
        return self.node_by_kind.get(normalized, self.default_node)


@dataclass(frozen=True)
class RenderSettings:
    """Configuracion visual resuelta para una corrida de render."""

    layout_kind: LayoutKind
    theme_name: str
    typography_name: str
    page_size_name: str
    layout_config: LayoutConfig
    typography: TypographyConfig
    theme: ThemeConfig
    show_node_numbers: bool


@dataclass(frozen=True)
class ViewportTransform:
    """Transformacion final de layout-space a page-space SVG."""

    scale: float
    translate_x: float
    translate_y: float

    def svg_transform(self) -> str:
        return f"translate({self.translate_x},{self.translate_y}) scale({self.scale})"


@dataclass(frozen=True)
class RenderContext:
    """Paquete completo que consume el renderizador SVG."""

    parsed: ParsedDocument
    scene: LayoutScene
    settings: RenderSettings
    viewport: ViewportTransform


@dataclass(frozen=True)
class RenderResult:
    """Resultado observable de una corrida de render."""

    output_svg: Path
    context: RenderContext


@dataclass(frozen=True)
class SvgRenderRequest:
    """Parametros de entrada del pipeline SVG.

    Agrupa en un solo objeto:
    - el documento ya parseado
    - el directorio base donde se resolvera la salida
    - overrides opcionales del CLI para render y path
    """

    parsed: ParsedDocument
    base_dir: Path
    output_dir_name: Optional[str] = None
    default_output_dir_name: Optional[str] = None
    layout_kind: Optional[LayoutKind] = None
    theme_name: Optional[str] = None
    typography_name: Optional[str] = None
    page_size_name: Optional[str] = None


@dataclass(frozen=True)
class SvgTextStyle:
    """Estilo tipografico ya resuelto para un bloque o linea de texto SVG."""

    font_size: float
    font_family: str
    fill: str
    text_align: str
    font_weight: Optional[str] = None


@dataclass(frozen=True)
class SvgTextLineSpec:
    """Una sola linea de texto posicionada dentro del canvas."""

    line: str
    x: float
    y: float
    max_width: float
    is_last_line: bool
    style: SvgTextStyle


@dataclass(frozen=True)
class SvgTextBlockSpec:
    """Bloque multi-linea que se convierte en varias `SvgTextLineSpec`."""

    lines: list[str]
    x: float
    start_y: float
    line_step: float
    max_width: float
    style: SvgTextStyle

    def line_spec(self, index: int, line: str) -> SvgTextLineSpec:
        return SvgTextLineSpec(
            line=line,
            x=self.x,
            y=self.start_y + (index * self.line_step),
            max_width=self.max_width,
            is_last_line=index == len(self.lines) - 1,
            style=self.style,
        )


@dataclass(frozen=True)
class SvgNodeRenderSpec:
    """Datos listos para dibujar un nodo y su contenido."""

    box: LayoutBox
    node: ConceptNode
    node_style: NodeStyle
    border_width: float
    title_block: SvgTextBlockSpec
    body_block: Optional[SvgTextBlockSpec]
