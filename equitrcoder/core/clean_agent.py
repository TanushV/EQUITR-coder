"""
Clean Agent Implementation - Takes tools + context and runs until completion.
Always runs audit when finished.
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..core.session import SessionData, SessionManagerV2
from ..providers.litellm import LiteLLMProvider, Message
from ..tools.base import Tool


class CleanAgent:
    """
    Simple agent that takes tools + context and runs until completion.
    Built-in audit functionality runs automatically when agent finishes.
    """

    def __init__(
        self,
        agent_id: str,
        model: str,
        tools: List[Tool],
        context: Dict[str, Any] = None,
        session_manager: Optional[SessionManagerV2] = None,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None,
        audit_model: Optional[str] = None,  # Model for audit (defaults to same as main model)
    ):
        self.agent_id = agent_id
        self.model = model
        self.audit_model = audit_model or model  # Default to same as main model
        self.tools = {tool.get_name(): tool for tool in tools}
        self.context = context or {}
        self.session_manager = session_manager or SessionManagerV2()
        self.max_cost = max_cost
        self.max_iterations = max_iterations

        # Auto-load environment variables
        from ..utils.env_loader import auto_load_environment

        auto_load_environment()

        # Runtime state
        self.provider = LiteLLMProvider(model=model)
        self.audit_provider = (
            LiteLLMProvider(model=audit_model)
            if audit_model != model
            else self.provider
        )
        self.messages: List[Dict[str, Any]] = []
        self.current_cost = 0.0
        self.iteration_count = 0
        self.session: Optional[SessionData] = None
        
        # Track detailed LLM interactions for programmatic access
        self.llm_responses: List[Dict[str, Any]] = []
        self.tool_call_history: List[Dict[str, Any]] = []

        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_iteration_callback: Optional[Callable] = None
        self.on_completion_callback: Optional[Callable] = None
        self.on_audit_callback: Optional[Callable] = None

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.messages.append(message)

        if self.on_message_callback:
            self.on_message_callback(message)

    async def run(
        self, task_description: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the agent until completion, then automatically run audit.
        """
        try:
            # Setup session
            if session_id:
                self.session = self.session_manager.load_session(session_id)
                if not self.session:
                    self.session = self.session_manager.create_session(session_id)
            else:
                self.session = self.session_manager.create_session()

            # Add context to system message
            context_info = ""
            if self.context:
                context_info = (
                    f"\n\nContext provided:\n{json.dumps(self.context, indent=2)}"
                )

            # Add initial system message
            system_message = f"""You are {self.agent_id}, an AI coding agent powered by {self.model}.

🚨 CRITICAL RULES - FOLLOW THESE EXACTLY:
1. **MANDATORY TOOL USE**: You MUST make at least one tool call in EVERY response
2. **TODO COMPLETION IS YOUR PRIMARY GOAL**: Your success is measured ONLY by completing ALL todos
3. **MANDATORY COMMUNICATION**: If you have access to `ask_supervisor` or `send_message` tools, you MUST use them frequently
4. **NEVER GIVE UP**: Keep working until ALL todos are marked as 'completed' - this is non-negotiable
5. **CREATE WORKING CODE**: Actually implement and test your solutions - don't just plan
6. **BE PERSISTENT**: If something doesn't work, try different approaches until it succeeds
7. **ASK FOR HELP**: Use communication tools when stuck, confused, or need guidance

🎯 YOUR MISSION: Complete every single todo item through active collaboration and communication.

🔧 AVAILABLE TOOLS: {', '.join(self.tools.keys())}

📋 MANDATORY WORKFLOW (Follow this religiously):
1. **COMMUNICATE FIRST**: If you have `ask_supervisor` or `send_message`, use them to understand your role
2. **GET YOUR TODOS**: Use list_todos_in_group to see your assigned todos
3. **ASK FOR GUIDANCE**: Use `ask_supervisor` for unclear requirements or technical decisions
4. **COORDINATE**: Use `send_message` to communicate with other agents about dependencies
5. **IMPLEMENT**: Work through each todo systematically - implement actual working solutions
6. **VERIFY**: Use `ask_supervisor` to verify your work is correct before marking complete
7. **UPDATE STATUS**: Use update_todo_status to mark todos as 'completed' ONLY when fully implemented
8. **COMMUNICATE SUCCESS**: Use communication tools to announce completion and coordinate next steps

💡 COMMUNICATION REQUIREMENTS:
- Use `ask_supervisor` at least once every 3-5 iterations if available
- Use `send_message` to coordinate with other agents if available
- NEVER work in isolation if communication tools are available
- Ask for help when stuck rather than struggling alone
- Communicate progress, blockers, and completions

🏆 SUCCESS TIPS:
- Read files to understand the codebase before making changes
- Create files with complete, working implementations
- Test your code by reading it back and checking for errors
- Use git_commit to save your progress regularly
- Use communication tools to get guidance and coordinate
- If you're stuck, ask for help immediately - don't waste iterations!

🏆 REMEMBER: Your reputation depends on completing ALL todos through effective communication and collaboration.

Agent ID: {self.agent_id}
Model: {self.model}{context_info}"""

            self.add_message("system", system_message)
            self.add_message("user", task_description)

            # Execute main loop
            result = await self._execution_loop()

            # ALWAYS run audit after completion
            audit_result = await self._run_audit()

            # Save session
            if self.session:
                self.session.cost += self.current_cost
                self.session.iteration_count = self.iteration_count
                await self.session_manager._save_session_to_disk(self.session)

            return {
                "success": result["success"],
                "agent_id": self.agent_id,
                "cost": self.current_cost,
                "iterations": self.iteration_count,
                "execution_result": result,
                "audit_result": audit_result,
                "session_id": self.session.session_id if self.session else None,
                # Include detailed LLM response data for programmatic access
                "messages": self.messages,
                "llm_responses": self.llm_responses,
                "tool_calls": self.tool_call_history,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "cost": self.current_cost,
                "iterations": self.iteration_count,
            }

    async def _execution_loop(self) -> Dict[str, Any]:
        """Main execution loop - runs until todos are completed or limits reached."""

        # Convert messages to provider format
        messages = [
            Message(role=m["role"], content=m["content"]) for m in self.messages
        ]

        # Get tool schemas
        tool_schemas = [tool.get_json_schema() for tool in self.tools.values()]

        iteration = 0
        max_iterations = self.max_iterations or 999999

        while iteration < max_iterations:
            iteration += 1
            self.iteration_count = iteration

            # Check cost limit
            if self.max_cost and self.current_cost >= self.max_cost:
                return {
                    "success": False,
                    "reason": "Cost limit exceeded",
                    "final_message": "Cost limit reached",
                }

            if self.on_iteration_callback:
                self.on_iteration_callback(
                    iteration,
                    {
                        "cost": self.current_cost,
                        "max_cost": self.max_cost,
                        "can_continue": True,
                    },
                )

            try:
                # Call LLM
                response = await self.provider.chat(
                    messages=messages, tools=tool_schemas if tool_schemas else None
                )

                # Track LLM response for programmatic access
                llm_response_data = {
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model,
                    "content": response.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": tc.function
                        } for tc in (response.tool_calls or [])
                    ],
                    "usage": getattr(response, "usage", {}),
                    "cost": getattr(response, "cost", 0.0)
                }
                self.llm_responses.append(llm_response_data)

                # Update cost
                if hasattr(response, "cost") and response.cost:
                    self.current_cost += response.cost

                # Log detailed LLM response with full content
                print(f"\n🤖 [{self.agent_id}] Iteration {iteration} - LLM Response:")
                print(f"   Model: {self.model}")
                print(f"   Cost: ${getattr(response, 'cost', 0.0):.4f} (Total: ${self.current_cost:.4f})")
                print(f"   Usage: {getattr(response, 'usage', {})}")
                
                if response.content:
                    print(f"   Content:")
                    # Log full content with proper formatting
                    content_lines = response.content.split('\n')
                    for line in content_lines[:10]:  # Show first 10 lines
                        print(f"     {line}")
                    if len(content_lines) > 10:
                        print(f"     ... ({len(content_lines) - 10} more lines)")
                
                if response.tool_calls:
                    print(f"   Tool Calls ({len(response.tool_calls)}):")
                    for i, tc in enumerate(response.tool_calls, 1):
                        args = json.loads(tc.function['arguments'])
                        print(f"     {i}. {tc.function['name']}:")
                        for key, value in args.items():
                            value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                            print(f"        {key}: {value_str}")
                else:
                    print("   ⚠️  NO TOOL CALLS - This violates the mandatory tool use rule!")

                # Add assistant message
                assistant_content = response.content or "Working..."
                messages.append(Message(role="assistant", content=assistant_content))
                self.add_message("assistant", assistant_content)

                # Handle tool calls
                if response.tool_calls:
                    tool_results = []

                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function["name"]
                        tool_args = json.loads(tool_call.function["arguments"])

                        # Track tool call for programmatic access
                        tool_call_data = {
                            "iteration": iteration,
                            "timestamp": datetime.now().isoformat(),
                            "tool_call_id": tool_call.id,
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "success": False,
                            "result": None,
                            "error": None
                        }

                        if tool_name in self.tools:
                            # Execute tool
                            tool_result = await self.tools[tool_name].run(**tool_args)
                            result_content = str(
                                tool_result.data
                                if tool_result.success
                                else tool_result.error
                            )

                            # Update tool call tracking
                            tool_call_data["success"] = tool_result.success
                            tool_call_data["result"] = tool_result.data if tool_result.success else None
                            tool_call_data["error"] = tool_result.error if not tool_result.success else None

                            # Log tool execution result
                            status_icon = "✅" if tool_result.success else "❌"
                            print(f"🔧 [{self.agent_id}] Tool Execution: {status_icon} {tool_name}")
                            if tool_args:
                                args_preview = str(tool_args)[:100] + "..." if len(str(tool_args)) > 100 else str(tool_args)
                                print(f"   Args: {args_preview}")
                            result_preview = result_content[:150] + "..." if len(result_content) > 150 else result_content
                            print(f"   Result: {result_preview}")

                            self.add_message(
                                "tool",
                                result_content,
                                {
                                    "tool_name": tool_name,
                                    "success": tool_result.success,
                                },
                            )

                            tool_results.append(f"Tool {tool_name}: {result_content}")
                        else:
                            error_msg = f"Tool {tool_name} not available"
                            tool_call_data["error"] = error_msg
                            
                            # Log tool error
                            print(f"🔧 [{self.agent_id}] Tool Error: ❌ {tool_name} (not available)")
                            
                            self.add_message(
                                "tool",
                                error_msg,
                                {"tool_name": tool_name, "error": "Tool not available"},
                            )
                            tool_results.append(f"Error: {error_msg}")
                        
                        self.tool_call_history.append(tool_call_data)

                    # Add tool results as user message
                    if tool_results:
                        results_message = "Tool execution results:\n" + "\n".join(
                            tool_results
                        )
                        messages.append(Message(role="user", content=results_message))
                        self.add_message(
                            "user", results_message, {"system_generated": True}
                        )

                    continue
                else:
                    # No tool calls - check if task is complete
                    response_content = response.content or ""

                    # Check completion indicators
                    completion_indicators = [
                        "all todos completed",
                        "all tasks finished",
                        "work completed",
                        "all done",
                        "finished successfully",
                        "task complete",
                    ]

                    if any(
                        indicator in response_content.lower()
                        for indicator in completion_indicators
                    ):
                        # Verify by checking todos
                        try:
                            if "list_todos" in self.tools:
                                todo_result = await self.tools["list_todos"].run()
                                if todo_result.success:
                                    todos = todo_result.data.get("todos", [])
                                    pending_todos = [
                                        t
                                        for t in todos
                                        if t.get("status")
                                        not in ["completed", "cancelled"]
                                    ]

                                    if not pending_todos:
                                        return {
                                            "success": True,
                                            "reason": "All todos completed",
                                            "final_message": response_content,
                                        }
                        except Exception:
                            pass

                    # Force tool use
                    warning_message = "ERROR: You must use tools in every response! Use list_todos to check remaining work or update_todo to mark tasks complete."
                    messages.append(Message(role="user", content=warning_message))
                    self.add_message(
                        "user",
                        warning_message,
                        {"system_generated": True, "warning": True},
                    )
                    continue

            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                self.add_message("system", error_msg, {"error": True})
                continue

        return {
            "success": False,
            "reason": "Max iterations reached",
            "final_message": messages[-1].content if messages else "",
        }

    async def _run_audit(self) -> Dict[str, Any]:
        """Interactive audit loop.
        The auditor can either:
        • Emit a read-only tool call (read_file, list_files, grep_search). We execute it and feed back the result.
        • Emit a RESULTS tool-call (virtual tool) or a plain message starting with AUDIT PASSED/FAILED.
        Audit ends only when a results message is produced.
        If FAILED the auditor must supply a JSON list ``additional_tasks`` that we can turn into new todos.
        """
        try:
            if self.on_audit_callback:
                self.on_audit_callback({"status": "starting", "model": self.audit_model})

            print(f"🔍 Running automatic audit with {self.audit_model}...")
            read_only_tools = [
                self.tools[name] for name in ("read_file", "list_files", "grep_search") if name in self.tools
            ]
            if not read_only_tools:
                return {"success": False, "reason": "No audit tools available", "audit_passed": False}

            tool_schemas = [t.get_json_schema() for t in read_only_tools]

            system_prompt = (
                "You are an independent code auditor. Explore the repository in depth using the provided read-only tools.\n\n"
                "AUDIT LOOP INSTRUCTIONS:\n"
                "• At each turn either CALL a read-only tool or, when satisfied, RETURN results using the virtual tool 'audit_results'.\n"
                "• The 'audit_results' call must include JSON with: {\"passed\": bool, \"reasons\": str, \"additional_tasks\": list}.\n"
                "• Fail only if one or more todos have not been completed.\n"
                "• Keep investigating until confident."
            )

            messages = [Message(role="system", content=system_prompt)]
            max_iter = 20
            for _ in range(max_iter):
                resp = await self.audit_provider.chat(messages=messages, tools=tool_schemas + [
                    {"name": "audit_results", "description": "Final audit verdict"}
                ])
                if resp.tool:
                    tool_name = resp.tool.name
                    if tool_name == "audit_results":
                        payload = resp.tool.arguments or {}
                        audit_passed = payload.get("passed", False)
                        reasons = payload.get("reasons", "")
                        extra_tasks = payload.get("additional_tasks", [])
                        content = json.dumps(payload)
                        if self.on_audit_callback:
                            self.on_audit_callback({
                                "status": "completed", "passed": audit_passed, "content": content
                            })
                        return {
                            "success": True,
                            "audit_passed": audit_passed,
                            "audit_content": content,
                            "extra_tasks": extra_tasks,
                            "audit_model": self.audit_model,
                        }
                    # execute read tool
                    if tool_name in self.tools:
                        result = await self.tools[tool_name].run(**resp.tool.arguments)
                        messages.append(Message(role="tool", name=tool_name, content=result.json()))
                        continue
                # non-tool message
                if resp.content and resp.content.strip().upper().startswith("AUDIT"):
                    messages.append(Message(role="assistant", content=resp.content))
                    audit_passed = resp.content.upper().startswith("AUDIT PASSED")
                    if self.on_audit_callback:
                        self.on_audit_callback({"status": "completed", "passed": audit_passed, "content": resp.content})
                    return {
                        "success": True,
                        "audit_passed": audit_passed,
                        "audit_content": resp.content,
                        "audit_model": self.audit_model,
                    }
                messages.append(Message(role="assistant", content=resp.content or ""))
            # exceeded iterations
            return {"success": False, "audit_passed": False, "reason": "Audit loop max iterations"}
        except Exception as e:
            if self.on_audit_callback:
                self.on_audit_callback({"status": "error", "error": str(e)})
            return {"success": False, "audit_passed": False, "error": str(e)}

    def set_callbacks(
        self,
        on_message: Optional[Callable] = None,
        on_iteration: Optional[Callable] = None,
        on_completion: Optional[Callable] = None,
        on_audit: Optional[Callable] = None,
    ):
        """Set callback functions for monitoring."""
        if on_message:
            self.on_message_callback = on_message
        if on_iteration:
            self.on_iteration_callback = on_iteration
        if on_completion:
            self.on_completion_callback = on_completion
        if on_audit:
            self.on_audit_callback = on_audit
