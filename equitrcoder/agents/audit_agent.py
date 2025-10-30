"""
AuditAgent orchestrates post-task-group completion audits:
- Builds a focused codebase summary for the group section
- Creates audit-owned tests for the section
- Runs tests and evaluates results
- Optionally unmarks the task group or adds follow-up todos
- Produces an audit report with references to requirements/design docs
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from ..tools.builtin.todo import (
    get_todo_manager,
    set_global_todo_file,
)
from ..tools.custom.audit_tests import (
    CreateGroupTests,
    GetGroupTestStatuses,
    ListGroupTests,
)
from ..providers.litellm import LiteLLMProvider, Message


class AuditAgent(BaseAgent):
    def __init__(
        self,
        agent_id: Optional[str] = None,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None,
    ):
        super().__init__(agent_id=agent_id, max_cost=max_cost, max_iterations=max_iterations)
        # Register only the audit-safe tools (mutation gated by token at call-time)
        self.add_tool(CreateGroupTests())
        self.add_tool(GetGroupTestStatuses())
        self.add_tool(ListGroupTests())

    async def run_audit_for_group(
        self,
        *,
        task_name: str,
        todo_file: str,
        group_id: str,
        auth_token: str,
        section_paths: Optional[List[str]] = None,
        sections_mapping_file: Optional[str] = None,
        docs_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        set_global_todo_file(todo_file)
        manager = get_todo_manager()
        group = manager.get_task_group(group_id)
        if not group:
            return {"success": False, "error": f"Group '{group_id}' not found"}
        if group.status != "completed":
            return {"success": True, "skipped": True, "reason": "group not completed"}

        resolved_section_paths = self._resolve_section_paths(
            group_id=group_id,
            section_paths=section_paths,
            sections_mapping_file=sections_mapping_file,
        )

        audit_root = Path("audits") / task_name / f"group_{group_id}"
        audit_root.mkdir(parents=True, exist_ok=True)

        # 1) Codebase summary for the section
        summary_text = self._build_section_summary(resolved_section_paths)
        (audit_root / "summary.txt").write_text(summary_text, encoding="utf-8")

        # 2) Create audit-owned tests for the section
        create_resp = await self.call_tool(
            "audit_create_group_tests",
            group_id=group_id,
            section_paths=[str(p) for p in resolved_section_paths],
            auth_token=auth_token,
            overwrite=False,
        )
        if not create_resp.get("success"):
            return {"success": False, "error": f"Failed to create tests: {create_resp.get('error')}"}

        # 3) Run tests and capture results
        test_status = await self.call_tool(
            "audit_get_group_test_statuses",
            group_id=group_id,
            pytest_args=[],
        )
        res_obj = test_status.get("result")
        if hasattr(res_obj, "model_dump"):
            status_payload = res_obj.model_dump()
        elif hasattr(res_obj, "dict"):
            status_payload = res_obj.dict()
        else:
            status_payload = res_obj
        if isinstance(status_payload, dict):
            (audit_root / "test_report.json").write_text(json.dumps(status_payload, indent=2), encoding="utf-8")

        # 4) Policy: if tests failed, unmark group and add a follow-up todo
        unmarked = False
        missing_pytest = False
        try:
            # Detect explicit missing pytest signal from tool payload
            if isinstance(status_payload, dict):
                missing_pytest = bool(status_payload.get("data", {}).get("missing_pytest", False))
        except Exception:
            missing_pytest = False

        if not test_status.get("success") and not missing_pytest:
            try:
                manager.update_task_group_status(group_id, "in_progress")
                manager.add_todo_to_group(group_id, f"Fix failing audit tests for {group_id}")
                unmarked = True
            except Exception:
                pass
        elif missing_pytest:
            try:
                manager.add_todo_to_group(group_id, "Install pytest to enable audit test execution")
            except Exception:
                pass

        # 5) Produce audit report with doc references and model commentary
        tests_list_resp = await self.call_tool("audit_list_group_tests", group_id=group_id)
        tl_obj = tests_list_resp.get("result")
        if hasattr(tl_obj, "model_dump"):
            tests_list_data = tl_obj.model_dump()
        elif hasattr(tl_obj, "dict"):
            tests_list_data = tl_obj.dict()
        else:
            tests_list_data = tl_obj
        commentary = await self._generate_commentary(
            docs_dir=Path(docs_dir) if docs_dir else (Path("docs") / task_name),
            group_id=group_id,
            test_status=status_payload if isinstance(status_payload, dict) else {},
            test_list=tests_list_data if isinstance(tests_list_data, dict) else {},
        )
        report_text = self._render_report(
            task_name=task_name,
            group_id=group_id,
            docs_dir=Path(docs_dir) if docs_dir else (Path("docs") / task_name),
            summary_text=summary_text,
            test_status_data=status_payload if isinstance(status_payload, dict) else {},
            unmarked=unmarked,
        )
        # Append model commentary
        full_report = report_text + "\n## Model Commentary\n\n" + (commentary or "(no commentary)") + "\n"
        (audit_root / "audit.md").write_text(full_report, encoding="utf-8")

        return {
            "success": True,
            "group_id": group_id,
            "unmarked": unmarked,
            "audit_dir": str(audit_root),
        }

    def _resolve_section_paths(
        self,
        *,
        group_id: str,
        section_paths: Optional[List[str]],
        sections_mapping_file: Optional[str],
    ) -> List[Path]:
        if section_paths:
            return [Path(p).resolve() for p in section_paths]
        if sections_mapping_file and Path(sections_mapping_file).exists():
            try:
                mapping = json.loads(Path(sections_mapping_file).read_text(encoding="utf-8"))
                paths = mapping.get(group_id) or mapping.get("default") or []
                if isinstance(paths, list) and paths:
                    return [Path(p).resolve() for p in paths]
            except Exception:
                pass
        # Fallback: scope to main package folder if present
        pkg_root = Path("equitrcoder")
        return [pkg_root.resolve()] if pkg_root.exists() else [Path(".").resolve()]

    def _build_section_summary(self, paths: List[Path], max_files: int = 500) -> str:
        lines: List[str] = []
        count = 0
        for base in paths:
            base = base.resolve()
            if base.is_file():
                meta = self._summarize_file(base)
                lines.append(meta)
                count += 1
            elif base.is_dir():
                for fp in sorted(base.rglob("*")):
                    if count >= max_files:
                        lines.append("... (truncated)")
                        break
                    if fp.is_file():
                        if fp.name.startswith("."):
                            continue
                        meta = self._summarize_file(fp)
                        lines.append(meta)
                        count += 1
        return "\n".join(lines)

    def _summarize_file(self, p: Path) -> str:
        size = 0
        try:
            size = p.stat().st_size
        except Exception:
            pass
        head = ""
        if p.suffix == ".py" and size < 200_000:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                lines = [ln for ln in text.splitlines() if ln.strip()]
                head = "; ".join(lines[:4])
            except Exception:
                head = ""
        return f"{p} ({size} bytes){(' - ' + head) if head else ''}"

    def _render_report(
        self,
        *,
        task_name: str,
        group_id: str,
        docs_dir: Path,
        summary_text: str,
        test_status_data: Dict[str, Any],
        unmarked: bool,
    ) -> str:
        ts = datetime.now().isoformat(timespec="seconds")
        req_path = docs_dir / "requirements.md"
        des_path = docs_dir / "design.md"
        req_ref = str(req_path) if req_path.exists() else "(missing)"
        des_ref = str(des_path) if des_path.exists() else "(missing)"
        status_summary = (
            test_status_data.get("data", {}).get("summary")
            if isinstance(test_status_data, dict)
            else None
        ) or "no tests or no summary"
        body: List[str] = []
        body.append(f"# Audit Report for group '{group_id}' ({ts})")
        body.append("")
        body.append(f"- Requirements: {req_ref}")
        body.append(f"- Design: {des_ref}")
        body.append(f"- Test Summary: {status_summary}")
        body.append(f"- Group Unmarked: {unmarked}")
        body.append("")
        body.append("## Section Summary (truncated)")
        body.append("")
        body.append("```")
        body.append(summary_text[:10000])
        body.append("```")
        body.append("")
        body.append("## Notes")
        body.append("- The audit generated tests are owned by the audit process.")
        body.append("- Modify tests only via audit tools to maintain integrity.")
        return "\n".join(body) + "\n"

    async def _generate_commentary(
        self,
        *,
        docs_dir: Path,
        group_id: str,
        test_status: Dict[str, Any],
        test_list: Dict[str, Any],
        model: Optional[str] = None,
    ) -> str:
        try:
            req = (docs_dir / "requirements.md").read_text(encoding="utf-8") if (docs_dir / "requirements.md").exists() else ""
            des = (docs_dir / "design.md").read_text(encoding="utf-8") if (docs_dir / "design.md").exists() else ""
        except Exception:
            req, des = "", ""

        model_name = model or os.environ.get("EQUITR_AUDIT_MODEL", "moonshot/kimi-k2-0711-preview")
        provider = LiteLLMProvider(model=model_name)
        system = (
            "You are an independent audit model. Evaluate if the completed task group meets the requirements and design. "
            "You have test results and the list of audit-owned tests for context. "
            "Provide detailed commentary, point out gaps, and recommend next steps."
        )
        user = (
            f"Group ID: {group_id}\n\n"
            f"Requirements:\n{req[:8000]}\n\n"
            f"Design:\n{des[:8000]}\n\n"
            f"Test Status:\n{json.dumps(test_status, indent=2)[:8000]}\n\n"
            f"Audit Tests:\n{json.dumps(test_list, indent=2)[:8000]}\n\n"
            "Deliverables:\n- A reasoned verdict on correctness and spec compliance\n- Specific commentary for the agent\n- Optional suggestions for additional tasks\n"
        )
        try:
            resp = await provider.chat(messages=[Message(role="system", content=system), Message(role="user", content=user)])
            return resp.content.strip()
        except Exception:
            return ""


