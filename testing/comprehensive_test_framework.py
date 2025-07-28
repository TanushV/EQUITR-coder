"""
Comprehensive Testing Framework for EquitrCoder

This module implements a comprehensive testing framework that validates different
agent configurations and workflows in isolated environments.
"""

import asyncio
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
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
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class TestConfig:
    """Configuration for a test scenario."""
    model: str = "moonshot/kimi-k2-0711-preview"
    max_cost: float = 5.0
    max_iterations: int = 20
    timeout_seconds: int = 300
    test_task: str = "Create a simple calculator application with basic arithmetic operations, CLI interface, input validation, error handling, and unit tests"
    expected_files: Optional[List[str]] = None
    expected_todos: Optional[int] = None
    
    def __post_init__(self):
        if self.expected_files is None:
            self.expected_files = [
                "requirements.md",
                "design.md", 
                "todos.md",
                "calculator.py",
                "test_calculator.py"
            ]
        if self.expected_todos is None:
            self.expected_todos = 10  # Expected number of todos


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


@dataclass
class FailureAnalysis:
    """Analysis of a test failure."""
    error_category: ErrorCategory
    root_cause: str
    error_message: str
    stack_trace: str
    suggested_fixes: List[str]
    context: Dict[str, Any]


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    status: TestStatus
    success: bool
    execution_time: float
    cost: float
    iterations: int
    error_message: Optional[str] = None
    root_cause: Optional[str] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    artifacts: Optional[List[str]] = None
    failure_analysis: Optional[FailureAnalysis] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert enums to strings
        if self.failure_analysis:
            result['failure_analysis']['error_category'] = self.failure_analysis.error_category.value
        result['status'] = self.status.value
        return result


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


@dataclass
class MultiAgentTestResults:
    """Results from multi-agent testing."""
    document_creation: TestResult
    todo_completion: TestResult
    agent_coordination: TestResult
    audit_functionality: TestResult
    overall_success: bool
    total_execution_time: float
    total_cost: float
    mode: str = "sequential"  # "sequential" or "parallel"
    parallel_execution: Optional[TestResult] = None  # Only for parallel mode


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'single_agent_results': {
                'document_creation': self.single_agent_results.document_creation.to_dict(),
                'todo_completion': self.single_agent_results.todo_completion.to_dict(),
                'agent_execution': self.single_agent_results.agent_execution.to_dict(),
                'audit_functionality': self.single_agent_results.audit_functionality.to_dict(),
                'overall_success': self.single_agent_results.overall_success,
                'total_execution_time': self.single_agent_results.total_execution_time,
                'total_cost': self.single_agent_results.total_cost
            },
            'multi_agent_sequential_results': {
                'document_creation': self.multi_agent_sequential_results.document_creation.to_dict(),
                'todo_completion': self.multi_agent_sequential_results.todo_completion.to_dict(),
                'agent_coordination': self.multi_agent_sequential_results.agent_coordination.to_dict(),
                'audit_functionality': self.multi_agent_sequential_results.audit_functionality.to_dict(),
                'overall_success': self.multi_agent_sequential_results.overall_success,
                'total_execution_time': self.multi_agent_sequential_results.total_execution_time,
                'total_cost': self.multi_agent_sequential_results.total_cost,
                'mode': self.multi_agent_sequential_results.mode
            },
            'multi_agent_parallel_results': {
                'document_creation': self.multi_agent_parallel_results.document_creation.to_dict(),
                'todo_completion': self.multi_agent_parallel_results.todo_completion.to_dict(),
                'agent_coordination': self.multi_agent_parallel_results.agent_coordination.to_dict(),
                'audit_functionality': self.multi_agent_parallel_results.audit_functionality.to_dict(),
                'parallel_execution': self.multi_agent_parallel_results.parallel_execution.to_dict() if self.multi_agent_parallel_results.parallel_execution else None,
                'overall_success': self.multi_agent_parallel_results.overall_success,
                'total_execution_time': self.multi_agent_parallel_results.total_execution_time,
                'total_cost': self.multi_agent_parallel_results.total_cost,
                'mode': self.multi_agent_parallel_results.mode
            },
            'overall_success': self.overall_success,
            'total_execution_time': self.total_execution_time,
            'total_cost': self.total_cost,
            'failure_analysis': [
                {
                    'error_category': fa.error_category.value,
                    'root_cause': fa.root_cause,
                    'error_message': fa.error_message,
                    'stack_trace': fa.stack_trace,
                    'suggested_fixes': fa.suggested_fixes,
                    'context': fa.context
                } for fa in self.failure_analysis
            ],
            'performance_comparison': self.performance_comparison,
            'test_timestamp': self.test_timestamp
        }


