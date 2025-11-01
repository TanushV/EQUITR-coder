"""MCP server integration tools and utilities.

This package exposes dynamic tool wrappers for configured MCP servers.
Configuration is read from `~/.EQUITR-coder/mcp_servers.json` by default,
or from a path specified in `EQUITR_MCP_SERVERS`.
"""

from .config import (
    MCPServerConfig,
    MCPServersFile,
    load_mcp_config,
    find_mcp_config_path,
)

__all__ = [
    "MCPServerConfig",
    "MCPServersFile",
    "load_mcp_config",
    "find_mcp_config_path",
]
