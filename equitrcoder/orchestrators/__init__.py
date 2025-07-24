"""
Orchestrator classes for equitrcoder.
"""

from .single_orchestrator import SingleAgentOrchestrator
from .multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig, TaskResult
from .research_orchestrator import (
    ResearchOrchestrator,
    ExperimentConfig,
    ExperimentResult,
    MachineSpecs,
    create_research_orchestrator,
)

__all__ = [
    "SingleAgentOrchestrator",
    "MultiAgentOrchestrator",
    "WorkerConfig",
    "TaskResult",
    "ResearchOrchestrator",
    "ExperimentConfig",
    "ExperimentResult",
    "MachineSpecs",
    "create_research_orchestrator",
]
