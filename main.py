from pathlib import Path

from core.io import load_input_text
from core.parser import parse_concept_text
from render.pdf_render import render_pdf
from render.svg_render import render_svg

INPUT_FILE = "mocks/concepts.txt"     # puede ser .txt o .docx
OUTPUT_DIR = "output"


def main() -> None:
    base_dir = Path(__file__).parent
    output_dir = base_dir / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    text = load_input_text(INPUT_FILE)
    parsed = parse_concept_text(text)

    output_svg = output_dir / "concept_map.svg"
    output_pdf = output_dir / "concept_map.pdf"

    render_svg(parsed, output_svg)
    render_pdf(parsed, output_pdf)

    print(f"SVG generado: {output_svg}")
    print(f"PDF generado: {output_pdf}")


if __name__ == "__main__":
    main()
