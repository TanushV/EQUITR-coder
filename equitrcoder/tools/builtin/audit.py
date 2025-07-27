"""
Audit system for EQUITR-coder - automatically runs when all todos are completed.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

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
                "last_updated": datetime.now().isoformat()
            }
            with open(self.audit_history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save audit history: {e}")

    def should_trigger_audit(self) -> bool:
        """Check if audit should be triggered - ALWAYS returns True after worker completion."""
        # CRITICAL: Audits should ALWAYS run after ANY worker finishes, regardless of todo status
        # This ensures work quality and creates new todos when work is incomplete
        return True

    def record_audit_result(self, passed: bool, audit_result: str = "") -> bool:
        """
        Record audit result and handle failure logic.
        Returns True if audit cycle should continue, False if escalated to user.
        """
        if passed:
            print("✅ Audit passed! Resetting failure count.")
            self.audit_failure_count = 0
            self._save_audit_history()
            return False  # Audit cycle complete
        else:
            self.audit_failure_count += 1
            print(f"❌ Audit failed (attempt {self.audit_failure_count}/{self.max_failures_before_escalation})")
            
            if self.audit_failure_count >= self.max_failures_before_escalation:
                print("🚨 Maximum audit failures reached - escalating to user!")
                self._escalate_to_user(audit_result)
                return False  # Stop audit cycle, escalate to user
            else:
                print("🔄 Creating new todos from audit findings and continuing cycle...")
                self._save_audit_history()
                return True  # Continue audit cycle

    def _escalate_to_user(self, audit_result: str):
        """Escalate to user after maximum failures."""
        escalation_todo = self.todo_manager.create_todo(
            title="🚨 URGENT: Manual Review Required - Audit Failed Multiple Times",
            description=f"""
CRITICAL: The automated audit has failed {self.audit_failure_count} times.
Manual intervention is required to resolve the issues.

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
            assignee="user"
        )
        
        print(f"📋 Created escalation todo: {escalation_todo.id}")
        
        # Reset failure count after escalation
        self.audit_failure_count = 0
        self._save_audit_history()

    def parse_audit_findings(self, audit_result: str) -> List[Dict[str, Any]]:
        """Parse audit result to extract specific issues for todo creation."""
        findings = []
        
        # Look for common audit failure patterns
        lines = audit_result.split('\n')
        current_issue = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect issue indicators
            if any(indicator in line.lower() for indicator in [
                'missing', 'error', 'failed', 'incomplete', 'todo:', 'fix:', 'issue:'
            ]):
                if current_issue:
                    findings.append(current_issue)
                
                current_issue = {
                    'title': line[:100],  # Truncate long titles
                    'description': line,
                    'priority': 'high' if any(urgent in line.lower() for urgent in ['critical', 'error', 'failed']) else 'medium'
                }
            elif current_issue and line:
                # Add additional context to current issue
                current_issue['description'] += f"\n{line}"
        
        # Add the last issue if exists
        if current_issue:
            findings.append(current_issue)
        
        # If no specific issues found, create a general issue
        if not findings:
            findings.append({
                'title': 'General audit failure - requires investigation',
                'description': f"Audit failed but no specific issues were identified.\n\nFull audit result:\n{audit_result}",
                'priority': 'medium'
            })
        
        return findings

    def create_todos_from_audit_failure(self, audit_result: str):
        """Create specific todos based on audit failure findings."""
        findings = self.parse_audit_findings(audit_result)
        
        print(f"📋 Creating {len(findings)} todos from audit findings...")
        
        for i, finding in enumerate(findings):
            todo = self.todo_manager.create_todo(
                title=f"Fix: {finding['title']}",
                description=f"""
Audit Failure Issue #{i+1}:

{finding['description']}

This issue was identified during automated audit failure #{self.audit_failure_count}.
Please resolve this issue to allow the audit to pass.
                """.strip(),
                priority=finding['priority'],
                tags=['audit-fix', f'audit-failure-{self.audit_failure_count}'],
                assignee=None
            )
            print(f"  ✓ Created todo: {todo.id} - {todo.title}")

    def get_audit_context(self) -> Optional[str]:
        """Get audit context if audit should be triggered."""
        if not self.should_trigger_audit():
            return None

        todos = self.todo_manager.list_todos()
        return self._prepare_audit_context(todos)

    def _prepare_audit_context(self, todos: List[Any]) -> str:
        """Prepare context for audit with improved reliability."""
        completed_todos = [todo for todo in todos if todo.status == "completed"]
        pending_todos = [todo for todo in todos if todo.status not in ["completed", "cancelled"]]
        
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
        recent_completed = completed_todos[-10:] if len(completed_todos) > 10 else completed_todos
        completed_list = "\n".join([f"✅ {todo.title}" for todo in recent_completed]) if recent_completed else "No todos completed yet"
        
        # Show only first few pending todos
        first_pending = pending_todos[:5] if len(pending_todos) > 5 else pending_todos
        pending_list = "\n".join([f"⏳ {todo.title}" for todo in first_pending]) if first_pending else "No pending todos"
        if len(pending_todos) > 5:
            pending_list += f"\n... and {len(pending_todos) - 5} more pending todos"

        return f"""WORKER COMPLETION AUDIT - STRUCTURED VALIDATION
==================================================
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
- If audit passes: Respond EXACTLY with 'AUDIT PASSED'
- If audit fails: Respond EXACTLY with 'AUDIT FAILED' followed by:
  * SPECIFIC ISSUES FOUND: List each concrete problem
  * For each issue, use create_todo tool to create a fix task
  * Be precise about what needs to be fixed or implemented

{attempt_info}

REMEMBER: Focus on whether completed todos were actually implemented, not on future work."""


# Global audit manager instance
audit_manager = AutoAuditManager()
