"""
Enhanced Multi-Agent Orchestrator with robust features from core orchestrator.
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from ..agents.worker_agent import WorkerAgent
from ..agents.base_agent import BaseAgent
from ..core.session import SessionManagerV2, SessionData
from ..core.context_manager import ContextManager
from ..core.supervisor import SupervisorAgent
from ..repository.indexer import RepositoryIndexer
from ..tools.builtin.ask_supervisor import AskSupervisor
from ..providers.litellm import LiteLLMProvider, Message
from ..tools.discovery import discover_tools


@dataclass
class TaskResult:
    """Result of a multi-agent task."""
    task_id: str
    worker_id: str
    success: bool
    result: Any = None
    error: str = None
    execution_time: float = 0.0
    cost: float = 0.0
    tokens_used: int = 0
    iteration_count: int = 0


@dataclass
class WorkerConfig:
    """Configuration for a worker agent."""
    worker_id: str
    scope_paths: List[str]
    allowed_tools: List[str]
    max_cost: Optional[float] = None
    max_iterations: Optional[int] = None


class MultiAgentOrchestrator:
    """Enhanced orchestrator for coordinating multiple worker agents with robust features."""

    def __init__(
        self,
        supervisor_provider: Optional[LiteLLMProvider] = None,
        worker_provider: Optional[LiteLLMProvider] = None,
        session_manager: Optional[SessionManagerV2] = None,
        repo_path: str = ".",
        max_concurrent_workers: int = 3,
        global_cost_limit: float = 10.0,
        max_total_iterations: int = 100,
        context_max_tokens: int = 8000
    ):
        self.supervisor_provider = supervisor_provider
        self.worker_provider = worker_provider
        self.repo_path = Path(repo_path)
        self.max_concurrent_workers = max_concurrent_workers
        self.global_cost_limit = global_cost_limit
        self.max_total_iterations = max_total_iterations
        
        # Initialize session management
        self.session_manager = session_manager or SessionManagerV2()
        
        # Initialize context management
        self.context_manager = ContextManager(
            max_tokens=context_max_tokens,
            model=getattr(supervisor_provider, "model", "gpt-4") if supervisor_provider else "gpt-4"
        )
        
        # Initialize repository indexer
        self.repo_indexer = RepositoryIndexer(repo_path=str(self.repo_path))
        
        # Initialize supervisor if provider available
        self.supervisor = None
        if supervisor_provider:
            self.supervisor = SupervisorAgent(
                supervisor_provider,
                self.session_manager,
                str(self.repo_path),
                use_multi_agent=True,
                worker_provider=worker_provider
            )

        # Runtime state
        self.workers: Dict[str, WorkerAgent] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: List[TaskResult] = []
        self.total_cost = 0.0
        self.total_iterations = 0
        
        # Callbacks
        self.on_task_start_callback: Optional[Callable] = None
        self.on_task_complete_callback: Optional[Callable] = None
        self.on_worker_message_callback: Optional[Callable] = None
        self.on_cost_update_callback: Optional[Callable] = None

    def create_worker(
        self,
        config: WorkerConfig,
        provider: Optional[LiteLLMProvider] = None
    ) -> WorkerAgent:
        """Create and register a new worker agent."""
        worker_provider = provider or self.worker_provider
        
        worker = WorkerAgent(
            worker_id=config.worker_id,
            scope_paths=config.scope_paths,
            allowed_tools=config.allowed_tools,
            project_root=str(self.repo_path),
            provider=worker_provider,
            max_cost=config.max_cost,
            max_iterations=config.max_iterations
        )

        # Set up callbacks
        if self.on_worker_message_callback:
            worker.on_message_callback = self.on_worker_message_callback
        
        if self.on_cost_update_callback:
            worker.on_cost_update_callback = self._handle_worker_cost_update

        # Register worker with message pool for inter-agent communication
        asyncio.create_task(self._register_worker_with_message_pool(config.worker_id))

        # Add communication tools to worker
        from ..tools.builtin.agent_communication import create_agent_communication_tools
        comm_tools = create_agent_communication_tools(config.worker_id)
        for tool in comm_tools:
            worker.add_tool(tool)

        self.workers[config.worker_id] = worker
        return worker

    async def _register_worker_with_message_pool(self, worker_id: str):
        """Register a worker with the global message pool."""
        from ..core.message_pool import message_pool
        await message_pool.register_agent(worker_id)

    def _handle_worker_cost_update(self, total_cost: float, delta: float):
        """Handle cost updates from workers."""
        self.total_cost += delta
        if self.on_cost_update_callback:
            self.on_cost_update_callback(self.total_cost, delta)

    async def execute_task(
        self,
        task_id: str,
        worker_id: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> TaskResult:
        """Execute a task using a specific worker."""
        if worker_id not in self.workers:
            return TaskResult(
                task_id=task_id,
                worker_id=worker_id,
                success=False,
                error=f"Worker {worker_id} not found",
            )

        worker = self.workers[worker_id]
        start_time = time.time()
        start_cost = worker.current_cost

        # Register supervisor with message pool if not already registered
        from ..core.message_pool import message_pool, MessageType
        try:
            await message_pool.register_agent("supervisor")
        except:
            pass  # Already registered

        # Call task start callback
        if self.on_task_start_callback:
            self.on_task_start_callback(task_id, worker_id, task_description)

        # Send coordination message to worker
        await message_pool.send_message(
            sender_agent="supervisor",
            content=f"Starting task: {task_description}",
            message_type=MessageType.COORDINATION,
            recipient_agent=worker_id,
            task_id=task_id,
            metadata={"task_assignment": True}
        )

        try:
            # Create or load session
            if session_id:
                session = self.session_manager.load_session(session_id)
                if not session:
                    session = self.session_manager.create_session(session_id)
            else:
                session = self.session_manager.create_session()
            
            worker.session = session

            # Check global limits
            if self.total_cost >= self.global_cost_limit:
                raise Exception(f"Global cost limit ({self.global_cost_limit}) exceeded")
            
            if self.total_iterations >= self.max_total_iterations:
                raise Exception(f"Global iteration limit ({self.max_total_iterations}) exceeded")

            # Add task context
            if context:
                worker.add_message("system", f"Task context: {json.dumps(context)}")
            
            # Add task message
            worker.add_message("user", task_description)

            # Execute task
            result = await self._execute_worker_task(worker, task_description, context)
            
            # Send completion message
            await message_pool.send_message(
                sender_agent=worker_id,
                content=f"Completed task: {task_description}",
                message_type=MessageType.STATUS_UPDATE,
                task_id=task_id,
                metadata={"task_completed": True, "success": True}
            )
            
            # Update session
            session.cost += worker.current_cost - start_cost
            session.iteration_count = worker.iteration_count
            await self.session_manager._save_session_to_disk(session)

            execution_time = time.time() - start_time
            cost_delta = worker.current_cost - start_cost
            
            task_result = TaskResult(
                task_id=task_id,
                worker_id=worker_id,
                success=True,
                result=result,
                execution_time=execution_time,
                cost=cost_delta,
                tokens_used=result.get("tokens_used", 0) if isinstance(result, dict) else 0,
                iteration_count=worker.iteration_count
            )

            self.task_results.append(task_result)
            self.total_iterations += worker.iteration_count

            # Call task complete callback
            if self.on_task_complete_callback:
                self.on_task_complete_callback(task_result)

            return task_result

        except Exception as e:
            # Send error message
            await message_pool.send_message(
                sender_agent=worker_id,
                content=f"Task failed: {str(e)}",
                message_type=MessageType.ERROR,
                task_id=task_id,
                metadata={"task_completed": True, "success": False}
            )
            
            execution_time = time.time() - start_time
            cost_delta = worker.current_cost - start_cost
            
            task_result = TaskResult(
                task_id=task_id,
                worker_id=worker_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                cost=cost_delta,
                iteration_count=worker.iteration_count
            )

            self.task_results.append(task_result)
            
            # Call task complete callback
            if self.on_task_complete_callback:
                self.on_task_complete_callback(task_result)

            return task_result

    async def _execute_worker_task(
        self,
        worker: WorkerAgent,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the actual task using the worker."""
        
        # Get initial messages from worker
        messages = [Message(role=m['role'], content=m['content']) for m in worker.get_messages()]
        
        # Add system prompt if no system message exists
        if not messages or messages[0].role != 'system':
            system_prompt = f'You are a worker agent named {worker.agent_id}. Use the available tools to complete the task. Be thorough and create working code.'
            messages.insert(0, Message(role='system', content=system_prompt))
        
        # Get available tools and their schemas
        available_tools = worker.get_available_tools()
        tool_schemas = []
        for tool_name in available_tools:
            if worker.can_use_tool(tool_name):
                tool = worker.tool_registry[tool_name]
                tool_schemas.append(tool.get_json_schema())
        
        iteration = 0
        max_iterations = worker.max_iterations or 10
        
        # Use worker's provider for LLM calls
        provider = self.worker_provider
        if not provider:
            # Create a default provider if none exists
            provider = LiteLLMProvider(model="moonshot/kimi-k2-0711-preview")
        
        while iteration < max_iterations:
            iteration += 1
            worker.iteration_count = iteration
            
            try:
                # Call LLM with tool schemas
                response = await provider.chat(
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None
                )
                
                # Update cost tracking
                if hasattr(response, 'cost') and response.cost:
                    worker.current_cost += response.cost
                
                # Add assistant message
                assistant_message = Message(role='assistant', content=response.content or "Working...")
                messages.append(assistant_message)
                
                # Add to worker messages
                worker.add_message('assistant', response.content or "Working...")
                
                # Handle tool calls
                if response.tool_calls:
                    tool_results = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function['name']
                        tool_args = json.loads(tool_call.function['arguments'])
                        
                        # Execute tool through worker
                        if worker.can_use_tool(tool_name):
                            tool_result = await worker.call_tool(tool_name, **tool_args)
                            result_content = str(tool_result['result'] if tool_result['success'] else tool_result['error'])
                            
                            # Add to worker messages (for logging/history)
                            worker.add_message('tool', result_content, {
                                'tool_name': tool_name,
                                'success': tool_result['success']
                            })
                            
                            tool_results.append(f"Tool {tool_name}: {result_content}")
                        else:
                            error_msg = f'Tool {tool_name} not available'
                            
                            # Add to worker messages (for logging/history)
                            worker.add_message('tool', error_msg, {
                                'tool_name': tool_name,
                                'error': 'Tool not available'
                            })
                            
                            tool_results.append(f"Error: {error_msg}")
                    
                    # Add a user message with tool results so LLM knows what happened
                    if tool_results:
                        results_message = "Tool execution results:\n" + "\n".join(tool_results)
                        user_message = Message(role='user', content=results_message)
                        messages.append(user_message)
                        
                        # Add to worker messages too
                        worker.add_message('user', results_message, {'system_generated': True})
                    
                    # Continue to next iteration
                    continue
                else:
                    # No tool calls, task is complete
                    break
                    
            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                worker.add_message('system', error_msg, {'error': True})
                break
        
        return {
            "task_description": task_description,
            "final_response": messages[-1].content if messages else '',
            "iterations": iteration,
            "total_tokens": 0,  # TODO: Track tokens properly
            "worker_status": worker.get_status(),
            "tokens_used": 100  # Mock value for now
        }

    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[TaskResult]:
        """Execute multiple tasks in parallel with proper concurrency control."""
        # Limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_concurrent_workers)

        async def execute_with_semaphore(task_info):
            async with semaphore:
                return await self.execute_task(**task_info)

        # Execute tasks concurrently
        task_coroutines = [execute_with_semaphore(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Handle exceptions
        task_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_results.append(
                    TaskResult(
                        task_id=tasks[i].get("task_id", f"task_{i}"),
                        worker_id=tasks[i].get("worker_id", "unknown"),
                        success=False,
                        error=str(result),
                    )
                )
            else:
                task_results.append(result)

        return task_results

    async def coordinate_workers(
        self,
        coordination_task: str,
        worker_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Coordinate multiple workers with supervisor oversight."""
        if not self.supervisor:
            # Fallback to simple parallel execution
            results = await self.execute_parallel_tasks(worker_tasks)
            
            # ALWAYS check and trigger audit after task completion
            print("🔍 Checking if audit should be triggered...")
            try:
                await self._check_and_trigger_audit()
            except Exception as audit_error:
                print(f"⚠️ Audit check failed: {audit_error}")
                # Continue execution even if audit fails
            
            return {
                "coordination_task": coordination_task,
                "worker_results": results,
                "success": all(r.success for r in results)
            }
        
        # Use supervisor for coordination
        try:
            # Execute worker tasks
            worker_results = await self.execute_parallel_tasks(worker_tasks)
            
            # Get supervisor analysis
            supervisor_context = {
                "coordination_task": coordination_task,
                "worker_results": [r.__dict__ for r in worker_results],
                "total_cost": self.total_cost,
                "total_iterations": self.total_iterations
            }
            
            # This would involve calling the supervisor to analyze results
            # For now, return a simple coordination result
            coordination_result = {
                "coordination_task": coordination_task,
                "worker_results": worker_results,
                "supervisor_analysis": "Tasks completed successfully",
                "success": all(r.success for r in worker_results),
                "total_cost": sum(r.cost for r in worker_results),
                "total_time": sum(r.execution_time for r in worker_results)
            }
            
            # ALWAYS check and trigger audit after successful coordination
            print("🔍 Checking if audit should be triggered...")
            try:
                await self._check_and_trigger_audit()
            except Exception as audit_error:
                print(f"⚠️ Audit check failed: {audit_error}")
                # Continue execution even if audit fails
            
            return coordination_result
            
        except Exception as e:
            return {
                "coordination_task": coordination_task,
                "success": False,
                "error": str(e),
                "worker_results": []
            }

    async def _check_and_trigger_audit(self, task_name: str = None):
        """Check if audit should be triggered and run it using supervisor with infinite loop."""
        try:
            # Import audit manager
            from ..tools.builtin.audit import audit_manager

            # Check if audit should be triggered for specific task
            if not audit_manager.should_trigger_audit(task_name):
                return False

            print(f"🔍 All todos completed for task: {task_name or 'all todos'}! Triggering automatic audit...")

            # Use supervisor if available, otherwise create a specialized audit worker
            if self.supervisor:
                await self.supervisor.trigger_audit()
            else:
                # Fallback: create an audit worker if no supervisor - with infinite loop
                await self._trigger_audit_with_worker_loop(task_name)

            return True

        except Exception as e:
            print(f"⚠️ Multi-agent audit trigger error: {e}")
            return False

    async def _trigger_audit_with_worker_loop(self, task_name: str = None):
        """Trigger audit using a dedicated audit worker with infinite loop when no supervisor is available."""
        try:
            from ..tools.builtin.audit import audit_manager
            
            # Infinite audit loop with failure tracking
            while True:
                print(f"🔍 Starting audit with dedicated worker for task: {task_name or 'all todos'}...")

                # Get audit context for specific task
                audit_context = audit_manager.get_audit_context(task_name)
                if not audit_context:
                    print("ℹ️  No audit needed - no completed todos found")
                    break

                # Create audit worker config
                audit_config = WorkerConfig(
                    worker_id="audit_worker",
                    scope_paths=["."],
                    allowed_tools=["read_file", "list_files", "grep_search", "git_status", "git_diff", "create_todo"],
                    max_cost=1.0,  # Small budget for audit
                    max_iterations=20
                )

                # Create audit worker
                audit_worker = self.create_worker(audit_config)

                # Execute audit task
                audit_result = await self.execute_task(
                    task_id="audit_task",
                    worker_id="audit_worker",
                    task_description=f"""
Perform comprehensive audit of the completed project:

{audit_context}

Use available tools to:
1. list_files - examine project structure
2. read_file - review design documents, requirements, and implementations  
3. grep_search - verify implementations match requirements
4. Check code quality and completeness

Determine if project is complete and faithful to requirements.
If complete: conclude with "AUDIT PASSED"
If issues found: conclude with "AUDIT FAILED" and list specific issues for fixing
""",
                    context={"audit": True}
                )

                # Process audit result and extract reason
                audit_result_content = ""
                audit_passed = False
                audit_reason = ""

                if audit_result.success:
                    audit_result_content = str(audit_result.result)
                    if "AUDIT PASSED" in audit_result_content:
                        print("✅ Multi-agent audit completed successfully!")
                        audit_passed = True
                        # Extract reason after "AUDIT PASSED"
                        lines = audit_result_content.split('\n')
                        for line in lines:
                            if line.strip().startswith("REASON FOR PASSING:") or "AUDIT PASSED" in line:
                                audit_reason = line.replace("AUDIT PASSED", "").replace("REASON FOR PASSING:", "").strip()
                                if audit_reason.startswith("-"):
                                    audit_reason = audit_reason[1:].strip()
                                break
                        if not audit_reason:
                            audit_reason = "Audit passed but no specific reason provided"
                    elif "AUDIT FAILED" in audit_result_content:
                        print("❌ Multi-agent audit failed - issues found")
                        audit_passed = False
                        # Extract reason after "AUDIT FAILED"
                        lines = audit_result_content.split('\n')
                        for line in lines:
                            if line.strip().startswith("REASON FOR FAILING:") or "AUDIT FAILED" in line:
                                audit_reason = line.replace("AUDIT FAILED", "").replace("REASON FOR FAILING:", "").strip()
                                if audit_reason.startswith("-"):
                                    audit_reason = audit_reason[1:].strip()
                                break
                        if not audit_reason:
                            audit_reason = "Audit failed but no specific reason provided"
                    else:
                        print("⚠️ Multi-agent audit completed with unclear result")
                        audit_passed = False
                        audit_reason = "Audit result unclear - no AUDIT PASSED/FAILED found"
                else:
                    print("❌ Multi-agent audit execution failed")
                    audit_result_content = audit_result.error or "Audit execution failed"
                    audit_passed = False
                    audit_reason = "Audit execution failed"

                # Record audit result with reason and determine next action
                should_continue = audit_manager.record_audit_result(audit_passed, audit_result_content, audit_reason)
                
                if audit_passed:
                    # Audit passed - exit the loop
                    break
                elif not should_continue:
                    # Escalated to user - exit the loop
                    print("🚨 Audit has been escalated to user - stopping audit loop")
                    break
                else:
                    # Audit failed but should continue - create todos and loop again
                    audit_manager.create_todos_from_audit_failure(audit_result_content, audit_reason)
                    print("🔄 New todos created from audit findings. Continuing audit cycle...")
                    
                    # Small delay before next audit attempt
                    import asyncio
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"⚠️ Audit worker creation error: {e}")
            
            # Record the exception as an audit failure
            from ..tools.builtin.audit import audit_manager
            audit_manager.record_audit_result(False, f"Audit system error: {str(e)}")
            audit_manager.create_todos_from_audit_failure(f"Audit system error: {str(e)}")

    def get_worker_status(self, worker_id: str) -> Dict[str, Any]:
        """Get status of a specific worker."""
        if worker_id not in self.workers:
            return {"error": f"Worker {worker_id} not found"}

        worker = self.workers[worker_id]
        return worker.get_worker_status()

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status."""
        successful_tasks = sum(1 for r in self.task_results if r.success)
        failed_tasks = len(self.task_results) - successful_tasks
        
        return {
            "orchestrator_type": "multi_agent",
            "total_workers": len(self.workers),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results),
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "total_cost": self.total_cost,
            "cost_limit": self.global_cost_limit,
            "total_iterations": self.total_iterations,
            "iteration_limit": self.max_total_iterations,
            "max_concurrent_workers": self.max_concurrent_workers,
            "has_supervisor": self.supervisor is not None,
            "repo_path": str(self.repo_path)
        }

    def set_callbacks(
        self,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_worker_message: Optional[Callable] = None,
        on_cost_update: Optional[Callable] = None
    ):
        """Set callback functions for monitoring."""
        self.on_task_start_callback = on_task_start
        self.on_task_complete_callback = on_task_complete
        self.on_worker_message_callback = on_worker_message
        self.on_cost_update_callback = on_cost_update

    async def shutdown(self):
        """Shutdown all workers and clean up resources."""
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(
                *self.active_tasks.values(), return_exceptions=True
            )

        # Unregister workers from message pool
        from ..core.message_pool import message_pool
        for worker_id in self.workers.keys():
            await message_pool.unregister_agent(worker_id)

        # Reset workers
        for worker in self.workers.values():
            worker.reset()

        # Clear state
        self.workers.clear()
        self.active_tasks.clear()
        
        # Save final session state
        if hasattr(self, 'session_manager'):
            await self.session_manager._flush_dirty_sessions()


# Global orchestrator instance for backward compatibility
_orchestrator = None


def get_orchestrator(project_root: str = ".") -> MultiAgentOrchestrator:
    """Get global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator(repo_path=project_root)
    return _orchestrator


async def run_multi_agent_workflow(project_root: str = ".") -> Dict[str, Any]:
    """Convenience function to run the multi-agent workflow."""
    orchestrator = get_orchestrator(project_root)
    # This would need to be implemented based on specific workflow requirements
    return {"message": "Multi-agent workflow completed", "orchestrator_status": orchestrator.get_orchestrator_status()}
