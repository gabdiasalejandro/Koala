"""Catalogo de themes y kinds semanticos del render.

Este archivo agrupa en un solo lugar:
- la lista actual de `kind::` universales
- las definiciones especificas de cada theme
- la composicion final de un `ThemeConfig`

La regla es simple:
- los kinds universales se aplican sobre el `default_node` del theme
- cada theme aporta sus kinds propios, hoy `main`, `hl` y `focus`
"""

from typing import Dict

from koala.render.models import NodeStyle, NodeStyleOverride, ThemeConfig, ThemeDefinition


DEFAULT_THEME_NAME = "default"


class ThemeCatalog:
    """Registro declarativo de themes disponibles."""

    UNIVERSAL_KIND_STYLES: Dict[str, NodeStyleOverride] = {
        "note": NodeStyleOverride(
            fill="#EDF5FF",
            stroke="#7CA6D8",
            title="#27496D",
            body="#45627C",
        ),
        "warn": NodeStyleOverride(
            fill="#FFF1E5",
            stroke="#E08A4E",
            title="#8A4315",
            body="#915937",
        ),
        "soft": NodeStyleOverride(
            fill="#F3F5F7",
            stroke="#9AA8B5",
            title="#4A5562",
            body="#6A7480",
        ),
    }

    DEFINITIONS: Dict[str, ThemeDefinition] = {
        "default": ThemeDefinition(
            default_node=NodeStyle(
                fill="#F8FAFC",
                stroke="#4A647D",
                title="#1A3044",
                body="#314252",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#FFE7CC",
                    stroke="#FF8A00",
                    title="#7A3E00",
                    body="#8A5620",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFF4D8",
                    stroke="#D39A2C",
                    title="#6B4D00",
                    body="#624E21",
                ),
                "focus": NodeStyleOverride(
                    fill="#E8F2FF",
                    stroke="#4A88D3",
                    title="#123E72",
                    body="#335A86",
                ),
            },
            edge_color="#93A7B8",
            implicit_edge_color="#5C7286",
            relation_color="#A14F1A",
            number_pill_bg="#E6EDF3",
            number_pill_text="#5A6E7D",
        ),
        "terracotta": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FFF7F1",
                stroke="#8F5D4A",
                title="#48281E",
                body="#66483F",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#FFD8C8",
                    stroke="#D74A1D",
                    title="#7A2411",
                    body="#8A4631",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFE0D1",
                    stroke="#C35A34",
                    title="#6A2817",
                    body="#7A4332",
                ),
                "focus": NodeStyleOverride(
                    fill="#FCE4DA",
                    stroke="#B56C4F",
                    title="#79311F",
                    body="#8A5444",
                ),
            },
            edge_color="#B48B7A",
            implicit_edge_color="#7A6258",
            relation_color="#8C2F46",
            number_pill_bg="#F4E0D6",
            number_pill_text="#8B6557",
        ),
        "jungle": ThemeDefinition(
            default_node=NodeStyle(
                fill="#F2FBF8",
                stroke="#4C8C78",
                title="#184A44",
                body="#2D5F68",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#D8F7BF",
                    stroke="#4EA72E",
                    title="#1F5E16",
                    body="#3D6D2E",
                ),
                "hl": NodeStyleOverride(
                    fill="#DDF6F0",
                    stroke="#2F9B8F",
                    title="#0F5A63",
                    body="#2C6670",
                ),
                "focus": NodeStyleOverride(
                    fill="#E3F7E8",
                    stroke="#5D9D5B",
                    title="#1C5A36",
                    body="#3D6D4A",
                ),
            },
            edge_color="#86B8AD",
            implicit_edge_color="#4E7F86",
            relation_color="#146B8C",
            number_pill_bg="#DDEFEA",
            number_pill_text="#5A8E95",
        ),
        "frutal": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FFF8F2",
                stroke="#C96C4A",
                title="#5E2416",
                body="#7A4A3A",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#FFD66B",
                    stroke="#E28A12",
                    title="#6F3B00",
                    body="#8B5A16",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFC2D1",
                    stroke="#D94B76",
                    title="#7D183A",
                    body="#8C4160",
                ),
                "focus": NodeStyleOverride(
                    fill="#DFF4C8",
                    stroke="#76A83B",
                    title="#355A12",
                    body="#55713B",
                ),
            },
            edge_color="#D39A7E",
            implicit_edge_color="#8A5E52",
            relation_color="#B53A3A",
            number_pill_bg="#F9E3D6",
            number_pill_text="#9B5B47",
        ),
        "ocean": ThemeDefinition(
            default_node=NodeStyle(
                fill="#F0F8FF",
                stroke="#2E86AB",
                title="#0A3D5C",
                body="#1A5274",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#C8EEFF",
                    stroke="#1A6E9A",
                    title="#083050",
                    body="#0F4468",
                ),
                "hl": NodeStyleOverride(
                    fill="#D4F4F0",
                    stroke="#1A9E8F",
                    title="#0C4C48",
                    body="#136060",
                ),
                "focus": NodeStyleOverride(
                    fill="#DCF0FF",
                    stroke="#2878C0",
                    title="#0A2A5C",
                    body="#123E78",
                ),
            },
            edge_color="#5BA8C8",
            implicit_edge_color="#3A7A98",
            relation_color="#0A5A8C",
            number_pill_bg="#D8EEF8",
            number_pill_text="#2A6888",
        ),
        "dusk": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FDF6FF",
                stroke="#8B6BAE",
                title="#3A1F6E",
                body="#5A3A8A",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#F0D8FF",
                    stroke="#7040B0",
                    title="#2E1060",
                    body="#4A2878",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFE8F4",
                    stroke="#C05898",
                    title="#7A1850",
                    body="#903068",
                ),
                "focus": NodeStyleOverride(
                    fill="#FFE8D8",
                    stroke="#C07040",
                    title="#7A3810",
                    body="#985030",
                ),
            },
            edge_color="#A888C8",
            implicit_edge_color="#786098",
            relation_color="#7840A8",
            number_pill_bg="#EDD8F8",
            number_pill_text="#7848A8",
        ),
        "academic": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FCFCFA",
                stroke="#6F6F6F",
                title="#111111",
                body="#111111",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#F0F0EC",
                    stroke="#3F3F3F",
                    title="#000000",
                    body="#111111",
                ),
                "hl": NodeStyleOverride(
                    fill="#F6F6F3",
                    stroke="#585858",
                    title="#000000",
                    body="#111111",
                ),
                "focus": NodeStyleOverride(
                    fill="#F2F2EE",
                    stroke="#4C4C4C",
                    title="#000000",
                    body="#111111",
                ),
            },
            edge_color="#7A7A7A",
            implicit_edge_color="#555555",
            relation_color="#222222",
            number_pill_bg="#F1F1ED",
            number_pill_text="#111111",
        ),
    }

    @classmethod
    def available_names(cls) -> tuple[str, ...]:
        return tuple(sorted(cls.DEFINITIONS.keys()))

    @classmethod
    def resolve(cls, theme_name: str | None) -> ThemeConfig:
        resolved_name = theme_name or DEFAULT_THEME_NAME
        definition = cls.DEFINITIONS.get(resolved_name)
        if definition is None:
            available = ", ".join(sorted(cls.DEFINITIONS.keys()))
            raise ValueError(f"theme '{resolved_name}' no existe. Disponibles: {available}.")
        return cls._build_config(definition)

    @classmethod
    def _build_config(cls, definition: ThemeDefinition) -> ThemeConfig:
        node_by_kind = {
            cls._normalize_kind(kind): definition.default_node.apply(override)
            for kind, override in cls.UNIVERSAL_KIND_STYLES.items()
        }

        for kind, override in definition.kind_overrides.items():
            normalized_kind = cls._normalize_kind(kind)
            base_style = node_by_kind.get(normalized_kind, definition.default_node)
            node_by_kind[normalized_kind] = base_style.apply(override)

        return ThemeConfig(
            default_node=definition.default_node,
            node_by_kind=node_by_kind,
            edge_color=definition.edge_color,
            implicit_edge_color=definition.implicit_edge_color,
            relation_color=definition.relation_color,
            number_pill_bg=definition.number_pill_bg,
            number_pill_text=definition.number_pill_text,
        )

    @staticmethod
    def _normalize_kind(kind: str) -> str:
        return kind.strip().lower()


def available_theme_names() -> tuple[str, ...]:
    return ThemeCatalog.available_names()
