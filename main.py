import argparse
from pathlib import Path
from typing import Sequence

from core.io import load_input_text
from core.parser import parse_concept_text
from layout.models import LayoutKind
from render.models import SvgRenderRequest
from render.settings import available_page_size_names, available_typography_names
from render.svg_render import render_svg
from render.themes import available_theme_names

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


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    base_dir = Path(__file__).parent

    text = load_input_text(args.input)
    parsed = parse_concept_text(text)

    request = SvgRenderRequest(
        parsed=parsed,
        base_dir=base_dir,
        output_dir_name=args.output_dir,
        default_output_dir_name=OUTPUT_DIR,
        layout_kind=args.layout,
        theme_name=args.theme,
        typography_name=args.typography,
        page_size_name=args.size,
    )
    result = render_svg(request)

    print(f"SVG generado: {result.output_svg}")
    print(f"Layout usado: {result.context.settings.layout_kind}")
    print(f"Tema usado: {result.context.settings.theme_name}")
    print(f"Tipografia usada: {result.context.settings.typography_name}")
    print(f"Tamano de pagina usado: {result.context.settings.page_size_name}")


if __name__ == "__main__":
    main()
