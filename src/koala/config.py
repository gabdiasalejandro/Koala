"""Carga y validacion de la configuracion de usuario del CLI."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from koala.layout.models import LayoutKind
from koala.render.settings import available_page_size_names, available_typography_names
from koala.render.themes import available_theme_names


OutputMode = Literal["next_to_input", "desktop", "cwd"]
_SUPPORTED_OUTPUT_MODES: tuple[OutputMode, ...] = ("next_to_input", "desktop", "cwd")
_SUPPORTED_TEXT_ALIGNS = {"left", "justify"}
_AVAILABLE_LAYOUTS: tuple[LayoutKind, ...] = ("tree", "synoptic", "synoptic_boxes", "radial")


@dataclass(frozen=True)
class KoalaUserConfig:
    path: Path
    exists: bool
    default_layout: LayoutKind | None = None
    default_theme: str | None = None
    default_typography: str | None = None
    default_size: str | None = None
    default_text_align: str | None = None
    default_show_node_numbers: bool | None = None
    default_output_mode: OutputMode = "next_to_input"
    default_output_dir: str | None = None


def default_user_config_path() -> Path:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home).expanduser() / "koala" / "config.toml"
    return Path.home() / ".config" / "koala" / "config.toml"


def load_user_config() -> KoalaUserConfig:
    primary_path = default_user_config_path()
    legacy_path = Path.home() / ".koala.toml"

    if primary_path.exists():
        config_path = primary_path
    elif legacy_path.exists():
        config_path = legacy_path
    else:
        return KoalaUserConfig(path=primary_path, exists=False)

    raw_payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    payload = _extract_payload(raw_payload)

    return KoalaUserConfig(
        path=config_path,
        exists=True,
        default_layout=_validate_choice(
            payload,
            "default_layout",
            _AVAILABLE_LAYOUTS,
        ),
        default_theme=_validate_choice(
            payload,
            "default_theme",
            available_theme_names(),
        ),
        default_typography=_validate_choice(
            payload,
            "default_typography",
            available_typography_names(),
        ),
        default_size=_validate_choice(
            payload,
            "default_size",
            available_page_size_names(),
        ),
        default_text_align=_validate_choice(
            payload,
            "default_text_align",
            tuple(sorted(_SUPPORTED_TEXT_ALIGNS)),
        ),
        default_show_node_numbers=_validate_optional_bool(payload, "default_show_node_numbers"),
        default_output_mode=_validate_choice(
            payload,
            "default_output_mode",
            _SUPPORTED_OUTPUT_MODES,
            default="next_to_input",
        ),
        default_output_dir=_validate_optional_str(payload, "default_output_dir"),
    )


def _extract_payload(raw_payload: dict) -> dict:
    tool_payload = raw_payload.get("tool")
    if isinstance(tool_payload, dict):
        koala_payload = tool_payload.get("koala")
        if isinstance(koala_payload, dict):
            return koala_payload

    koala_payload = raw_payload.get("koala")
    if isinstance(koala_payload, dict):
        return koala_payload

    return raw_payload


def _validate_choice(
    payload: dict,
    key: str,
    allowed: tuple[str, ...],
    *,
    default: str | None = None,
):
    raw_value = payload.get(key, default)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise ValueError(f"Config '{key}' debe ser string.")
    normalized = raw_value.strip()
    if normalized not in allowed:
        available = ", ".join(allowed)
        raise ValueError(f"Config '{key}' invalido: '{normalized}'. Disponibles: {available}.")
    return normalized


def _validate_optional_bool(payload: dict, key: str) -> bool | None:
    raw_value = payload.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, bool):
        raise ValueError(f"Config '{key}' debe ser booleano.")
    return raw_value


def _validate_optional_str(payload: dict, key: str) -> str | None:
    raw_value = payload.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise ValueError(f"Config '{key}' debe ser string.")
    normalized = raw_value.strip()
    return normalized or None
