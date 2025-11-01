import json

import pytest

from equitrcoder.tools.base import Tool, ToolResult
from equitrcoder.tools.builtin.ask_supervisor import AskSupervisor


class DummyReadFile(Tool):
    def get_name(self):
        return "read_file"

    def get_description(self):
        return "Read file"

    def get_args_schema(self):
        from pydantic import BaseModel, Field

        class Args(BaseModel):
            path: str = Field(...)

        return Args

    async def run(self, **kwargs) -> ToolResult:
        # Return a minimal payload similar to builtin ReadFile
        return ToolResult(
            success=True, data={"path": kwargs.get("path"), "content": "dummy"}
        )


class _ToolCallLike:
    def __init__(self, function: dict):
        self.function = function


class _Resp:
    def __init__(self, content: str = "", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage = {}
        self.cost = 0.0


class FakeProvider:
    def __init__(self):
        self.calls = 0

    async def chat(self, messages, tools=None, **kwargs):
        self.calls += 1
        # First iteration: request a read_file tool call
        if self.calls == 1:
            return _Resp(
                content="",
                tool_calls=[
                    _ToolCallLike(
                        {
                            "name": "read_file",
                            "arguments": json.dumps({"path": "README.md"}),
                        }
                    )
                ],
            )
        # Second iteration: return final content (no tool calls)
        return _Resp(content="Final advisory answer")


@pytest.mark.asyncio
async def test_ask_supervisor_audit_style_loop_with_docs_and_tools(monkeypatch):
    # Patch discover_tools used by AskSupervisor.run to return our dummy read_file
    import importlib

    discovery_mod = importlib.import_module("equitrcoder.tools.discovery")
    monkeypatch.setattr(
        discovery_mod, "discover_tools", lambda: [DummyReadFile()], raising=True
    )

    # Instantiate AskSupervisor with a fake provider and docs_context
    provider = FakeProvider()
    tool = AskSupervisor(
        provider=provider,
        docs_context={
            "requirements_content": "REQS",
            "design_content": "DESIGN",
            "docs_dir": "docs/task_123",
            "todos_path": "docs/task_123/todos.json",
        },
    )

    result = await tool.run(
        question="How should I proceed?",
        include_repo_tree=False,
        include_git_status=False,
    )

    assert result.success is True
    assert isinstance(result.data, str)
    assert "Final advisory answer" in result.data
    # Ensure at least two provider calls (one tool call, one final answer)
    assert provider.calls >= 2
