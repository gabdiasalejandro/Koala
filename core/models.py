from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ConceptNode:
    number: str
    title: str
    relation_from_parent: str = ""
    kind: str = "default"
    attributes: Dict[str, str] = field(default_factory=dict)
    paragraphs: List[str] = field(default_factory=list)
    children: List["ConceptNode"] = field(default_factory=list)
    parent: Optional["ConceptNode"] = None

    def add_paragraph_line(self, text: str) -> None:
        text = text.strip()
        if text:
            self.paragraphs.append(text)

    def body_text(self) -> str:
        return " ".join(self.paragraphs).strip()


@dataclass
class ParseWarning:
    line_no: int
    message: str


@dataclass
class ParsedDocument:
    root_nodes: List[ConceptNode]
    node_index: Dict[str, ConceptNode]
    metadata: Dict[str, str]
    warnings: List[ParseWarning]
