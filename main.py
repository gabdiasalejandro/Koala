import argparse
from pathlib import Path
from typing import Sequence

from core.io import load_input_text
from core.parser import parse_concept_text
from layout.models import LayoutKind
from render.defaults import available_theme_names, available_typography_names
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
        default="tree",
        help="Tipo de layout a usar (default: tree).",
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
        default=OUTPUT_DIR,
        help=f"Carpeta de salida (default: {OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--theme",
        choices=available_theme_names(),
        default="default",
        help="Tema de color a usar en el render SVG.",
    )
    parser.add_argument(
        "--typography",
        choices=available_typography_names(),
        default=None,
        help="Preset tipografico a usar; si se omite, usa el default del layout.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    base_dir = Path(__file__).parent
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    text = load_input_text(args.input)
    parsed = parse_concept_text(text)

    output_svg = output_dir / f"concept_map_{args.layout}.svg"

    render_svg(
        parsed,
        output_svg,
        layout_kind=args.layout,
        theme_name=args.theme,
        typography_name=args.typography,
    )

    print(f"SVG generado: {output_svg}")
    print(f"Layout usado: {args.layout}")
    print(f"Tema usado: {args.theme}")
    print(f"Tipografia usada: {args.typography or 'default del layout'}")


if __name__ == "__main__":
    main()
