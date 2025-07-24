from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional, List
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """Base class for all tools."""

    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.args_schema = self.get_args_schema()

    @abstractmethod
    def get_name(self) -> str:
        """Return the tool name."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return the tool description."""
        pass

    @abstractmethod
    def get_args_schema(self) -> Type[BaseModel]:
        """Return the Pydantic schema for tool arguments."""
        pass

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    def get_json_schema(self) -> Dict[str, Any]:
        """Get JSON schema for the tool arguments."""
        schema = self.args_schema.model_json_schema()
        return {
            "name": self.name,
            "description": self.description,
            "parameters": schema,
        }

    def validate_args(self, args: Dict[str, Any]) -> BaseModel:
        """Validate arguments against the schema."""
        return self.args_schema(**args)


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()

    def get_enabled_tools(self, enabled_names: List[str]) -> Dict[str, Tool]:
        """Get tools that are enabled."""
        return {
            name: tool for name, tool in self._tools.items() if name in enabled_names
        }

    def get_schemas(self, enabled_names: List[str] = None) -> List[Dict[str, Any]]:
        """Get JSON schemas for enabled tools."""
        if enabled_names is None:
            tools = self._tools.values()
        else:
            tools = [self._tools[name] for name in enabled_names if name in self._tools]

        return [tool.get_json_schema() for tool in tools]


# Global tool registry
registry = ToolRegistry()