class TestResultsCollector:
    """Collects and manages test results."""
    
    def __init__(self):
        self.results: Dict[str, TestResult] = {}
        self.failure_analyses: List[FailureAnalysis] = []
    
    def collect_result(self, test_name: str, result: TestResult) -> None:
        """Collect a test result."""
        self.results[test_name] = result
        if result.failure_analysis:
            self.failure_analyses.append(result.failure_analysis)
    
    def get_all_results(self) -> Dict[str, TestResult]:
        """Get all collected results."""
        return self.results.copy()
    
    def analyze_failures(self) -> List[FailureAnalysis]:
        """Get all failure analyses."""
        return self.failure_analyses.copy()
    
    def generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance comparison metrics."""
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results.values() if r.success]
        failed_results = [r for r in self.results.values() if not r.success]
        
        return {
            'total_tests': len(self.results),
            'successful_tests': len(successful_results),
            'failed_tests': len(failed_results),
            'success_rate': len(successful_results) / len(self.results) if self.results else 0,
            'average_execution_time': sum(r.execution_time for r in successful_results) / len(successful_results) if successful_results else 0,
            'total_cost': sum(r.cost for r in self.results.values()),
            'average_cost': sum(r.cost for r in self.results.values()) / len(self.results) if self.results else 0,
            'total_iterations': sum(r.iterations for r in self.results.values()),
            'average_iterations': sum(r.iterations for r in self.results.values()) / len(self.results) if self.results else 0
        }


class ComprehensiveTestController:
    """Main controller for comprehensive testing framework."""
    
    def __init__(self, base_test_dir: str = "testing/comprehensive_tests"):
        self.base_test_dir = Path(base_test_dir)
        self.base_test_dir.mkdir(parents=True, exist_ok=True)
        self.results_collector = TestResultsCollector()
        self.test_config = TestConfig()
        
        # Create timestamp for this test run
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_run_dir = self.base_test_dir / f"run_{self.test_run_id}"
        self.test_run_dir.mkdir(exist_ok=True)
        
        print(f"🧪 Initialized comprehensive test framework")
        print(f"📁 Test run directory: {self.test_run_dir}")
    
    async def run_all_tests(self) -> ComprehensiveTestResults:
        """Run all test scenarios and return comprehensive results."""
        print("🚀 Starting comprehensive testing of EquitrCoder...")
        start_time = time.time()
        
        try:
            # Run single agent tests
            print("\n" + "="*60)
            print("🤖 SINGLE AGENT TESTING")
            print("="*60)
            single_agent_results = await self.run_single_agent_tests()
            
            # Run multi-agent sequential tests
            print("\n" + "="*60)
            print("👥 MULTI-AGENT SEQUENTIAL TESTING")
            print("="*60)
            multi_agent_sequential_results = await self.run_multi_agent_sequential_tests()
            
            # Run multi-agent parallel tests
            print("\n" + "="*60)
            print("⚡ MULTI-AGENT PARALLEL TESTING")
            print("="*60)
            multi_agent_parallel_results = await self.run_multi_agent_parallel_tests()
            
            # Calculate overall results
            total_execution_time = time.time() - start_time
            total_cost = (single_agent_results.total_cost + 
                         multi_agent_sequential_results.total_cost + 
                         multi_agent_parallel_results.total_cost)
            
            overall_success = (single_agent_results.overall_success and 
                             multi_agent_sequential_results.overall_success and 
                             multi_agent_parallel_results.overall_success)
            
            # Generate performance comparison
            performance_comparison = self._generate_performance_comparison(
                single_agent_results, 
                multi_agent_sequential_results, 
                multi_agent_parallel_results
            )
            
            # Create comprehensive results
            comprehensive_results = ComprehensiveTestResults(
                single_agent_results=single_agent_results,
                multi_agent_sequential_results=multi_agent_sequential_results,
                multi_agent_parallel_results=multi_agent_parallel_results,
                overall_success=overall_success,
                total_execution_time=total_execution_time,
                total_cost=total_cost,
                failure_analysis=self.results_collector.analyze_failures(),
                performance_comparison=performance_comparison,
                test_timestamp=datetime.now().isoformat()
            )
            
            # Generate and save comprehensive report
            report = self.generate_comprehensive_report(comprehensive_results)
            report_path = self.test_run_dir / "comprehensive_test_report.md"
            report_path.write_text(report)
            
            # Save results as JSON
            results_path = self.test_run_dir / "test_results.json"
            with open(results_path, 'w') as f:
                json.dump(comprehensive_results.to_dict(), f, indent=2)
            
            print(f"\n📊 Comprehensive testing completed!")
            print(f"📁 Results saved to: {self.test_run_dir}")
            print(f"⏱️  Total execution time: {total_execution_time:.2f} seconds")
            print(f"💰 Total cost: ${total_cost:.4f}")
            print(f"✅ Overall success: {overall_success}")
            
            return comprehensive_results
            
        except Exception as e:
            print(f"❌ Comprehensive testing failed: {str(e)}")
            raise
    
    async def run_single_agent_tests(self) -> SingleAgentTestResults:
        """Run single agent test scenarios."""
        from .test_environment_manager import TestEnvironmentManager
        from .test_single_agent_suite import SingleAgentTestSuite
        
        # Create environment manager
        env_manager = TestEnvironmentManager(str(self.test_run_dir / "single_agent_envs"))
        
        # Create test suite
        test_suite = SingleAgentTestSuite(self.test_config, env_manager)
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Collect results
        self.results_collector.collect_result("single_agent_document_creation", results.document_creation)
        self.results_collector.collect_result("single_agent_todo_completion", results.todo_completion)
        self.results_collector.collect_result("single_agent_execution", results.agent_execution)
        self.results_collector.collect_result("single_agent_audit", results.audit_functionality)
        
        return results
    
    async def run_multi_agent_sequential_tests(self) -> MultiAgentTestResults:
        """Run multi-agent sequential test scenarios."""
        from .test_environment_manager import TestEnvironmentManager
        from .test_multi_agent_suite import MultiAgentTestSuite
        
        # Create environment manager
        env_manager = TestEnvironmentManager(str(self.test_run_dir / "multi_agent_sequential_envs"))
        
        # Create test suite for sequential mode
        test_suite = MultiAgentTestSuite(self.test_config, env_manager, parallel_mode=False)
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Collect results
        self.results_collector.collect_result("multi_agent_seq_document_creation", results.document_creation)
        self.results_collector.collect_result("multi_agent_seq_todo_completion", results.todo_completion)
        self.results_collector.collect_result("multi_agent_seq_coordination", results.agent_coordination)
        self.results_collector.collect_result("multi_agent_seq_audit", results.audit_functionality)
        
        return results
    
    async def run_multi_agent_parallel_tests(self) -> MultiAgentTestResults:
        """Run multi-agent parallel test scenarios."""
        from .test_environment_manager import TestEnvironmentManager
        from .test_multi_agent_suite import MultiAgentTestSuite
        
        # Create environment manager
        env_manager = TestEnvironmentManager(str(self.test_run_dir / "multi_agent_parallel_envs"))
        
        # Create test suite for parallel mode
        test_suite = MultiAgentTestSuite(self.test_config, env_manager, parallel_mode=True)
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Collect results
        self.results_collector.collect_result("multi_agent_par_document_creation", results.document_creation)
        self.results_collector.collect_result("multi_agent_par_todo_completion", results.todo_completion)
        self.results_collector.collect_result("multi_agent_par_coordination", results.agent_coordination)
        self.results_collector.collect_result("multi_agent_par_audit", results.audit_functionality)
        if results.parallel_execution:
            self.results_collector.collect_result("multi_agent_par_execution", results.parallel_execution)
        
        return results
    
    def _generate_performance_comparison(
        self, 
        single: SingleAgentTestResults,
        sequential: MultiAgentTestResults, 
        parallel: MultiAgentTestResults
    ) -> Dict[str, Any]:
        """Generate performance comparison between different modes."""
        return {
            'execution_time_comparison': {
                'single_agent': single.total_execution_time,
                'multi_agent_sequential': sequential.total_execution_time,
                'multi_agent_parallel': parallel.total_execution_time
            },
            'cost_comparison': {
                'single_agent': single.total_cost,
                'multi_agent_sequential': sequential.total_cost,
                'multi_agent_parallel': parallel.total_cost
            },
            'success_rate_comparison': {
                'single_agent': single.overall_success,
                'multi_agent_sequential': sequential.overall_success,
                'multi_agent_parallel': parallel.overall_success
            }
        }
    
    def generate_comprehensive_report(self, results: ComprehensiveTestResults) -> str:
        """Generate a comprehensive test report."""
        report = f"""# EquitrCoder Comprehensive Test Report

