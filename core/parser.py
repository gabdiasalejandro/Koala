import re
from typing import List, Optional, Dict
from .models import ConceptNode, ParseWarning, ParsedDocument


KIND_PREFIX_RE = r'(?:(?P<kind>[A-Za-z_][\w-]*)\s*::\s*)?'
RELATION_PREFIX_RE = r'(?:(?P<relation>.+?)\s*(?:→|->)\s*)?'

NODE_LINE_RE = re.compile(
    rf'^\s*{KIND_PREFIX_RE}{RELATION_PREFIX_RE}(?P<number>\d+(?:\.\d+)*)\s+(?P<title>.+?)\s*$'
)


def get_parent_number(number: str) -> Optional[str]:
    parts = number.split(".")
    if len(parts) == 1:
        return None
    return ".".join(parts[:-1])


def resolve_parent_number(number: str, has_super_root: bool) -> Optional[str]:
    parent_number = get_parent_number(number)
    if parent_number is not None:
        return parent_number

    if has_super_root and number != "0":
        return "0"

    return None


def detect_missing_levels(number: str, node_index: Dict[str, ConceptNode], warnings: List[ParseWarning]):

    parts = number.split(".")

    for i in range(1, len(parts)):
        prefix = ".".join(parts[:i])
        if prefix not in node_index:
            warnings.append(
                ParseWarning(
                    0,
                    f"Falta nodo intermedio '{prefix}' antes de '{number}'"
                )
            )


def normalize_kind(raw_kind: Optional[str]) -> str:
    if not raw_kind:
        return "default"
    return raw_kind.strip().lower()


def parse_concept_text(text: str) -> ParsedDocument:

    lines = text.splitlines()

    node_index: Dict[str, ConceptNode] = {}
    warnings: List[ParseWarning] = []

    current_node: Optional[ConceptNode] = None

    # ----------------------------------------------------
    # FASE 1: crear nodos
    # ----------------------------------------------------

    for line_no, raw_line in enumerate(lines, start=1):

        line = raw_line.strip()

        if not line:
            continue

        match_node = NODE_LINE_RE.match(line)

        if match_node:
            kind = normalize_kind(match_node.group("kind"))
            relation = (match_node.group("relation") or "").strip()
            number = match_node.group("number").strip()
            title = match_node.group("title").strip()

            node = ConceptNode(
                number=number,
                title=title,
                relation_from_parent=relation,
                kind=kind,
            )

            if number in node_index:
                warnings.append(ParseWarning(
                    line_no,
                    f"Nodo duplicado '{number}'. Se sobrescribirá."
                ))

            node_index[number] = node
            current_node = node
            continue

        if current_node is None:
            warnings.append(ParseWarning(
                line_no,
                "Texto encontrado antes de cualquier nodo. Línea ignorada."
            ))
            continue

        current_node.add_paragraph_line(line)

    # ----------------------------------------------------
    # FASE 2: reconstruir jerarquía
    # ----------------------------------------------------

    root_nodes: List[ConceptNode] = []
    has_super_root = "0" in node_index

    for number, node in node_index.items():
        parent_number = resolve_parent_number(number, has_super_root)

        if parent_number is None:
            root_nodes.append(node)
            continue

        parent = node_index.get(parent_number)

        if parent is None:

            warnings.append(ParseWarning(
                0,
                f"No se encontró el padre '{parent_number}' para '{number}'. Se tratará como raíz."
            ))

            root_nodes.append(node)

        else:
            node.parent = parent
            parent.children.append(node)

        detect_missing_levels(number, node_index, warnings)

    # ----------------------------------------------------
    # Advertencias de estilo para layout
    # ----------------------------------------------------

    for number, node in node_index.items():

        title_words = len(node.title.split())
        text_words = len(node.body_text().split())

        if title_words > 10:
            warnings.append(ParseWarning(
                0,
                f"El nodo '{number}' tiene un título largo ({title_words} palabras)."
            ))

        if text_words > 100:
            warnings.append(ParseWarning(
                0,
                f"El nodo '{number}' tiene mucho texto ({text_words} palabras)."
            ))

        if len(node.children) > 7:
            warnings.append(ParseWarning(
                0,
                f"El nodo '{number}' tiene muchos hijos ({len(node.children)})."
            ))

    return ParsedDocument(
        root_nodes=root_nodes,
        node_index=node_index,
        warnings=warnings
    )
