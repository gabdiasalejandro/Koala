"""API publica de alto nivel para usar Koala como libreria."""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, replace as _dc_replace
from typing import TypedDict


from koala.config import KoalaUserConfig, load_user_config
from koala.core.shared.io import load_input_text
from koala.core.tree.models import ParseWarning
from koala.core.shared.errors import InputLimitExceededError, InvalidRenderConfigError, KoalaInputError
from koala.core.shared.registry import DocumentPipelineRegistry
from koala.core.shared.types import DocumentType
# `layout` es un identificador opaco a nivel API. Cada pipeline de documento
# valida que el layout exista entre los suyos (por ejemplo `TREE_LAYOUTS`).
LayoutKind = str
from koala.render.shared.export import ExportConverter
from koala.render.shared.models import (
    ExportFormat,
    ExportQuality,
    ExportResult,
    RenderAdvisory,
    RenderContext,
    RenderResult,
)
from koala.render.shared.settings import (
    available_typography_names,
    available_typography_names_for,
)
from typing_extensions import Unpack


class ContextConfig(TypedDict, total=False):
    """Configuracion comun para resolver contexto sin escribir archivos."""

    type: DocumentType
    layout: LayoutKind
    theme: str
    typography: str
    size: str
    text_align: str
    show_node_numbers: bool
    background: str
    use_user_config: bool
    user_config: KoalaUserConfig
    max_input_bytes: int
    max_input_lines: int
    max_nodes: int
    max_warnings: int
    node_warn_threshold: int


class CompileConfig(TypedDict, total=False):
    """Configuracion aceptada por `koala.compile(path, **config)`."""

    type: DocumentType
    layout: LayoutKind
    theme: str
    typography: str
    size: str
    text_align: str
    show_node_numbers: bool
    background: str
    output: str | Path
    output_dir: str | Path
    desktop: bool
    use_user_config: bool
    user_config: KoalaUserConfig
    max_input_bytes: int
    max_input_lines: int
    max_nodes: int
    max_warnings: int
    node_warn_threshold: int


class CompileTextConfig(CompileConfig, total=False):
    """Configuracion aceptada por `koala.compile_text(text, **config)`."""

    base_dir: str | Path
    output_name: str


class ValidateTextConfig(ContextConfig, total=False):
    """Configuracion aceptada por `koala.validate_text(text, **config)`."""

    strict: bool


class SafeRenderConfig(ContextConfig, total=False):
    """Configuracion aceptada por `koala.safe_render_text(text, **config)`."""


class SaveTextConfig(TypedDict, total=False):
    """Configuracion aceptada por `koala.save_text(text, output, **config)`."""

    base_dir: str | Path


@dataclass(frozen=True)
class ValidationError(KoalaInputError):
    """Error de validacion para la API de libreria."""

    warnings: tuple[ParseWarning, ...]

    def __str__(self) -> str:
        count = len(self.warnings)
        if count == 0:
            return "Validacion fallida."

        first_warning = self.warnings[0]
        location = f"linea {first_warning.line_no}" if first_warning.line_no else "documento"
        return f"Validacion fallida con {count} warning(s). Primero: {location}: {first_warning.message}"


@dataclass(frozen=True)
class _RenderLimits:
    max_input_bytes: int | None = None
    max_input_lines: int | None = None
    max_nodes: int | None = None
    max_warnings: int | None = None
    node_warn_threshold: int | None = None


SAFE_RENDER_DEFAULT_LIMITS = {
    "max_input_bytes": 80_000,
    "max_input_lines": 800,
    "max_nodes": 250,
    "max_warnings": 0,
    "node_warn_threshold": 80,
}
SAFE_RENDER_DOCUMENT_TYPES = ("matrix", "tree")


