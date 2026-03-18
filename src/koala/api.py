"""API publica de alto nivel para usar Koala como libreria."""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict

from koala.config import KoalaUserConfig, load_user_config
from koala.core.io import load_input_text
from koala.core.models import ParseWarning
from koala.core.parser import parse_concept_text
from koala.layout.models import LayoutKind
from koala.render.context import MetadataValueResolver, RenderContextBuilder
from koala.render.models import RenderContext, RenderResult, SvgRenderRequest
from koala.render.settings import DEFAULT_LAYOUT_KIND
from koala.render.svg_render import render_svg
from typing_extensions import Unpack


class ContextConfig(TypedDict, total=False):
    """Configuracion comun para resolver contexto sin escribir archivos."""

    layout: LayoutKind
    theme: str
    typography: str
    size: str
    text_align: str
    show_node_numbers: bool
    use_user_config: bool
    user_config: KoalaUserConfig


class CompileConfig(TypedDict, total=False):
    """Configuracion aceptada por `koala.compile(path, **config)`."""

    layout: LayoutKind
    theme: str
    typography: str
    size: str
    text_align: str
    show_node_numbers: bool
    output: str | Path
    output_dir: str | Path
    desktop: bool
    use_user_config: bool
    user_config: KoalaUserConfig


class CompileTextConfig(CompileConfig, total=False):
    """Configuracion aceptada por `koala.compile_text(text, **config)`."""

    base_dir: str | Path
    output_name: str


class ValidateTextConfig(ContextConfig, total=False):
    """Configuracion aceptada por `koala.validate_text(text, **config)`."""

    strict: bool


@dataclass(frozen=True)
class ValidationError(ValueError):
    """Error de validacion para la API de libreria."""

    warnings: tuple[ParseWarning, ...]

    def __str__(self) -> str:
        count = len(self.warnings)
        if count == 0:
            return "Validacion fallida."

        first_warning = self.warnings[0]
        location = f"linea {first_warning.line_no}" if first_warning.line_no else "documento"
        return f"Validacion fallida con {count} warning(s). Primero: {location}: {first_warning.message}"


_ALLOWED_COMPILE_CONFIG_KEYS = frozenset(CompileConfig.__annotations__)
_ALLOWED_COMPILE_TEXT_CONFIG_KEYS = frozenset(CompileTextConfig.__annotations__)
_ALLOWED_CONTEXT_CONFIG_KEYS = frozenset(ContextConfig.__annotations__)
_ALLOWED_VALIDATE_TEXT_CONFIG_KEYS = frozenset(ValidateTextConfig.__annotations__)


def compile(path: str | Path, **config: Unpack[CompileConfig]) -> RenderResult:
    """Compila un archivo fuente de Koala y retorna el resultado de render."""

    _validate_config_keys(config, _ALLOWED_COMPILE_CONFIG_KEYS, "koala.compile")

    layout = config.get("layout")
    theme = config.get("theme")
    typography = config.get("typography")
    size = config.get("size")
    text_align = config.get("text_align")
    show_node_numbers = config.get("show_node_numbers")
    output = config.get("output")
    output_dir = config.get("output_dir")
    desktop = config.get("desktop", False)
    use_user_config = config.get("use_user_config", False)
    user_config = config.get("user_config")

    input_path = Path(path).expanduser().resolve()
    resolved_user_config = _resolve_user_config(use_user_config, user_config)
    source_text = load_input_text(str(input_path))
    return _compile_source_text(
        source_text,
        base_dir=input_path.parent,
        default_output_file_name_stem=input_path.stem,
        layout=layout,
        theme=theme,
        typography=typography,
        size=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        output=output,
        output_dir=output_dir,
        desktop=desktop,
        user_config=resolved_user_config,
        desktop_fallback_dir=input_path.parent,
    )


