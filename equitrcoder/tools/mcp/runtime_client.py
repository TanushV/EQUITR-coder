"""
Runtime utilities to connect to MCP servers based on configuration.

Currently supports the 'stdio' transport using the official MCP Python SDK.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Tuple

try:
    from mcp import types as mcp_types
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    HAS_MCP = True
except Exception:  # pragma: no cover - optional dependency
    HAS_MCP = False

from .config import MCPServerConfig

logger = logging.getLogger(__name__)


@asynccontextmanager
async def connect_stdio(
    server: MCPServerConfig,
) -> AsyncIterator[Tuple[ClientSession, any, any]]:
    """Connect to an MCP server over stdio.

    Yields a tuple (session, read, write). Caller is responsible for using
    the session and closing the context manager.
    """

    if not HAS_MCP:
        raise RuntimeError(
            "MCP Python SDK not installed. Please install 'modelcontextprotocol' (python-sdk)."
        )

    env: Dict[str, str] = dict(os.environ)
    env.update(server.env or {})

    params = StdioServerParameters(
        command=server.command, args=list(server.args or []), env=env
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session, read, write


async def list_server_tools(session: "ClientSession") -> Dict[str, mcp_types.Tool]:
    tools = await session.list_tools()
    return {t.name: t for t in tools.tools}


async def call_server_tool(
    session: "ClientSession", tool_name: str, arguments: Dict
) -> mcp_types.CallToolResult:
    return await session.call_tool(tool_name, arguments or {})
