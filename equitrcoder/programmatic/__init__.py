"""
Programmatic Interface for EQUITR Coder

This module provides clean, OOP interfaces for using EQUITR Coder programmatically.
"""

from .interface import EquitrCoder
from .interface import (
    TaskConfiguration,
    MultiAgentTaskConfiguration,
    ExecutionResult,
)

# Legacy alias for backward compatibility
EquitrCoderAPI = EquitrCoder

__all__ = [
    "EquitrCoder",
    "EquitrCoderAPI",
    "TaskConfiguration",
    "MultiAgentTaskConfiguration",
    "ExecutionResult",
]
