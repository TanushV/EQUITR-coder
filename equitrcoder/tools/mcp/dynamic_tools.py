"""
Dynamic Tool wrappers for MCP servers configured via JSON.

This module exposes a generic `MCPToolProxy` that maps a remote MCP tool
to the local Tool interface, performing a connect-call-disconnect flow
on each invocation for simplicity and robustness.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Type

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .config import MCPServerConfig
from .runtime_client import call_server_tool, connect_stdio

logger = logging.getLogger(__name__)


class _ArgsSchema(BaseModel):
    tool: str = Field(..., description="Remote MCP tool name to call")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the remote tool"
    )


class MCPToolProxy(Tool):
    """A generic proxy that calls a specific MCP server's tools."""

    def __init__(self, server_name: str, server_cfg: MCPServerConfig):
        self._server_name = server_name
        self._server_cfg = server_cfg
        super().__init__()

    def get_name(self) -> str:
        return f"mcp:{self._server_name}"

    def get_description(self) -> str:
        return (
            f"Call tools on MCP server '{self._server_name}'. "
            "Provide 'tool' and optional 'arguments'."
        )

    def get_args_schema(self) -> Type[BaseModel]:
        return _ArgsSchema

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            if self._server_cfg.transport != "stdio":
                return ToolResult(
                    success=False, error="Only 'stdio' transport is supported currently"
                )

            async with connect_stdio(self._server_cfg) as (session, _read, _write):
                result = await call_server_tool(session, args.tool, args.arguments)
                payload: Dict[str, Any] = {"structuredContent": None, "content": []}
                if getattr(result, "structuredContent", None):
                    payload["structuredContent"] = result.structuredContent
                if getattr(result, "content", None):
                    try:
                        payload["content"] = [c.model_dump() for c in result.content]  # type: ignore[attr-defined]
                    except Exception:
                        payload["content"] = []

                return ToolResult(success=True, data=payload)

        except Exception as e:
            logger.exception("MCP tool proxy call failed")
            return ToolResult(success=False, error=str(e))