_ALLOWED_COMPILE_CONFIG_KEYS = frozenset(CompileConfig.__annotations__)
_ALLOWED_COMPILE_TEXT_CONFIG_KEYS = frozenset(CompileTextConfig.__annotations__)
_ALLOWED_CONTEXT_CONFIG_KEYS = frozenset(ContextConfig.__annotations__)
_ALLOWED_VALIDATE_TEXT_CONFIG_KEYS = frozenset(ValidateTextConfig.__annotations__)
_ALLOWED_SAFE_RENDER_CONFIG_KEYS = frozenset(SafeRenderConfig.__annotations__)
_ALLOWED_SAVE_TEXT_CONFIG_KEYS = frozenset(SaveTextConfig.__annotations__)


def available_document_types() -> tuple[str, ...]:
    """Retorna los tipos de documento disponibles para la API publica."""

    return DocumentPipelineRegistry.available_types()


def available_typographies(type: DocumentType | None = None) -> tuple[str, ...]:
    """Retorna presets tipograficos disponibles.

    Si `type` se omite, retorna la union de presets disponibles en Koala.
    Si se pasa, retorna solo las tipografias registradas para ese tipo.
    """

    if type is None:
        return available_typography_names()

    document_type = DocumentPipelineRegistry.normalize_type(type)
    DocumentPipelineRegistry.require(document_type)
    return available_typography_names_for(document_type)


def compile(path: str | Path, **config: Unpack[CompileConfig]) -> RenderResult:
    """Compila un archivo fuente de Koala y retorna el resultado de render."""

    _validate_config_keys(config, _ALLOWED_COMPILE_CONFIG_KEYS, "koala.compile")

    layout = config.get("layout")
    document_type = config.get("type")
    theme = config.get("theme")
    typography = config.get("typography")
    size = config.get("size")
    text_align = config.get("text_align")
    show_node_numbers = config.get("show_node_numbers")
    background = config.get("background")
    output = config.get("output")
    output_dir = config.get("output_dir")
    desktop = config.get("desktop", False)
    use_user_config = config.get("use_user_config", False)
    user_config = config.get("user_config")

    input_path = Path(path).expanduser().resolve()
    resolved_user_config = _resolve_user_config(use_user_config, user_config)
    source_text = load_input_text(str(input_path))
    return _render_source_text(
        source_text,
        base_dir=input_path.parent,
        default_output_file_name_stem=input_path.stem,
        persist_output=True,
        document_type=document_type,
        layout=layout,
        theme=theme,
        typography=typography,
        size=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        background=background,
        output=output,
        output_dir=output_dir,
        desktop=desktop,
        user_config=resolved_user_config,
        desktop_fallback_dir=input_path.parent,
        limits=_limits_from_config(config),
    )


def compile_text(text: str, **config: Unpack[CompileTextConfig]) -> RenderResult:
    """Compila texto Koala y escribe un SVG en disco.

    Las rutas relativas de salida se resuelven contra `base_dir` si se provee.
    Si no se pasa, se usa `Path.cwd()`.

    Esta funcion se mantiene por compatibilidad y utiliza el nuevo pipeline
    basado en generacion de SVG en memoria.
    """

    _validate_config_keys(config, _ALLOWED_COMPILE_TEXT_CONFIG_KEYS, "koala.compile_text")

    layout = config.get("layout")
    document_type = config.get("type")
    theme = config.get("theme")
    typography = config.get("typography")
    size = config.get("size")
    text_align = config.get("text_align")
    show_node_numbers = config.get("show_node_numbers")
    background = config.get("background")
    output = config.get("output")
    output_dir = config.get("output_dir")
    desktop = config.get("desktop", False)
    use_user_config = config.get("use_user_config", False)
    user_config = config.get("user_config")
    base_dir = _resolve_base_dir(config.get("base_dir"))
    output_name = config.get("output_name")

    resolved_user_config = _resolve_user_config(use_user_config, user_config)
    return _render_source_text(
        text,
        base_dir=base_dir,
        default_output_file_name_stem=output_name or "concept_map",
        persist_output=True,
        document_type=document_type,
        layout=layout,
        theme=theme,
        typography=typography,
        size=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        background=background,
        output=output,
        output_dir=output_dir,
        desktop=desktop,
        user_config=resolved_user_config,
        desktop_fallback_dir=base_dir,
        limits=_limits_from_config(config),
    )


