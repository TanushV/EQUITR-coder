"""
Main controller for comprehensive mode testing.
"""

import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import ComprehensiveTestConfig
from .results import (
    ComprehensiveTestResults,
    SingleAgentTestResults,
    MultiAgentTestResults,
    TestResult,
    FailureAnalysis
)


class ComprehensiveModeTestController:
    """Main controller for comprehensive mode testing."""
    
    def __init__(self, config: Optional[ComprehensiveTestConfig] = None):
        """Initialize the test controller."""
        self.config = config or ComprehensiveTestConfig()
        
        # Create test run ID with timestamp
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set up test directories
        self.test_run_dir = self.config.get_test_run_dir(self.test_run_id)
        self.test_run_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        from .environment_manager import IsolatedTestEnvironmentManager
        self.environment_manager = IsolatedTestEnvironmentManager(str(self.test_run_dir))
        self.error_analyzer = None  # Will be implemented in task 5
        self.auto_fix_engine = None  # Will be implemented in task 6
        self.report_generator = None  # Will be implemented in task 8
        
        # Results tracking
        self.all_test_results: List[TestResult] = []
        self.failure_analyses: List[FailureAnalysis] = []
        
        if self.config.verbose_output:
            print("🧪 Initialized comprehensive mode test controller")
            print(f"📁 Test run directory: {self.test_run_dir}")
            print(f"🤖 Model: {self.config.model}")
            print(f"💰 Max cost per test: ${self.config.max_cost_per_test}")
            print(f"🔄 Max iterations per test: {self.config.max_iterations_per_test}")
    
    async def run_comprehensive_tests(self) -> ComprehensiveTestResults:
        """Run all test modes and return comprehensive results."""
        if self.config.verbose_output:
            print("\n🚀 Starting comprehensive testing of EquitrCoder...")
            print("="*80)
        
        start_time = time.time()
        
        try:
            # Validate environment before starting
            issues = self.config.validate_environment()
            if issues:
                raise RuntimeError(f"Environment validation failed: {'; '.join(issues)}")
            
            # Run single agent tests
            if self.config.verbose_output:
                print("\n" + "="*60)
                print("🤖 SINGLE AGENT TESTING")
                print("="*60)
            single_agent_results = await self.run_single_agent_tests()
            
            # Run multi-agent sequential tests
            if self.config.verbose_output:
                print("\n" + "="*60)
                print("👥 MULTI-AGENT SEQUENTIAL TESTING")
                print("="*60)
            multi_agent_sequential_results = await self.run_multi_agent_sequential_tests()
            
            # Run multi-agent parallel tests
            if self.config.verbose_output:
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
                failure_analysis=self.failure_analyses.copy(),
                performance_comparison=performance_comparison,
                test_timestamp=datetime.now().isoformat(),
                test_run_id=self.test_run_id
            )
            
            # Save results
            await self._save_results(comprehensive_results)
            
            if self.config.verbose_output:
                print("\n📊 Comprehensive testing completed!")
                print(f"📁 Results saved to: {self.test_run_dir}")
                print(f"⏱️  Total execution time: {total_execution_time:.2f} seconds")
                print(f"💰 Total cost: ${total_cost:.4f}")
                print(f"✅ Overall success: {overall_success}")
                print(f"📈 Success rate: {comprehensive_results.get_success_rate():.1%}")
            
            return comprehensive_results
            
        except Exception as e:
            if self.config.verbose_output:
                print(f"❌ Comprehensive testing failed: {str(e)}")
                if self.config.verbose_output:
                    traceback.print_exc()
            raise
    
    async def run_single_agent_tests(self) -> SingleAgentTestResults:
        """Run single agent test scenarios."""
        from .single_agent_suite import SingleAgentTestSuite
        
        # Create test suite
        test_suite = SingleAgentTestSuite(self.config, self.environment_manager)
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Collect results for tracking
        self.all_test_results.extend([
            results.document_creation,
            results.todo_completion,
            results.agent_execution,
            results.audit_functionality
        ])
        
        # Collect failure analyses
        for test_result in [results.document_creation, results.todo_completion, 
                           results.agent_execution, results.audit_functionality]:
            if test_result.failure_analysis:
                self.failure_analyses.append(test_result.failure_analysis)
        
        return results
    
    async def run_multi_agent_sequential_tests(self) -> MultiAgentTestResults:
        """Run multi-agent sequential test scenarios."""
        from .multi_agent_suite import MultiAgentTestSuite
        
        # Create test suite for sequential mode
        test_suite = MultiAgentTestSuite(self.config, self.environment_manager, parallel_mode=False)
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Collect results for tracking
        self.all_test_results.extend([
            results.document_creation,
            results.todo_completion,
            results.agent_coordination,
            results.audit_functionality
        ])
        
        # Collect failure analyses
        for test_result in [results.document_creation, results.todo_completion, 
                           results.agent_coordination, results.audit_functionality]:
            if test_result.failure_analysis:
                self.failure_analyses.append(test_result.failure_analysis)
        
        return results
    
    async def run_multi_agent_parallel_tests(self) -> MultiAgentTestResults:
        """Run multi-agent parallel test scenarios."""
        from .multi_agent_suite import MultiAgentTestSuite
        
        # Create test suite for parallel mode
        test_suite = MultiAgentTestSuite(self.config, self.environment_manager, parallel_mode=True)
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Collect results for tracking
        test_results = [
            results.document_creation,
            results.todo_completion,
            results.agent_coordination,
            results.audit_functionality
        ]
        
        if results.parallel_execution:
            test_results.append(results.parallel_execution)
        
        self.all_test_results.extend(test_results)
        
        # Collect failure analyses
        for test_result in test_results:
            if test_result.failure_analysis:
                self.failure_analyses.append(test_result.failure_analysis)
        
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
            },
            'fastest_mode': min([
                ('single_agent', single.total_execution_time),
                ('multi_agent_sequential', sequential.total_execution_time),
                ('multi_agent_parallel', parallel.total_execution_time)
            ], key=lambda x: x[1])[0],
            'cheapest_mode': min([
                ('single_agent', single.total_cost),
                ('multi_agent_sequential', sequential.total_cost),
                ('multi_agent_parallel', parallel.total_cost)
            ], key=lambda x: x[1])[0]
        }
    
    async def _save_results(self, results: ComprehensiveTestResults):
        """Save test results to files."""
        # Save JSON results
        if self.config.results_format in ["json", "both"]:
            json_path = self.test_run_dir / "test_results.json"
            results.save_to_json(str(json_path))
            if self.config.verbose_output:
                print(f"📄 JSON results saved to: {json_path}")
        
        # Save markdown report (will be implemented in task 8)
        if self.config.results_format in ["markdown", "both"]:
            report_path = self.test_run_dir / "comprehensive_test_report.md"
            # Placeholder for now
            report_content = f"""# Comprehensive Test Report

**Test Run ID:** {self.test_run_id}
**Timestamp:** {results.test_timestamp}
**Overall Success:** {'✅ PASSED' if results.overall_success else '❌ FAILED'}
**Total Execution Time:** {results.total_execution_time:.2f} seconds
**Total Cost:** ${results.total_cost:.4f}

## Summary

This is a placeholder report. Full reporting will be implemented in task 8.

## Results

- Single Agent: {'✅ PASSED' if results.single_agent_results.overall_success else '❌ FAILED'}
- Multi-Agent Sequential: {'✅ PASSED' if results.multi_agent_sequential_results.overall_success else '❌ FAILED'}
- Multi-Agent Parallel: {'✅ PASSED' if results.multi_agent_parallel_results.overall_success else '❌ FAILED'}

---
*Report generated by EquitrCoder Comprehensive Testing Framework*
"""
            report_path.write_text(report_content)
            if self.config.verbose_output:
                print(f"📄 Markdown report saved to: {report_path}")
    
    def get_test_run_directory(self) -> Path:
        """Get the test run directory."""
        return self.test_run_dir
    
    def get_all_test_results(self) -> List[TestResult]:
        """Get all test results."""
        return self.all_test_results.copy()
    
    def get_failure_analyses(self) -> List[FailureAnalysis]:
        """Get all failure analyses."""
        return self.failure_analyses.copy()