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

from koala.core.shared.errors import InvalidRenderConfigError
from koala.render.shared.models import NodeStyle, NodeStyleOverride, ThemeConfig, ThemeDefinition


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
                fill="#FBF1E8",
                stroke="#A36A52",
                title="#4A2418",
                body="#6B3D2E",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#F4C9A8",
                    stroke="#C4502A",
                    title="#5C1F0E",
                    body="#7A3520",
                ),
                "hl": NodeStyleOverride(
                    fill="#F8DCC2",
                    stroke="#D88550",
                    title="#5A2A14",
                    body="#74442C",
                ),
                "focus": NodeStyleOverride(
                    fill="#EBB48E",
                    stroke="#9C3A1A",
                    title="#3F1408",
                    body="#5C2410",
                ),
            },
            edge_color="#B5876C",
            implicit_edge_color="#8A5E48",
            relation_color="#A8421C",
            number_pill_bg="#F2DDC8",
            number_pill_text="#6B3220",
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
                fill="#FFF4F2",
                stroke="#E8607A",
                title="#5C0A1F",
                body="#7A1A30",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#FFB8C0",
                    stroke="#E62848",
                    title="#5A0014",
                    body="#7A0A24",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFD4A8",
                    stroke="#FF7A3A",
                    title="#6B2400",
                    body="#8A3A0A",
                ),
                "focus": NodeStyleOverride(
                    fill="#D8F0A8",
                    stroke="#5AB82A",
                    title="#1F4A00",
                    body="#2E5A0A",
                ),
            },
            edge_color="#F58AA0",
            implicit_edge_color="#C45878",
            relation_color="#FF7A3A",
            number_pill_bg="#FFD8DE",
            number_pill_text="#7A0A24",
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
                fill="#F6F0FA",
                stroke="#7A5E9C",
                title="#2C1654",
                body="#4A3070",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#D4B8E8",
                    stroke="#5E2C9C",
                    title="#1F0850",
                    body="#3A1670",
                ),
                "hl": NodeStyleOverride(
                    fill="#E2C8F0",
                    stroke="#9558C0",
                    title="#3A1670",
                    body="#542890",
                ),
                "focus": NodeStyleOverride(
                    fill="#C49AE0",
                    stroke="#4A1A88",
                    title="#180440",
                    body="#2E0A60",
                ),
            },
            edge_color="#9C7AB8",
            implicit_edge_color="#705890",
            relation_color="#6A2AA0",
            number_pill_bg="#E8D8F2",
            number_pill_text="#3A1670",
        ),
        "academic": ThemeDefinition(
            default_node=NodeStyle(
                fill="#F4F1EA",
                stroke="#5A6F8A",
                title="#1A2638",
                body="#2C2C2C",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#D8E0EC",
                    stroke="#1E3A5F",
                    title="#0C1F38",
                    body="#1E3A5F",
                ),
                "hl": NodeStyleOverride(
                    fill="#E4EAF2",
                    stroke="#3A5878",
                    title="#162C48",
                    body="#2C2C2C",
                ),
                "focus": NodeStyleOverride(
                    fill="#C2D0E2",
                    stroke="#0C2848",
                    title="#06162C",
                    body="#0C1F38",
                ),
            },
            edge_color="#5A6F8A",
            implicit_edge_color="#3A5878",
            relation_color="#1E3A5F",
            number_pill_bg="#E4EAF2",
            number_pill_text="#1E3A5F",
        ),
        "black": ThemeDefinition(
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
        "pastel": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FBF4F8",
                stroke="#C8A8C0",
                title="#4A3848",
                body="#5C4A58",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#F2D4E2",
                    stroke="#B07898",
                    title="#4A1E38",
                    body="#5C2E48",
                ),
                "hl": NodeStyleOverride(
                    fill="#F6DEEA",
                    stroke="#C898B0",
                    title="#5A3850",
                    body="#6B485E",
                ),
                "focus": NodeStyleOverride(
                    fill="#E8B8D0",
                    stroke="#9C5878",
                    title="#380A24",
                    body="#4C1A38",
                ),
            },
            edge_color="#C8A8C0",
            implicit_edge_color="#9C7898",
            relation_color="#A85878",
            number_pill_bg="#F4DCE8",
            number_pill_text="#5A2E48",
        ),
        "neon": ThemeDefinition(
            default_node=NodeStyle(
                fill="#0E1118",
                stroke="#3FAFD8",
                title="#E8F4FF",
                body="#B8D8E8",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#0A1F2E",
                    stroke="#00D9FF",
                    title="#5CEFFF",
                    body="#A8E8F8",
                ),
                "hl": NodeStyleOverride(
                    fill="#0E1A28",
                    stroke="#3FAFD8",
                    title="#88D4F0",
                    body="#A8C8D8",
                ),
                "focus": NodeStyleOverride(
                    fill="#0A1A22",
                    stroke="#00FFD0",
                    title="#5CFFE0",
                    body="#A8F0E0",
                ),
            },
            edge_color="#3FAFD8",
            implicit_edge_color="#2A7898",
            relation_color="#00FFD0",
            number_pill_bg="#0A1F2E",
            number_pill_text="#5CEFFF",
        ),
        "sepia": ThemeDefinition(
            default_node=NodeStyle(
                fill="#F2E4CC",
                stroke="#8B6F47",
                title="#3E2818",
                body="#5C4030",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#D8B888",
                    stroke="#5C3818",
                    title="#2A1408",
                    body="#3E2818",
                ),
                "hl": NodeStyleOverride(
                    fill="#E4C49C",
                    stroke="#8A5828",
                    title="#3E1F0A",
                    body="#5C3418",
                ),
                "focus": NodeStyleOverride(
                    fill="#C4A06E",
                    stroke="#3E2008",
                    title="#1A0A02",
                    body="#2A1408",
                ),
            },
            edge_color="#8B6F47",
            implicit_edge_color="#5C4030",
            relation_color="#7A3818",
            number_pill_bg="#E4C49C",
            number_pill_text="#3E1F0A",
        ),
        "colorblind": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FFFFFF",
                stroke="#0173B2",
                title="#000000",
                body="#1A1A1A",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#D6E8F4",
                    stroke="#0173B2",
                    title="#003A5C",
                    body="#000000",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFE4B8",
                    stroke="#DE8F05",
                    title="#5A3800",
                    body="#000000",
                ),
                "focus": NodeStyleOverride(
                    fill="#D8E8C8",
                    stroke="#1F8538",
                    title="#0E3A18",
                    body="#000000",
                ),
            },
            edge_color="#0173B2",
            implicit_edge_color="#56B4E9",
            relation_color="#CC79A7",
            number_pill_bg="#D6E8F4",
            number_pill_text="#003A5C",
        ),
        "minimal": ThemeDefinition(
            default_node=NodeStyle(
                fill="#FAFAFA",
                stroke="#D1D5DB",
                title="#111827",
                body="#4B5563",
            ),
            kind_overrides={
                "main": NodeStyleOverride(
                    fill="#F3F4F6",
                    stroke="#4B5563",
                    title="#0B1220",
                    body="#374151",
                ),
                "hl": NodeStyleOverride(
                    fill="#FFFFFF",
                    stroke="#9CA3AF",
                    title="#1F2937",
                    body="#4B5563",
                ),
                "focus": NodeStyleOverride(
                    fill="#1F2937",
                    stroke="#0B1220",
                    title="#FFFFFF",
                    body="#E5E7EB",
                ),
            },
            edge_color="#9CA3AF",
            implicit_edge_color="#D1D5DB",
            relation_color="#1F2937",
            number_pill_bg="#E5E7EB",
            number_pill_text="#1F2937",
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
            raise InvalidRenderConfigError(
                key="theme",
                value=resolved_name,
                expected=f"uno de: {available}",
            )
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
