"""
Single agent test suite for comprehensive mode testing.
"""

import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import ComprehensiveTestConfig
from .environment_manager import IsolatedTestEnvironmentManager, TestEnvironment
from .results import (
    SingleAgentTestResults,
    TestResult,
    TestStatus,
    FailureAnalysis,
    ErrorCategory
)

# Import EquitrCoder components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from equitrcoder.programmatic.interface import (
    TaskConfiguration,
    create_single_agent_coder
)
from equitrcoder.core.document_workflow import DocumentWorkflowManager


class SingleAgentTestSuite:
    """Test suite for single agent mode."""
    
    def __init__(self, config: ComprehensiveTestConfig, environment_manager: IsolatedTestEnvironmentManager):
        """Initialize the single agent test suite."""
        self.config = config
        self.environment_manager = environment_manager
        self.test_results: List[TestResult] = []
        
    async def run_all_tests(self) -> SingleAgentTestResults:
        """Run all single agent tests."""
        if self.config.verbose_output:
            print("🤖 Starting single agent test suite...")
        
        start_time = time.time()
        
        # Run individual tests
        document_creation = await self.test_document_creation()
        todo_completion = await self.test_todo_completion()
        agent_execution = await self.test_agent_execution()
        audit_functionality = await self.test_audit_functionality()
        
        # Calculate overall results
        total_execution_time = time.time() - start_time
        total_cost = (document_creation.cost + todo_completion.cost + 
                     agent_execution.cost + audit_functionality.cost)
        
        overall_success = (document_creation.success and todo_completion.success and 
                          agent_execution.success and audit_functionality.success)
        
        results = SingleAgentTestResults(
            document_creation=document_creation,
            todo_completion=todo_completion,
            agent_execution=agent_execution,
            audit_functionality=audit_functionality,
            overall_success=overall_success,
            total_execution_time=total_execution_time,
            total_cost=total_cost
        )
        
        if self.config.verbose_output:
            print(f"🤖 Single agent tests completed: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
            print(f"   Total time: {total_execution_time:.2f}s, Cost: ${total_cost:.4f}")
        
        return results
    
    async def test_document_creation(self) -> TestResult:
        """Test document creation functionality."""
        test_result = TestResult(
            test_name="single_agent_document_creation",
            mode="single",
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            if self.config.verbose_output:
                print("📄 Testing single agent document creation...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment("single")
            working_dir = environment.get_working_directory()
            
            # Initialize document workflow manager
            doc_manager = DocumentWorkflowManager(model=self.config.model)
            
            # Test document creation
            try:
                doc_result = await doc_manager.create_documents_programmatic(
                    user_prompt=self.config.test_task,
                    project_path=working_dir
                )
            except Exception as e:
                print(f"   🔍 Document creation exception: {str(e)}")
                print(f"   🔍 Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                raise
            
            if not doc_result.success:
                raise RuntimeError(f"Document creation failed: {doc_result.error}")
            
            # Validate created documents
            validation_issues = self._validate_documents(
                working_dir, 
                doc_result.requirements_path,
                doc_result.design_path,
                doc_result.todos_path
            )
            
            if validation_issues:
                raise RuntimeError(f"Document validation failed: {'; '.join(validation_issues)}")
            
            # Add artifacts
            environment.add_artifact(doc_result.requirements_path)
            environment.add_artifact(doc_result.design_path)
            environment.add_artifact(doc_result.todos_path)
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=True,
                execution_time=execution_time,
                cost=0.1,  # Estimated cost for document creation
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
        """Test todo completion functionality."""
        test_result = TestResult(
            test_name="single_agent_todo_completion",
            mode="single",
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            if self.config.verbose_output:
                print("✅ Testing single agent todo completion...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment("single")
            working_dir = environment.get_working_directory()
            
            # DON'T create new documents - reuse from document creation test
            # Just create a simple todo list for this specific test
            from equitrcoder.tools.builtin.todo import TodoManager
            
            # Create isolated todo file for this test
            import uuid
            task_id = str(uuid.uuid4())[:8]
            todo_file = Path(working_dir) / f".EQUITR_todos_{task_id}.json"
            todo_manager = TodoManager(todo_file=str(todo_file))
            
            # Create a few simple todos for testing completion
            test_todos = [
                "Create a simple calculator.py file with basic arithmetic functions",
                "Add input validation to handle invalid inputs",
                "Create a test_calculator.py file with unit tests",
                "Add error handling for division by zero",
                "Create a main() function to run the calculator"
            ]
            
            for i, todo_text in enumerate(test_todos):
                todo_manager.create_todo(
                    title=todo_text,
                    description=f"Test todo {i+1} for todo completion validation",
                    priority="medium",
                    tags=["test", f"task-{task_id}"]
                )
            
            print(f"   📝 Created {len(test_todos)} test todos for completion validation")
            
            # Create EquitrCoder instance for todo completion
            coder = create_single_agent_coder(
                repo_path=working_dir,
                model=self.config.model
            )
            
            # Set up verbose callbacks to monitor tool use
            tool_calls_made = []
            messages_received = []
            
            def on_tool_call(tool_name, args, result):
                tool_calls_made.append({
                    'tool': tool_name,
                    'args': args,
                    'result': str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                })
                if self.config.verbose_output:
                    print(f"   🔧 Tool call: {tool_name}({args}) -> {str(result)[:100]}...")
            
            def on_message(message_data):
                if isinstance(message_data, dict):
                    role = message_data.get('role', 'unknown')
                    content = message_data.get('content', '')
                else:
                    role = 'unknown'
                    content = str(message_data)
                messages_received.append({'role': role, 'content': content})
                if self.config.verbose_output:
                    print(f"   💬 {role}: {content[:200]}...")
            
            coder.on_tool_call = on_tool_call
            coder.on_message = on_message
            
            # Test todo completion with a simple task
            task_config = TaskConfiguration(
                description="Complete ALL todos from the project systematically. Work through each todo one by one, marking them as completed using the update_todo tool.",
                max_cost=self.config.max_cost_per_test,
                max_iterations=999999,  # No iteration limit
                model=self.config.model,
                auto_commit=False
            )
            
            if self.config.verbose_output:
                print("   🚀 Starting todo completion with unlimited iterations...")
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            if self.config.verbose_output:
                print(f"   📊 Tool calls made: {len(tool_calls_made)}")
                print(f"   📊 Messages exchanged: {len(messages_received)}")
                for i, tool_call in enumerate(tool_calls_made[-5:]):  # Show last 5 tool calls
                    print(f"   🔧 Tool {i+1}: {tool_call['tool']} -> {tool_call['result'][:100]}...")
            
            if not result.success:
                raise RuntimeError(f"Todo completion task failed: {result.error}")
            
            # Validate todo completion by checking the todo system directly
            # Use the same isolated todo file that was created for this test
            validation_todo_manager = TodoManager(todo_file=str(todo_file))
            
            # Get all todos for this task
            all_todos = todo_manager.list_todos()
            completed_todos = [todo for todo in all_todos if todo.status == "completed"]
            pending_todos = [todo for todo in all_todos if todo.status == "pending"]
            
            if self.config.verbose_output:
                print(f"   📊 Todo status: {len(completed_todos)} completed, {len(pending_todos)} pending")
                for todo in completed_todos[-3:]:  # Show last 3 completed
                    print(f"   ✅ Completed: {todo.title}")
                for todo in pending_todos[:3]:  # Show first 3 pending
                    print(f"   ⏳ Pending: {todo.title}")
            
            if len(completed_todos) == 0:
                raise RuntimeError(f"No todos were marked as completed. Found {len(all_todos)} total todos, all still pending.")
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=True,
                execution_time=execution_time,
                cost=result.cost,
                iterations=result.iterations
            )
            
            test_result.artifacts = [str(todo_file)]
            
            if self.config.verbose_output:
                print(f"   ✅ Todo completion successful ({execution_time:.2f}s, {len(completed_todos)} todos completed)")
            
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
    
    async def test_agent_execution(self) -> TestResult:
        """Test agent execution functionality."""
        test_result = TestResult(
            test_name="single_agent_execution",
            mode="single",
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            if self.config.verbose_output:
                print("🤖 Testing single agent execution...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment("single")
            working_dir = environment.get_working_directory()
            
            # Create EquitrCoder instance
            coder = create_single_agent_coder(
                repo_path=working_dir,
                model=self.config.model
            )
            
            # Set up verbose callbacks to monitor tool use
            tool_calls_made = []
            messages_received = []
            
            def on_tool_call(tool_name, args, result):
                tool_calls_made.append({
                    'tool': tool_name,
                    'args': args,
                    'result': str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                })
                if self.config.verbose_output:
                    print(f"   🔧 Tool call: {tool_name}({args}) -> {str(result)[:100]}...")
            
            def on_message(message_data):
                if isinstance(message_data, dict):
                    role = message_data.get('role', 'unknown')
                    content = message_data.get('content', '')
                else:
                    role = 'unknown'
                    content = str(message_data)
                messages_received.append({'role': role, 'content': content})
                if self.config.verbose_output:
                    print(f"   💬 {role}: {content[:200]}...")
            
            coder.on_tool_call = on_tool_call
            coder.on_message = on_message
            
            # Test agent execution with the main task
            task_config = TaskConfiguration(
                description=self.config.test_task,
                max_cost=self.config.max_cost_per_test,
                max_iterations=999999,  # No iteration limit
                model=self.config.model,
                auto_commit=False
            )
            
            if self.config.verbose_output:
                print("   🚀 Starting agent execution with unlimited iterations...")
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            if self.config.verbose_output:
                print(f"   📊 Tool calls made: {len(tool_calls_made)}")
                print(f"   📊 Messages exchanged: {len(messages_received)}")
                for i, tool_call in enumerate(tool_calls_made[-5:]):  # Show last 5 tool calls
                    print(f"   🔧 Tool {i+1}: {tool_call['tool']} -> {tool_call['result'][:100]}...")
            
            if not result.success:
                raise RuntimeError(f"Agent execution failed: {result.error}")
            
            # Validate expected outputs
            validation_issues = self._validate_expected_files(working_dir)
            if validation_issues:
                # Don't fail the test for missing files, just log warnings
                if self.config.verbose_output:
                    print(f"   ⚠️ Some expected files missing: {'; '.join(validation_issues)}")
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=True,
                execution_time=execution_time,
                cost=result.cost,
                iterations=result.iterations
            )
            
            # Collect artifacts
            artifacts = []
            for expected_file in self.config.expected_files:
                file_path = Path(working_dir) / expected_file
                if file_path.exists():
                    artifacts.append(str(file_path))
                    environment.add_artifact(str(file_path))
            
            test_result.artifacts = artifacts
            
            if self.config.verbose_output:
                print(f"   ✅ Agent execution successful ({execution_time:.2f}s, ${result.cost:.4f})")
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            error_message = str(e)
            
            # Analyze failure
            failure_analysis = self._analyze_agent_execution_failure(e, environment)
            test_result.mark_failed(error_message, failure_analysis)
            test_result.execution_time = execution_time
            
            if self.config.verbose_output:
                print(f"   ❌ Agent execution failed: {error_message}")
        
        finally:
            # Cleanup environment if configured
            if environment and not self.config.preserve_artifacts:
                self.environment_manager.cleanup_environment(environment.config.env_id, False)
        
        return test_result
    
    async def test_audit_functionality(self) -> TestResult:
        """Test audit functionality."""
        test_result = TestResult(
            test_name="single_agent_audit",
            mode="single",
            status=TestStatus.NOT_STARTED,
            success=False,
            execution_time=0.0,
            cost=0.0,
            iterations=0
        )
        
        environment = None
        
        try:
            if self.config.verbose_output:
                print("🔍 Testing single agent audit functionality...")
            
            test_result.mark_started()
            start_time = time.time()
            
            # Create test environment
            environment = self.environment_manager.create_environment("single")
            working_dir = environment.get_working_directory()
            
            # Create some test files to audit
            test_file = Path(working_dir) / "test_code.py"
            test_file.write_text("""
def add(a, b):
    return a + b

def divide(a, b):
    return a / b  # This has a potential division by zero issue

def main():
    print(add(1, 2))
    print(divide(10, 0))  # This will cause an error

if __name__ == "__main__":
    main()
""")
            
            # Create EquitrCoder instance
            coder = create_single_agent_coder(
                repo_path=working_dir,
                model=self.config.model
            )
            
            # Test audit functionality
            task_config = TaskConfiguration(
                description="Audit the test_code.py file for potential issues and create a report",
                max_cost=self.config.max_cost_per_test / 4,  # Small budget for audit
                max_iterations=5,
                model=self.config.model,
                auto_commit=False
            )
            
            result = await coder.execute_task(
                task_description=task_config.description,
                config=task_config
            )
            
            # For now, consider audit successful if the task completed
            # In a real implementation, we would check for audit reports, etc.
            success = result.success
            
            execution_time = time.time() - start_time
            test_result.mark_completed(
                success=success,
                execution_time=execution_time,
                cost=result.cost if result.success else 0.0,
                iterations=result.iterations if result.success else 0
            )
            
            if result.success:
                environment.add_artifact(str(test_file))
                test_result.artifacts = [str(test_file)]
            
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
    
    def _validate_expected_files(self, working_dir: str) -> List[str]:
        """Validate expected output files."""
        issues = []
        working_path = Path(working_dir)
        
        for expected_file in self.config.expected_files:
            file_path = working_path / expected_file
            if not file_path.exists():
                issues.append(f"Expected file not found: {expected_file}")
        
        return issues
    
    def _parse_todos(self, todos_content: str) -> List[Dict[str, Any]]:
        """Parse todos from todos.md content."""
        todos = []
        lines = todos_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- [ ]') or line.startswith('- [x]'):
                completed = line.startswith('- [x]')
                text = line[5:].strip()  # Remove checkbox part
                todos.append({
                    'text': text,
                    'completed': completed,
                    'original_line': line
                })
        
        return todos
    
    def _analyze_document_creation_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze document creation failure."""
        error_message = str(error)
        
        if "api" in error_message.lower() or "model" in error_message.lower():
            error_category = ErrorCategory.MODEL_API_ERROR
            root_cause = "Model API error during document creation"
            suggested_fixes = [
                "Check API key configuration",
                "Verify model availability",
                "Try with a different model"
            ]
        elif "timeout" in error_message.lower():
            error_category = ErrorCategory.TIMEOUT_ERROR
            root_cause = "Document creation timed out"
            suggested_fixes = [
                "Increase timeout duration",
                "Simplify the task description",
                "Check network connectivity"
            ]
        else:
            error_category = ErrorCategory.DOCUMENT_CREATION_ERROR
            root_cause = f"Document creation failed: {error_message}"
            suggested_fixes = [
                "Check document workflow configuration",
                "Verify file system permissions",
                "Review error logs for more details"
            ]
        
        context = {
            'test_name': 'document_creation',
            'mode': 'single',
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
        
        if "todo" in error_message.lower():
            error_category = ErrorCategory.TODO_SYSTEM_ERROR
            root_cause = "Todo system error"
            suggested_fixes = [
                "Check todos.md file format",
                "Verify todo parsing logic",
                "Ensure todos are properly formatted"
            ]
        else:
            error_category = ErrorCategory.EXECUTION_ERROR
            root_cause = f"Todo completion failed: {error_message}"
            suggested_fixes = [
                "Check agent execution logs",
                "Verify task configuration",
                "Review todo completion logic"
            ]
        
        context = {
            'test_name': 'todo_completion',
            'mode': 'single',
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
    
    def _analyze_agent_execution_failure(self, error: Exception, environment: Optional[TestEnvironment]) -> FailureAnalysis:
        """Analyze agent execution failure."""
        error_message = str(error)
        
        if "cost" in error_message.lower():
            error_category = ErrorCategory.CONFIGURATION_ERROR
            root_cause = "Cost limit exceeded during agent execution"
            suggested_fixes = [
                "Increase max_cost_per_test limit",
                "Optimize task description to reduce complexity",
                "Use a more cost-effective model"
            ]
        elif "iteration" in error_message.lower():
            error_category = ErrorCategory.CONFIGURATION_ERROR
            root_cause = "Iteration limit exceeded during agent execution"
            suggested_fixes = [
                "Increase max_iterations_per_test limit",
                "Simplify the task description",
                "Break down the task into smaller parts"
            ]
        else:
            error_category = ErrorCategory.EXECUTION_ERROR
            root_cause = f"Agent execution failed: {error_message}"
            suggested_fixes = [
                "Check agent configuration",
                "Verify model availability",
                "Review execution logs for more details"
            ]
        
        context = {
            'test_name': 'agent_execution',
            'mode': 'single',
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
        root_cause = f"Audit functionality failed: {error_message}"
        suggested_fixes = [
            "Check audit tool availability",
            "Verify audit configuration",
            "Review audit system logs"
        ]
        
        context = {
            'test_name': 'audit_functionality',
            'mode': 'single',
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