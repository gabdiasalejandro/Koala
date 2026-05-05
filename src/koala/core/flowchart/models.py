"""Modelos de datos para documentos tipo `flowchart`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


FlowchartNodeKind = Literal["process", "decision", "start", "end", "note"]

ROLE_TO_KIND: Dict[str, str] = {
    "start": "main",
    "end": "main",
    "process": "default",
    "decision": "focus",
    "note": "note",
}


@dataclass
class FlowchartNode:
    """Nodo en un diagrama de flujo."""

    node_id: str
    label: str
    kind: FlowchartNodeKind = "process"
    body: str = ""

    @property
    def number(self) -> str:
        return self.node_id

    @property
    def title(self) -> str:
        return self.label

    @property
    def role(self) -> str:
        return self.kind


@dataclass
class FlowchartEdge:
    """Arista dirigida entre dos nodos del flowchart."""

    source_id: str
    target_id: str
    label: str = ""
    condition: str = ""


@dataclass
class ParseWarning:
    line_no: int
    message: str


@dataclass
class ParsedFlowchartDocument:
    """Documento flowchart ya parseado, listo para layout y render."""

    title: str
    nodes: Dict[str, FlowchartNode]
    edges: List[FlowchartEdge]
    ordered_node_ids: List[str]
    metadata: Dict[str, str] = field(default_factory=dict)
    warnings: List[ParseWarning] = field(default_factory=list)

    @property
    def root_nodes(self) -> List[FlowchartNode]:
        starts = [n for n in self.nodes.values() if n.kind == "start"]
        return starts or (list(self.nodes.values())[:1] if self.nodes else [])

    @property
    def node_index(self) -> Dict[str, FlowchartNode]:
        return self.nodes
