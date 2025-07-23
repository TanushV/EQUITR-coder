"""Supervisor for multi-agent task decomposition and coordination."""

import json
import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from .task import Task, TaskList
from .session import SessionManagerV2
from .message_pool import message_pool, MessageType
from ..providers.openrouter import OpenRouterProvider, Message
from ..tools.builtin.agent_communication import create_agent_communication_tools
from ..tools.builtin.git_auto import GitAutoCommit


class WorkerAgent:
    """Individual worker agent with restricted capabilities."""

    def __init__(
        self,
        name: str,
        tools: List[str],
        provider: OpenRouterProvider,
        session_manager: SessionManagerV2,
        repo_path: str,
    ):
        self.name = name
        self.tools = tools
        self.provider = provider
        self.session_manager = session_manager
        self.repo_path = repo_path
        self.current_task: Optional[Task] = None
        self.is_busy = False
        self.communication_tools = create_agent_communication_tools(name)

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with restricted tool access."""
        if self.is_busy:
            return {"success": False, "error": "Agent is busy"}

        self.is_busy = True
        self.current_task = task

        try:
            # Register agent with message pool
            await message_pool.register_agent(self.name)

            # Send status update to other agents
            await message_pool.send_message(
                sender_agent=self.name,
                content=f"Starting task: {task.description}",
                message_type=MessageType.STATUS_UPDATE,
                task_id=task.id,
                metadata={"task_status": "started"},
            )

            # Check for messages from other agents before starting
            messages = await message_pool.get_messages_for_agent(self.name)
            coordination_info = ""
            if messages:
                coordination_info = "\n\nRECENT MESSAGES FROM OTHER AGENTS:\n"
                for msg in messages[-3:]:  # Show last 3 messages
                    coordination_info += f"- {msg.sender_agent}: {msg.content}\n"

            # Create a focused prompt for the task with MANDATORY documentation context
            task_prompt = self._create_task_prompt(task) + coordination_info

            # CRITICAL VALIDATION: Ensure task prompt includes documentation context
            if "MANDATORY PROJECT DOCUMENTATION CONTEXT" not in task_prompt:
                # Add documentation context to task prompt
                task_prompt = f"""
MANDATORY PROJECT DOCUMENTATION CONTEXT:
[This task is part of a larger project. The full documentation context should be available from the supervisor.]

{task_prompt}

IMPORTANT: Reference the project requirements, design, and todo list when completing this task.
"""

            # Execute task using a restricted orchestrator (same as single-agent mode)
            result = await self._execute_task_with_orchestrator(task_prompt, task)

            # Send completion message to other agents
            await message_pool.send_message(
                sender_agent=self.name,
                content=f"Completed task: {task.description}. Result: {result[:100]}",
                message_type=MessageType.STATUS_UPDATE,
                task_id=task.id,
                metadata={"task_status": "completed", "result": result},
            )

            return {
                "success": True,
                "result": result,
                "agent": self.name,
                "task_id": task.id,
            }

        except Exception as e:
            # Send error message to other agents
            await message_pool.send_message(
                sender_agent=self.name,
                content=f"Error in task: {task.description}. Error: {str(e)}",
                message_type=MessageType.ERROR,
                task_id=task.id,
                metadata={"task_status": "failed", "error": str(e)},
            )

            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "task_id": task.id,
            }
        finally:
            self.is_busy = False
            self.current_task = None

    def _create_task_prompt(self, task: Task) -> str:
        """Create a focused prompt for the task."""
        prompt = f"""You are a specialized worker agent named '{self.name}'.

TASK: {task.description}

AVAILABLE TOOLS: {", ".join(self.tools + [tool.name for tool in self.communication_tools])}

FOCUS FILES: {", ".join(task.files) if task.files else "No specific files"}

COMMUNICATION TOOLS:
- send_agent_message: Send messages to other agents
- receive_agent_messages: Check for messages from other agents
- get_message_history: View message history
- get_active_agents: See which agents are active

INSTRUCTIONS:
- Focus ONLY on completing this specific task
- Use only the tools available to you: {", ".join(self.tools)}
- Communicate with other agents when coordination is needed
- Check for messages from other agents that might affect your work
- Send status updates to keep other agents informed
- Be concise and efficient
- When you're done, provide a clear summary of what was accomplished
- Do not attempt tasks outside your scope

