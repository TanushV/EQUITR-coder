"""
Orchestrator classes for equitrcoder.
"""

from .single_orchestrator import SingleAgentOrchestrator
from .multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig, TaskResult

__all__ = [
    "SingleAgentOrchestrator", 
    "MultiAgentOrchestrator", 
    "WorkerConfig", 
    "TaskResult"
] 