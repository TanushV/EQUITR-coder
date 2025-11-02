"""Dynamic mode loader for EQUITR Coder."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import logging
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from ..core.unified_config import get_config_manager
from ..utils.paths import get_extension_search_paths

logger = logging.getLogger(__name__)

ModeCallable = Callable[..., Awaitable[Dict[str, Any]]]


@dataclass
class ModeEntry:
    """Metadata for a registered mode."""

    name: str
    callable: ModeCallable
    source: str
    description: Optional[str] = None


class ModeLoader:
    """Discovers and loads mode entrypoints from built-in and extension sources."""

    def __init__(self):
        self._config_manager = get_config_manager()
        self._registry: Dict[str, ModeEntry] = {}
        self._loaded_modules: set[str] = set()
        self._module_prefix = "equitrcoder_ext.modes"
        self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        """Reload available modes from all sources."""

        self._registry.clear()
        for module_name in list(self._loaded_modules):
            if module_name.startswith(self._module_prefix):
                sys.modules.pop(module_name, None)
        self._loaded_modules.clear()

        self._discover_builtin_modes()
        self._discover_extension_modes()

    def list_modes(self) -> Dict[str, ModeEntry]:
        """Return registered modes keyed by their primary name."""

        return {
            name: entry for name, entry in self._registry.items() if entry.name == name
        }

    def get_mode(self, name: str) -> Optional[ModeEntry]:
        """Retrieve a mode entry by name or alias."""

        return self._registry.get(name)

    def register_mode(
        self,
        name: str,
        func: ModeCallable,
        source: str,
        description: Optional[str] = None,
        aliases: Optional[Iterable[str]] = None,
    ) -> ModeEntry:
        entry = ModeEntry(
            name=name, callable=func, source=source, description=description
        )

        existing = self._registry.get(name)
        if existing:
            logger.info(
                "Overriding mode '%s' from %s with %s",
                name,
                existing.source,
                source,
            )

        self._registry[name] = entry

        for alias in aliases or []:
            alias_existing = self._registry.get(alias)
            if alias_existing and alias_existing is not entry:
                logger.info(
                    "Overriding mode alias '%s' from %s with %s",
                    alias,
                    alias_existing.source,
                    source,
                )
            self._registry[alias] = entry

        return entry

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    def _discover_builtin_modes(self) -> None:
        specs = [
            (
                "single",
                "equitrcoder.modes.single_agent_mode",
                "run_single_agent_mode",
                "Single agent execution mode",
                ["single_agent"],
            ),
            (
                "multi_parallel",
                "equitrcoder.modes.multi_agent_mode",
                "run_multi_agent_parallel",
                "Multi-agent parallel execution",
                ["multi", "multi_agent_parallel"],
            ),
            (
                "multi_sequential",
                "equitrcoder.modes.multi_agent_mode",
                "run_multi_agent_sequential",
                "Multi-agent sequential execution",
                ["multi_agent_sequential"],
            ),
            (
                "research",
                "equitrcoder.modes.researcher_mode",
                "run_researcher_mode",
                "Research coordination mode",
                ["researcher"],
            ),
        ]

        for name, module_path, attr, description, aliases in specs:
            func = self._resolve_callable(module_path, attr)
            if func:
                self.register_mode(name, func, module_path, description, aliases)

    def _discover_extension_modes(self) -> None:
        config = self._config_manager.get_cached_config()
        configured_entries: List[str] = []
        if isinstance(config.extensions, dict):
            configured_entries.extend(config.extensions.get("modes", []) or [])

        module_specs: List[str] = []
        path_templates: List[str] = []
        for entry in configured_entries:
            if isinstance(entry, str) and entry.startswith("module:"):
                module_specs.append(entry[len("module:") :])
            else:
                path_templates.append(entry)

        for spec in module_specs:
            self._load_mode_from_spec(spec)

        for path in get_extension_search_paths(
            "modes",
            configured_paths=path_templates,
            project_root=Path.cwd(),
        ):
            candidate = Path(path)
            if not candidate.exists():
                continue
            if candidate.is_dir():
                self._load_modes_from_directory(candidate)
            elif candidate.suffix == ".py":
                module = self._load_module_from_file(candidate)
                if module:
                    self._register_modes_from_module(module)

    def _load_mode_from_spec(self, spec: str) -> None:
        module_path, sep, attr = spec.partition(":")
        if not sep:
            logger.warning(
                "Mode spec '%s' is missing an attribute (expected 'module:callable')",
                spec,
            )
            return

        func = self._resolve_callable(module_path, attr)
        if func:
            description = getattr(func, "__doc__", None)
            mode_name = getattr(func, "__mode_name__", attr)
            self.register_mode(mode_name, func, module_path, description)

    def _load_modes_from_directory(self, directory: Path) -> None:
        if (directory / "__init__.py").is_file():
            package_name = self._module_name_for_path(directory)
            module = self._load_module_from_spec_file(
                package_name, directory / "__init__.py", [str(directory)]
            )
            if module:
                self._register_modes_from_module(module)
                for finder, name, _ in pkgutil.walk_packages(
                    [str(directory)], package_name + "."
                ):
                    if name in self._loaded_modules:
                        continue
                    try:
                        submodule = importlib.import_module(name)
                        self._loaded_modules.add(name)
                        self._register_modes_from_module(submodule)
                    except Exception as exc:
                        logger.warning(
                            "Failed to import mode submodule %s: %s", name, exc
                        )
            return

        for entry in sorted(directory.iterdir()):
            if entry.is_dir():
                self._load_modes_from_directory(entry)
            elif entry.suffix == ".py":
                module = self._load_module_from_file(entry)
                if module:
                    self._register_modes_from_module(module)

    def _register_modes_from_module(self, module) -> None:
        registry = getattr(module, "MODE_REGISTRY", None)
        if isinstance(registry, dict):
            for name, func in registry.items():
                if callable(func):
                    description = getattr(func, "__doc__", None)
                    self.register_mode(name, func, module.__name__, description)

        for attr_name in dir(module):
            if not attr_name.startswith("run_"):
                continue
            func = getattr(module, attr_name)
            if callable(func):
                mode_name = getattr(func, "__mode_name__", attr_name[4:])
                description = getattr(func, "__doc__", None)
                self.register_mode(mode_name, func, module.__name__, description)

    # ------------------------------------------------------------------
    # Module loading helpers
    # ------------------------------------------------------------------
    def _resolve_callable(self, module_path: str, attr: str) -> Optional[ModeCallable]:
        try:
            module = importlib.import_module(module_path)
            target = getattr(module, attr)
            if callable(target):
                return target
            logger.warning(
                "Attribute '%s' in module '%s' is not callable", attr, module_path
            )
        except Exception as exc:
            logger.warning(
                "Failed to import mode callable %s:%s - %s", module_path, attr, exc
            )
        return None

    def _module_name_for_path(self, path: Path) -> str:
        resolved = str(path.resolve())
        digest = hashlib.md5(resolved.encode("utf-8")).hexdigest()
        stem = path.stem if path.is_file() else path.name or "ext"
        return f"{self._module_prefix}.{stem}_{digest}"

    def _load_module_from_file(self, file_path: Path) -> Optional[Any]:
        module_name = self._module_name_for_path(file_path)
        return self._load_module_from_spec_file(module_name, file_path)

    def _load_module_from_spec_file(
        self,
        module_name: str,
        file_path: Path,
        search_locations: Optional[List[str]] = None,
    ) -> Optional[Any]:
        if module_name in self._loaded_modules:
            return sys.modules.get(module_name)

        spec = importlib.util.spec_from_file_location(
            module_name,
            file_path,
            submodule_search_locations=search_locations,
        )
        if spec is None or spec.loader is None:
            logger.warning("Unable to create module spec for %s", file_path)
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            self._loaded_modules.add(module_name)
            return module
        except Exception as exc:
            logger.warning("Failed to load mode module %s: %s", file_path, exc)
            sys.modules.pop(module_name, None)
            return None


# Global loader instance
mode_loader = ModeLoader()


def get_available_modes() -> Dict[str, ModeEntry]:
    """Return a mapping of available mode entries keyed by name."""

    return mode_loader.list_modes()


def get_mode_callable(name: str) -> Optional[ModeCallable]:
    """Return a callable for a mode by name or alias."""

    entry = mode_loader.get_mode(name)
    return entry.callable if entry else None