**Test Run ID:** {self.test_run_id}
**Timestamp:** {results.test_timestamp}
**Overall Success:** {'✅ PASSED' if results.overall_success else '❌ FAILED'}
**Total Execution Time:** {results.total_execution_time:.2f} seconds
**Total Cost:** ${results.total_cost:.4f}

## Executive Summary

This report presents the results of comprehensive testing of the EquitrCoder system across three different agent configurations:
1. Single Agent Mode
2. Multi-Agent Sequential Mode  
3. Multi-Agent Parallel Mode

All tests used the **{self.test_config.model}** model for consistency.

## Test Results Overview

### Single Agent Results
- **Overall Success:** {'✅ PASSED' if results.single_agent_results.overall_success else '❌ FAILED'}
- **Execution Time:** {results.single_agent_results.total_execution_time:.2f}s
- **Cost:** ${results.single_agent_results.total_cost:.4f}

### Multi-Agent Sequential Results  
- **Overall Success:** {'✅ PASSED' if results.multi_agent_sequential_results.overall_success else '❌ FAILED'}
- **Execution Time:** {results.multi_agent_sequential_results.total_execution_time:.2f}s
- **Cost:** ${results.multi_agent_sequential_results.total_cost:.4f}

### Multi-Agent Parallel Results
- **Overall Success:** {'✅ PASSED' if results.multi_agent_parallel_results.overall_success else '❌ FAILED'}
- **Execution Time:** {results.multi_agent_parallel_results.total_execution_time:.2f}s
- **Cost:** ${results.multi_agent_parallel_results.total_cost:.4f}

