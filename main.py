import argparse
from pathlib import Path
from typing import Sequence

from core.io import load_input_text
from core.parser import parse_concept_text
from layout.models import LayoutKind
from render.pdf_render import render_pdf
from render.svg_render import render_svg

INPUT_FILE = "mocks/concepts.txt"     # puede ser .txt o .docx
OUTPUT_DIR = "output"
AVAILABLE_LAYOUTS: tuple[LayoutKind, ...] = ("tree", "synoptic", "radial")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compila el DSL a SVG y PDF, eligiendo el tipo de layout.",
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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    base_dir = Path(__file__).parent
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    text = load_input_text(args.input)
    parsed = parse_concept_text(text)

    output_svg = output_dir / f"concept_map_{args.layout}.svg"
    output_pdf = output_dir / f"concept_map_{args.layout}.pdf"

    render_svg(parsed, output_svg, layout_kind=args.layout)
    render_pdf(parsed, output_pdf, layout_kind=args.layout)

    print(f"SVG generado: {output_svg}")
    print(f"PDF generado: {output_pdf}")
    print(f"Layout usado: {args.layout}")


if __name__ == "__main__":
    main()
