"""
Base Agent class providing common functionality for all agent types.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..core.session import SessionData
from ..tools.base import Tool
from ..tools.discovery import discover_tools


class BaseAgent:
    """Base class for all agents providing common functionality."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None,
        session: Optional[SessionData] = None,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        self.current_cost = 0.0
        self.iteration_count = 0

        # Initialize simple message storage
        self.messages: List[Dict[str, Any]] = []

        # Initialize session
        self.session = session

        # Initialize tool registry
        self.tool_registry: Dict[str, Tool] = {}
        self._setup_tools(tools or [])

        # Callbacks for monitoring
        self.on_message_callback: Optional[Callable] = None
        self.on_tool_call_callback: Optional[Callable] = None
        self.on_cost_update_callback: Optional[Callable] = None

    def _setup_tools(self, tools: List[Tool]):
        """Setup the tool registry with provided tools."""
        for tool in tools:
            self.tool_registry[tool.get_name()] = tool

    def add_tool(self, tool: Tool):
        """Add a tool to the agent's registry."""
        self.tool_registry[tool.get_name()] = tool

    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent's registry."""
        self.tool_registry.pop(tool_name, None)

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tool_registry.keys())

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a specific tool."""
        return tool_name in self.tool_registry

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a message to the agent's message pool."""
        message_data = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            **(metadata or {}),
        }

        self.messages.append(message_data)

        # Call callback if set
        if self.on_message_callback:
            self.on_message_callback(message_data)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from the agent's message storage."""
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit > 0 else []

    def update_cost(self, cost_delta: float):
        """Update the agent's cost tracking."""
        self.current_cost += cost_delta

        if self.on_cost_update_callback:
            self.on_cost_update_callback(self.current_cost, cost_delta)

    def check_limits(self) -> Dict[str, Any]:
        """Check if agent has exceeded any limits."""
        limits_status = {
            "cost_exceeded": False,
            "iterations_exceeded": False,
            "can_continue": True,
        }

        if self.max_cost and self.current_cost >= self.max_cost:
            limits_status["cost_exceeded"] = True
            limits_status["can_continue"] = False

        if self.max_iterations and self.iteration_count >= self.max_iterations:
            limits_status["iterations_exceeded"] = True
            limits_status["can_continue"] = False

        return limits_status

    def increment_iteration(self):
        """Increment the iteration counter."""
        self.iteration_count += 1

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "current_cost": self.current_cost,
            "max_cost": self.max_cost,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
            "available_tools": self.get_available_tools(),
            "message_count": len(self.get_messages()),
            "limits_status": self.check_limits(),
        }

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool by name with given arguments."""
        if not self.can_use_tool(tool_name):
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available to this agent",
            }

        tool = self.tool_registry[tool_name]

        try:
            # Call the tool
            result = await tool.run(**kwargs)

            # Log the tool call
            tool_call_data = {
                "tool_name": tool_name,
                "arguments": kwargs,
                "result": (
                    result.model_dump() if hasattr(result, "model_dump") else result
                ),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
            }

            if self.on_tool_call_callback:
                self.on_tool_call_callback(tool_call_data)

            return {"success": True, "result": result}

        except Exception as e:
            error_data = {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "arguments": kwargs,
            }

            if self.on_tool_call_callback:
                self.on_tool_call_callback(error_data)

            return error_data

    def reset(self):
        """Reset agent state (costs, iterations, messages)."""
        self.current_cost = 0.0
        self.iteration_count = 0
        self.messages = []

    def __repr__(self) -> str:
        return f"BaseAgent(id={self.agent_id}, tools={len(self.tool_registry)}, cost={self.current_cost})"
