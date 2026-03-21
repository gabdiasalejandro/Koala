"""Resolucion y persistencia de outputs del render.

Este archivo concentra la parte file-oriented del pipeline:
- combina override explicito y defaults externos
- construye el nombre final del archivo SVG
- persiste el SVG serializado solo cuando el caller lo pide

La politica de output ya no se resuelve desde metadata del documento.
"""

from pathlib import Path

from koala.core.models import ParsedDocument
from koala.layout.models import LayoutKind
class RenderOutputResolver:
    """Resuelve la ruta final del SVG a partir de inputs ya conocidos."""

    @classmethod
    def resolve_svg_path(
        cls,
        *,
        base_dir: Path,
        parsed: ParsedDocument,
        layout_kind: LayoutKind,
        output_svg_path: Path | None,
        output_dir_name: str | None,
        output_file_name: str | None,
        default_output_dir_name: str | None,
    ) -> Path:
        if output_svg_path is not None:
            return output_svg_path

        output_dir = cls.resolve_output_dir_path(
            base_dir=base_dir,
            parsed=parsed,
            output_dir_name=output_dir_name,
            default_output_dir_name=default_output_dir_name,
        )
        resolved_output_file_name = output_file_name or f"concept_map_{layout_kind}.svg"
        return output_dir / resolved_output_file_name

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
        return output_dir

    @staticmethod
    def _resolve_output_dir_name(
        *,
        parsed: ParsedDocument,
        output_dir_name: str | None,
        default_output_dir_name: str | None,
    ) -> str:
        del parsed
        resolved_output_dir_name = output_dir_name or default_output_dir_name
        if resolved_output_dir_name is None:
            raise ValueError(
                "No se resolvio output_dir. Pasa un output explicito, `output_dir`, o un default externo."
            )
        return resolved_output_dir_name


class RenderOutputWriter:
    """Persistencia opcional de SVGs serializados."""

    @staticmethod
    def write_svg(path: Path, svg: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
        return path
