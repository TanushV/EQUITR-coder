import os
import json
import shutil
from pathlib import Path

import pytest


from equitrcoder.tools.custom.audit_tests import (
    CreateGroupTests,
    ListGroupTests,
    GetGroupTestStatuses,
    MarkDefectiveTests,
    RemoveDefectiveTests,
)
from equitrcoder.tools.base import ToolResult
from equitrcoder.agents.audit_agent import AuditAgent
from equitrcoder.tools.builtin.todo import set_global_todo_file
from equitrcoder.providers.litellm import ChatResponse


@pytest.fixture(autouse=True)
def _ensure_clean_env(tmp_path):
    # Ensure auth token fallback is accepted for dev
    os.environ.pop("EQUITR_AUDIT_TOKEN", None)
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    yield
    # Cleanup artifacts created by tests where feasible
    shutil.rmtree(Path("tests") / "audit", ignore_errors=True)
    shutil.rmtree(Path("audits"), ignore_errors=True)


def test_audit_tools_create_list_and_mark_remove_defective(tmp_path):
    src_file = Path("equitrcoder") / "tools" / "base.py"
    assert src_file.exists(), "Expected source file exists for test generation"

    # Create tests for demo group using DEV_ALLOW fallback
    create_tool = CreateGroupTests()
    res = _run_async(create_tool.run, group_id="demo", section_paths=[str(src_file)], auth_token="DEV_ALLOW", overwrite=True)
    # NOTE: pytest.run for async helper (defined below)
    assert isinstance(res, ToolResult) and res.success
    assert res.data and res.data.get("total", 0) >= 1

    # List created tests
    list_tool = ListGroupTests()
    res_list = _run_async(list_tool.run, group_id="demo")
    assert res_list.success
    tests = res_list.data.get("tests", [])
    assert any(t.get("path", "").endswith("test_base.py") for t in tests)

    # Mark as defective
    mark_tool = MarkDefectiveTests()
    res_mark = _run_async(mark_tool.run, group_id="demo", test_patterns_or_paths=["test_base.py"], auth_token="DEV_ALLOW")
    assert res_mark.success
    assert any("test_base.py" in p for p in res_mark.data.get("marked_defective", []))

    # Remove defective
    remove_tool = RemoveDefectiveTests()
    res_rm = _run_async(remove_tool.run, group_id="demo", auth_token="DEV_ALLOW", remove_files=True)
    assert res_rm.success


def test_audit_agent_flow_generates_report_and_tests(tmp_path, monkeypatch):
    task_name = "test_session"
    docs_dir = Path("docs") / task_name
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "requirements.md").write_text("Reqs", encoding="utf-8")
    (docs_dir / "design.md").write_text("Design", encoding="utf-8")

    # Prepare a todo file with completed group
    todos_path = docs_dir / "todos.json"
    plan = {
        "task_name": task_name,
        "task_groups": [
            {
                "group_id": "demo",
                "specialization": "default",
                "description": "Demo group",
                "dependencies": [],
                "status": "completed",
                "todos": [],
            }
        ],
    }
    todos_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    set_global_todo_file(str(todos_path))

    # Sections mapping -> choose a stable python file
    sections_map = {"demo": ["equitrcoder/tools/base.py"]}
    sections_file = docs_dir / "group_sections.json"
    sections_file.write_text(json.dumps(sections_map, indent=2), encoding="utf-8")

    # Stub out LLM commentary to avoid network
    async def _fake_chat(self, messages, tools=None, temperature=None, max_tokens=None, **kwargs):
        return ChatResponse(content="OK", tool_calls=[], usage={}, cost=0.0)

    monkeypatch.setattr("equitrcoder.agents.audit_agent.LiteLLMProvider.chat", _fake_chat)

    agent = AuditAgent()
    result = _run_async(
        agent.run_audit_for_group,
        task_name=task_name,
        todo_file=str(todos_path),
        group_id="demo",
        auth_token="DEV_ALLOW",
        section_paths=None,
        sections_mapping_file=str(sections_file),
        docs_dir=str(docs_dir),
    )

    assert result.get("success"), f"Audit agent failed: {result}"
    audit_dir = Path("audits") / task_name / "group_demo"
    assert (audit_dir / "audit.md").exists()
    assert (Path("tests") / "audit" / "demo").exists()


# Helper: allow awaiting async tool/agent methods in sync pytest
def _await(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


def _run_async(async_fn, *args, **kwargs):
    return _await(async_fn(*args, **kwargs))


# No pytest hook needed; tests call _run_async directly.