def compile_file(path: str | Path, **config: Unpack[CompileConfig]) -> RenderResult:
    """Alias explicito de `koala.compile(path, **config)`."""

    return compile(path, **config)


def render_text(text: str, **config: Unpack[ContextConfig]) -> RenderResult:
    """Renderiza texto Koala y retorna el SVG en memoria.

    No escribe archivos. El SVG final queda disponible en `result.svg`.
    """

    _validate_config_keys(config, _ALLOWED_CONTEXT_CONFIG_KEYS, "koala.render_text")
    resolved_user_config = _resolve_user_config(
        config.get("use_user_config", False),
        config.get("user_config"),
    )
    return _render_source_text(
        text,
        base_dir=Path.cwd(),
        default_output_file_name_stem="concept_map",
        persist_output=False,
        document_type=config.get("type"),
        layout=config.get("layout"),
        theme=config.get("theme"),
        typography=config.get("typography"),
        size=config.get("size"),
        text_align=config.get("text_align"),
        show_node_numbers=config.get("show_node_numbers"),
        background=config.get("background"),
        output=None,
        output_dir=None,
        desktop=False,
        user_config=resolved_user_config,
        desktop_fallback_dir=Path.cwd(),
        limits=_limits_from_config(config),
    )


def safe_render_text(text: str, **config: Unpack[SafeRenderConfig]) -> RenderResult:
    """Renderiza texto con defaults defensivos para inputs no confiables.

    Esta entrada esta pensada para servidores que reciben DSL generado por IA:
    limita tamano/lineas/nodos, falla si hay warnings y por ahora solo acepta
    `type="tree"` o `type="matrix"`.
    """

    _validate_config_keys(config, _ALLOWED_SAFE_RENDER_CONFIG_KEYS, "koala.safe_render_text")
    safe_config = _merge_safe_render_config(config)
    _require_safe_document_type(safe_config.get("type"))
    return render_text(text, **safe_config)  # type: ignore[arg-type]


def export_text(
    text: str,
    *,
    format: ExportFormat = "pdf",
    quality: ExportQuality = "high",
    title: str | None = None,
    output: str | Path | None = None,
    **config: Unpack[ContextConfig],
) -> ExportResult:
    """Exporta texto Koala a SVG, PNG o PDF y retorna bytes en memoria.

    PNG se exporta directamente desde el SVG canonico usando la calidad
    solicitada. PDF aplica un marco profesional con titulo y paleta del theme.
    Si `output` se pasa, tambien escribe el archivo y retorna `output_path`.
    """

    _validate_config_keys(config, _ALLOWED_CONTEXT_CONFIG_KEYS, "koala.export_text")
    render = render_text(text, **config)
    export = ExportConverter.convert(render, format=format, quality=quality, title=title)
    if output is None:
        return export
    return ExportConverter.write(export, _resolve_export_output_path(output, Path.cwd()))


def safe_export_text(
    text: str,
    *,
    format: ExportFormat = "svg",
    quality: ExportQuality = "high",
    title: str | None = None,
    **config: Unpack[SafeRenderConfig],
) -> ExportResult:
    """Exporta texto con los mismos limites defensivos de `safe_render_text`.

    No acepta `output`: el resultado vuelve en memoria para que el servidor
    decida como responder o almacenar los bytes.
    """

    _validate_config_keys(config, _ALLOWED_SAFE_RENDER_CONFIG_KEYS, "koala.safe_export_text")
    safe_config = _merge_safe_render_config(config)
    _require_safe_document_type(safe_config.get("type"))
    render = render_text(text, **safe_config)  # type: ignore[arg-type]
    return ExportConverter.convert(render, format=format, quality=quality, title=title)


