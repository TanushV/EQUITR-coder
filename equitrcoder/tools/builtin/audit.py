"""
Audit system for EQUITR-coder - automatically runs when all todos are completed.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .todo import TodoManager


class AutoAuditManager:
    """Manager for automatic audit triggering with failure tracking and escalation."""

    def __init__(self):
        self.todo_manager = TodoManager()
        self.audit_failure_count = 0
        self.max_failures_before_escalation = 2
        self.audit_history_file = Path(".EQUITR_audit_history.json")
        self._load_audit_history()

    def _load_audit_history(self):
        """Load audit failure history from file."""
        if self.audit_history_file.exists():
            try:
                with open(self.audit_history_file, "r") as f:
                    data = json.load(f)
                    self.audit_failure_count = data.get("failure_count", 0)
            except Exception as e:
                print(f"Warning: Could not load audit history: {e}")
                self.audit_failure_count = 0
        else:
            self.audit_failure_count = 0

    def _save_audit_history(self):
        """Save audit failure history to file."""
        try:
            data = {
                "failure_count": self.audit_failure_count,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.audit_history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save audit history: {e}")

    def should_trigger_audit(self, task_name: str = None) -> bool:
        """
        Check if audit should be triggered - only when ALL todos for a task are completed.

        Args:
            task_name: Specific task to check (e.g., "task_20241227_143022")
                      If None, checks all todos in the system
        """
        todos = self.todo_manager.list_todos()

        if task_name:
            # Filter todos for specific task
            task_todos = [t for t in todos if f"task-{task_name}" in t.tags]
            if not task_todos:
                print(f"⚠️ No todos found for task: {task_name}")
                return False

            # Check if ALL todos for this task are completed
            pending_todos = [
                t for t in task_todos if t.status not in ["completed", "cancelled"]
            ]
            completed_todos = [t for t in task_todos if t.status == "completed"]

            print(
                f"📊 Task '{task_name}' status: {len(completed_todos)}/{len(task_todos)} todos completed"
            )

            if pending_todos:
                print(
                    f"⏳ Audit not triggered - {len(pending_todos)} todos still pending for task '{task_name}':"
                )
                for todo in pending_todos[:3]:  # Show first 3 pending
                    print(f"  - {todo.title}")
                if len(pending_todos) > 3:
                    print(f"  ... and {len(pending_todos) - 3} more")
                return False
            else:
                print(
                    f"✅ All todos completed for task '{task_name}' - audit triggered!"
                )
                return True
        else:
            # Check all todos in system (legacy behavior)
            pending_todos = [
                t for t in todos if t.status not in ["completed", "cancelled"]
            ]
            completed_todos = [t for t in todos if t.status == "completed"]

            print(
                f"📊 System status: {len(completed_todos)}/{len(todos)} todos completed"
            )

            if pending_todos:
                print(
                    f"⏳ Audit not triggered - {len(pending_todos)} todos still pending"
                )
                return False
            else:
                print("✅ All todos completed - audit triggered!")
                return True

    def record_audit_result(
        self, passed: bool, audit_result: str = "", reason: str = ""
    ) -> bool:
        """
        Record audit result and handle failure logic.
        Returns True if audit cycle should continue, False if escalated to user.

        Args:
            passed: Whether the audit passed or failed
            audit_result: Full audit result content
            reason: Specific reason for pass/fail decision (required)
        """
        if not reason:
            print(
                "⚠️ Warning: No reason provided for audit result - this may affect audit quality"
            )
            reason = "No specific reason provided"

        if passed:
            print(f"✅ Audit passed! Reason: {reason}")
            print("🔄 Resetting failure count.")
            self.audit_failure_count = 0
            self._save_audit_history()
            return False  # Audit cycle complete
        else:
            self.audit_failure_count += 1
            print(
                f"❌ Audit failed (attempt {self.audit_failure_count}/{self.max_failures_before_escalation})"
            )
            print(f"📝 Failure reason: {reason}")

            if self.audit_failure_count >= self.max_failures_before_escalation:
                print("🚨 Maximum audit failures reached - escalating to user!")
                self._escalate_to_user(audit_result, reason)
                return False  # Stop audit cycle, escalate to user
            else:
                print(
                    "🔄 Creating new todos from audit findings and continuing cycle..."
                )
                self._save_audit_history()
                return True  # Continue audit cycle

    def _escalate_to_user(self, audit_result: str, reason: str = ""):
        """Escalate to user after maximum failures."""
        escalation_todo = self.todo_manager.create_todo(
            title="🚨 URGENT: Manual Review Required - Audit Failed Multiple Times",
            description=f"""