Complete this task now."""

        return prompt

    async def _execute_task_with_orchestrator(
        self, task_prompt: str, task: Task
    ) -> str:
        """Execute task using a restricted orchestrator (same logic as single-agent mode)."""
        import asyncio
        import json
        from ..providers.openrouter import Message, ToolCall
        from ..tools import registry, discovery
        from ..repository.indexer import RepositoryIndexer
        from .context_manager import ContextManager
        from ..tools.base import ToolResult

        try:
            # Initialize tools (same as in orchestrator)
            discovery.discover_builtin_tools()
            discovery.discover_custom_tools()
            # Create a temporary session for this task
            temp_session = self.session_manager.create_session()

            # Add task prompt as user message
            user_message = Message(role="user", content=task_prompt)
            temp_session.messages.append(user_message)

            # Get repository context for the task
            repo_indexer = RepositoryIndexer(repo_path=self.repo_path)
            repo_context = await repo_indexer.get_context(task_prompt)

            # Build system prompt
            system_prompt = f"""You are EQUITR Coder, a specialized worker agent named '{self.name}'.

You have access to various tools for:
- File system operations (create, read, edit, list files)
- Git operations (commit, status, diff)
- Shell command execution (in a sandboxed environment)

Focus on completing the specific task assigned to you. Use tools efficiently and provide clear results.

Current working directory: {self.repo_path}
Agent name: {self.name}"""

            if repo_context:
                system_prompt += f"\n\nRepository context:\n{repo_context}"

            # Get conversation history
            messages = temp_session.messages.copy()

            # Add system message
            messages.insert(0, Message(role="system", content=system_prompt))

            # Get enabled tools (restricted to worker agent tools)
            all_tools = registry.get_all()
            enabled_tools = {
                name: tool for name, tool in all_tools.items() if name in self.tools
            }

            # Build tool schemas
            tool_schemas = [tool.get_json_schema() for tool in enabled_tools.values()]

            # Execute with unlimited iterations - continue until model indicates completion
            iteration = 0

            while True:
                iteration += 1

                # Call LLM with tools
                tools_to_use = tool_schemas if tool_schemas else None

                response = await self.provider.chat(
                    messages=messages,
                    tools=tools_to_use,
                    temperature=0.7,
                    max_tokens=4096,
                )

                # Add assistant message
                assistant_message = Message(role="assistant", content=response.content)

                # Handle tool calls if any
                if response.tool_calls:
                    # Add assistant message with tool calls
                    assistant_message.tool_calls = response.tool_calls
                    messages.append(assistant_message)

                    # Execute tools
                    tool_results = await self._execute_tools(
                        response.tool_calls, enabled_tools
                    )

                    # Add tool results to messages
                    for tool_call, result in zip(response.tool_calls, tool_results):
                        tool_message = Message(
                            role="tool", content=str(result), tool_call_id=tool_call.id
                        )
                        messages.append(tool_message)

                    # Continue to next iteration for follow-up response
                    continue
                else:
                    # No tool calls, task is complete
                    break

            # Return the final response content
            return (
                response.content
                or f"Task '{task.description}' completed by {self.name}"
            )

        except Exception as e:
            return f"Error executing task '{task.description}': {str(e)}"

    async def _execute_tools(self, tool_calls: list, enabled_tools: dict) -> list:
        """Execute tool calls concurrently."""
        tasks = []

        for tool_call in tool_calls:
            tool_name = tool_call.function["name"]
            tool_args = tool_call.function.get("arguments", {})

            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}

            if tool_name in enabled_tools:
                tool = enabled_tools[tool_name]
                tasks.append(tool.run(**tool_args))
            else:
                # Return error for unknown tool
                async def error_result():
                    from ..tools.base import ToolResult

                    return ToolResult(
                        success=False,
                        error=f"Tool '{tool_name}' not found or not enabled",
                    )

                tasks.append(error_result())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                from ..tools.base import ToolResult

                final_results.append(ToolResult(success=False, error=str(result)))
            else:
                final_results.append(result)

        return final_results


class SupervisorAgent:
    """Supervisor agent that coordinates multiple worker agents."""

    def __init__(
        self,
        provider: OpenRouterProvider,
        session_manager: SessionManagerV2,
        repo_path: str = ".",
        use_multi_agent: bool = False,
        worker_provider: Optional[OpenRouterProvider] = None,
    ):
        self.provider = provider
        self.worker_provider = (
            worker_provider or provider
        )  # Use separate provider for workers if provided
        self.session_manager = session_manager
        self.repo_path = repo_path
        self.use_multi_agent = use_multi_agent
        self.worker_agents: Dict[str, WorkerAgent] = {}
        self.task_queue = asyncio.Queue()
        self.worker_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent workers
        self.active_tasks: Set[str] = set()
        self.git_auto = GitAutoCommit(repo_path)

        # Initialize default worker agents
        self._initialize_workers()

        # Register supervisor with message pool
        asyncio.create_task(self._register_supervisor())

    def _initialize_workers(self):
        """Initialize default worker agents with specialized tools."""
        self.worker_agents = {
            "file_worker": WorkerAgent(
                name="file_worker",
                tools=["read_file", "write_file", "list_files", "create_file"],
                provider=self.worker_provider,
                session_manager=self.session_manager,
                repo_path=self.repo_path,
            ),
            "search_worker": WorkerAgent(
                name="search_worker",
                tools=["search_files", "grep_search", "web_search"],
                provider=self.worker_provider,
                session_manager=self.session_manager,
                repo_path=self.repo_path,
            ),
            "code_worker": WorkerAgent(
                name="code_worker",
                tools=["read_file", "write_file", "run_shell", "git_commit"],
                provider=self.worker_provider,
                session_manager=self.session_manager,
                repo_path=self.repo_path,
            ),
            "analysis_worker": WorkerAgent(
                name="analysis_worker",
                tools=["read_file", "search_files", "analyze_code"],
                provider=self.worker_provider,
                session_manager=self.session_manager,
                repo_path=self.repo_path,
            ),
        }

    async def _register_supervisor(self):
        """Register supervisor with message pool."""
        await message_pool.register_agent("supervisor")

    async def break_into_tasks(self, user_input: str) -> TaskList:
        """Break down user input into a structured task list with MANDATORY documentation context."""

        # CRITICAL VALIDATION: Ensure documentation context is present
        if "MANDATORY PROJECT DOCUMENTATION CONTEXT" not in user_input:
            raise Exception(
                "CRITICAL: Task decomposition requires MANDATORY documentation context (requirements, design, todos)"
            )

        # Create a specialized prompt for task decomposition
        decomposition_prompt = f"""You are a project supervisor. Break down the following request into specific, actionable tasks.

