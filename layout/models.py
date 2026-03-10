from dataclasses import dataclass, field
from typing import Dict, List, Literal, Mapping

from core.models import ConceptNode


LayoutKind = Literal["tree", "synoptic", "radial"]


@dataclass(frozen=True)
class TypographyConfig:
    title_font: str = "Helvetica-Bold"
    body_font: str = "Helvetica"
    title_size_base: float = 20.0
    title_size_min: float = 18.0
    body_size: float = 12.0
    relation_size: float = 11.0
    body_leading: float = 15.0
    max_title_lines: int = 3
    title_line_extra: float = 1.8


@dataclass(frozen=True)
class LayoutConfig:
    page_width: float
    page_height: float
    margin_x: float
    margin_y: float
    node_width_base: float
    min_node_width: float
    root_width_factor: float
    depth_width_reduction: float
    max_depth_reduction: float
    h_gap_base: float
    v_gap_base: float
    inner_pad_x: float
    inner_pad_y: float
    corner_radius: float
    title_body_gap: float


@dataclass(frozen=True)
class NodeStyle:
    fill: str
    stroke: str
    title: str
    body: str


@dataclass(frozen=True)
class ThemeConfig:
    default_node: NodeStyle
    node_by_kind: Mapping[str, NodeStyle] = field(default_factory=dict)
    edge_color: str = "#8AA3B7"
    relation_color: str = "#4E6472"
    number_pill_bg: str = "#E3EDF5"

    def style_for(self, kind: str) -> NodeStyle:
        normalized = kind.strip().lower() if kind else "default"
        return self.node_by_kind.get(normalized, self.default_node)


@dataclass
class LayoutBox:
    node: ConceptNode
    depth: int
    width: float
    height: float
    subtree_width: float
    x: float
    y: float
    title_lines: List[str]
    title_font_size: float
    title_height: float
    body_lines: List[str]


@dataclass
class LayoutScene:
    boxes: Dict[str, LayoutBox]
    content_bottom: float
    content_right: float