CRITICAL: The automated audit has failed {self.audit_failure_count} times.
Manual intervention is required to resolve the issues.

Last failure reason: {reason}

Last audit result:
{audit_result}

Action required:
1. Review the audit findings above
2. Manually fix the identified issues
3. Reset the audit failure count by deleting .EQUITR_audit_history.json
4. Re-run the system to continue automated auditing

This todo has been marked as high priority and assigned for immediate attention.
            """.strip(),
            priority="high",
            tags=["urgent", "manual-review", "audit-failure"],
            assignee="user",
        )

        print(f"📋 Created escalation todo: {escalation_todo.id}")

        # Reset failure count after escalation
        self.audit_failure_count = 0
        self._save_audit_history()

    def parse_audit_findings(self, audit_result: str) -> List[Dict[str, Any]]:
        """Parse audit result to extract specific issues for todo creation."""
        findings = []

        # Look for common audit failure patterns
        lines = audit_result.split("\n")
        current_issue = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect issue indicators
            if any(
                indicator in line.lower()
                for indicator in [
                    "missing",
                    "error",
                    "failed",
                    "incomplete",
                    "todo:",
                    "fix:",
                    "issue:",
                ]
            ):
                if current_issue:
                    findings.append(current_issue)

                current_issue = {
                    "title": line[:100],  # Truncate long titles
                    "description": line,
                    "priority": (
                        "high"
                        if any(
                            urgent in line.lower()
                            for urgent in ["critical", "error", "failed"]
                        )
                        else "medium"
                    ),
                }
            elif current_issue and line:
                # Add additional context to current issue
                current_issue["description"] += f"\n{line}"

        # Add the last issue if exists
        if current_issue:
            findings.append(current_issue)

        # If no specific issues found, create a general issue
        if not findings:
            findings.append(
                {
                    "title": "General audit failure - requires investigation",
                    "description": f"Audit failed but no specific issues were identified.\n\nFull audit result:\n{audit_result}",
                    "priority": "medium",
                }
            )

        return findings

    def create_todos_from_audit_failure(self, audit_result: str, reason: str = ""):
        """Create specific todos based on audit failure findings."""
        findings = self.parse_audit_findings(audit_result)

        print(f"📋 Creating {len(findings)} todos from audit findings...")

        for i, finding in enumerate(findings):
            todo = self.todo_manager.create_todo(
                title=f"Fix: {finding['title']}",
                description=f"""
Audit Failure Issue #{i+1}:

Failure Reason: {reason if reason else 'No specific reason provided'}

{finding['description']}

This issue was identified during automated audit failure #{self.audit_failure_count}.
Please resolve this issue to allow the audit to pass.
                """.strip(),
                priority=finding["priority"],
                tags=["audit-fix", f"audit-failure-{self.audit_failure_count}"],
                assignee=None,
            )
            print(f"  ✓ Created todo: {todo.id} - {todo.title}")

    def get_audit_context(self, task_name: str = None) -> Optional[str]:
        """Get audit context if audit should be triggered for a specific task."""
        if not self.should_trigger_audit(task_name):
            return None

        todos = self.todo_manager.list_todos()

        # Filter todos for specific task if provided
        if task_name:
            todos = [t for t in todos if f"task-{task_name}" in t.tags]
            if not todos:
                print(f"⚠️ No todos found for task: {task_name}")
                return None

        return self._prepare_audit_context(todos, task_name)

    def _prepare_audit_context(self, todos: List[Any], task_name: str = None) -> str:
        """Prepare context for audit with improved reliability."""
        completed_todos = [todo for todo in todos if todo.status == "completed"]
        pending_todos = [
            todo for todo in todos if todo.status not in ["completed", "cancelled"]
        ]

        failure_history = ""
        if self.audit_failure_count > 0:
            failure_history = f"""
