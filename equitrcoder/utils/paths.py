"""Utilities for resolving EQUITR Coder configuration and extension paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

PROJECT_CONFIG_DIR = ".equitr"
ENV_HOME = "EQUITR_HOME"
ENV_EXTENSION_ROOT = "EQUITR_EXTENSIONS_DIR"
ENV_EXTENSION_MAP = {
    "tools": "EQUITR_TOOLS_PATH",
    "profiles": "EQUITR_PROFILES_PATH",
    "modes": "EQUITR_MODES_PATH",
    "mcp": "EQUITR_MCP_PATH",
}

PACKAGE_DEFAULTS = {
    "tools": Path(__file__).resolve().parents[1] / "tools" / "custom",
    "profiles": Path(__file__).resolve().parents[1] / "profiles",
    "modes": Path(__file__).resolve().parents[1] / "modes",
    "mcp": Path(__file__).resolve().parents[1] / "config",
}


def _split_env_paths(value: str) -> List[Path]:
    """Split an os.pathsep-delimited string into a list of Paths."""

    return [Path(part).expanduser() for part in value.split(os.pathsep) if part]


def get_equitr_home(create: bool = False) -> Path:
    """
    Resolve the EQUITR home directory.

    Precedence:
        1. ``EQUITR_HOME`` environment variable
        2. Default ``~/.EQUITR-coder`` directory
    """

    env_value = os.getenv(ENV_HOME)
    base = (
        Path(env_value).expanduser()
        if env_value
        else Path("~/.EQUITR-coder").expanduser()
    )
    if create:
        base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def get_user_extensions_root(create: bool = False) -> Path:
    """
    Return the primary user extensions root directory.

    If ``EQUITR_EXTENSIONS_DIR`` is provided, the first entry is returned.
    Otherwise ``<equitr_home>/extensions`` is used.
    """

    env_value = os.getenv(ENV_EXTENSION_ROOT)
    if env_value:
        candidates = _split_env_paths(env_value)
        if candidates:
            root = candidates[0].resolve()
            if create:
                root.mkdir(parents=True, exist_ok=True)
            return root

    default_root = get_equitr_home(create=create) / "extensions"
    if create:
        default_root.mkdir(parents=True, exist_ok=True)
    return default_root.resolve()


def get_project_config_dir(project_root: Optional[Path | str] = None) -> Optional[Path]:
    """
    Return the project-level configuration directory (``.equitr``) if it exists.
    """

    if project_root is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_root)

    candidate = (project_path / PROJECT_CONFIG_DIR).resolve()
    return candidate if candidate.exists() and candidate.is_dir() else None


def _resolve_template(template: str, home: Path, project_root: Optional[Path]) -> Path:
    """Resolve a path template replacing ``{home}`` and ``{project}`` placeholders."""

    value = template
    placeholders = {
        "{home}": str(home),
        "{project}": str(project_root) if project_root else "",
    }

    for placeholder, replacement in placeholders.items():
        value = value.replace(placeholder, replacement)

    expanded = os.path.expanduser(os.path.expandvars(value))
    return Path(expanded)


def get_extension_search_paths(
    kind: str,
    configured_paths: Optional[Iterable[str]] = None,
    project_root: Optional[Path | str] = None,
    *,
    include_package_defaults: bool = True,
    include_nonexistent: bool = False,
) -> List[Path]:
    """
    Compute search paths for a given extension kind.

    Args:
        kind: Extension category ("tools", "profiles", "modes", "mcp", ...).
        configured_paths: Optional iterable of path templates from configuration.
        project_root: Optional project directory used to resolve ``{project}``.
        include_package_defaults: Whether to append packaged defaults.
        include_nonexistent: Whether to include paths that do not yet exist.

    Returns:
        Ordered list of unique Paths respecting precedence:
        environment overrides → project → configured templates → package defaults.
    """

    normalized_kind = kind.lower()
    paths: List[Path] = []

    def add_candidate(path: Path) -> None:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            resolved = path
        if not include_nonexistent and not resolved.exists():
            return
        if resolved not in paths:
            paths.append(resolved)

    home_dir = get_equitr_home()
    project_path = Path(project_root).resolve() if project_root else None

    # Environment-specific override (highest precedence)
    env_var = ENV_EXTENSION_MAP.get(normalized_kind)
    if env_var:
        env_value = os.getenv(env_var)
        if env_value:
            for candidate in _split_env_paths(env_value):
                add_candidate(candidate)

    # Environment-provided extension roots
    env_root_value = os.getenv(ENV_EXTENSION_ROOT)
    if env_root_value:
        for root in _split_env_paths(env_root_value):
            add_candidate(root / normalized_kind)

    # Project-level configuration directory
    project_config_dir = get_project_config_dir(project_path) if project_path else None
    if project_config_dir:
        add_candidate(project_config_dir / normalized_kind)

    # Configured templates
    for template in configured_paths or []:
        if not template:
            continue
        candidate = _resolve_template(template, home_dir, project_path)
        add_candidate(candidate)

    # User extensions root fallback
    user_root = get_user_extensions_root()
    add_candidate(user_root / normalized_kind)

    if include_package_defaults:
        default_path = PACKAGE_DEFAULTS.get(normalized_kind)
        if default_path is not None:
            add_candidate(default_path)

    return paths


__all__ = [
    "get_equitr_home",
    "get_project_config_dir",
    "get_user_extensions_root",
    "get_extension_search_paths",
]