CRITICAL: The user input contains MANDATORY PROJECT DOCUMENTATION that you MUST reference when creating tasks.

USER REQUEST WITH MANDATORY DOCUMENTATION: {user_input}

IMPORTANT INSTRUCTIONS:
- You MUST analyze the requirements, design, and todo list provided in the user input
- You MUST create tasks that align with the documented requirements and design
- You MUST reference the todo list when creating implementation tasks
- You MUST ensure all tasks contribute to the documented project goals

Return a JSON object with a "tasks" array. Each task should have:
- description: Clear, specific description of what needs to be done
- files: Array of file paths this task should focus on (if applicable)
- dependencies: Array of task IDs this task depends on (use incremental numbers: "1", "2", etc.)
- assigned_agent: One of: file_worker, search_worker, code_worker, analysis_worker
- priority: Number 1-10 (higher = more important)
- estimated_duration: Estimated minutes to complete

AGENT CAPABILITIES:
- file_worker: Read, write, create files and directories
- search_worker: Search files, grep patterns, web search
- code_worker: Write code, run shell commands, git operations
- analysis_worker: Analyze code, understand file structures

EXAMPLE RESPONSE:
{{
  "tasks": [
    {{
      "id": "1",
      "description": "Analyze the current codebase structure",
      "files": ["src/", "*.py"],
      "dependencies": [],
      "assigned_agent": "analysis_worker",
      "priority": 8,
      "estimated_duration": 10
    }},
    {{
      "id": "2",
      "description": "Create new feature implementation",
      "files": ["src/feature.py"],
      "dependencies": ["1"],
      "assigned_agent": "code_worker",
      "priority": 7,
      "estimated_duration": 30
    }}
  ]
}}

