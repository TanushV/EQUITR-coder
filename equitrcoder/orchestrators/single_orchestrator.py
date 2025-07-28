"""
Single Agent Orchestrator - Simple wrapper around BaseAgent for single-agent tasks.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ..core.session import SessionData, SessionManagerV2
from ..tools.discovery import discover_tools
from ..providers.litellm import LiteLLMProvider, Message, ToolCall
from ..tools.base import ToolResult
from ..providers.openrouter import Message


class SingleAgentOrchestrator:
    """Orchestrator for single-agent tasks with session management and cost tracking."""
    
    def __init__(
        self,
        agent: BaseAgent,
        model: str,  # Required parameter - no default
        session_manager: Optional[SessionManagerV2] = None,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None
    ):
        self.agent = agent
        self.session_manager = session_manager or SessionManagerV2()
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        self.provider = LiteLLMProvider(model=model)
        self.total_cost = 0.0  # Track total cost
        
        # Set limits on agent if provided
        if max_cost:
            self.agent.max_cost = max_cost
        if max_iterations:
            self.agent.max_iterations = max_iterations
        
        # Initialize supervisor for audit functionality
        from ..core.supervisor import SupervisorAgent
        from ..providers.openrouter import OpenRouterProvider
        
        # Create supervisor for audit functionality
        # Try to create a compatible provider, but don't fail if it doesn't work
        supervisor_provider = None
        try:
            # Try to create OpenRouter provider for supervisor
            supervisor_provider = OpenRouterProvider.from_env(model=model)
        except Exception as e:
            print(f"⚠️ Could not create OpenRouter provider for supervisor: {e}")
            # Try to use the LiteLLM provider directly (may not work with supervisor)
            try:
                # Import OpenRouter Message and create a wrapper
                from ..providers.openrouter import Message as OpenRouterMessage
                
                # Create a simple wrapper that converts LiteLLM to OpenRouter format
                class ProviderWrapper:
                    def __init__(self, litellm_provider):
                        self.litellm_provider = litellm_provider
                        self.model = getattr(litellm_provider, 'model', model)
                    
                    async def chat(self, messages, **kwargs):
                        # Convert OpenRouter messages to LiteLLM format if needed
                        litellm_messages = []
                        for msg in messages:
                            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                                litellm_messages.append({"role": msg.role, "content": msg.content})
                            else:
                                litellm_messages.append(msg)
                        
                        # Call LiteLLM provider
                        return await self.litellm_provider.chat(messages=litellm_messages, **kwargs)
                
                supervisor_provider = ProviderWrapper(self.provider)
            except Exception as wrapper_error:
                print(f"⚠️ Could not create provider wrapper: {wrapper_error}")
                supervisor_provider = None
            
        # Create supervisor if we have a provider
        if supervisor_provider:
            try:
                self.supervisor = SupervisorAgent(
                    provider=supervisor_provider,
                    session_manager=self.session_manager,
                    repo_path=".",
                    use_multi_agent=False,  # Single agent mode
                    worker_provider=supervisor_provider
                )
            except Exception as supervisor_error:
                print(f"⚠️ Could not create supervisor: {supervisor_error}")
                self.supervisor = None
        else:
            print("⚠️ No supervisor provider available - audit will be limited")
            self.supervisor = None
        
        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_iteration_callback: Optional[Callable] = None
        self.on_completion_callback: Optional[Callable] = None
    
    async def execute_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a single task using the agent."""
        
        # Create or load session
        if session_id:
            session = self.session_manager.load_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
        else:
            session = self.session_manager.create_session()
        
        self.agent.session = session
        
        # Add initial task message
        self.agent.add_message("user", task_description, {"context": context})
        
        try:
            # Execute task
            result = await self._execute_task_loop(task_description, context)
            
            # Update session
            session.cost += self.total_cost  # Use orchestrator's total cost
            session.total_tokens += result.get("total_tokens", 0)
            session.iteration_count = self.agent.iteration_count
            
            # Save session
            await self.session_manager._save_session_to_disk(session)
            
            # ALWAYS check and trigger audit after successful task completion
            print("🔍 Checking if audit should be triggered...")
            try:
                # Extract task name from enhanced task description if available
                task_name = None
                if "Documents:" in task_description and "docs/" in task_description:
                    # Try to extract task name from document paths
                    import re
                    match = re.search(r'docs/([^/]+)/', task_description)
                    if match:
                        task_name = match.group(1)
                        print(f"📋 Extracted task name for audit: {task_name}")
                
                await self._check_and_trigger_audit(task_name)
            except Exception as audit_error:
                print(f"⚠️ Audit check failed: {audit_error}")
                # Continue execution even if audit fails
            
            return {
                "success": True,
                "result": result,
                "session_id": session.session_id,
                "cost": self.total_cost,  # Use orchestrator's total cost
                "iterations": self.agent.iteration_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session.session_id if session else None,
                "cost": self.total_cost,  # Use orchestrator's total cost
                "iterations": self.agent.iteration_count
            }
    
    async def _execute_task_loop(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main task execution loop."""
        
        # Get initial messages from agent
        messages = [Message(role=m['role'], content=m['content']) for m in self.agent.get_messages()]
        
        # Add system prompt if no system message exists
        if not messages or messages[0].role != 'system':
            system_prompt = """You are an AI coding assistant that MUST use tools in every response.

🚨 CRITICAL RULES - VIOLATION WILL RESULT IN ERROR:
1. **MANDATORY TOOL USE**: You MUST make at least one tool call in EVERY response. Text-only responses are FORBIDDEN.
2. **TODO COMPLETION**: When you finish a task, you MUST use update_todo to mark it completed.
3. **SYSTEMATIC APPROACH**: Start with list_todos, work through each todo, mark as completed when done.
4. **CONTINUOUS PROGRESS**: Always use tools to make progress - create files, edit code, run tests, etc.

🔧 AVAILABLE TOOLS (USE THESE CONSTANTLY):
- list_todos: Check current todos and their status
- update_todo: Mark todos as completed (ESSENTIAL!)
- create_file: Create new files
- edit_file: Modify existing files  
- read_file: Read file contents
- run_command: Execute shell commands
- search_files: Search for content in files

🎯 WORKFLOW:
1. ALWAYS start by calling list_todos to see what needs to be done
2. Pick the first incomplete todo
3. Use appropriate tools to work on it (create_file, edit_file, run_command, etc.)
4. When complete, call update_todo to mark it done
5. Call list_todos again to see remaining work
6. Repeat until all todos are completed

⚠️ REMEMBER: Every response MUST include tool calls. Never respond with just text!"""
            messages.insert(0, Message(role='system', content=system_prompt))
        
        # Get available tools and their schemas
        available_tools = self.agent.get_available_tools()
        tool_schemas = []
        for tool_name in available_tools:
            if self.agent.can_use_tool(tool_name):
                tool = self.agent.tool_registry[tool_name]
                tool_schemas.append(tool.get_json_schema())
        
        iteration = 0
        max_iterations = self.max_iterations or 999999  # Effectively unlimited by default
        
        while iteration < max_iterations:
            iteration += 1
            self.agent.iteration_count = iteration
            
            # Call iteration callback
            if self.on_iteration_callback:
                self.on_iteration_callback(iteration, self.agent.get_status())
            
            try:
                # Call LLM with tool schemas
                response = await self.provider.chat(
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None
                )
                
                # Update cost tracking
                if hasattr(response, 'cost') and response.cost:
                    self.total_cost += response.cost
                    self.agent.current_cost += response.cost
                
                # VERBOSE: Show LLM response (only if callback is set, indicating verbose mode)
                if self.on_message_callback:
                    print(f"\n🤖 LLM Response (Iteration {iteration}):")
                    print(f"💬 Content: {response.content or '(No content - tool calls only)'}")
                    if response.tool_calls:
                        print(f"🔧 Tool calls: {len(response.tool_calls)}")
                        for i, tc in enumerate(response.tool_calls):
                            print(f"   {i+1}. {tc.function['name']}({tc.function['arguments']})")
                    else:
                        print("⚠️  NO TOOL CALLS - This will trigger a warning!")
                    print(f"💰 Cost: ${response.cost:.4f}" if hasattr(response, 'cost') and response.cost else "💰 Cost: Unknown")
                
                # Add assistant message
                assistant_message = Message(role='assistant', content=response.content or "Working...")
                messages.append(assistant_message)
                
                # Add to agent messages
                self.agent.add_message('assistant', response.content or "Working...")
                
                # Call message callback
                if self.on_message_callback:
                    self.on_message_callback({
                        'role': 'assistant',
                        'content': response.content or "Working...",
                        'iteration': iteration,
                        'tool_calls': len(response.tool_calls) if response.tool_calls else 0,
                        'cost': response.cost if hasattr(response, 'cost') else 0
                    })
                
                # Handle tool calls
                if response.tool_calls:
                    tool_results = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function['name']
                        tool_args = json.loads(tool_call.function['arguments'])
                        
                        # Execute tool through agent
                        if self.agent.can_use_tool(tool_name):
                            tool_result = await self.agent.call_tool(tool_name, **tool_args)
                            result_content = str(tool_result['result'] if tool_result['success'] else tool_result['error'])
                            
                            # Add to agent messages (for logging/history)
                            self.agent.add_message('tool', result_content, {
                                'tool_name': tool_name,
                                'success': tool_result['success']
                            })
                            
                            # VERBOSE: Show tool result
                            if self.on_message_callback:
                                print(f"   🔧 Tool Result: {tool_name} -> {'✅ SUCCESS' if tool_result['success'] else '❌ FAILED'}")
                                print(f"      📄 Output: {result_content[:200]}{'...' if len(result_content) > 200 else ''}")
                            
                            # Call message callback for tool result
                            if self.on_message_callback:
                                self.on_message_callback({
                                    'role': 'tool',
                                    'content': result_content,
                                    'tool_name': tool_name,
                                    'success': tool_result['success']
                                })
                            
                            tool_results.append(f"Tool {tool_name}: {result_content}")
                        else:
                            error_msg = f'Tool {tool_name} not available'
                            
                            # Add to agent messages (for logging/history)
                            self.agent.add_message('tool', error_msg, {
                                'tool_name': tool_name,
                                'error': 'Tool not available'
                            })
                            
                            tool_results.append(f"Error: {error_msg}")
                    
                    # Add a user message with tool results so LLM knows what happened
                    if tool_results:
                        results_message = "Tool execution results:\n" + "\n".join(tool_results)
                        user_message = Message(role='user', content=results_message)
                        messages.append(user_message)
                        
                        # Add to agent messages too
                        self.agent.add_message('user', results_message, {'system_generated': True})
                    
                    # Continue to next iteration
                    continue
                else:
                    # No tool calls - this is NOT allowed! Force the agent to use tools
                    warning_message = "ERROR: You must use tools in every response! You cannot just provide text without tool calls. Please use a tool like list_todos, create_file, or update_todo to continue working."
                    user_message = Message(role='user', content=warning_message)
                    messages.append(user_message)
                    
                    # Add to agent messages too
                    self.agent.add_message('user', warning_message, {'system_generated': True, 'warning': True})
                    
                    # Call message callback for warning
                    if self.on_message_callback:
                        self.on_message_callback({
                            'role': 'user',
                            'content': warning_message,
                            'warning': True
                        })
                    
                    # Continue to force tool use
                    continue
                    
            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                self.agent.add_message('system', error_msg, {'error': True})
                if self.on_message_callback:
                    self.on_message_callback({
                        'role': 'system',
                        'content': error_msg,
                        'error': True
                    })
                break
        
        # Call completion callback
        if self.on_completion_callback:
            self.on_completion_callback({
                'iterations': iteration,
                'final_message': messages[-1].content if messages else '',
                'success': True
            })
        
        return {
            "task_description": task_description,
            "final_response": messages[-1].content if messages else '',
            "iterations": iteration,
            "total_tokens": 0,  # TODO: Track tokens properly
            "worker_status": "completed"
        }

    async def _check_and_trigger_audit(self, task_name: str = None):
        """Check if audit should be triggered and run it using supervisor with infinite loop."""
        try:
            # Import audit manager
            from ..tools.builtin.audit import audit_manager

            # Check if audit should be triggered for specific task
            if not audit_manager.should_trigger_audit(task_name):
                return False

            print(f"🔍 Worker finished! Triggering automatic audit for task: {task_name or 'all todos'}")

            # Infinite audit loop with failure tracking
            while True:
                # Use supervisor to trigger audit if available
                if self.supervisor:
                    # Get audit context first for specific task
                    audit_context = audit_manager.get_audit_context(task_name)
                    if not audit_context:
                        print("ℹ️  No audit needed - no todos found or all todos completed")
                        break

                    # Execute audit via supervisor (which has its own loop)
                    await self.supervisor.trigger_audit()
                    break  # Supervisor handles the loop internally
                else:
                    print("❌ Supervisor not available for audit")
                    
                    # Record supervisor unavailable as audit failure
                    audit_manager.record_audit_result(False, "Supervisor not available for audit", "Supervisor not available for audit")
                    audit_manager.create_todos_from_audit_failure("Supervisor not available for audit", "Supervisor not available for audit")
                    break

            return True

        except Exception as e:
            print(f"⚠️ Single-agent audit trigger error: {e}")
            
            # Record the exception as an audit failure
            from ..tools.builtin.audit import audit_manager
            audit_manager.record_audit_result(False, f"Audit system error: {str(e)}", f"Audit system error: {str(e)}")
            audit_manager.create_todos_from_audit_failure(f"Audit system error: {str(e)}", f"Audit system error: {str(e)}")
            return False
    
    def set_callbacks(self, on_message=None, on_iteration=None, on_completion=None):
        """Set callback functions for monitoring task execution."""
        if on_message:
            self.on_message_callback = on_message
        if on_iteration:
            self.on_iteration_callback = on_iteration
        if on_completion:
            self.on_completion_callback = on_completion 