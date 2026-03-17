"""CLI instalable de Koala."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from koala.api import compile as compile_document
from koala.config import default_user_config_path, load_user_config
from koala.core.io import load_input_text
from koala.core.parser import parse_concept_text
from koala.layout.models import LayoutKind
from koala.render.context import RenderContextBuilder
from koala.render.settings import (
    available_page_size_names,
    available_typography_names,
)
from koala.render.themes import available_theme_names


AVAILABLE_LAYOUTS: tuple[LayoutKind, ...] = ("tree", "synoptic", "synoptic_boxes", "radial")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="koala",
        description="Compila el DSL de Koala a SVG y expone utilidades del proyecto.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="koala 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compila un archivo .txt/.docx a SVG.")
    _add_input_argument(compile_parser)
    _add_render_arguments(compile_parser)
    output_group = compile_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-o",
        "--output",
        help="Ruta final del SVG de salida.",
    )
    output_group.add_argument(
        "--output-dir",
        help="Carpeta de salida. Si es relativa, se resuelve desde el archivo fuente.",
    )
    output_group.add_argument(
        "--desktop",
        action="store_true",
        help="Envía la salida al escritorio del usuario.",
    )
    compile_parser.set_defaults(handler=_handle_compile)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspecciona el documento parseado y los settings resueltos sin renderizar.",
    )
    _add_input_argument(inspect_parser)
    _add_render_arguments(inspect_parser)
    inspect_parser.set_defaults(handler=_handle_inspect)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Valida parsing, metadata y settings resueltos del documento.",
    )
    _add_input_argument(validate_parser)
    _add_render_arguments(validate_parser)
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Retorna exit code 1 si hay warnings del parser.",
    )
    validate_parser.set_defaults(handler=_handle_validate)

    themes_parser = subparsers.add_parser("themes", help="Lista los themes disponibles.")
    themes_parser.set_defaults(handler=_handle_themes)

    layouts_parser = subparsers.add_parser("layouts", help="Lista los layouts disponibles.")
    layouts_parser.set_defaults(handler=_handle_layouts)

    typographies_parser = subparsers.add_parser(
        "typographies",
        help="Lista las tipografias disponibles.",
    )
    typographies_parser.set_defaults(handler=_handle_typographies)

    config_parser = subparsers.add_parser(
        "config-path",
        help="Muestra la ruta esperada para la config de usuario.",
    )
    config_parser.set_defaults(handler=_handle_config_path)

    return parser


def _add_input_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", help="Archivo fuente .txt o .docx.")


def _add_render_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-l",
        "--layout",
        choices=AVAILABLE_LAYOUTS,
        default=None,
        help="Layout a usar. Precedencia: CLI > metadata > config de usuario > default interno.",
    )
    parser.add_argument(
        "-t",
        "--theme",
        choices=available_theme_names(),
        default=None,
        help="Theme a usar. Precedencia: CLI > metadata > config de usuario > default interno.",
    )
    parser.add_argument(
        "-ty",
        "--typography",
        choices=available_typography_names(),
        default=None,
        help="Tipografía a usar. Precedencia: CLI > metadata > config de usuario > default interno.",
    )
    parser.add_argument(
        "-s",
        "--size",
        choices=available_page_size_names(),
        default=None,
        help="Tamaño de página. Precedencia: CLI > metadata > config de usuario > default interno.",
    )
    parser.add_argument(
        "--text-align",
        choices=("left", "justify"),
        default=None,
        help="Alineado de texto. Precedencia: CLI > metadata > config de usuario > default interno.",
    )
    node_numbers_group = parser.add_mutually_exclusive_group()
    node_numbers_group.add_argument(
        "--show-node-numbers",
        action="store_true",
        dest="show_node_numbers",
        help="Fuerza la numeración visible en los nodos.",
    )
    node_numbers_group.add_argument(
        "--hide-node-numbers",
        action="store_false",
        dest="show_node_numbers",
        help="Oculta la numeración de nodos.",
    )
    parser.set_defaults(show_node_numbers=None)


def _handle_compile(args: argparse.Namespace) -> int:
    result = compile_document(
        args.input,
        layout=args.layout,
        theme=args.theme,
        typography=args.typography,
        size=args.size,
        text_align=args.text_align,
        show_node_numbers=args.show_node_numbers,
        output=args.output,
        output_dir=args.output_dir,
        desktop=args.desktop,
        use_user_config=True,
    )

    print(f"SVG generado: {result.output_svg}")
    print(f"Layout usado: {result.context.settings.layout_kind}")
    print(f"Tema usado: {result.context.settings.theme_name}")
    print(f"Tipografia usada: {result.context.settings.typography_name}")
    print(f"Tamano de pagina usado: {result.context.settings.page_size_name}")
    print(f"Alineado usado: {result.context.settings.typography.text_align}")
    print(f"Numeracion visible: {result.context.settings.show_node_numbers}")
    print(f"Nodos: {len(result.context.parsed.node_index)}")
    return 0


def _handle_inspect(args: argparse.Namespace) -> int:
    config = load_user_config()
    input_path, parsed = _load_parsed_document(args.input)
    context = RenderContextBuilder.build(
        parsed,
        layout_kind=args.layout,
        theme_name=args.theme,
        typography_name=args.typography,
        page_size_name=args.size,
        text_align=args.text_align,
        show_node_numbers=args.show_node_numbers,
        default_layout_kind=config.default_layout,
        default_theme_name=config.default_theme,
        default_typography_name=config.default_typography,
        default_page_size_name=config.default_size,
        default_text_align=config.default_text_align,
        default_show_node_numbers=config.default_show_node_numbers,
    )

    print(f"Input: {input_path}")
    print(f"Config path: {config.path}")
    print(f"Config cargada: {'si' if config.exists else 'no'}")
    print(f"Raices: {len(parsed.root_nodes)}")
    print(f"Nodos: {len(parsed.node_index)}")
    print(f"Warnings: {len(parsed.warnings)}")
    print(f"Metadata keys: {', '.join(sorted(parsed.metadata.keys())) or '(none)'}")
    print(f"Layout resuelto: {context.settings.layout_kind}")
    print(f"Theme resuelto: {context.settings.theme_name}")
    print(f"Tipografia resuelta: {context.settings.typography_name}")
    print(f"Tamano resuelto: {context.settings.page_size_name}")
    print(f"Alineado resuelto: {context.settings.typography.text_align}")
    print(f"Numeracion visible: {context.settings.show_node_numbers}")

    if parsed.warnings:
        print("Warnings del parser:")
        for warning in parsed.warnings:
            location = f"linea {warning.line_no}" if warning.line_no else "documento"
            print(f"- {location}: {warning.message}")
    return 0


def _handle_validate(args: argparse.Namespace) -> int:
    config = load_user_config()
    input_path, parsed = _load_parsed_document(args.input)
    context = RenderContextBuilder.build(
        parsed,
        layout_kind=args.layout,
        theme_name=args.theme,
        typography_name=args.typography,
        page_size_name=args.size,
        text_align=args.text_align,
        show_node_numbers=args.show_node_numbers,
        default_layout_kind=config.default_layout,
        default_theme_name=config.default_theme,
        default_typography_name=config.default_typography,
        default_page_size_name=config.default_size,
        default_text_align=config.default_text_align,
        default_show_node_numbers=config.default_show_node_numbers,
    )

    print(f"Validacion OK: {input_path}")
    print(f"Layout: {context.settings.layout_kind}")
    print(f"Theme: {context.settings.theme_name}")
    print(f"Tipografia: {context.settings.typography_name}")
    print(f"Tamano: {context.settings.page_size_name}")

    if parsed.warnings:
        print("Warnings:")
        for warning in parsed.warnings:
            location = f"linea {warning.line_no}" if warning.line_no else "documento"
            print(f"- {location}: {warning.message}")
        return 1 if args.strict else 0

    print("Sin warnings.")
    return 0


def _handle_themes(_: argparse.Namespace) -> int:
    for name in available_theme_names():
        print(name)
    return 0


def _handle_layouts(_: argparse.Namespace) -> int:
    for name in AVAILABLE_LAYOUTS:
        print(name)
    return 0


def _handle_typographies(_: argparse.Namespace) -> int:
    for name in available_typography_names():
        print(name)
    return 0


def _handle_config_path(_: argparse.Namespace) -> int:
    print(default_user_config_path())
    return 0


def _load_parsed_document(input_arg: str) -> tuple[Path, object]:
    input_path = Path(input_arg).expanduser().resolve()
    text = load_input_text(str(input_path))
    return input_path, parse_concept_text(text)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Exception as exc:  # pragma: no cover - CLI edge surface
        parser.exit(status=1, message=f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
