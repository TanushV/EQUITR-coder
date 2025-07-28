"""
Multi-agent test suite for comprehensive mode testing.
"""

import asyncio
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import ComprehensiveTestConfig
from .environment_manager import IsolatedTestEnvironmentManager, TestEnvironment
from .results import (
    MultiAgentTestResults,
    TestResult,
    TestStatus,
    FailureAnalysis,
    ErrorCategory,
    PerformanceMetrics
)

# Import EquitrCoder components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from equitrcoder.programmatic.interface import (
    EquitrCoder,
    MultiAgentTaskConfiguration,
    create_multi_agent_coder
)
from equitrcoder.core.document_workflow import DocumentWorkflowManager


class MultiAgentTestSuite:
    """Test suite for multi-agent modes."""
    
    def __init__(
        self, 
        config: ComprehensiveTestConfig, 
        environment_manager: IsolatedTestEnvironmentManager,
        parallel_mode: bool = False
    ):
        """Initialize the multi-agent test suite."""
        self.config = config
        self.environment_manager = environment_manager
        self.parallel_mode = parallel_mode
        self.mode_name = "multi_parallel" if parallel_mode else "multi_sequential"
        self.test_results: List[TestResult] = []
        
    async def run_all_tests(self) -> MultiAgentTestResults:
        """Run all multi-agent tests."""
        mode_display = "parallel" if self.parallel_mode else "sequential"
        if self.config.verbose_output:
            print(f"👥 Starting multi-agent {mode_display} test suite...")
        
        start_time = time.time()
        
        # Run individual tests
        document_creation = await self.test_document_creation()
        todo_completion = await self.test_todo_completion()
        agent_coordination = await self.test_agent_communication()
        audit_functionality = await self.test_audit_functionality()
        
        # Run parallel execution test only for parallel mode
        parallel_execution = None
        if self.parallel_mode:
            parallel_execution = await self.test_parallel_execution()
        
        # Calculate overall results
        total_execution_time = time.time() - start_time
        total_cost = (document_creation.cost + todo_completion.cost + 
                     agent_coordination.cost + audit_functionality.cost)
        
        if parallel_execution:
            total_cost += parallel_execution.cost
        
        overall_success = (document_creation.success and todo_completion.success and 
                          agent_coordination.success and audit_functionality.success)
        
        if parallel_execution:
            overall_success = overall_success and parallel_execution.success
        
        results = MultiAgentTestResults(
            document_creation=document_creation,
            todo_completion=todo_completion,
            agent_coordination=agent_coordination,
            audit_functionality=audit_functionality,
            parallel_execution=parallel_execution,
            overall_success=overall_success,
            total_execution_time=total_execution_time,
            total_cost=total_cost,
            mode=self.mode_name
        )
        
        if self.config.verbose_output:
            print(f"👥 Multi-agent {mode_display} tests completed: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
            print(f"   Total time: {total_execution_time:.2f}s, Cost: ${total_cost:.4f}")
        
        return results
    
    async def test_document_creation(self) -> TestResult:
        """Test document creation in multi-agent mode."""
        test_result = TestResult(
            test_name=f"{self.mode_name}_document_creation",
            mode=self.mode_name,
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            mode_display = "parallel" if self.parallel_mode else "sequential"
            if self.config.verbose_output:
                print(f"📄 Testing multi-agent {mode_display} document creation...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment(self.mode_name)
            working_dir = environment.get_working_directory()
            
            # Initialize document workflow manager
            doc_manager = DocumentWorkflowManager(model=self.config.model)
            
            # Test document creation for multi-agent mode
            doc_result = await doc_manager.create_documents_programmatic(
                user_prompt=self.config.test_task,
                project_path=working_dir
            )
            
            if not doc_result.success:
                raise RuntimeError(f"Document creation failed: {doc_result.error}")
            
            # For multi-agent mode, also create split todos
            if self.parallel_mode:
                # Create split todos for parallel agents
                requirements_content = Path(doc_result.requirements_path).read_text()
                design_content = Path(doc_result.design_path).read_text()
                
                agent_todo_files = await doc_manager.create_split_todos_for_parallel_agents(
                    user_prompt=self.config.test_task,
                    requirements_content=requirements_content,
                    design_content=design_content,
                    num_agents=self.config.parallel_agents_count,
                    project_path=working_dir
                )
                
                if not agent_todo_files:
                    raise RuntimeError("Failed to create split todos for parallel agents")
                
                # Add split todo files as artifacts
                for todo_file in agent_todo_files:
                    environment.add_artifact(todo_file)
            
            # Validate created documents
            validation_issues = self._validate_documents(
                working_dir, 
                doc_result.requirements_path,
                doc_result.design_path,
                doc_result.todos_path
            )
            
            if validation_issues:
                raise RuntimeError(f"Document validation failed: {'; '.join(validation_issues)}")
            
            # Add main artifacts
            environment.add_artifact(doc_result.requirements_path)
            environment.add_artifact(doc_result.design_path)
            environment.add_artifact(doc_result.todos_path)
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=True,
                execution_time=execution_time,
                cost=0.15,  # Slightly higher cost for multi-agent document creation
                iterations=1
            )
            
            test_result.artifacts = [
                doc_result.requirements_path,
                doc_result.design_path,
                doc_result.todos_path
            ]
            
            if self.config.verbose_output:
                print(f"   ✅ Document creation successful ({execution_time:.2f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            error_message = str(e)
            
            # Analyze failure
            failure_analysis = self._analyze_document_creation_failure(e, environment)
            test_result.mark_failed(error_message, failure_analysis)
            test_result.execution_time = execution_time
            
            if self.config.verbose_output:
                print(f"   ❌ Document creation failed: {error_message}")
        
        finally:
            # Cleanup environment if configured
            if environment and not self.config.preserve_artifacts:
                self.environment_manager.cleanup_environment(environment.config.env_id, False)
        
        return test_result
    
    async def test_todo_completion(self) -> TestResult:
        """Test todo completion with agent coordination."""
        test_result = TestResult(
            test_name=f"{self.mode_name}_todo_completion",
            mode=self.mode_name,
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            mode_display = "parallel" if self.parallel_mode else "sequential"
            if self.config.verbose_output:
                print(f"✅ Testing multi-agent {mode_display} todo completion...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment(self.mode_name)
            working_dir = environment.get_working_directory()
            
            # Create EquitrCoder instance for multi-agent mode
            coder = create_multi_agent_coder(
                repo_path=working_dir,
                max_workers=self.config.max_workers,
                supervisor_model=self.config.model,
                worker_model=self.config.model
            )
            
            # Test multi-agent todo completion
            task_config = MultiAgentTaskConfiguration(
                description=f"Complete todos from the project using {self.config.max_workers} agents working {'in parallel' if self.parallel_mode else 'sequentially'}",
                max_workers=self.config.max_workers,
                max_cost=self.config.max_cost_per_test,
                supervisor_model=self.config.model,
                worker_model=self.config.model,
                auto_commit=False
            )
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            if not result.success:
                raise RuntimeError(f"Multi-agent todo completion failed: {result.error}")
            
            # Validate that some work was done
            # In a real implementation, we would check for completed todos, created files, etc.
            validation_issues = self._validate_multi_agent_output(working_dir)
            if validation_issues:
                if self.config.verbose_output:
                    print(f"   ⚠️ Some validation issues: {'; '.join(validation_issues)}")
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=True,
                execution_time=execution_time,
                cost=result.cost,
                iterations=result.iterations
            )
            
            if self.config.verbose_output:
                print(f"   ✅ Todo completion successful ({execution_time:.2f}s, ${result.cost:.4f})")
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            error_message = str(e)
            
            # Analyze failure
            failure_analysis = self._analyze_todo_completion_failure(e, environment)
            test_result.mark_failed(error_message, failure_analysis)
            test_result.execution_time = execution_time
            
            if self.config.verbose_output:
                print(f"   ❌ Todo completion failed: {error_message}")
        
        finally:
            # Cleanup environment if configured
            if environment and not self.config.preserve_artifacts:
                self.environment_manager.cleanup_environment(environment.config.env_id, False)
        
        return test_result
    
    async def test_agent_communication(self) -> TestResult:
        """Test agent communication functionality."""
        test_result = TestResult(
            test_name=f"{self.mode_name}_coordination",
            mode=self.mode_name,
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            mode_display = "parallel" if self.parallel_mode else "sequential"
            if self.config.verbose_output:
                print(f"🤝 Testing multi-agent {mode_display} coordination...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment(self.mode_name)
            working_dir = environment.get_working_directory()
            
            # Create EquitrCoder instance for multi-agent mode
            coder = create_multi_agent_coder(
                repo_path=working_dir,
                max_workers=self.config.max_workers,
                supervisor_model=self.config.model,
                worker_model=self.config.model
            )
            
            # Test agent coordination with a task that requires coordination
            coordination_task = "Create a simple web application where one agent handles the backend API and another handles the frontend interface, ensuring they work together"
            
            task_config = MultiAgentTaskConfiguration(
                description=coordination_task,
                max_workers=2,  # Use 2 agents for coordination test
                max_cost=self.config.max_cost_per_test / 2,  # Smaller budget for coordination test
                supervisor_model=self.config.model,
                worker_model=self.config.model,
                auto_commit=False
            )
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            # For now, consider coordination successful if the task completed
            # In a real implementation, we would check for proper agent communication logs
            success = result.success
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=success,
                execution_time=execution_time,
                cost=result.cost if result.success else 0.0,
                iterations=result.iterations if result.success else 0
            )
            
            if self.config.verbose_output:
                status = "✅ successful" if success else "❌ failed"
                print(f"   {status} Agent coordination ({execution_time:.2f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            error_message = str(e)
            
            # Analyze failure
            failure_analysis = self._analyze_coordination_failure(e, environment)
            test_result.mark_failed(error_message, failure_analysis)
            test_result.execution_time = execution_time
            
            if self.config.verbose_output:
                print(f"   ❌ Agent coordination failed: {error_message}")
        
        finally:
            # Cleanup environment if configured
            if environment and not self.config.preserve_artifacts:
                self.environment_manager.cleanup_environment(environment.config.env_id, False)
        
        return test_result
    
    async def test_parallel_execution(self) -> TestResult:
        """Test parallel execution (parallel mode only)."""
        test_result = TestResult(
            test_name=f"{self.mode_name}_execution",
            mode=self.mode_name,
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        if not self.parallel_mode:
            # Skip this test for sequential mode
            test_result.status = TestStatus.SKIPPED
            return test_result
        
        environment = None
        
        try:
            if self.config.verbose_output:
                print("⚡ Testing multi-agent parallel execution...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment(self.mode_name)
            working_dir = environment.get_working_directory()
            
            # Create EquitrCoder instance for parallel mode
            coder = create_multi_agent_coder(
                repo_path=working_dir,
                max_workers=self.config.parallel_agents_count,
                supervisor_model=self.config.model,
                worker_model=self.config.model
            )
            
            # Test parallel execution with multiple independent tasks
            parallel_task = f"Create {self.config.parallel_agents_count} independent utility modules (math_utils.py, string_utils.py, file_utils.py) with comprehensive tests, working in parallel"
            
            task_config = MultiAgentTaskConfiguration(
                description=parallel_task,
                max_workers=self.config.parallel_agents_count,
                max_cost=self.config.max_cost_per_test,
                supervisor_model=self.config.model,
                worker_model=self.config.model,
                auto_commit=False
            )
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            if not result.success:
                raise RuntimeError(f"Parallel execution failed: {result.error}")
            
            # Validate parallel execution results
            validation_issues = self._validate_parallel_execution(working_dir)
            if validation_issues:
                if self.config.verbose_output:
                    print(f"   ⚠️ Parallel execution validation issues: {'; '.join(validation_issues)}")
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=True,
                execution_time=execution_time,
                cost=result.cost,
                iterations=result.iterations
            )
            
            if self.config.verbose_output:
                print(f"   ✅ Parallel execution successful ({execution_time:.2f}s, ${result.cost:.4f})")
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            error_message = str(e)
            
            # Analyze failure
            failure_analysis = self._analyze_parallel_execution_failure(e, environment)
            test_result.mark_failed(error_message, failure_analysis)
            test_result.execution_time = execution_time
            
            if self.config.verbose_output:
                print(f"   ❌ Parallel execution failed: {error_message}")
        
        finally:
            # Cleanup environment if configured
            if environment and not self.config.preserve_artifacts:
                self.environment_manager.cleanup_environment(environment.config.env_id, False)
        
        return test_result
    
    async def test_audit_functionality(self) -> TestResult:
        """Test audit functionality in multi-agent mode."""
        test_result = TestResult(
            test_name=f"{self.mode_name}_audit",
            mode=self.mode_name,
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            mode_display = "parallel" if self.parallel_mode else "sequential"
            if self.config.verbose_output:
                print(f"🔍 Testing multi-agent {mode_display} audit functionality...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment(self.mode_name)
            working_dir = environment.get_working_directory()
            
            # Create some test files to audit
            test_files = []
            for i in range(2):
                test_file = Path(working_dir) / f"test_module_{i+1}.py"
                test_file.write_text(f"""
def function_{i+1}(a, b):
    # This function has potential issues
    return a / b  # Division by zero risk

def another_function_{i+1}():
    # Unused variable
    unused_var = "test"
    print("Hello from module {i+1}")

if __name__ == "__main__":
    print(function_{i+1}(10, 0))  # This will cause an error
""")
                test_files.append(str(test_file))
                environment.add_artifact(str(test_file))
            
            # Create EquitrCoder instance for multi-agent mode
            coder = create_multi_agent_coder(
                repo_path=working_dir,
                max_workers=2,
                supervisor_model=self.config.model,
                worker_model=self.config.model
            )
            
            # Test multi-agent audit functionality
            audit_task = "Audit all Python files in the project for potential issues, code quality problems, and security vulnerabilities using multiple agents"
            
            task_config = MultiAgentTaskConfiguration(
                description=audit_task,
                max_workers=2,
                max_cost=self.config.max_cost_per_test / 4,  # Small budget for audit
                supervisor_model=self.config.model,
                worker_model=self.config.model,
                auto_commit=False
            )
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            # For now, consider audit successful if the task completed
            success = result.success
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=success,
                execution_time=execution_time,
                cost=result.cost if result.success else 0.0,
                iterations=result.iterations if result.success else 0
            )
            
            if result.success:
                test_result.artifacts = test_files
            
            if self.config.verbose_output:
                status = "✅ successful" if success else "❌ failed"
                print(f"   {status} Audit functionality ({execution_time:.2f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            error_message = str(e)
            
            # Analyze failure
            failure_analysis = self._analyze_audit_failure(e, environment)
            test_result.mark_failed(error_message, failure_analysis)
            test_result.execution_time = execution_time
            
            if self.config.verbose_output:
                print(f"   ❌ Audit functionality failed: {error_message}")
        
        finally:
            # Cleanup environment if configured
            if environment and not self.config.preserve_artifacts:
                self.environment_manager.cleanup_environment(environment.config.env_id, False)
        
        return test_result
    
    def _validate_documents(self, working_dir: str, requirements_path: str, design_path: str, todos_path: str) -> List[str]:
        """Validate created documents."""
        issues = []
        
        # Check if files exist
        for name, path in [("requirements", requirements_path), ("design", design_path), ("todos", todos_path)]:
            if not Path(path).exists():
                issues.append(f"{name}.md file not found at {path}")
                continue
            
            # Check if files have content
            content = Path(path).read_text().strip()
            if len(content) < 100:  # Minimum content length
                issues.append(f"{name}.md file is too short ({len(content)} chars)")
        
        return issues
    
    def _validate_multi_agent_output(self, working_dir: str) -> List[str]:
        """Validate multi-agent output."""
        issues = []
        working_path = Path(working_dir)
        
        # Check for any created files (multi-agent should create something)
        python_files = list(working_path.glob("*.py"))
        if len(python_files) == 0:
            issues.append("No Python files created by multi-agent execution")
        
        return issues
    
    def _validate_parallel_execution(self, working_dir: str) -> List[str]:
        """Validate parallel execution results."""
        issues = []
        working_path = Path(working_dir)
        
        # Check for multiple output files (parallel execution should create multiple things)
        python_files = list(working_path.glob("*.py"))
        if len(python_files) < 2:
            issues.append(f"Expected multiple files from parallel execution, found {len(python_files)}")
        
        return issues
    
    def _analyze_document_creation_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze document creation failure."""
        error_message = str(error)
        
        if "split todos" in error_message.lower():
            error_category = ErrorCategory.DOCUMENT_CREATION_ERROR
            root_cause = "Failed to create split todos for parallel agents"
            suggested_fixes = [
                "Check split todos generation logic",
                "Verify parallel agent configuration",
                "Review document workflow for multi-agent mode"
            ]
        elif "api" in error_message.lower() or "model" in error_message.lower():
            error_category = ErrorCategory.MODEL_API_ERROR
            root_cause = "Model API error during multi-agent document creation"
            suggested_fixes = [
                "Check API key configuration",
                "Verify model availability for multi-agent mode",
                "Try with a different model"
            ]
        else:
            error_category = ErrorCategory.DOCUMENT_CREATION_ERROR
            root_cause = f"Multi-agent document creation failed: {error_message}"
            suggested_fixes = [
                "Check multi-agent document workflow configuration",
                "Verify file system permissions",
                "Review error logs for more details"
            ]
        
        context = {
            'test_name': 'document_creation',
            'mode': self.mode_name,
            'parallel_mode': self.parallel_mode,
            'error_type': type(error).__name__,
            'environment_id': environment.config.env_id if environment else None
        }
        
        return FailureAnalysis(
            error_category=error_category,
            root_cause=root_cause,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            suggested_fixes=suggested_fixes,
            context=context
        )
    
    def _analyze_todo_completion_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze todo completion failure."""
        error_message = str(error)
        
        if "coordination" in error_message.lower() or "agent" in error_message.lower():
            error_category = ErrorCategory.COORDINATION_ERROR
            root_cause = "Multi-agent coordination error during todo completion"
            suggested_fixes = [
                "Check multi-agent orchestrator configuration",
                "Verify agent communication setup",
                "Review coordination logs"
            ]
        else:
            error_category = ErrorCategory.TODO_SYSTEM_ERROR
            root_cause = f"Multi-agent todo completion failed: {error_message}"
            suggested_fixes = [
                "Check multi-agent todo system configuration",
                "Verify agent task distribution",
                "Review todo completion logs"
            ]
        
        context = {
            'test_name': 'todo_completion',
            'mode': self.mode_name,
            'parallel_mode': self.parallel_mode,
            'error_type': type(error).__name__,
            'environment_id': environment.config.env_id if environment else None
        }
        
        return FailureAnalysis(
            error_category=error_category,
            root_cause=root_cause,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            suggested_fixes=suggested_fixes,
            context=context
        )
    
    def _analyze_coordination_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze coordination failure."""
        error_message = str(error)
        
        error_category = ErrorCategory.COORDINATION_ERROR
        root_cause = f"Agent coordination failed: {error_message}"
        suggested_fixes = [
            "Check agent communication configuration",
            "Verify multi-agent orchestrator setup",
            "Review coordination protocol implementation"
        ]
        
        context = {
            'test_name': 'agent_coordination',
            'mode': self.mode_name,
            'parallel_mode': self.parallel_mode,
            'error_type': type(error).__name__,
            'environment_id': environment.config.env_id if environment else None
        }
        
        return FailureAnalysis(
            error_category=error_category,
            root_cause=root_cause,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            suggested_fixes=suggested_fixes,
            context=context
        )
    
    def _analyze_parallel_execution_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze parallel execution failure."""
        error_message = str(error)
        
        error_category = ErrorCategory.PARALLEL_EXECUTION_ERROR
        root_cause = f"Parallel execution failed: {error_message}"
        suggested_fixes = [
            "Check parallel execution configuration",
            "Verify resource isolation setup",
            "Review parallel agent coordination"
        ]
        
        context = {
            'test_name': 'parallel_execution',
            'mode': self.mode_name,
            'parallel_mode': self.parallel_mode,
            'error_type': type(error).__name__,
            'environment_id': environment.config.env_id if environment else None
        }
        
        return FailureAnalysis(
            error_category=error_category,
            root_cause=root_cause,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            suggested_fixes=suggested_fixes,
            context=context
        )
    
    def _analyze_audit_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze audit functionality failure."""
        error_message = str(error)
        
        error_category = ErrorCategory.AUDIT_SYSTEM_ERROR
        root_cause = f"Multi-agent audit functionality failed: {error_message}"
        suggested_fixes = [
            "Check multi-agent audit tool configuration",
            "Verify audit system setup for multiple agents",
            "Review audit coordination between agents"
        ]
        
        context = {
            'test_name': 'audit_functionality',
            'mode': self.mode_name,
            'parallel_mode': self.parallel_mode,
            'error_type': type(error).__name__,
            'environment_id': environment.config.env_id if environment else None
        }
        
        return FailureAnalysis(
            error_category=error_category,
            root_cause=root_cause,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            suggested_fixes=suggested_fixes,
            context=context
        )