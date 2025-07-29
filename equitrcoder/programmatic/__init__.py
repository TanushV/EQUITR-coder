"""
Programmatic Interface for EQUITR Coder

This module provides clean, OOP interfaces for using EQUITR Coder programmatically.
"""

from .interface import EquitrCoderAPI  # Legacy alias
from .interface import (
    EquitrCoder,
    ExecutionResult,
    MultiAgentTaskConfiguration,
    TaskConfiguration,
    WorkerConfiguration,
    create_multi_agent_coder,
    create_single_agent_coder,
)

__all__ = [
    "EquitrCoder",
    "EquitrCoderAPI",
    "TaskConfiguration",
    "MultiAgentTaskConfiguration",
    "WorkerConfiguration",
    "ExecutionResult",
    "create_single_agent_coder",
    "create_multi_agent_coder",
]
