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
from .unified_config import get_config


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
        context: Optional[Dict[str, Any]] = None,
        session_manager: Optional[SessionManagerV2] = None,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None,
        audit_model: Optional[str] = None,  # Model for audit (defaults to same as main model)
    ):
        self.agent_id = agent_id
        self.model = model
        self.audit_model = audit_model or model  # Default to same as main model
        self.tools = {tool.get_name(): tool for tool in tools}
        self.base_context = context or {}  # Store original context separately
        self.session_manager = session_manager or SessionManagerV2()
        self.max_cost = max_cost
        self.max_iterations = max_iterations

        # Auto-load environment variables
        from ..utils.env_loader import auto_load_environment

        auto_load_environment()

        # Runtime state
        self.provider = LiteLLMProvider(model=model)
        self.audit_provider = (
            LiteLLMProvider(model=audit_model or model)
            if (audit_model and audit_model != model)
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
        
        # Build enhanced context once at initialization (without repo map - that's generated dynamically)
        self.context = self._build_enhanced_context()

    def _build_enhanced_context(self) -> Dict[str, Any]:
        """Build comprehensive context that includes all required information."""
        enhanced_context = dict(self.base_context)  # Start with original context
        
        # If we have basic docs_result, enhance it with additional context
        if self.base_context:
            # Get full repo map
            from pathlib import Path
            
            def get_repo_map(path=".", max_depth=None, max_tokens=None):
                max_depth = max_depth or get_config('limits.max_depth', 3)
                max_tokens = max_tokens or get_config('limits.context_max_tokens', 4000)
                """Generate a comprehensive repo map with functions, limited to max_tokens"""
                import re
                import tiktoken
                
                try:
                    # Use tiktoken to count tokens accurately
                    encoding = tiktoken.get_encoding("cl100k_base")
                except (ImportError, AttributeError, Exception):
                    # Fallback to rough estimation if tiktoken fails
                    encoding = None
                
                def count_tokens(text):
                    if encoding:
                        return len(encoding.encode(text))
                    else:
                        # Rough estimation: ~4 chars per token
                        return len(text) // 4
                
                def extract_functions(file_path):
                    """Extract function/class definitions from code files"""
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        functions = []
                        
                        # Python functions and classes
                        if file_path.suffix == '.py':
                            # Find function definitions
                            func_pattern = r'^(def\s+\w+\([^)]*\):|class\s+\w+[^:]*:)'
                            for match in re.finditer(func_pattern, content, re.MULTILINE):
                                functions.append(match.group(1).strip())
                        
                        # JavaScript/TypeScript functions
                        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                            # Find function definitions
                            func_patterns = [
                                r'function\s+\w+\s*\([^)]*\)',
                                r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',
                                r'class\s+\w+',
                                r'export\s+function\s+\w+\s*\([^)]*\)'
                            ]
                            for pattern in func_patterns:
                                for match in re.finditer(pattern, content, re.MULTILINE):
                                    functions.append(match.group(0).strip())
                        
                        return functions[:5]  # Limit to 5 functions per file
                    except (OSError, UnicodeDecodeError, Exception):
                        return []
                
                repo_map = []
                current_tokens = 0
                path = Path(path)
                
                def scan_directory(dir_path, current_depth=0, prefix=""):
                    nonlocal current_tokens
                    if current_depth > max_depth or current_tokens >= max_tokens:
                        return
                    
                    try:
                        items = sorted(dir_path.iterdir())
                        for item in items:
                            if current_tokens >= max_tokens:
                                break
                                
                            if item.name.startswith('.') and item.name not in ['.gitignore', '.env.example']:
                                continue
                            
                            if item.is_file():
                                size = item.stat().st_size
                                file_line = f"{prefix}📄 {item.name} ({size} bytes)"
                                
                                # Add functions for code files
                                if item.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx'] and size < 50000:  # Skip very large files
                                    functions = extract_functions(item)
                                    if functions:
                                        file_line += f" - Functions: {', '.join(functions)}"
                                
                                # Check token count with buffer
                                line_tokens = count_tokens(file_line)
                                if current_tokens + line_tokens > max_tokens - 100:  # Leave 100 token buffer
                                    repo_map.append(f"{prefix}... (truncated - token limit reached)")
                                    return
                                
                                repo_map.append(file_line)
                                current_tokens += line_tokens
                                
                            elif item.is_dir():
                                dir_line = f"{prefix}📁 {item.name}/"
                                line_tokens = count_tokens(dir_line)
                                
                                if current_tokens + line_tokens > max_tokens - 100:  # Leave 100 token buffer
                                    repo_map.append(f"{prefix}... (truncated - token limit reached)")
                                    return
                                
                                repo_map.append(dir_line)
                                current_tokens += line_tokens
                                scan_directory(item, current_depth + 1, prefix + "  ")
                                
                    except PermissionError:
                        error_line = f"{prefix}❌ Permission denied"
                        if current_tokens + count_tokens(error_line) <= max_tokens:
                            repo_map.append(error_line)
                            current_tokens += count_tokens(error_line)
                
                scan_directory(path)
                result = "\n".join(repo_map)
                
                # Final token check and truncation if needed
                if count_tokens(result) > max_tokens:
                    # Truncate to fit within token limit
                    lines = repo_map
                    truncated_lines = []
                    tokens_used = 0
                    
                    for line in lines:
                        line_tokens = count_tokens(line + "\n")
                        if tokens_used + line_tokens > max_tokens:
                            truncated_lines.append("... (truncated - token limit reached)")
                            break
                        truncated_lines.append(line)
                        tokens_used += line_tokens
                    
                    result = "\n".join(truncated_lines)
                
                return result
            
            # Don't add repo map here - it will be generated dynamically in the system message
            
            # Add requirements and design content if we have paths but not content
            if "requirements_path" in enhanced_context and "requirements_content" not in enhanced_context:
                try:
                    req_path = Path(enhanced_context["requirements_path"])
                    if req_path.exists():
                        enhanced_context["requirements_content"] = req_path.read_text()
                except Exception:
                    enhanced_context["requirements_content"] = "Requirements file not found or unreadable"
            
            if "design_path" in enhanced_context and "design_content" not in enhanced_context:
                try:
                    design_path = Path(enhanced_context["design_path"])
                    if design_path.exists():
                        enhanced_context["design_content"] = design_path.read_text()
                except Exception:
                    enhanced_context["design_content"] = "Design file not found or unreadable"
            
            # Remove path fields - not needed in context
            for path_key in ["requirements_path", "design_path", "todos_path", "docs_dir"]:
                enhanced_context.pop(path_key, None)
            
            # Add current task group todos if not already present
            if "current_task_group" not in enhanced_context:
                # Try to extract task group info from agent_id if it follows the pattern
                if hasattr(self, 'agent_id') and '_agent_' in self.agent_id:
                    try:
                        from ..tools.builtin.todo import get_todo_manager
                        parts = self.agent_id.split('_agent_')
                        if len(parts) >= 2:
                            group_id = parts[1]
                            manager = get_todo_manager()
                            current_group = manager.get_task_group(group_id)
                            if current_group:
                                enhanced_context["current_task_group"] = {
                                    "group_id": current_group.group_id,
                                    "specialization": current_group.specialization,
                                    "description": current_group.description,
                                    "dependencies": current_group.dependencies,
                                    "todos": [todo.model_dump() for todo in current_group.todos]
                                }
                    except Exception as e:
                        # Todo manager not available, log warning and continue
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Todo manager not available for context enhancement: {e}")
            
            # Add agent profile info if not already present
            if "agent_profile" not in enhanced_context:
                enhanced_context["agent_profile"] = {
                    "agent_id": self.agent_id,
                    "model": self.model,
                    "available_tools": list(self.tools.keys())
                }
        
        return enhanced_context

    def _generate_live_repo_map(self, path=".", max_depth=None, max_tokens=None):
        max_depth = max_depth or get_config('limits.max_depth', 3)
        max_tokens = max_tokens or get_config('limits.context_max_tokens', 4000)
        """Generate a LIVE/dynamic repo map that reflects current file system state."""
        import re
        import tiktoken
        from pathlib import Path
        
        try:
            # Use tiktoken to count tokens accurately
            encoding = tiktoken.get_encoding("cl100k_base")
        except (ImportError, AttributeError, Exception):
            # Fallback to rough estimation if tiktoken fails
            encoding = None
        
        def count_tokens(text):
            if encoding:
                return len(encoding.encode(text))
            else:
                # Rough estimation: ~4 chars per token
                return len(text) // 4
        
        def extract_functions(file_path):
            """Extract function/class definitions from code files"""
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                functions = []
                
                # Python functions and classes
                if file_path.suffix == '.py':
                    # Find function definitions
                    func_pattern = r'^(def\s+\w+\([^)]*\):|class\s+\w+[^:]*:)'
                    for match in re.finditer(func_pattern, content, re.MULTILINE):
                        functions.append(match.group(1).strip())
                
                # JavaScript/TypeScript functions
                elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                    # Find function definitions
                    func_patterns = [
                        r'function\s+\w+\s*\([^)]*\)',
                        r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',
                        r'class\s+\w+',
                        r'export\s+function\s+\w+\s*\([^)]*\)'
                    ]
                    for pattern in func_patterns:
                        for match in re.finditer(pattern, content, re.MULTILINE):
                            functions.append(match.group(0).strip())
                
                return functions[:5]  # Limit to 5 functions per file
            except (OSError, UnicodeDecodeError, Exception):
                return []
        
        repo_map = []
        current_tokens = 0
        path = Path(path)
        
        def scan_directory(dir_path, current_depth=0, prefix=""):
            nonlocal current_tokens
            if current_depth > max_depth or current_tokens >= max_tokens:
                return
            
            try:
                items = sorted(dir_path.iterdir())
                for item in items:
                    if current_tokens >= max_tokens:
                        break
                        
                    if item.name.startswith('.') and item.name not in ['.gitignore', '.env.example']:
                        continue
                    
                    if item.is_file():
                        size = item.stat().st_size
                        file_line = f"{prefix}📄 {item.name} ({size} bytes)"
                        
                        # Add functions for code files
                        if item.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx'] and size < 50000:  # Skip very large files
                            functions = extract_functions(item)
                            if functions:
                                file_line += f" - Functions: {', '.join(functions)}"
                        
                        # Check token count with buffer
                        line_tokens = count_tokens(file_line)
                        if current_tokens + line_tokens > max_tokens - 100:  # Leave 100 token buffer
                            repo_map.append(f"{prefix}... (truncated - token limit reached)")
                            return
                        
                        repo_map.append(file_line)
                        current_tokens += line_tokens
                        
                    elif item.is_dir():
                        dir_line = f"{prefix}📁 {item.name}/"
                        line_tokens = count_tokens(dir_line)
                        
                        if current_tokens + line_tokens > max_tokens - 100:  # Leave 100 token buffer
                            repo_map.append(f"{prefix}... (truncated - token limit reached)")
                            return
                        
                        repo_map.append(dir_line)
                        current_tokens += line_tokens
                        scan_directory(item, current_depth + 1, prefix + "  ")
                        
            except PermissionError:
                error_line = f"{prefix}❌ Permission denied"
                if current_tokens + count_tokens(error_line) <= max_tokens:
                    repo_map.append(error_line)
                    current_tokens += count_tokens(error_line)
        
        scan_directory(path)
        result = "\n".join(repo_map)
        
        # Final token check and truncation if needed
        if count_tokens(result) > max_tokens:
            # Truncate to fit within token limit
            lines = repo_map
            truncated_lines = []
            tokens_used = 0
            
            for line in lines:
                line_tokens = count_tokens(line + "\n")
                if tokens_used + line_tokens > max_tokens:
                    truncated_lines.append("... (truncated - token limit reached)")
                    break
                truncated_lines.append(line)
                tokens_used += line_tokens
            
            result = "\n".join(truncated_lines)
        
        return result

    def _preserve_core_context(self, compressed_context: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure core context information is preserved during compression."""
        # Define core context keys that must never be compressed
        core_context_keys = [
            "repo_map", "requirements_content", "design_content", 
            "current_task_group", "agent_profile", "task_name"
        ]
        
        # Preserve core context from original enhanced context
        for key in core_context_keys:
            if key in self.context and key not in compressed_context:
                compressed_context[key] = self.context[key]
        
        return compressed_context

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
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

            # Create single comprehensive system message with mandatory context and task
            # Generate LIVE repo map (dynamic, not cached)
            live_repo_map = self._generate_live_repo_map()
            
            # Build mandatory context with live repo map
            mandatory_context = dict(self.context)
            mandatory_context["repo_map"] = live_repo_map
            mandatory_context_json = json.dumps(mandatory_context, indent=2)

            # Load system prompt from ProfileManager
            from .profile_manager import ProfileManager
            pm = ProfileManager()
            system_prompt_template = pm.get_base_system_prompt()
            
            # Check if this agent has a profile-specific system prompt to append
            # This would need to be passed in somehow - for now, just use base prompt

            # Format the system prompt with actual values
            system_message = system_prompt_template.format(
                agent_id=self.agent_id,
                model=self.model,
                available_tools=', '.join(self.tools.keys()),
                mandatory_context_json=mandatory_context_json,
                task_description=task_description
            )

            # Add only the single comprehensive system message - no separate user message
            self.add_message("system", system_message)

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

    def _check_and_compress_context(self, messages: List[Message]) -> List[Message]:
        """Check if context is >75% full and compress if needed, preserving MANDATORY context."""
        try:
            import tiktoken
            
            # Get model max tokens (fallback to 4096 if get_max_tokens unavailable)
            try:
                from litellm import get_max_tokens
                model_max_tokens = get_max_tokens(self.model)
            except Exception:
                model_max_tokens = 4096
            
            # Count current tokens
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                # Fallback to rough estimation
                encoding = None
            
            def count_tokens(text):
                if encoding:
                    return len(encoding.encode(text))
                else:
                    # Rough estimation: ~4 chars per token
                    return len(text) // 4
            
            # MANDATORY CONTEXT - These are IMMUNE to compression
            mandatory_context_keys = [
                "repo_map", "requirements_content", "design_content", 
                "current_task_group", "agent_profile", "task_name"
            ]
            
            # Calculate tokens for MANDATORY context (never compressed)
            mandatory_context = {k: v for k, v in self.context.items() if k in mandatory_context_keys}
            mandatory_tokens = count_tokens(json.dumps(mandatory_context))
            
            # Calculate tokens for conversation messages (can be compressed)
            conversation_tokens = 0
            for msg in messages:
                conversation_tokens += count_tokens(msg.content)
            
            total_tokens = mandatory_tokens + conversation_tokens
            
            # Check if we're using >75% of context
            usage_percentage = total_tokens / model_max_tokens
            
            if usage_percentage > 0.75:
                print(f"🗜️ [{self.agent_id}] Context compression triggered:")
                print(f"   Total tokens: {total_tokens}/{model_max_tokens} ({usage_percentage:.1%})")
                print(f"   Mandatory context: {mandatory_tokens} tokens (IMMUNE to compression)")
                print(f"   Conversation: {conversation_tokens} tokens (compressible)")
                
                # CRITICAL: Only compress conversation messages, NEVER mandatory context
                compressed_messages = []
                
                # 1. ALWAYS keep system message (contains MANDATORY context)
                if messages and messages[0].role == "system":
                    # Rebuild system message with MANDATORY context to ensure it's preserved
                    system_content = messages[0].content
                    # Extract the part before context and rebuild with current mandatory context
                    if "Context provided:" in system_content:
                        base_system = system_content.split("Context provided:")[0]
                        system_content = f"{base_system}Context provided:\n{json.dumps(mandatory_context, indent=2)}"
                    
                    compressed_messages.append(Message(role="system", content=system_content))
                
                # 2. Keep only recent conversation messages (compressible part)
                recent_messages = messages[-8:] if len(messages) > 8 else messages[1:]  # Skip system message
                
                # 3. Add compression notice
                if len(messages) > len(recent_messages) + 1:  # +1 for system message
                    compression_notice = Message(
                        role="system", 
                        content=f"[CONTEXT COMPRESSED: Keeping last {len(recent_messages)} conversation messages out of {len(messages)-1} total. MANDATORY context (repo map, requirements, design, todos, agent profile) is FULLY PRESERVED and IMMUNE to compression.]"
                    )
                    compressed_messages.append(compression_notice)
                
                compressed_messages.extend(recent_messages)
                
                # Calculate new token count
                new_conversation_tokens = sum(count_tokens(msg.content) for msg in compressed_messages)
                new_total_tokens = mandatory_tokens + new_conversation_tokens
                new_usage_percentage = new_total_tokens / model_max_tokens
                
                print("   After compression:")
                print(f"     Mandatory context: {mandatory_tokens} tokens (preserved)")
                print(f"     Conversation: {new_conversation_tokens} tokens (compressed)")
                print(f"     Total: {new_total_tokens}/{model_max_tokens} ({new_usage_percentage:.1%})")
                print(f"     Saved: {total_tokens - new_total_tokens} tokens")
                
                return compressed_messages
            
            return messages
            
        except Exception as e:
            print(f"⚠️ Context compression failed: {e}")
            return messages

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
                # Check and compress context if needed before LLM call
                messages = self._check_and_compress_context(messages)
                
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
                    print("   Content:")
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
                        except Exception as e:
                            # Failed to check todo completion status, log warning and continue
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Failed to check todo completion status: {e}")

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
                self.tools[name] for name in ("read_file", "list_files", "grep_search", "git_status", "git_diff") if name in self.tools
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
            audit_results_tool = {
                "type": "function",
                "function": {
                    "name": "audit_results",
                    "description": "Final audit verdict",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean"},
                            "reasons": {"type": "string"},
                            "additional_tasks": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["passed"],
                    },
                },
            }
            for _ in range(max_iter):
                resp = await self.audit_provider.chat(messages=messages, tools=tool_schemas + [audit_results_tool])
                if resp.tool_calls:
                    # Expecting at most one tool call per iteration
                    tc = resp.tool_calls[0]
                    tool_name = tc.function.get("name", "")
                    if tool_name == "audit_results":
                        payload = json.loads(tc.function.get("arguments", "{}"))
                        audit_passed = payload.get("passed", False)
                        _ = payload.get("reasons", "")
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
                        tool_args = json.loads(tc.function.get("arguments", "{}"))
                        result = await self.tools[tool_name].run(**tool_args)
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
