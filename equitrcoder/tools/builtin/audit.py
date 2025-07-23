"""
Audit system for EQUITR-coder - automatically runs when all todos are completed.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from .todo import TodoManager


class AutoAuditManager:
    """Manager for automatic audit triggering."""

    def __init__(self):
        self.todo_manager = TodoManager()

    def should_trigger_audit(self) -> bool:
        """Check if audit should be triggered based on todo completion."""
        todos = self.todo_manager.list_todos()
        if not todos:
            return False

        # Check if all todos are completed
        incomplete_todos = [
            todo for todo in todos if todo.status not in ["completed", "cancelled"]
        ]
        return len(incomplete_todos) == 0

    def get_audit_context(self) -> Optional[str]:
        """Get audit context if audit should be triggered."""
        if not self.should_trigger_audit():
            return None

        todos = self.todo_manager.list_todos()
        return self._prepare_audit_context(todos)

    def _prepare_audit_context(self, todos: List[Any]) -> str:
        """Prepare context for audit."""
        context_parts = []

        # Todo summary
        completed_todos = [todo for todo in todos if todo.status == "completed"]
        context_parts.append(f"TODOS COMPLETED: {len(completed_todos)}/{len(todos)}")
        context_parts.append("=" * 50)

        for todo in completed_todos:
            context_parts.append(f"✅ {todo.title}")

        # Available tools for audit
        context_parts.append("\nAUDIT TOOLS AVAILABLE:")
        context_parts.append("- read_file: Read any file in the codebase")
        context_parts.append("- list_files: List files in directories")
        context_parts.append("- grep_search: Search for patterns in code")
        context_parts.append("- git_status: Check git status")
        context_parts.append("- git_diff: See changes made")

        # Instructions for audit
        context_parts.append("\nAUDIT INSTRUCTIONS:")
        context_parts.append("1. Use list_files to examine project structure")
        context_parts.append(
            "2. Use read_file to examine design and requirements documents"
        )
        context_parts.append(
            "3. Use grep_search to verify implementation matches requirements"
        )
        context_parts.append(
            "4. Check code quality, completeness, and adherence to design"
        )
        context_parts.append(
            "5. If everything is complete and faithful: respond with 'AUDIT PASSED'"
        )
        context_parts.append(
            "6. If issues found: respond with 'AUDIT FAILED' and create new todos for fixes"
        )

        return "\n".join(context_parts)


# Global audit manager instance
audit_manager = AutoAuditManager()
