"""Resolucion de rutas de salida del render.

Este archivo separa del backend SVG la politica de paths:
- combina override explicito, metadata y default externo
- crea el directorio destino si hace falta
- construye el nombre final del archivo SVG

El default del output no vive aqui; lo recibe desde quien invoque el render.
"""

from pathlib import Path

from core.models import ParsedDocument
from layout.models import LayoutKind
from render.context import MetadataValueResolver


class RenderOutputResolver:
    """Resuelve la ruta final del SVG a partir de inputs ya conocidos."""

    @classmethod
    def resolve_svg_path(
        cls,
        *,
        base_dir: Path,
        parsed: ParsedDocument,
        layout_kind: LayoutKind,
        output_dir_name: str | None,
        default_output_dir_name: str | None,
    ) -> Path:
        output_dir = cls.resolve_output_dir_path(
            base_dir=base_dir,
            parsed=parsed,
            output_dir_name=output_dir_name,
            default_output_dir_name=default_output_dir_name,
        )
        return output_dir / f"concept_map_{layout_kind}.svg"

    @classmethod
    def resolve_output_dir_path(
        cls,
        *,
        base_dir: Path,
        parsed: ParsedDocument,
        output_dir_name: str | None,
        default_output_dir_name: str | None,
    ) -> Path:
        resolved_output_dir_name = cls._resolve_output_dir_name(
            parsed=parsed,
            output_dir_name=output_dir_name,
            default_output_dir_name=default_output_dir_name,
        )
        output_dir = base_dir / resolved_output_dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @staticmethod
    def _resolve_output_dir_name(
        *,
        parsed: ParsedDocument,
        output_dir_name: str | None,
        default_output_dir_name: str | None,
    ) -> str:
        resolved_output_dir_name = (
            output_dir_name
            or MetadataValueResolver.resolve_value(parsed.metadata, "output-dir", "output_dir")
            or default_output_dir_name
        )
        if resolved_output_dir_name is None:
            raise ValueError(
                "No se resolvio output_dir. Pasa un output explicito, metadata `@output-dir`, o un default externo."
            )
        return resolved_output_dir_name
