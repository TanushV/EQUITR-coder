"""
Single Agent Test Suite

This module implements comprehensive testing for single agent mode.
"""

import asyncio
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from .comprehensive_test_framework import (
    TestResult, TestStatus, PerformanceMetrics, FailureAnalysis, 
    ErrorCategory, SingleAgentTestResults
)
from .test_environment_manager import TestEnvironmentManager, TestEnvironmentConfig


class SingleAgentTestSuite:
    """Test suite for single agent functionality."""
    
    def __init__(self, test_config, environment_manager: TestEnvironmentManager):
        self.test_config = test_config
        self.environment_manager = environment_manager
        self.model = test_config.model
    
    async def run_all_tests(self) -> SingleAgentTestResults:
        """Run all single agent tests."""
        print("🤖 Starting single agent test suite...")
        start_time = time.time()
        
        # Run individual tests
        doc_result = await self.test_document_creation()
        todo_result = await self.test_todo_completion()
        exec_result = await self.test_agent_execution()
        audit_result = await self.test_audit_functionality()
        
        # Calculate overall results
        total_time = time.time() - start_time
        total_cost = doc_result.cost + todo_result.cost + exec_result.cost + audit_result.cost
        overall_success = all([
            doc_result.success, todo_result.success, 
            exec_result.success, audit_result.success
        ])
        
        return SingleAgentTestResults(
            document_creation=doc_result,
            todo_completion=todo_result,
            agent_execution=exec_result,
            audit_functionality=audit_result,
            overall_success=overall_success,
            total_execution_time=total_time,
            total_cost=total_cost
        )
    
    async def test_document_creation(self) -> TestResult:
        """Test document creation functionality."""
        print("📄 Testing single agent document creation...")
        start_time = time.time()
        
        try:
            # Create isolated environment
            env_config = TestEnvironmentConfig(
                environment_name="single_agent_docs",
                model=self.model,
                test_task=self.test_config.test_task
            )
            env_path = self.environment_manager.create_isolated_environment(
                "single_agent_docs", env_config
            )
            
            # Import and test document workflow
            from equitrcoder.core.document_workflow import DocumentWorkflowManager
            
            doc_manager = DocumentWorkflowManager(model=self.model)
            result = await doc_manager.create_documents_programmatic(
                user_prompt=self.test_config.test_task,
                project_path=str(env_path)
            )
            
            # Validate results
            success = result.success
            if success and result.requirements_path and result.design_path and result.todos_path:
                success = all([
                    Path(result.requirements_path).exists(),
                    Path(result.design_path).exists(),
                    Path(result.todos_path).exists()
                ])
            else:
                success = False
            
            execution_time = time.time() - start_time
            
            if success:
                print("✅ Document creation test passed")
                return TestResult(
                    test_name="single_agent_document_creation",
                    status=TestStatus.COMPLETED,
                    success=True,
                    execution_time=execution_time,
                    cost=0.5,  # Estimated cost
                    iterations=1,
                    artifacts=[
                        result.requirements_path,
                        result.design_path,
                        result.todos_path
                    ] if result.success else None
                )
            else:
                error_msg = result.error or "Document creation failed validation"
                print(f"❌ Document creation test failed: {error_msg}")
                return TestResult(
                    test_name="single_agent_document_creation",
                    status=TestStatus.FAILED,
                    success=False,
                    execution_time=execution_time,
                    cost=0.2,
                    iterations=1,
                    error_message=error_msg,
                    root_cause="Document creation or validation failed"
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            print(f"❌ Document creation test error: {error_msg}")
            
            return TestResult(
                test_name="single_agent_document_creation",
                status=TestStatus.FAILED,
                success=False,
                execution_time=execution_time,
                cost=0.1,
                iterations=0,
                error_message=error_msg,
                root_cause="Exception during document creation test",
                failure_analysis=FailureAnalysis(
                    error_category=ErrorCategory.DOCUMENT_CREATION_ERROR,
                    root_cause="Exception during document creation",
                    error_message=error_msg,
                    stack_trace=traceback.format_exc(),
                    suggested_fixes=[
                        "Check API key configuration",
                        "Verify model availability",
                        "Check network connectivity"
                    ],
                    context={"model": self.model, "task": self.test_config.test_task}
                )
            )
    
    async def test_todo_completion(self) -> TestResult:
        """Test todo completion functionality."""
        print("✅ Testing single agent todo completion...")
        start_time = time.time()
        
        try:
            # Create isolated environment
            env_config = TestEnvironmentConfig(
                environment_name="single_agent_todos",
                model=self.model,
                test_task=self.test_config.test_task
            )
            env_path = self.environment_manager.create_isolated_environment(
                "single_agent_todos", env_config
            )
            
            # For now, simulate todo completion test
            await asyncio.sleep(1)  # Simulate processing time
            
            execution_time = time.time() - start_time
            
            # This is a placeholder - actual implementation would test todo system
            print("⚠️ Todo completion test not fully implemented yet")
            return TestResult(
                test_name="single_agent_todo_completion",
                status=TestStatus.SKIPPED,
                success=False,
                execution_time=execution_time,
                cost=0.0,
                iterations=0,
                error_message="Test not yet implemented",
                root_cause="Implementation pending"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            print(f"❌ Todo completion test error: {error_msg}")
            
            return TestResult(
                test_name="single_agent_todo_completion",
                status=TestStatus.FAILED,
                success=False,
                execution_time=execution_time,
                cost=0.0,
                iterations=0,
                error_message=error_msg,
                root_cause="Exception during todo completion test"
            )
    
    async def test_agent_execution(self) -> TestResult:
        """Test basic agent execution functionality."""
        print("🤖 Testing single agent execution...")
        start_time = time.time()
        
        try:
            # Create isolated environment
            env_config = TestEnvironmentConfig(
                environment_name="single_agent_exec",
                model=self.model,
                test_task=self.test_config.test_task
            )
            env_path = self.environment_manager.create_isolated_environment(
                "single_agent_exec", env_config
            )
            
            # Test programmatic interface
            from equitrcoder.programmatic.interface import EquitrCoder, TaskConfiguration
            
            # Create single agent coder
            coder = EquitrCoder(
                mode="single",
                repo_path=str(env_path),
                git_enabled=False  # Disable git for testing
            )
            
            # Create task configuration
            task_config = TaskConfiguration(
                description=self.test_config.test_task,
                max_cost=2.0,
                max_iterations=10,
                model=self.model
            )
            
            # Execute task
            result = await coder.execute_task(
                task_description=self.test_config.test_task,
                config=task_config
            )
            
            execution_time = time.time() - start_time
            
            if result.success:
                print("✅ Agent execution test passed")
                return TestResult(
                    test_name="single_agent_execution",
                    status=TestStatus.COMPLETED,
                    success=True,
                    execution_time=execution_time,
                    cost=result.cost,
                    iterations=result.iterations,
                    performance_metrics=PerformanceMetrics(
                        execution_time=execution_time,
                        cost=result.cost,
                        iterations=result.iterations
                    )
                )
            else:
                error_msg = result.error or "Agent execution failed"
                print(f"❌ Agent execution test failed: {error_msg}")
                return TestResult(
                    test_name="single_agent_execution",
                    status=TestStatus.FAILED,
                    success=False,
                    execution_time=execution_time,
                    cost=result.cost,
                    iterations=result.iterations,
                    error_message=error_msg,
                    root_cause="Agent execution failed"
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            print(f"❌ Agent execution test error: {error_msg}")
            
            return TestResult(
                test_name="single_agent_execution",
                status=TestStatus.FAILED,
                success=False,
                execution_time=execution_time,
                cost=0.0,
                iterations=0,
                error_message=error_msg,
                root_cause="Exception during agent execution test",
                failure_analysis=FailureAnalysis(
                    error_category=ErrorCategory.EXECUTION_ERROR,
                    root_cause="Exception during agent execution",
                    error_message=error_msg,
                    stack_trace=traceback.format_exc(),
                    suggested_fixes=[
                        "Check programmatic interface setup",
                        "Verify model configuration",
                        "Check environment isolation"
                    ],
                    context={"model": self.model, "task": self.test_config.test_task}
                )
            )
    
    async def test_audit_functionality(self) -> TestResult:
        """Test audit functionality."""
        print("🔍 Testing single agent audit functionality...")
        start_time = time.time()
        
        try:
            # Create isolated environment
            env_config = TestEnvironmentConfig(
                environment_name="single_agent_audit",
                model=self.model,
                test_task=self.test_config.test_task
            )
            env_path = self.environment_manager.create_isolated_environment(
                "single_agent_audit", env_config
            )
            
            # For now, simulate audit test
            await asyncio.sleep(1)  # Simulate processing time
            
            execution_time = time.time() - start_time
            
            # This is a placeholder - actual implementation would test audit system
            print("⚠️ Audit functionality test not fully implemented yet")
            return TestResult(
                test_name="single_agent_audit",
                status=TestStatus.SKIPPED,
                success=False,
                execution_time=execution_time,
                cost=0.0,
                iterations=0,
                error_message="Test not yet implemented",
                root_cause="Implementation pending"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            print(f"❌ Audit functionality test error: {error_msg}")
            
            return TestResult(
                test_name="single_agent_audit",
                status=TestStatus.FAILED,
                success=False,
                execution_time=execution_time,
                cost=0.0,
                iterations=0,
                error_message=error_msg,
                root_cause="Exception during audit functionality test"
            )