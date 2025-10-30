from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..agents.audit_agent import AuditAgent
from ..tools.builtin.todo import get_todo_manager, set_global_todo_file


class AuditMonitor:
    """
    Watches a session-local todo plan and runs an audit whenever a task group
    transitions to 'completed'. Audits are scoped to that group's section(s).
    """

    def __init__(
        self,
        *,
        todo_file: str,
        task_name: str,
        auth_token: str,
        sections_mapping_file: Optional[str] = None,
        poll_interval: float = 10.0,
    ):
        self.todo_file = Path(todo_file)
        self.task_name = task_name
        self.auth_token = auth_token
        self.sections_mapping_file = sections_mapping_file
        self.poll_interval = poll_interval
        self._state_file = self.todo_file.with_suffix(self.todo_file.suffix + ".audit_state.json")

    def _load_state(self) -> Dict[str, str]:
        if self._state_file.exists():
            try:
                return json.loads(self._state_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_state(self, data: Dict[str, str]) -> None:
        try:
            self._state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    async def _detect_completed_transitions(self, prev: Dict[str, str]) -> List[str]:
        set_global_todo_file(str(self.todo_file))
        manager = get_todo_manager()
        completed: List[str] = []
        for group in manager.plan.task_groups:
            before = prev.get(group.group_id)
            after = group.status
            if before != "completed" and after == "completed":
                completed.append(group.group_id)
        return completed

    async def run_forever(self) -> None:
        state = self._load_state()
        while True:
            try:
                to_audit = await self._detect_completed_transitions(state)
                if to_audit:
                    for group_id in to_audit:
                        await self._run_single_audit(group_id)
                # Refresh state snapshot from live plan
                set_global_todo_file(str(self.todo_file))
                manager = get_todo_manager()
                state = {g.group_id: g.status for g in manager.plan.task_groups}
                self._save_state(state)
            except Exception:
                # Swallow to keep monitoring resilient
                pass
            await asyncio.sleep(self.poll_interval)

    async def _run_single_audit(self, group_id: str) -> None:
        agent = AuditAgent()
        await agent.run_audit_for_group(
            task_name=self.task_name,
            todo_file=str(self.todo_file),
            group_id=group_id,
            auth_token=self.auth_token,
            section_paths=None,
            sections_mapping_file=self.sections_mapping_file,
            docs_dir=str(Path("docs") / self.task_name),
        )


