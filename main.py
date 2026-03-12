import argparse
from pathlib import Path
from typing import Sequence

from core.io import load_input_text
from core.parser import parse_concept_text
from layout.models import LayoutKind
from render.defaults import available_page_size_names, available_theme_names, available_typography_names
from render.svg_render import render_svg

INPUT_FILE = "mocks/concepts.txt"     # puede ser .txt o .docx
OUTPUT_DIR = "output"
AVAILABLE_LAYOUTS: tuple[LayoutKind, ...] = ("tree", "synoptic", "synoptic_boxes", "radial")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compila el DSL a SVG, eligiendo layout, tema y tipografia.",
    )
    parser.add_argument(
        "-l",
        "--layout",
        choices=AVAILABLE_LAYOUTS,
        default=None,
        help="Tipo de layout a usar; si se omite, intenta usar metadata y luego el default.",
    )
    parser.add_argument(
        "-i",
        "--input",
        default=INPUT_FILE,
        help=f"Archivo de entrada .txt/.docx (default: {INPUT_FILE}).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help=f"Carpeta de salida; si se omite, intenta usar metadata y luego {OUTPUT_DIR}.",
    )
    parser.add_argument(
        "-t",
        "--theme",
        choices=available_theme_names(),
        default=None,
        help="Tema de color a usar; si se omite, intenta usar metadata y luego el default.",
    )
    parser.add_argument(
        "-ty",
        "--typography",
        choices=available_typography_names(),
        default=None,
        help="Preset tipografico a usar; si se omite, intenta usar metadata y luego el default del layout.",
    )
    parser.add_argument(
        "-s",
        "--size",
        choices=available_page_size_names(),
        default=None,
        help="Tamano de pagina a usar; si se omite, intenta usar metadata y luego el default configurado.",
    )
    return parser.parse_args(argv)


def _resolve_metadata_value(metadata: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if value:
            return value
    return None


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    base_dir = Path(__file__).parent

    text = load_input_text(args.input)
    parsed = parse_concept_text(text)

    resolved_layout = args.layout or _resolve_metadata_value(parsed.metadata, "layout") or "tree"
    resolved_theme = args.theme or _resolve_metadata_value(parsed.metadata, "theme") or "default"
    resolved_typography = args.typography or _resolve_metadata_value(parsed.metadata, "typography")
    resolved_size = args.size or _resolve_metadata_value(parsed.metadata, "size", "page-size")
    resolved_output_dir = args.output_dir or _resolve_metadata_value(parsed.metadata, "output-dir", "output_dir") or OUTPUT_DIR

    output_dir = base_dir / resolved_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    output_svg = output_dir / f"concept_map_{resolved_layout}.svg"

    render_svg(
        parsed,
        output_svg,
        layout_kind=resolved_layout,
        theme_name=resolved_theme,
        typography_name=resolved_typography,
        page_size_name=resolved_size,
    )

    print(f"SVG generado: {output_svg}")
    print(f"Layout usado: {resolved_layout}")
    print(f"Tema usado: {resolved_theme}")
    print(f"Tipografia usada: {resolved_typography or 'default del layout'}")
    print(f"Tamano de pagina usado: {resolved_size or 'default configurado'}")


if __name__ == "__main__":
    main()
