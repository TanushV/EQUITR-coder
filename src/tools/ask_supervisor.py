import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class AskSupervisorTool:
    def __init__(self, supervisor_callback):
        self.supervisor_callback = supervisor_callback
        self.call_count = 0
        self.max_calls = 5

    def __call__(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        if self.call_count >= self.max_calls:
            return {
                "error": f"Maximum supervisor calls ({self.max_calls}) exceeded",
                "suggestion": "Try to proceed independently or request manual intervention",
            }

        self.call_count += 1

        try:
            response = self.supervisor_callback(question, context)
            return {
                "response": response,
                "call_count": self.call_count,
                "remaining_calls": self.max_calls - self.call_count,
            }
        except Exception as e:
            return {
                "error": f"Failed to contact supervisor: {str(e)}",
                "call_count": self.call_count,
            }


class SupervisorSession:
    def __init__(self):
        self.conversation_history = []

    def ask(self, question: str, context: Optional[str] = None) -> str:
        self.conversation_history.append(
            {"type": "worker_question", "question": question, "context": context}
        )

        # Simple supervisor response - in real implementation, this would call the strong model
        response = self._generate_response(question, context)

        self.conversation_history.append(
            {"type": "supervisor_response", "response": response}
        )

        return response

    def _generate_response(self, question: str, context: Optional[str] = None) -> str:
        # Placeholder for actual supervisor logic
        if "error" in question.lower():
            return "Check the error message carefully. Look for file paths, line numbers, and specific error types. Try to isolate the issue by testing smaller components."
        elif "test" in question.lower():
            return "Run the existing tests first to understand the current state. Then add tests for your new functionality before implementing the feature."
        elif "refactor" in question.lower():
            return "Focus on one small piece at a time. Ensure tests pass after each change. Document what you're refactoring and why."
        else:
            return "Proceed step by step. Make small, testable changes. If blocked, provide specific details about what's not working."

    def get_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history


# Global supervisor instance
_supervisor = None


def get_supervisor() -> SupervisorSession:
    global _supervisor
    if _supervisor is None:
        _supervisor = SupervisorSession()
    return _supervisor


def create_ask_supervisor_tool() -> AskSupervisorTool:
    supervisor = get_supervisor()
    return AskSupervisorTool(supervisor.ask)