## Performance Comparison

{self._format_performance_comparison(results.performance_comparison)}

## Failure Analysis

{self._format_failure_analysis(results.failure_analysis)}

## Recommendations

{self._generate_recommendations(results)}

---
*Report generated by EquitrCoder Comprehensive Testing Framework*
"""
        return report
    
    def _format_performance_comparison(self, comparison: Dict[str, Any]) -> str:
        """Format performance comparison section."""
        if not comparison:
            return "No performance data available."
        
        return f"""
| Metric | Single Agent | Multi-Agent Sequential | Multi-Agent Parallel |
|--------|--------------|----------------------|---------------------|
| Execution Time | {comparison['execution_time_comparison']['single_agent']:.2f}s | {comparison['execution_time_comparison']['multi_agent_sequential']:.2f}s | {comparison['execution_time_comparison']['multi_agent_parallel']:.2f}s |
| Cost | ${comparison['cost_comparison']['single_agent']:.4f} | ${comparison['cost_comparison']['multi_agent_sequential']:.4f} | ${comparison['cost_comparison']['multi_agent_parallel']:.4f} |
| Success Rate | {'✅' if comparison['success_rate_comparison']['single_agent'] else '❌'} | {'✅' if comparison['success_rate_comparison']['multi_agent_sequential'] else '❌'} | {'✅' if comparison['success_rate_comparison']['multi_agent_parallel'] else '❌'} |
"""
    
    def _format_failure_analysis(self, failures: List[FailureAnalysis]) -> str:
        """Format failure analysis section."""
        if not failures:
            return "✅ No failures detected across all test scenarios."
        
        analysis = f"❌ {len(failures)} failure(s) detected:\n\n"
        for i, failure in enumerate(failures, 1):
            analysis += f"""
### Failure {i}: {failure.error_category.value.replace('_', ' ').title()}

**Root Cause:** {failure.root_cause}
**Error Message:** {failure.error_message}
**Suggested Fixes:**
{chr(10).join(f'- {fix}' for fix in failure.suggested_fixes)}

"""
        return analysis
    
    def _generate_recommendations(self, results: ComprehensiveTestResults) -> str:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if not results.overall_success:
            recommendations.append("🔧 **Critical:** Address all failing tests before production use")
        
        # Performance recommendations
        perf = results.performance_comparison
        if perf:
            fastest_mode = min(perf['execution_time_comparison'], key=perf['execution_time_comparison'].get)
            cheapest_mode = min(perf['cost_comparison'], key=perf['cost_comparison'].get)
            
            recommendations.append(f"⚡ **Performance:** {fastest_mode.replace('_', ' ').title()} mode is fastest")
            recommendations.append(f"💰 **Cost:** {cheapest_mode.replace('_', ' ').title()} mode is most cost-effective")
        
        if results.failure_analysis:
            error_categories = [f.error_category for f in results.failure_analysis]
            most_common = max(set(error_categories), key=error_categories.count)
            recommendations.append(f"🎯 **Focus Area:** Address {most_common.value.replace('_', ' ')} issues first")
        
        if not recommendations:
            recommendations.append("✅ **Excellent:** All tests passed successfully!")
        
        return "\n".join(recommendations)