Break down the request into 3-8 specific tasks. Be detailed and specific."""

        try:
            # Get task decomposition from LLM
            messages = [Message(role="user", content=decomposition_prompt)]
            response = await self.provider.chat(messages)

            # Parse the JSON response
            response_text = response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            task_data = json.loads(response_text)

            # Create TaskList and add tasks
            task_list = TaskList()

            for task_info in task_data.get("tasks", []):
                task = Task(
                    id=task_info.get("id", str(len(task_list.tasks) + 1)),
                    description=task_info["description"],
                    files=task_info.get("files", []),
                    dependencies=task_info.get("dependencies", []),
                    assigned_agent=task_info.get("assigned_agent"),
                    priority=task_info.get("priority", 5),
                    estimated_duration=task_info.get("estimated_duration"),
                )
                task_list.add_task(task)

            return task_list

        except Exception as e:
            # Fallback: create a simple single task
            print(f"Failed to decompose tasks: {e}")
            task_list = TaskList()
            task = Task(
                id="1", description=user_input, assigned_agent="code_worker", priority=5
            )
            task_list.add_task(task)
            return task_list

    async def spawn_workers(self, task_list: TaskList) -> Dict[str, Any]:
        """Spawn worker agents to execute tasks concurrently."""

        results = {}
        completed_tasks = []

        # Send initial coordination message
        await message_pool.send_message(
            sender_agent="supervisor",
            content=f"Starting multi-agent task execution with {len(task_list.tasks)} tasks",
            message_type=MessageType.COORDINATION,
            metadata={"total_tasks": len(task_list.tasks)},
        )

        # Process tasks until all are complete
        while not task_list.is_complete():
            # Get ready tasks
            ready_tasks = task_list.get_ready_tasks()

            if not ready_tasks:
                # No ready tasks, wait a bit and check again
                await asyncio.sleep(1)
                continue

            # Create worker coroutines for ready tasks
            worker_coroutines = []

            for task in ready_tasks:
                if task.id not in self.active_tasks:
                    # Mark task as in progress
                    task_list.update_task_status(task.id, "in_progress")
                    self.active_tasks.add(task.id)

                    # Get appropriate worker agent
                    agent_name = task.assigned_agent or "code_worker"
                    if agent_name not in self.worker_agents:
                        agent_name = "code_worker"  # fallback

                    worker_agent = self.worker_agents[agent_name]

                    # Send task assignment message
                    await message_pool.send_message(
                        sender_agent="supervisor",
                        content=f"Assigning task to {agent_name}: {task.description}",
                        message_type=MessageType.COORDINATION,
                        recipient_agent=agent_name,
                        task_id=task.id,
                        metadata={"task_assignment": True},
                    )

                    # Create worker coroutine
                    worker_coroutine = self._execute_task_with_semaphore(
                        worker_agent, task, task_list
                    )
                    worker_coroutines.append(worker_coroutine)

            # Execute workers concurrently
            if worker_coroutines:
                task_results = await asyncio.gather(
                    *worker_coroutines, return_exceptions=True
                )

                for result in task_results:
                    if isinstance(result, Exception):
                        print(f"Worker error: {result}")
                        await message_pool.send_message(
                            sender_agent="supervisor",
                            content=f"Worker error occurred: {str(result)}",
                            message_type=MessageType.ERROR,
                            metadata={"error": str(result)},
                        )
                    elif isinstance(result, dict) and "task_id" in result:
                        results[result["task_id"]] = result
                        completed_tasks.append(result["task_id"])
                    else:
                        print(f"Unexpected result format: {result}")
                        await message_pool.send_message(
                            sender_agent="supervisor",
                            content=f"Unexpected result format: {str(result)}",
                            message_type=MessageType.ERROR,
                            metadata={
                                "error": f"Unexpected result format: {str(result)}"
                            },
                        )

        # Send completion message
        await message_pool.send_message(
            sender_agent="supervisor",
            content=f"All tasks completed. {len(completed_tasks)} tasks finished successfully.",
            message_type=MessageType.COORDINATION,
            metadata={"completion": True, "completed_tasks": len(completed_tasks)},
        )

        return {
            "task_results": results,
            "summary": task_list.get_progress_summary(),
            "completed_tasks": completed_tasks,
        }

    async def _execute_task_with_semaphore(
        self, worker_agent: WorkerAgent, task: Task, task_list: TaskList
    ) -> Dict[str, Any]:
        """Execute a task with semaphore control."""
        async with self.worker_semaphore:
            try:
                # Commit before starting task
                self.git_auto.commit_task_start(task.description)

                result = await worker_agent.execute_task(task)

                # Update task status based on result
                if result["success"]:
                    task_list.update_task_status(
                        task.id, "done", result=result["result"]
                    )
                    # Commit after successful task completion
                    self.git_auto.commit_checkpoint(task.description)
                else:
                    task_list.update_task_status(
                        task.id, "failed", error=result["error"]
                    )

                # Remove from active tasks
                self.active_tasks.discard(task.id)

                return result

            except Exception as e:
                task_list.update_task_status(task.id, "failed", error=str(e))
                self.active_tasks.discard(task.id)
                return {
                    "success": False,
                    "error": str(e),
                    "agent": worker_agent.name,
                    "task_id": task.id,
                }

    async def monitor_progress(self, task_list: TaskList) -> Dict[str, Any]:
        """Monitor and report progress of task execution."""

        summary = task_list.get_progress_summary()

        # Get detailed status of each task
        task_details = []
        for task in task_list.tasks:
            task_details.append(
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "assigned_agent": task.assigned_agent,
                    "priority": task.priority,
                    "duration": task.duration_minutes(),
                    "result": task.result[:100] + "..."
                    if task.result and len(task.result) > 100
                    else task.result,
                    "error": task.error,
                }
            )

        # Get message pool status
        pool_status = await message_pool.get_pool_status()

        return {
            "summary": summary,
            "tasks": task_details,
            "active_workers": [
                agent.name for agent in self.worker_agents.values() if agent.is_busy
            ],
            "message_pool": pool_status,
            "timestamp": datetime.now().isoformat(),
        }

    def should_use_multiagent(self, user_input: str) -> bool:
        """Determine if the request should use multi-agent processing."""

        # If multi-agent mode is explicitly enabled, always use it
        if self.use_multi_agent:
            return True

        # If multi-agent mode is explicitly disabled, never use it
        # This allows for strict control via configuration
        # For now, we'll keep it simple and respect the explicit setting
        return False

        # Future enhancement: Could add intelligent heuristics here
        # when use_multi_agent is None (not explicitly set)
        # Simple heuristics for when to use multi-agent
        multiagent_indicators = [
            "build complete",
            "create project",
            "implement system",
            "develop application",
            "multiple files",
            "full stack",
            "frontend and backend",
            "database and api",
            "comprehensive",
            "end-to-end",
        ]

        input_lower = user_input.lower()

        # Check for strong complexity indicators
        complexity_score = 0
        for indicator in multiagent_indicators:
            if indicator in input_lower:
                complexity_score += (
                    2  # Higher weight for explicit multi-component requests
                )

        # Check for file creation requests
        if "create" in input_lower and any(
            ext in input_lower for ext in [".py", ".js", ".html", ".css"]
        ):
            complexity_score += 1

        # Check length (longer requests are often more complex)
        if len(user_input.split()) > 30:
            complexity_score += 1

        # Use multi-agent if complexity score is 3 or higher (more conservative)
        return complexity_score >= 3

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status including message pool information."""
        pool_status = await message_pool.get_pool_status()
        recent_messages = await message_pool.get_message_history(limit=10)

        return {
            "active_workers": [
                agent.name for agent in self.worker_agents.values() if agent.is_busy
            ],
            "message_pool": pool_status,
            "recent_messages": [
                {
                    "sender": msg.sender_agent,
                    "recipient": msg.recipient_agent,
                    "type": msg.message_type.value,
                    "content": msg.content[:100] + "..."
                    if len(msg.content) > 100
                    else msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in recent_messages
            ],
            "timestamp": datetime.now().isoformat(),
        }

    async def trigger_audit(self):
        """Trigger audit using a specialized audit worker."""
        try:
            print("🔍 Starting multi-agent audit...")

            # Import audit manager
            from equitrcoder.tools.builtin.audit import audit_manager

            # Get audit context
            audit_context = audit_manager.get_audit_context()

            # Create audit task
            from equitrcoder.core.task import Task

            audit_task = Task(
                id="audit_task",
                description=f"""
Perform comprehensive audit of the completed project:

{audit_context}

Use available tools to:
1. list_files - examine project structure
2. read_file - review design documents, requirements, and implementations
3. grep_search - verify implementations match requirements
4. Check code quality and completeness

Determine if project is complete and faithful to requirements.
If complete: conclude with "AUDIT PASSED"
If issues found: conclude with "AUDIT FAILED" and create todos for fixes
""",
                assignee="analysis_worker",
                priority="high",
            )

            # Execute audit task using analysis worker
            if "analysis_worker" in self.workers:
                audit_result = await self.workers["analysis_worker"].execute_task(
                    audit_task
                )

                if audit_result.get("success", False):
                    result_content = audit_result.get("result", "")

                    if "AUDIT PASSED" in result_content:
                        print("✅ Multi-agent audit completed successfully!")
                    elif "AUDIT FAILED" in result_content:
                        print("❌ Multi-agent audit failed - issues found")
                    else:
                        print("⚠️ Multi-agent audit completed with unclear result")
                else:
                    print("❌ Multi-agent audit execution failed")
            else:
                print("❌ Analysis worker not available for audit")

        except Exception as e:
            print(f"⚠️ Multi-agent audit error: {e}")
