"""API publica de alto nivel para usar Koala como libreria."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from koala.config import KoalaUserConfig, load_user_config
from koala.core.io import load_input_text
from koala.core.parser import parse_concept_text
from koala.layout.models import LayoutKind
from koala.render.context import MetadataValueResolver
from koala.render.models import RenderResult, SvgRenderRequest
from koala.render.settings import DEFAULT_LAYOUT_KIND
from koala.render.svg_render import render_svg
from typing_extensions import Unpack


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


_ALLOWED_COMPILE_CONFIG_KEYS = frozenset(CompileConfig.__annotations__)


def compile(path: str | Path, **config: Unpack[CompileConfig]) -> RenderResult:
    """Compila un archivo fuente de Koala y retorna el resultado de render.

    La API publica esta pensada para uso programatico:

    ```python
    import koala

    result = koala.compile("mapa.txt", theme="academic", layout="tree")
    print(result.output_svg)
    ```
    """

    unknown_keys = sorted(set(config) - _ALLOWED_COMPILE_CONFIG_KEYS)
    if unknown_keys:
        available_keys = ", ".join(sorted(_ALLOWED_COMPILE_CONFIG_KEYS))
        invalid_keys = ", ".join(unknown_keys)
        raise TypeError(
            f"Parametros invalidos para koala.compile(...): {invalid_keys}. "
            f"Disponibles: {available_keys}."
        )

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
    config = _resolve_user_config(use_user_config, user_config)
    source_text = load_input_text(str(input_path))
    parsed = parse_concept_text(source_text)
    resolved_layout = _resolve_effective_layout(parsed, layout, config)
    explicit_output_svg_path = _resolve_explicit_output_path(output)
    output_dir_name, default_output_dir_name = _resolve_output_directory_policy(
        input_path=input_path,
        output_dir=output_dir,
        desktop=desktop,
        config=config,
        has_explicit_output=explicit_output_svg_path is not None,
    )

    request = SvgRenderRequest(
        parsed=parsed,
        base_dir=input_path.parent,
        output_svg_path=explicit_output_svg_path,
        output_dir_name=output_dir_name,
        output_file_name=None if explicit_output_svg_path is not None else f"{input_path.stem}.{resolved_layout}.svg",
        default_output_dir_name=default_output_dir_name,
        layout_kind=layout,
        theme_name=theme,
        typography_name=typography,
        page_size_name=size,
        text_align=text_align,
        show_node_numbers=show_node_numbers,
        default_layout_kind=config.default_layout,
        default_theme_name=config.default_theme,
        default_typography_name=config.default_typography,
        default_page_size_name=config.default_size,
        default_text_align=config.default_text_align,
        default_show_node_numbers=config.default_show_node_numbers,
    )
    return render_svg(request)


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
    input_path: Path,
    output_dir: str | Path | None,
    desktop: bool,
    config: KoalaUserConfig,
    has_explicit_output: bool,
) -> tuple[str | None, str | None]:
    if has_explicit_output:
        return None, None

    if output_dir is not None:
        return str(Path(output_dir).expanduser()), None

    if desktop:
        return str(_desktop_path_or_input_parent(input_path)), None

    return None, str(_config_default_output_dir(input_path, config))


def _config_default_output_dir(input_path: Path, config: KoalaUserConfig) -> Path:
    if config.default_output_dir:
        configured = Path(config.default_output_dir).expanduser()
        return configured if configured.is_absolute() else input_path.parent / configured

    if config.default_output_mode == "desktop":
        return _desktop_path_or_input_parent(input_path)
    if config.default_output_mode == "cwd":
        return Path.cwd()
    return input_path.parent


def _desktop_path_or_input_parent(input_path: Path) -> Path:
    desktop_path = Path.home() / "Desktop"
    if desktop_path.exists():
        return desktop_path
    return input_path.parent