def export_file(
    path: str | Path,
    *,
    format: ExportFormat = "pdf",
    quality: ExportQuality = "high",
    title: str | None = None,
    output: str | Path | None = None,
    **config: Unpack[ContextConfig],
) -> ExportResult:
    """Exporta un archivo fuente Koala a SVG, PNG o PDF y retorna bytes."""

    _validate_config_keys(config, _ALLOWED_CONTEXT_CONFIG_KEYS, "koala.export_file")

    input_path = Path(path).expanduser().resolve()
    resolved_user_config = _resolve_user_config(
        config.get("use_user_config", False),
        config.get("user_config"),
    )
    source_text = load_input_text(str(input_path))
    render = _render_source_text(
        source_text,
        base_dir=input_path.parent,
        default_output_file_name_stem=input_path.stem,
        persist_output=False,
        document_type=config.get("type"),
        layout=config.get("layout"),
        theme=config.get("theme"),
        typography=config.get("typography"),
        size=config.get("size"),
        text_align=config.get("text_align"),
        show_node_numbers=config.get("show_node_numbers"),
        background=config.get("background"),
        output=None,
        output_dir=None,
        desktop=False,
        user_config=resolved_user_config,
        desktop_fallback_dir=input_path.parent,
        limits=_limits_from_config(config),
    )
    export = ExportConverter.convert(render, format=format, quality=quality, title=title)
    if output is None:
        return export
    return ExportConverter.write(export, _resolve_export_output_path(output, input_path.parent))