def compile_text(text: str, **config: Unpack[CompileTextConfig]) -> RenderResult:
    """Compila texto Koala y retorna el resultado de render.

    Las rutas relativas de salida se resuelven contra `base_dir` si se provee.
    Si no se pasa, se usa `Path.cwd()`.
    """

    _validate_config_keys(config, _ALLOWED_COMPILE_TEXT_CONFIG_KEYS, "koala.compile_text")

    layout = config.get("layout")
    theme = config.get("theme")
    typography = config.get("typography")
    size = config.get("size")
    text_align = config.get("text_align")
    show_node_numbers = config.get("show_node_numbers")
    output = config.get("output")
    output_dir = config.get("output_dir")
    desktop = config.get("desktop", False)
    use_user_config = config.get("use_user_config", False)
    user_config = config.get("user_config")
    base_dir = _resolve_base_dir(config.get("base_dir"))
    output_name = config.get("output_name")

    resolved_user_config = _resolve_user_config(use_user_config, user_config)
    return _compile_source_text(
        text,
        base_dir=base_dir,
        default_output_file_name_stem=output_name or "concept_map",
        layout=layout,
        theme=theme,
        typography=typography,
        size=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        output=output,
        output_dir=output_dir,
        desktop=desktop,
        user_config=resolved_user_config,
        desktop_fallback_dir=base_dir,
    )


def inspect_text(text: str, **config: Unpack[ContextConfig]) -> RenderContext:
    """Parsea texto Koala y retorna el `RenderContext` resuelto sin escribir SVG."""

    _validate_config_keys(config, _ALLOWED_CONTEXT_CONFIG_KEYS, "koala.inspect_text")
    return _build_context_from_text(
        text,
        layout=config.get("layout"),
        theme=config.get("theme"),
        typography=config.get("typography"),
        size=config.get("size"),
        text_align=config.get("text_align"),
        show_node_numbers=config.get("show_node_numbers"),
        use_user_config=config.get("use_user_config", False),
        user_config=config.get("user_config"),
    )


def validate_text(text: str, **config: Unpack[ValidateTextConfig]) -> RenderContext:
    """Valida texto Koala y retorna el contexto resuelto.

    Si `strict=True`, levanta `ValidationError` cuando existan warnings del parser.
    """

    _validate_config_keys(config, _ALLOWED_VALIDATE_TEXT_CONFIG_KEYS, "koala.validate_text")
    strict = config.get("strict", False)
    context = _build_context_from_text(
        text,
        layout=config.get("layout"),
        theme=config.get("theme"),
        typography=config.get("typography"),
        size=config.get("size"),
        text_align=config.get("text_align"),
        show_node_numbers=config.get("show_node_numbers"),
        use_user_config=config.get("use_user_config", False),
        user_config=config.get("user_config"),
    )
    if strict and context.parsed.warnings:
        raise ValidationError(tuple(context.parsed.warnings))
    return context


def _compile_source_text(
    source_text: str,
    *,
    base_dir: Path,
    default_output_file_name_stem: str,
    layout: LayoutKind | None,
    theme: str | None,
    typography: str | None,
    size: str | None,
    text_align: str | None,
    show_node_numbers: bool | None,
    output: str | Path | None,
    output_dir: str | Path | None,
    desktop: bool,
    user_config: KoalaUserConfig,
    desktop_fallback_dir: Path,
) -> RenderResult:
    parsed = parse_concept_text(source_text)
    resolved_layout = _resolve_effective_layout(parsed, layout, user_config)
    explicit_output_svg_path = _resolve_explicit_output_path(output)
    output_dir_name, default_output_dir_name = _resolve_output_directory_policy(
        resolution_base_dir=base_dir,
        output_dir=output_dir,
        desktop=desktop,
        config=user_config,
        has_explicit_output=explicit_output_svg_path is not None,
        desktop_fallback_dir=desktop_fallback_dir,
    )

    request = SvgRenderRequest(
        parsed=parsed,
        base_dir=base_dir,
        output_svg_path=explicit_output_svg_path,
        output_dir_name=output_dir_name,
        output_file_name=(
            None
            if explicit_output_svg_path is not None
            else _resolve_output_file_name(default_output_file_name_stem, resolved_layout)
        ),
        default_output_dir_name=default_output_dir_name,
        layout_kind=layout,
        theme_name=theme,
        typography_name=typography,
        page_size_name=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        default_layout_kind=user_config.default_layout,
        default_theme_name=user_config.default_theme,
        default_typography_name=user_config.default_typography,
        default_page_size_name=user_config.default_size,
        default_text_align=user_config.default_text_align,
        default_show_node_numbers=user_config.default_show_node_numbers,
    )
    return render_svg(request)


