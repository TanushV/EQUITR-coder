import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import List, Type

from .base import Tool, registry
from .mcp.config import load_mcp_config
from .mcp.dynamic_tools import MCPToolProxy

logger = logging.getLogger(__name__)


class ToolDiscovery:
    """Discovers and loads tools from various sources."""

    def __init__(self):
        self.loaded_modules = set()

    def discover_builtin_tools(self):
        """Discover and load built-in tools."""
        builtin_path = Path(__file__).parent / "builtin"
        self._discover_tools_in_package("equitrcoder.tools.builtin", builtin_path)

    def discover_custom_tools(self):
        """Discover and load custom tools."""
        custom_path = Path(__file__).parent / "custom"
        if custom_path.exists():
            self._discover_tools_in_package("equitrcoder.tools.custom", custom_path)

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

                    # Find Tool classes in the module
                    tools = self._extract_tools_from_module(module)
                    for tool_class in tools:
                        # Skip tools that require parameters for instantiation
                        if self._tool_requires_parameters(tool_class):
                            logger.info(
                                f"Skipping tool {tool_class.__name__} (requires parameters)"
                            )
                            continue

                        tool_instance = tool_class()
                        registry.register(tool_instance)
                        logger.info(f"Registered tool: {tool_instance.name}")

                except Exception as e:
                    logger.warning(f"Failed to load tool module {modname}: {e}")

        except ImportError as e:
            logger.warning(f"Failed to import package {package_name}: {e}")

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

    def reload_tools(self):
        """Reload all tools."""
        # Clear registry
        registry._tools.clear()
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
