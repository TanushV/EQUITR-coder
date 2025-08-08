import asyncio
from typing import Any, Dict, List

import pytest

from equitrcoder.core.clean_agent import CleanAgent
from equitrcoder.tools.base import Tool, ToolResult


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
        return ToolResult(success=True, data={"path": kwargs.get("path"), "content": "dummy"})


class DummyListFiles(Tool):
    def get_name(self):
        return "list_files"

    def get_description(self):
        return "List files"

    def get_args_schema(self):
        from pydantic import BaseModel, Field

        class Args(BaseModel):
            path: str = Field(default=".")

        return Args

    async def run(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"files": []})


@pytest.mark.asyncio
async def test_clean_agent_audit_unconditional(monkeypatch):
    # Prepare agent with minimal tools
    tools = [DummyReadFile(), DummyListFiles()]

    # Monkeypatch provider chat to immediately return an AUDIT PASSED message
    class Resp:
        def __init__(self):
            self.content = "AUDIT PASSED - ok"
            self.tool = None
            self.tool_calls = []
            self.usage = {}
            self.cost = 0.0

    async def fake_chat(*args, **kwargs):
        return Resp()

    # Patch both main and audit providers used by CleanAgent
    from equitrcoder import core as _core
    from equitrcoder.providers import litellm as _litellm

    monkeypatch.setattr(_litellm.LiteLLMProvider, "chat", fake_chat, raising=True)

    agent = CleanAgent(
        agent_id="test_agent",
        model="openai/gpt-4",
        tools=tools,
        context={"requirements_content": "", "design_content": ""},
        audit_model="openai/gpt-4",
    )

    # Also patch the main run loop to short-circuit
    async def fake_exec_loop(self) -> Dict[str, Any]:
        return {"success": True, "reason": "done", "final_message": ""}

    monkeypatch.setattr(CleanAgent, "_execution_loop", fake_exec_loop, raising=True)

    result = await agent.run("do work")

    assert result["success"] is True
    assert "audit_result" in result
    assert result["audit_result"]["success"] is True
    assert result["audit_result"]["audit_passed"] is True


@pytest.mark.asyncio
async def test_clean_agent_audit_includes_git_if_available(monkeypatch):
    # Provide tools including git_status and git_diff
    class DummyGitStatus(Tool):
        def get_name(self):
            return "git_status"

        def get_description(self):
            return "git status"

        def get_args_schema(self):
            from pydantic import BaseModel

            class Args(BaseModel):
                pass

            return Args

        async def run(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, data={"clean": True})

    class DummyGitDiff(Tool):
        def get_name(self):
            return "git_diff"

        def get_description(self):
            return "git diff"

        def get_args_schema(self):
            from pydantic import BaseModel

            class Args(BaseModel):
                pass

            return Args

        async def run(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, data={"diff": ""})

    tools = [DummyReadFile(), DummyListFiles(), DummyGitStatus(), DummyGitDiff()]

    # Intercept the audit provider tool schema argument to assert presence
    captured_tools: List[Dict[str, Any]] = []

    class Resp:
        def __init__(self):
            self.content = "AUDIT PASSED - ok"
            self.tool = None
            self.tool_calls = []
            self.usage = {}
            self.cost = 0.0

    async def fake_chat(*args, **kwargs):
        # tools kw contains tool schemas
        if "tools" in kwargs and kwargs["tools"]:
            captured_tools.extend(kwargs["tools"])
        return Resp()

    from equitrcoder.providers import litellm as _litellm
    monkeypatch.setattr(_litellm.LiteLLMProvider, "chat", fake_chat, raising=True)

    agent = CleanAgent(
        agent_id="test_agent",
        model="openai/gpt-4",
        tools=tools,
        context={},
        audit_model="openai/gpt-4",
    )

    async def fake_exec_loop(self) -> Dict[str, Any]:
        return {"success": True, "reason": "done", "final_message": ""}

    monkeypatch.setattr(CleanAgent, "_execution_loop", fake_exec_loop, raising=True)

    _ = await agent.run("do work")

    # Ensure git tools were included in audit tool schemas
    names = {t.get("function", {}).get("name") or t.get("name") for t in captured_tools}
    assert {"read_file", "list_files"}.issubset(names)
    assert {"git_status", "git_diff"}.issubset(names) 