def save_text(text: str, output: str | Path, **config: Unpack[SaveTextConfig]) -> Path:
    """Guarda texto plano en un archivo `.txt` y retorna la ruta final."""

    _validate_config_keys(config, _ALLOWED_SAVE_TEXT_CONFIG_KEYS, "koala.save_text")
    _require_text(text)
    base_dir = _resolve_base_dir(config.get("base_dir"))
    output_path = _resolve_text_output_path(output, base_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def inspect_text(text: str, **config: Unpack[ContextConfig]) -> RenderContext:
    """Parsea texto Koala y retorna el `RenderContext` resuelto sin escribir SVG."""

    _validate_config_keys(config, _ALLOWED_CONTEXT_CONFIG_KEYS, "koala.inspect_text")
    return _build_context_from_text(
        text,
        document_type=config.get("type"),
        layout=config.get("layout"),
        theme=config.get("theme"),
        typography=config.get("typography"),
        size=config.get("size"),
        text_align=config.get("text_align"),
        show_node_numbers=config.get("show_node_numbers"),
        background=config.get("background"),
        use_user_config=config.get("use_user_config", False),
        user_config=config.get("user_config"),
        limits=_limits_from_config(config),
    )


def validate_text(text: str, **config: Unpack[ValidateTextConfig]) -> RenderContext:
    """Valida texto Koala y retorna el contexto resuelto.

    Si `strict=True`, levanta `ValidationError` cuando existan warnings del parser.
    """

    _validate_config_keys(config, _ALLOWED_VALIDATE_TEXT_CONFIG_KEYS, "koala.validate_text")
    strict = config.get("strict", False)
    context = _build_context_from_text(
        text,
        document_type=config.get("type"),
        layout=config.get("layout"),
        theme=config.get("theme"),
        typography=config.get("typography"),
        size=config.get("size"),
        text_align=config.get("text_align"),
        show_node_numbers=config.get("show_node_numbers"),
        background=config.get("background"),
        use_user_config=config.get("use_user_config", False),
        user_config=config.get("user_config"),
        limits=_limits_from_config(config),
    )
    if strict and context.parsed.warnings:
        raise ValidationError(tuple(context.parsed.warnings))
    return context


def _render_source_text(
    source_text: str,
    *,
    base_dir: Path,
    default_output_file_name_stem: str,
    persist_output: bool,
    document_type: DocumentType | None,
    layout: LayoutKind | None,
    theme: str | None,
    typography: str | None,
    size: str | None,
    text_align: str | None,
    show_node_numbers: bool | None,
    background: str | None,
    output: str | Path | None,
    output_dir: str | Path | None,
    desktop: bool,
    user_config: KoalaUserConfig,
    desktop_fallback_dir: Path,
    limits: "_RenderLimits",
) -> RenderResult:
    _enforce_source_text_limits(source_text, limits)
    pipeline = DocumentPipelineRegistry.require(document_type)
    parsed = pipeline.parse(source_text)
    advisories = _enforce_parsed_document_limits(parsed, limits)
    explicit_output_svg_path = _resolve_explicit_output_path(output, base_dir)
    output_dir_name, default_output_dir_name = (None, None)
    if persist_output:
        output_dir_name, default_output_dir_name = _resolve_output_directory_policy(
            resolution_base_dir=base_dir,
            output_dir=output_dir,
            desktop=desktop,
            config=user_config,
            has_explicit_output=explicit_output_svg_path is not None,
            desktop_fallback_dir=desktop_fallback_dir,
        )

    output_file_name = (
        None
        if not persist_output or explicit_output_svg_path is not None
        else pipeline.resolve_output_file_name(
            parsed,
            stem=default_output_file_name_stem,
            layout=layout,
            user_config=user_config,
        )
    )
    result = pipeline.render_parsed(
        parsed,
        base_dir=base_dir,
        persist_output=persist_output,
        output_svg_path=explicit_output_svg_path,
        output_dir_name=output_dir_name,
        output_file_name=output_file_name,
        default_output_dir_name=default_output_dir_name,
        layout=layout,
        theme_name=theme,
        typography_name=typography,
        page_size_name=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        background_color=background,
        user_config=user_config,
    )
    if advisories:
        result = _dc_replace(result, advisories=advisories)
    return result


def _build_context_from_text(
    text: str,
    *,
    document_type: DocumentType | None,
    layout: LayoutKind | None,
    theme: str | None,
    typography: str | None,
    size: str | None,
    text_align: str | None,
    show_node_numbers: bool | None,
    background: str | None,
    use_user_config: bool,
    user_config: KoalaUserConfig | None,
    limits: "_RenderLimits",
) -> RenderContext:
    _enforce_source_text_limits(text, limits)
    resolved_user_config = _resolve_user_config(use_user_config, user_config)
    pipeline = DocumentPipelineRegistry.require(document_type)
    context = pipeline.inspect_text(
        text,
        layout=layout,
        theme_name=theme,
        typography_name=typography,
        page_size_name=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        background_color=background,
        user_config=resolved_user_config,
    )
    _enforce_parsed_document_limits(context.parsed, limits)
    return context


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


def _limits_from_config(config: dict) -> _RenderLimits:
    return _RenderLimits(
        max_input_bytes=_optional_positive_int(config.get("max_input_bytes"), "max_input_bytes"),
        max_input_lines=_optional_positive_int(config.get("max_input_lines"), "max_input_lines"),
        max_nodes=_optional_positive_int(config.get("max_nodes"), "max_nodes"),
        max_warnings=_optional_positive_int(
            config.get("max_warnings"),
            "max_warnings",
            allow_zero=True,
        ),
        node_warn_threshold=_optional_positive_int(
            config.get("node_warn_threshold"),
            "node_warn_threshold",
        ),
    )


def _merge_safe_render_config(config: dict) -> dict:
    merged = dict(SAFE_RENDER_DEFAULT_LIMITS)
    merged.update(config)
    return merged


def _require_safe_document_type(document_type: object) -> None:
    normalized = DocumentPipelineRegistry.normalize_type(document_type)  # type: ignore[arg-type]
    if normalized not in SAFE_RENDER_DOCUMENT_TYPES:
        available = ", ".join(SAFE_RENDER_DOCUMENT_TYPES)
        raise InvalidRenderConfigError(
            key="type",
            value=document_type if document_type is not None else normalized,
            expected=f"uno de: {available}",
        )


def _optional_positive_int(value: object, key: str, *, allow_zero: bool = False) -> int | None:
    if value is None:
        return None
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InvalidRenderConfigError(
            key=key,
            value=value,
            expected="entero positivo" if not allow_zero else "entero >= 0",
        )
    return value


def _require_text(text: object) -> str:
    if not isinstance(text, str):
        raise InvalidRenderConfigError(
            key="text",
            value=text,
            expected="string con DSL Koala",
        )
    return text


def _enforce_source_text_limits(source_text: object, limits: _RenderLimits) -> str:
    text = _require_text(source_text)
    if limits.max_input_bytes is not None:
        byte_count = len(text.encode("utf-8"))
        if byte_count > limits.max_input_bytes:
            raise InputLimitExceededError("max_input_bytes", byte_count, limits.max_input_bytes)

    if limits.max_input_lines is not None:
        line_count = len(text.splitlines())
        if line_count > limits.max_input_lines:
            raise InputLimitExceededError("max_input_lines", line_count, limits.max_input_lines)

    return text


def _enforce_parsed_document_limits(
    parsed, limits: _RenderLimits
) -> tuple[RenderAdvisory, ...]:
    node_count = _count_parsed_nodes(parsed)

    if limits.max_nodes is not None and node_count > limits.max_nodes:
        raise InputLimitExceededError("max_nodes", node_count, limits.max_nodes)

    if limits.max_warnings is not None:
        warning_count = len(getattr(parsed, "warnings", ()))
        if warning_count > limits.max_warnings:
            raise InputLimitExceededError("max_warnings", warning_count, limits.max_warnings)

    advisories: list[RenderAdvisory] = []
    if limits.node_warn_threshold is not None and node_count > limits.node_warn_threshold:
        advisories.append(
            RenderAdvisory(
                code="layout_quality_threshold",
                message=(
                    f"El documento tiene {node_count} nodos, por encima del umbral "
                    f"de calidad de layout ({limits.node_warn_threshold}). El render "
                    "puede verse comprimido o con tipografia chica."
                ),
            )
        )
    return tuple(advisories)


def _count_parsed_nodes(parsed) -> int:
    node_index = getattr(parsed, "node_index", None)
    if node_index is not None:
        return len(node_index)
    nodes = getattr(parsed, "nodes", None)
    if nodes is not None:
        return len(nodes)
    return 0


def _resolve_user_config(
    use_user_config: bool,
    user_config: KoalaUserConfig | None,
) -> KoalaUserConfig:
    if user_config is not None:
        return user_config
    if use_user_config:
        return load_user_config()
    return KoalaUserConfig(path=Path(), exists=False)


def _resolve_explicit_output_path(raw_output: str | Path | None, base_dir: Path) -> Path | None:
    if raw_output is None:
        return None

    output_path = Path(raw_output).expanduser()
    if not output_path.is_absolute():
        output_path = base_dir / output_path
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


def _resolve_text_output_path(output: str | Path, base_dir: Path) -> Path:
    output_path = Path(output).expanduser()
    if not output_path.is_absolute():
        output_path = base_dir / output_path
    if output_path.suffix.lower() != ".txt":
        output_path = output_path.with_suffix(".txt")
    return output_path.resolve()


def _resolve_export_output_path(output: str | Path, base_dir: Path) -> Path:
    output_path = Path(output).expanduser()
    if not output_path.is_absolute():
        output_path = base_dir / output_path
    return output_path.resolve()


def _desktop_path_or_fallback(fallback_dir: Path) -> Path:
    desktop_path = Path.home() / "Desktop"
    if desktop_path.exists():
        return desktop_path
    return fallback_dir