def _build_context_from_text(
    text: str,
    *,
    layout: LayoutKind | None,
    theme: str | None,
    typography: str | None,
    size: str | None,
    text_align: str | None,
    show_node_numbers: bool | None,
    use_user_config: bool,
    user_config: KoalaUserConfig | None,
) -> RenderContext:
    resolved_user_config = _resolve_user_config(use_user_config, user_config)
    parsed = parse_concept_text(text)
    return RenderContextBuilder.build(
        parsed,
        layout_kind=layout,
        theme_name=theme,
        typography_name=typography,
        page_size_name=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        default_layout_kind=resolved_user_config.default_layout,
        default_theme_name=resolved_user_config.default_theme,
        default_typography_name=resolved_user_config.default_typography,
        default_page_size_name=resolved_user_config.default_size,
        default_text_align=resolved_user_config.default_text_align,
        default_show_node_numbers=resolved_user_config.default_show_node_numbers,
    )


def _validate_config_keys(config: dict, allowed_keys: frozenset[str], func_name: str) -> None:
    unknown_keys = sorted(set(config) - allowed_keys)
    if not unknown_keys:
        return

    available_keys = ", ".join(sorted(allowed_keys))
    invalid_keys = ", ".join(unknown_keys)
    raise TypeError(
        f"Parametros invalidos para {func_name}(...): {invalid_keys}. "
        f"Disponibles: {available_keys}."
    )


def _resolve_user_config(
    use_user_config: bool,
    user_config: KoalaUserConfig | None,
) -> KoalaUserConfig:
    if user_config is not None:
        return user_config
    if use_user_config:
        return load_user_config()
    return KoalaUserConfig(path=Path(), exists=False)


def _resolve_effective_layout(
    parsed,
    explicit_layout: str | None,
    config: KoalaUserConfig,
) -> LayoutKind:
    metadata_layout = MetadataValueResolver.resolve_value(parsed.metadata, "layout")
    return explicit_layout or metadata_layout or config.default_layout or DEFAULT_LAYOUT_KIND


def _resolve_explicit_output_path(raw_output: str | Path | None) -> Path | None:
    if raw_output is None:
        return None
    output_path = Path(raw_output).expanduser()
    if output_path.suffix.lower() != ".svg":
        output_path = output_path.with_suffix(".svg")
    return output_path


def _resolve_output_directory_policy(
    *,
    resolution_base_dir: Path,
    output_dir: str | Path | None,
    desktop: bool,
    config: KoalaUserConfig,
    has_explicit_output: bool,
    desktop_fallback_dir: Path,
) -> tuple[str | None, str | None]:
    if has_explicit_output:
        return None, None

    if output_dir is not None:
        return str(Path(output_dir).expanduser()), None

    if desktop:
        return str(_desktop_path_or_fallback(desktop_fallback_dir)), None

    return None, str(
        _config_default_output_dir(
            resolution_base_dir=resolution_base_dir,
            config=config,
            desktop_fallback_dir=desktop_fallback_dir,
        )
    )


def _config_default_output_dir(
    *,
    resolution_base_dir: Path,
    config: KoalaUserConfig,
    desktop_fallback_dir: Path,
) -> Path:
    if config.default_output_dir:
        configured = Path(config.default_output_dir).expanduser()
        return configured if configured.is_absolute() else resolution_base_dir / configured

    if config.default_output_mode == "desktop":
        return _desktop_path_or_fallback(desktop_fallback_dir)
    if config.default_output_mode == "cwd":
        return Path.cwd()
    return resolution_base_dir


def _resolve_output_file_name(stem: str, layout: LayoutKind) -> str:
    sanitized_stem = stem.strip() or "concept_map"
    if sanitized_stem.lower().endswith(".svg"):
        return sanitized_stem
    return f"{sanitized_stem}.{layout}.svg"


def _resolve_base_dir(base_dir: str | Path | None) -> Path:
    if base_dir is None:
        return Path.cwd()
    return Path(base_dir).expanduser().resolve()


def _desktop_path_or_fallback(fallback_dir: Path) -> Path:
    desktop_path = Path.home() / "Desktop"
    if desktop_path.exists():
        return desktop_path
    return fallback_dir