⚠️  AUDIT FAILURE HISTORY: {self.audit_failure_count} previous failures
This audit must be thorough to avoid escalation to user.
"""

        attempt_info = f"🔄 AUDIT ATTEMPT: #{self.audit_failure_count + 1}"
        if self.audit_failure_count > 0:
            attempt_info += "\nPrevious audits failed - be extra thorough!"

        # Show only recent completed todos to avoid overwhelming context
        recent_completed = (
            completed_todos[-10:] if len(completed_todos) > 10 else completed_todos
        )
        completed_list = (
            "\n".join([f"✅ {todo.title}" for todo in recent_completed])
            if recent_completed
            else "No todos completed yet"
        )

        # Show only first few pending todos
        first_pending = pending_todos[:5] if len(pending_todos) > 5 else pending_todos
        pending_list = (
            "\n".join([f"⏳ {todo.title}" for todo in first_pending])
            if first_pending
            else "No pending todos"
        )
        if len(pending_todos) > 5:
            pending_list += f"\n... and {len(pending_todos) - 5} more pending todos"

        task_info = ""
        if task_name:
            task_info = f"""
🎯 TASK-SPECIFIC AUDIT: {task_name}
This audit is focused ONLY on todos for task: {task_name}
Task documents should be in: docs/{task_name}/
"""

        return f"""WORKER COMPLETION AUDIT - STRUCTURED VALIDATION
==================================================
{task_info}
TODOS COMPLETED: {len(completed_todos)}/{len(todos)}
{completed_list}

TODOS STILL PENDING: {len(pending_todos)}
{pending_list}
{failure_history}

AUDIT TOOLS AVAILABLE:
- read_file: Read any file in the codebase
- list_files: List files in directories
- grep_search: Search for patterns in code
- git_status: Check git status
- git_diff: See changes made
- create_todo: Create new todos for missing items

🔍 STRUCTURED AUDIT PROCESS:
Follow this exact sequence for reliable audits:

STEP 1: DOCUMENT VALIDATION
- Use read_file to check docs/requirements.md exists and is complete
- Use read_file to check docs/design.md exists and is complete
- Verify these documents contain clear, actionable specifications

STEP 2: PROJECT STRUCTURE CHECK
- Use list_files to examine the project structure
- Verify expected directories and files exist as per design
- Check for any missing core files or directories

STEP 3: IMPLEMENTATION VERIFICATION
- For each completed todo, verify the actual work was done
- Use read_file to check if files mentioned in todos exist
- Use grep_search to verify code implementations match requirements
- Check that code quality is acceptable (no obvious bugs)

STEP 4: REQUIREMENTS COMPLIANCE
- Cross-reference completed work against docs/requirements.md
- Ensure all functional requirements are being addressed
- Verify technical requirements are being followed

STEP 5: DESIGN COMPLIANCE
- Cross-reference completed work against docs/design.md
- Ensure implementation follows the specified architecture
- Verify components are built as designed

⚠️  AUDIT FAILURE CRITERIA (be specific):
- Required documents (requirements.md, design.md) are missing or incomplete
- Completed todos were not actually implemented (files don't exist)
- Work doesn't match requirements specifications
- Work doesn't follow design architecture
- Missing critical files that should have been created
- Code has obvious bugs or quality issues
- Incomplete implementations that claim to be complete

✅ AUDIT SUCCESS CRITERIA:
- Documents exist and are complete
- ALL completed todos have corresponding implementations
- Work matches both requirements and design documents
- Code quality is acceptable for the project stage
- No critical missing components for current progress

🎯 REQUIRED RESPONSE FORMAT:
You MUST provide a clear reason for your audit decision in both cases:

- If audit passes: Respond EXACTLY with 'AUDIT PASSED' followed by:
  * REASON FOR PASSING: Explain specifically why all completed todos were properly implemented
  * Example: "AUDIT PASSED - All 5 completed todos have corresponding implementations: authentication system files exist and function correctly, database schema matches design, API endpoints are implemented as specified."

- If audit fails: Respond EXACTLY with 'AUDIT FAILED' followed by:
  * REASON FOR FAILING: Explain specifically which completed todos were not properly implemented
  * SPECIFIC ISSUES FOUND: List each concrete problem
  * For each issue, use create_todo tool to create a fix task
  * Example: "AUDIT FAILED - Todo 'Create login endpoint' marked complete but no login.py file exists, Todo 'Setup database' complete but no database schema found."

CRITICAL: Your reasoning must focus ONLY on whether completed todos were actually implemented, not on future work or pending todos.

{attempt_info}

REMEMBER: Focus on whether completed todos were actually implemented, not on future work."""


# Global audit manager instance
audit_manager = AutoAuditManager()
