"""
Programmatic Interface for EQUITR Coder

This module provides clean, OOP interfaces for using EQUITR Coder programmatically.
"""

# Alias removed because EquitrCoderAPI no longer exists
from .interface import (
    EquitrCoder,
    ExecutionResult,
    MultiAgentTaskConfiguration,
    TaskConfiguration,
    create_multi_agent_coder,
    create_single_agent_coder,
)

__all__ = [
    "EquitrCoder",
    "TaskConfiguration",
    "MultiAgentTaskConfiguration",
    "ExecutionResult",
    "create_single_agent_coder",
    "create_multi_agent_coder",
]
