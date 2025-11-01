import json

import pytest

from equitrcoder.core.clean_orchestrator import CleanOrchestrator


@pytest.mark.asyncio
async def test_clean_orchestrator_retries_on_invalid_json(monkeypatch, tmp_path):
    orchestrator = CleanOrchestrator(model="openai/gpt-4")

    # Fake todo manager to avoid coupling to real TodoManager internals
    class FakeManager:
        def __init__(self):
            self.groups = {}
            self.todos = {}

        def create_task_group(
            self, group_id, specialization, description, dependencies
        ):
            self.groups[group_id] = {
                "specialization": specialization,
                "description": description,
                "dependencies": dependencies,
            }

        def add_todo_to_group(self, group_id, title):
            self.todos.setdefault(group_id, []).append(title)

        def get_task_group(self, group_id):
            return None

    fake = FakeManager()
    # Patch get_todo_manager and set_global_todo_file to isolate file writes
    import equitrcoder.tools.builtin.todo as todo_mod

    monkeypatch.setattr(todo_mod, "get_todo_manager", lambda: fake, raising=False)
    monkeypatch.setattr(
        todo_mod, "set_global_todo_file", lambda path: None, raising=False
    )

    # Monkeypatch provider.chat to return invalid JSON twice, then valid JSON list
    class Resp:
        def __init__(self, content):
            self.content = content
            self.tool_calls = []
            self.usage = {}
            self.cost = 0.0

    call_count = {"n": 0}

    async def fake_chat(messages=None, tools=None, **kwargs):
        call_count["n"] += 1
        if call_count["n"] in (1, 2):
            return Resp("not json")
        return Resp(
            json.dumps(
                [
                    {
                        "group_id": "grp1",
                        "specialization": "default",
                        "description": "",
                        "dependencies": [],
                    }
                ]
            )
        )

    async def fake_chat_stage2(messages=None, tools=None, **kwargs):
        return Resp(json.dumps([{"title": "Do thing"}]))

    # Patch provider.chat with a dispatcher that accepts both positional and keyword args
    from equitrcoder.providers import litellm as _litellm

    async def dispatcher(*args, **kwargs):
        messages = kwargs.get("messages")
        if messages is None and args:
            # Our provider passes messages positionally as first arg sometimes
            messages = args[0]
        if not messages:
            return Resp("")
        first = messages[0]
        content = (
            first.get("content", "")
            if isinstance(first, dict)
            else getattr(first, "content", "")
        )
        if "project manager" in content.lower():
            return await fake_chat(messages=messages, tools=kwargs.get("tools"))
        else:
            return await fake_chat_stage2(messages=messages, tools=kwargs.get("tools"))

    monkeypatch.setattr(_litellm.LiteLLMProvider, "chat", dispatcher, raising=True)

    result = await orchestrator.create_docs(
        task_description="Build something", project_path=str(tmp_path)
    )

    assert result["success"] is True
    assert result["requirements_path"].endswith("requirements.md")
    assert result["design_path"].endswith("design.md")
    assert result["todos_path"].endswith("todos.json")
