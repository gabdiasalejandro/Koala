"""Parser para diagramas de flujo tipo `flowchart`.

Sintaxis koala-flavored similar a mermaid:

    flowchart:: Titulo del diagrama
    @theme ocean

    start:: inicio
    step:: A :: Primer paso
    decision:: B :: ¿Condicion?
    step:: C :: Rama si
    step:: D :: Rama no
    end:: fin

    inicio -> A
    B -> C :: si
    B -> D :: no
    C -> fin
    D -> fin

Los nodos se declaran con `<kind>:: <id> :: <label>` o `<kind>:: <id>`.
Las aristas se declaran con `<source> -> <target>` o `<source> -> <target> :: <etiqueta>`.
"""

from __future__ import annotations

import re
from typing import Dict, List

from koala.core.flowchart.models import (
    FlowchartEdge,
    FlowchartNode,
    FlowchartNodeKind,
    ParseWarning,
    ParsedFlowchartDocument,
)


METADATA_RE = re.compile(r"^\s*@(?P<key>[A-Za-z][\w-]*)\s*(?::|\s)\s*(?P<value>.+?)\s*$")
FLOWCHART_RE = re.compile(r"^\s*flowchart::\s*(?P<title>.+?)\s*$", re.IGNORECASE)
NODE_RE = re.compile(
    r"^\s*(?P<kind>start|end|step|process|decision|note)::\s*(?P<id>[^\s:][^:]*?)\s*(?:::\s*(?P<label>.+?))?\s*$",
    re.IGNORECASE,
)
EDGE_RE = re.compile(
    r"^\s*(?P<source>[^\s\-][^\-]*?)\s*->\s*(?P<target>[^\s:][^:]*?)\s*(?:::\s*(?P<label>.+?))?\s*$"
)


_KIND_ALIASES: Dict[str, FlowchartNodeKind] = {
    "start": "start",
    "end": "end",
    "step": "process",
    "process": "process",
    "decision": "decision",
    "note": "note",
}


def parse_flowchart_text(text: str) -> ParsedFlowchartDocument:
    metadata: Dict[str, str] = {}
    warnings: List[ParseWarning] = []
    title = ""
    nodes: Dict[str, FlowchartNode] = {}
    edges: List[FlowchartEdge] = []
    ordered_node_ids: List[str] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        meta_m = METADATA_RE.match(line)
        if meta_m:
            key = meta_m.group("key").strip().lower()
            if key in metadata:
                warnings.append(ParseWarning(line_no, f"Metadata duplicada '{key}'. Se sobrescribira."))
            metadata[key] = meta_m.group("value").strip()
            continue

        fc_m = FLOWCHART_RE.match(line)
        if fc_m:
            title = fc_m.group("title").strip()
            continue

        node_m = NODE_RE.match(line)
        if node_m:
            raw_kind = node_m.group("kind").strip().lower()
            kind: FlowchartNodeKind = _KIND_ALIASES.get(raw_kind, "process")  # type: ignore[assignment]
            node_id = node_m.group("id").strip()
            raw_label = node_m.group("label")
            label = raw_label.strip() if raw_label else node_id
            if node_id in nodes:
                warnings.append(ParseWarning(line_no, f"Nodo '{node_id}' duplicado. Se sobrescribira."))
            nodes[node_id] = FlowchartNode(node_id=node_id, label=label, kind=kind)
            if node_id not in ordered_node_ids:
                ordered_node_ids.append(node_id)
            continue

        edge_m = EDGE_RE.match(line)
        if edge_m:
            source = edge_m.group("source").strip()
            target = edge_m.group("target").strip()
            raw_label = edge_m.group("label")
            edge_label = raw_label.strip() if raw_label else ""
            edges.append(FlowchartEdge(source_id=source, target_id=target, label=edge_label))
            continue

        warnings.append(ParseWarning(line_no, f"Linea no reconocida en flowchart: '{line[:60]}'."))

    if not title:
        title = "Diagrama de flujo"

    _validate_edges(edges, nodes, warnings)

    return ParsedFlowchartDocument(
        title=title,
        nodes=nodes,
        edges=edges,
        ordered_node_ids=ordered_node_ids,
        metadata=metadata,
        warnings=warnings,
    )


def _validate_edges(
    edges: List[FlowchartEdge],
    nodes: Dict[str, FlowchartNode],
    warnings: List[ParseWarning],
) -> None:
    for edge in edges:
        if edge.source_id not in nodes:
            warnings.append(ParseWarning(0, f"Arista desde nodo desconocido '{edge.source_id}'."))
        if edge.target_id not in nodes:
            warnings.append(ParseWarning(0, f"Arista hacia nodo desconocido '{edge.target_id}'."))
