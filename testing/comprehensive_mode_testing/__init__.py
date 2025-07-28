"""
Comprehensive Mode Testing Framework for EquitrCoder

This package provides comprehensive testing capabilities for all EquitrCoder modes:
- Single agent mode
- Multi-agent sequential mode  
- Multi-agent parallel mode

All tests use isolated environments and provide detailed error analysis.
"""

from .controller import ComprehensiveModeTestController
from .config import ComprehensiveTestConfig
from .results import (
    TestResult,
    SingleAgentTestResults,
    MultiAgentTestResults,
    ComprehensiveTestResults,
    ErrorCategory,
    FailureAnalysis
)

__all__ = [
    'ComprehensiveModeTestController',
    'ComprehensiveTestConfig',
    'TestResult',
    'SingleAgentTestResults', 
    'MultiAgentTestResults',
    'ComprehensiveTestResults',
    'ErrorCategory',
    'FailureAnalysis'
]