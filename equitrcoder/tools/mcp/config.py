"""
MCP servers configuration loader and models.

This module defines Pydantic models for MCP server configuration and
provides helper functions to locate and load a JSON config file that
declares external MCP servers to connect to.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server instance."""

    command: str = Field(..., description="Executable to launch the MCP server")
    args: List[str] = Field(
        default_factory=list, description="Arguments for the server command"
    )
    env: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables for the server process"
    )
    transport: str = Field(
        default="stdio",
        description="Transport type for MCP connection (supported: 'stdio').",
    )
    # Future extension for SSE/HTTP transports
    url: Optional[str] = Field(
        default=None,
        description="Optional URL for non-stdio transports (e.g., SSE). Not used for 'stdio'.",
    )


class MCPServersFile(BaseModel):
    """Top-level configuration file mapping server names to configs.

    The structure follows common MCP client configurations as seen in the
    Model Context Protocol Python SDK examples.
    """

    mcpServers: Dict[str, MCPServerConfig] = Field(default_factory=dict)


def _candidate_paths() -> List[Path]:
    """Return candidate paths (in priority order) for the MCP servers config."""

    env_path = os.getenv("EQUITR_MCP_SERVERS")
    candidates: List[Path] = []
    if env_path:
        candidates.append(Path(env_path).expanduser())

    # User-level config (align with other EQUITR paths using capitalized folder)
    candidates.append(Path("~/.EQUITR-coder/mcp_servers.json").expanduser())

    # Project packaged default
    packaged_default = (
        Path(__file__).resolve().parents[2] / "config" / "mcp_servers.json"
    )
    candidates.append(packaged_default)

    return candidates


def find_mcp_config_path() -> Optional[Path]:
    """Find the first existing MCP servers config file path, if any."""

    for p in _candidate_paths():
        if p.exists() and p.is_file():
            return p
    return None


def load_mcp_config() -> Tuple[Optional[MCPServersFile], Optional[Path], Optional[str]]:
    """Load MCP servers configuration from JSON.

    Returns:
        A tuple of (config_object, path_used, error_message). If loading or validation
        fails, config_object will be None and error_message will contain details.
    """

    path = find_mcp_config_path()
    if path is None:
        return None, None, None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover - filesystem errors vary by env
        return None, path, f"Failed to read MCP config JSON: {e}"

    try:
        cfg = MCPServersFile.model_validate(raw)
        return cfg, path, None
    except ValidationError as ve:
        return None, path, f"Invalid MCP servers config: {ve}"
