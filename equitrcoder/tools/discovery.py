import hashlib
import importlib
import importlib.util
import inspect
import logging
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, List, Optional, Type

from ..core.unified_config import get_config_manager
from ..utils.paths import get_extension_search_paths
from .base import Tool, registry
from .mcp.config import load_mcp_config
from .mcp.dynamic_tools import MCPToolProxy

logger = logging.getLogger(__name__)


class ToolDiscovery:
    """Discovers and loads tools from various sources."""

    def __init__(self):
        self.loaded_modules = set()
        self._config_manager = get_config_manager()
        self._external_prefix = "equitrcoder_ext"

    def discover_builtin_tools(self):
        """Discover and load built-in tools."""
        builtin_path = Path(__file__).parent / "builtin"
        self._discover_tools_in_package("equitrcoder.tools.builtin", builtin_path)

    def discover_custom_tools(self):
        """Discover and load custom tools from packaged and extension directories."""

        custom_package = (Path(__file__).parent / "custom").resolve()
        seen_custom_package = False

        for path in self._get_extension_paths("tools"):
            try:
                resolved = path.resolve()
            except FileNotFoundError:
                resolved = path

            if resolved == custom_package:
                if not seen_custom_package:
                    self._discover_tools_in_package(
                        "equitrcoder.tools.custom", custom_package
                    )
                    seen_custom_package = True
                continue

            self._discover_tools_in_external_source(resolved)

        if not seen_custom_package and custom_package.exists():
            self._discover_tools_in_package("equitrcoder.tools.custom", custom_package)

    def discover_mcp_tools(self):
        """Discover and load MCP server tools.

        Two sources are used:
        1) Static modules under equitrcoder.tools.mcp (if any) for built-ins
        2) Dynamic proxies created from JSON config (mcp_servers.json)
        """
        mcp_path = Path(__file__).parent / "mcp"
        if mcp_path.exists():
            self._discover_tools_in_package("equitrcoder.tools.mcp", mcp_path)

        # Load dynamic servers from JSON config
        cfg, path, err = load_mcp_config()
        if err:
            logger.warning(f"Failed to load MCP servers config ({path}): {err}")
            return
        if not cfg or not cfg.mcpServers:
            return

        for server_name, server_cfg in cfg.mcpServers.items():
            try:
                proxy = MCPToolProxy(server_name, server_cfg)
                registry.register(proxy)
                logger.info(f"Registered MCP server proxy tool: {proxy.name}")
            except Exception as e:
                logger.warning(f"Failed to register MCP server '{server_name}': {e}")

    def _discover_tools_in_package(self, package_name: str, package_path: Path):
        """Discover tools in a specific package."""
        if not package_path.exists():
            return

        try:
            # Import the package
            package = importlib.import_module(package_name)

            # Walk through all modules in the package
            for importer, modname, ispkg in pkgutil.iter_modules(
                package.__path__, package_name + "."
            ):
                if modname in self.loaded_modules:
                    continue

                try:
                    module = importlib.import_module(modname)
                    self.loaded_modules.add(modname)
                    self._register_tools_from_module(module)

                except Exception as e:
                    logger.warning(f"Failed to load tool module {modname}: {e}")

        except ImportError as e:
            logger.warning(f"Failed to import package {package_name}: {e}")

    def _discover_tools_in_external_source(self, path: Path) -> None:
        """Load tools from an arbitrary file or directory."""

        if not path.exists():
            return

        if path.is_dir():
            self._discover_tools_in_directory(path, f"{self._external_prefix}.tools")
        elif path.suffix == ".py":
            module = self._load_module_from_file(path, f"{self._external_prefix}.tools")
            if module:
                self._register_tools_from_module(module)

    def _discover_tools_in_directory(self, directory: Path, prefix: str) -> None:
        if (directory / "__init__.py").is_file():
            module_name = self._load_package_from_directory(directory, prefix)
            if module_name:
                self._discover_tools_in_package(module_name, directory)
            return

        for entry in sorted(directory.iterdir()):
            if entry.name.startswith("__"):
                continue
            if entry.is_dir():
                self._discover_tools_in_directory(entry, f"{prefix}.{entry.name}")
            elif entry.suffix == ".py":
                module = self._load_module_from_file(entry, prefix)
                if module:
                    self._register_tools_from_module(module)

    def _extract_tools_from_module(self, module) -> List[Type[Tool]]:
        """Extract Tool classes from a module."""
        tools = []

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Tool)
                and obj is not Tool
                and not inspect.isabstract(obj)
            ):
                tools.append(obj)

        return tools

    def _tool_requires_parameters(self, tool_class: Type[Tool]) -> bool:
        """Check if a tool class requires parameters for instantiation."""
        try:
            # Get the __init__ method signature
            init_signature = inspect.signature(tool_class.__init__)

            # Check if there are required parameters (excluding 'self')
            for param_name, param in init_signature.parameters.items():
                if param_name != "self" and param.default == inspect.Parameter.empty:
                    return True

            return False
        except Exception:
            # If we can't inspect, assume it needs parameters to be safe
            return True

    def _register_tools_from_module(self, module: ModuleType) -> None:
        tools = self._extract_tools_from_module(module)
        for tool_class in tools:
            if self._tool_requires_parameters(tool_class):
                logger.info(
                    f"Skipping tool {tool_class.__name__} (requires parameters)"
                )
                continue

            try:
                tool_instance = tool_class()
            except Exception as exc:
                logger.warning(
                    f"Failed to instantiate tool {tool_class.__name__}: {exc}"
                )
                continue

            registry.register(tool_instance)
            logger.info(f"Registered tool: {tool_instance.name}")

    def _module_name_for_path(self, prefix: str, path: Path) -> str:
        resolved = str(path.resolve())
        digest = hashlib.md5(resolved.encode("utf-8")).hexdigest()
        stem = path.stem if path.is_file() else path.name or "ext"
        return f"{prefix}.{stem}_{digest}"

    def _load_module_from_file(
        self, file_path: Path, prefix: str
    ) -> Optional[ModuleType]:
        module_name = self._module_name_for_path(prefix, file_path)
        if module_name in self.loaded_modules:
            return sys.modules.get(module_name)

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Unable to create spec for tool module {file_path}")
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            self.loaded_modules.add(module_name)
            return module
        except Exception as exc:
            logger.warning(f"Failed to load tool module from {file_path}: {exc}")
            sys.modules.pop(module_name, None)
            return None

    def _load_package_from_directory(
        self, directory: Path, prefix: str
    ) -> Optional[str]:
        module_name = self._module_name_for_path(prefix, directory)
        if module_name in self.loaded_modules:
            return module_name

        init_file = directory / "__init__.py"
        if not init_file.exists():
            return None

        spec = importlib.util.spec_from_file_location(
            module_name,
            init_file,
            submodule_search_locations=[str(directory)],
        )
        if spec is None or spec.loader is None:
            logger.warning(f"Unable to create package spec for {directory}")
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            self.loaded_modules.add(module_name)
            return module_name
        except Exception as exc:
            logger.warning(f"Failed to load tool package from {directory}: {exc}")
            sys.modules.pop(module_name, None)
            return None

    def _get_extension_paths(self, kind: str) -> List[Path]:
        config = self._config_manager.get_cached_config()
        configured_paths: Iterable[str] = []
        if isinstance(config.extensions, dict):
            configured_paths = config.extensions.get(kind, []) or []

        return list(
            get_extension_search_paths(
                kind,
                configured_paths=configured_paths,
                project_root=Path.cwd(),
            )
        )

    def reload_tools(self):
        """Reload all tools."""
        # Clear registry
        registry._tools.clear()
        for module_name in list(self.loaded_modules):
            if module_name.startswith(self._external_prefix):
                sys.modules.pop(module_name, None)
        self.loaded_modules.clear()

        # Rediscover all tools
        self.discover_builtin_tools()
        self.discover_custom_tools()
        self.discover_mcp_tools()


# Global tool discovery instance
discovery = ToolDiscovery()


def discover_tools() -> List[Tool]:
    """
    Convenience function to discover and return all available tools.

    Returns:
        List of discovered Tool instances
    """
    # Discover all tools
    discovery.discover_builtin_tools()
    discovery.discover_custom_tools()
    discovery.discover_mcp_tools()

    # Return tools from registry
    return list(registry._tools.values())


def discover_builtin_tools():
    """Discover built-in tools."""
    discovery.discover_builtin_tools()


def discover_custom_tools():
    """Discover custom tools."""
    discovery.discover_custom_tools()


def discover_mcp_tools():
    """Discover MCP tools."""
    discovery.discover_mcp_tools()
