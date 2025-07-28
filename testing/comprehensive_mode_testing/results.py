"""
Result classes for comprehensive mode testing.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Test execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ErrorCategory(Enum):
    """Categories of errors that can occur during testing."""
    CONFIGURATION_ERROR = "configuration_error"
    EXECUTION_ERROR = "execution_error"
    DOCUMENT_CREATION_ERROR = "document_creation_error"
    TODO_SYSTEM_ERROR = "todo_system_error"
    AUDIT_SYSTEM_ERROR = "audit_system_error"
    COORDINATION_ERROR = "coordination_error"
    PARALLEL_EXECUTION_ERROR = "parallel_execution_error"
    MODEL_API_ERROR = "model_api_error"
    ENVIRONMENT_ERROR = "environment_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class PerformanceMetrics:
    """Performance metrics for test execution."""
    execution_time: float
    cost: float
    iterations: int
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    api_calls: int = 0
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FailureAnalysis:
    """Analysis of a test failure."""
    error_category: ErrorCategory
    root_cause: str
    error_message: str
    stack_trace: str
    suggested_fixes: List[str]
    context: Dict[str, Any]
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['error_category'] = self.error_category.value
        return result


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    mode: str
    status: TestStatus
    success: bool
    execution_time: float
    cost: float
    iterations: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    root_cause: Optional[str] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    artifacts: List[str] = field(default_factory=list)
    failure_analysis: Optional[FailureAnalysis] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        if self.failure_analysis:
            result['failure_analysis'] = self.failure_analysis.to_dict()
        if self.performance_metrics:
            result['performance_metrics'] = self.performance_metrics.to_dict()
        return result
    
    def mark_started(self):
        """Mark test as started."""
        self.status = TestStatus.IN_PROGRESS
        self.start_time = datetime.now().isoformat()
    
    def mark_completed(self, success: bool, execution_time: float, cost: float, iterations: int):
        """Mark test as completed."""
        self.status = TestStatus.COMPLETED if success else TestStatus.FAILED
        self.success = success
        self.execution_time = execution_time
        self.cost = cost
        self.iterations = iterations
        self.end_time = datetime.now().isoformat()
    
    def mark_failed(self, error_message: str, failure_analysis: Optional[FailureAnalysis] = None):
        """Mark test as failed."""
        self.status = TestStatus.FAILED
        self.success = False
        self.error_message = error_message
        self.failure_analysis = failure_analysis
        self.end_time = datetime.now().isoformat()


@dataclass
class SingleAgentTestResults:
    """Results from single agent testing."""
    document_creation: TestResult
    todo_completion: TestResult
    agent_execution: TestResult
    audit_functionality: TestResult
    overall_success: bool
    total_execution_time: float
    total_cost: float
    mode: str = "single"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_creation': self.document_creation.to_dict(),
            'todo_completion': self.todo_completion.to_dict(),
            'agent_execution': self.agent_execution.to_dict(),
            'audit_functionality': self.audit_functionality.to_dict(),
            'overall_success': self.overall_success,
            'total_execution_time': self.total_execution_time,
            'total_cost': self.total_cost,
            'mode': self.mode
        }


@dataclass
class MultiAgentTestResults:
    """Results from multi-agent testing."""
    document_creation: TestResult
    todo_completion: TestResult
    agent_coordination: TestResult
    audit_functionality: TestResult
    parallel_execution: Optional[TestResult] = None  # Only for parallel mode
    overall_success: bool = False
    total_execution_time: float = 0.0
    total_cost: float = 0.0
    mode: str = "multi_sequential"  # "multi_sequential" or "multi_parallel"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'document_creation': self.document_creation.to_dict(),
            'todo_completion': self.todo_completion.to_dict(),
            'agent_coordination': self.agent_coordination.to_dict(),
            'audit_functionality': self.audit_functionality.to_dict(),
            'overall_success': self.overall_success,
            'total_execution_time': self.total_execution_time,
            'total_cost': self.total_cost,
            'mode': self.mode
        }
        if self.parallel_execution:
            result['parallel_execution'] = self.parallel_execution.to_dict()
        return result


@dataclass
class ComprehensiveTestResults:
    """Complete results from all test scenarios."""
    single_agent_results: SingleAgentTestResults
    multi_agent_sequential_results: MultiAgentTestResults
    multi_agent_parallel_results: MultiAgentTestResults
    overall_success: bool
    total_execution_time: float
    total_cost: float
    failure_analysis: List[FailureAnalysis]
    performance_comparison: Dict[str, Any]
    test_timestamp: str
    test_run_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'single_agent_results': self.single_agent_results.to_dict(),
            'multi_agent_sequential_results': self.multi_agent_sequential_results.to_dict(),
            'multi_agent_parallel_results': self.multi_agent_parallel_results.to_dict(),
            'overall_success': self.overall_success,
            'total_execution_time': self.total_execution_time,
            'total_cost': self.total_cost,
            'failure_analysis': [fa.to_dict() for fa in self.failure_analysis],
            'performance_comparison': self.performance_comparison,
            'test_timestamp': self.test_timestamp,
            'test_run_id': self.test_run_id
        }
    
    def save_to_json(self, file_path: str):
        """Save results to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate."""
        total_tests = 0
        successful_tests = 0
        
        # Count single agent tests
        for test_result in [
            self.single_agent_results.document_creation,
            self.single_agent_results.todo_completion,
            self.single_agent_results.agent_execution,
            self.single_agent_results.audit_functionality
        ]:
            total_tests += 1
            if test_result.success:
                successful_tests += 1
        
        # Count multi-agent sequential tests
        for test_result in [
            self.multi_agent_sequential_results.document_creation,
            self.multi_agent_sequential_results.todo_completion,
            self.multi_agent_sequential_results.agent_coordination,
            self.multi_agent_sequential_results.audit_functionality
        ]:
            total_tests += 1
            if test_result.success:
                successful_tests += 1
        
        # Count multi-agent parallel tests
        for test_result in [
            self.multi_agent_parallel_results.document_creation,
            self.multi_agent_parallel_results.todo_completion,
            self.multi_agent_parallel_results.agent_coordination,
            self.multi_agent_parallel_results.audit_functionality
        ]:
            total_tests += 1
            if test_result.success:
                successful_tests += 1
        
        if self.multi_agent_parallel_results.parallel_execution:
            total_tests += 1
            if self.multi_agent_parallel_results.parallel_execution.success:
                successful_tests += 1
        
        return successful_tests / total_tests if total_tests > 0 else 0.0
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get list of all failed tests."""
        failed_tests = []
        
        # Check single agent tests
        for test_result in [
            self.single_agent_results.document_creation,
            self.single_agent_results.todo_completion,
            self.single_agent_results.agent_execution,
            self.single_agent_results.audit_functionality
        ]:
            if not test_result.success:
                failed_tests.append(test_result)
        
        # Check multi-agent sequential tests
        for test_result in [
            self.multi_agent_sequential_results.document_creation,
            self.multi_agent_sequential_results.todo_completion,
            self.multi_agent_sequential_results.agent_coordination,
            self.multi_agent_sequential_results.audit_functionality
        ]:
            if not test_result.success:
                failed_tests.append(test_result)
        
        # Check multi-agent parallel tests
        for test_result in [
            self.multi_agent_parallel_results.document_creation,
            self.multi_agent_parallel_results.todo_completion,
            self.multi_agent_parallel_results.agent_coordination,
            self.multi_agent_parallel_results.audit_functionality
        ]:
            if not test_result.success:
                failed_tests.append(test_result)
        
        if (self.multi_agent_parallel_results.parallel_execution and 
            not self.multi_agent_parallel_results.parallel_execution.success):
            failed_tests.append(self.multi_agent_parallel_results.parallel_execution)
        
        return failed_tests