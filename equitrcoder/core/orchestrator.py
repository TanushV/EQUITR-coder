import asyncio
import json
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..providers.openrouter import OpenRouterProvider, Message, ToolCall
from ..providers.litellm import LiteLLMProvider
from ..tools import registry, discovery
from ..repository.indexer import RepositoryIndexer
from .context_manager import ContextManager
from .session import SessionManagerV2
from .config import Config, config_manager
from .supervisor import SupervisorAgent
from .documentation import DocumentationGenerator
from ..tools.builtin.git_auto import GitAutoCommit
from ..utils.tool_logger import get_tool_logger, configure_tool_logger


class AgentOrchestrator:
    """Main orchestrator for the EQUITR Coder."""

    def __init__(
        self,
        config: Config,
        repo_path: str = ".",
        provider: Optional[OpenRouterProvider] = None,
        session_manager: Optional[SessionManagerV2] = None,
        available_tools: Optional[List[str]] = None,
        max_iterations: Optional[int] = None,
        model: Optional[str] = None,
        supervisor_model: Optional[str] = None,
        worker_model: Optional[str] = None,
    ):
        self.config = config
        self.repo_path = repo_path
        # Optional model override (e.g. "openai/gpt-4" or "my_custom_model")
        self._model_override = model
        self._supervisor_model_override = supervisor_model
        self._worker_model_override = worker_model

        # Configure tool call logging
        configure_tool_logger(
            log_file=config.orchestrator.tool_log_file,
            enabled=config.orchestrator.log_tool_calls,
        )
        self.tool_logger = get_tool_logger()

        # Initialize components
        self.provider = provider or self._create_provider(config)
        self.context_manager = ContextManager(
            max_tokens=config.session.max_context,
            model=getattr(self.provider, "model", config.llm.model),
        )
        self.session_manager = session_manager or SessionManagerV2(
            config.session.session_dir
        )
        self.repo_indexer = RepositoryIndexer(
            repo_path=repo_path, ignore_patterns=config.repository.ignore_patterns
        )
        self.git_auto = GitAutoCommit(repo_path)

        # Initialize tools
        discovery.discover_builtin_tools()
        discovery.discover_custom_tools()

        # Register ask_supervisor tool only for multi-agent mode (weak agents)
        if self.config.orchestrator.use_multi_agent:
            from equitrcoder.tools.builtin.ask_supervisor import (
                create_ask_supervisor_tool,
            )

            registry.register(create_ask_supervisor_tool(self.provider))

        # Tool restrictions for worker agents
        self.available_tools = available_tools

        # Iteration limits for worker agents
        self.max_iterations = max_iterations or config.orchestrator.max_iterations

        # Runtime state
        self.total_cost = 0.0
        self.iteration_count = 0

        # Check model compatibility for function calling
        self._check_model_compatibility()

        # Initialize supervisor for multi-agent mode with separate models
        supervisor_provider = (
            self._create_supervisor_provider(config)
            if config.orchestrator.use_multi_agent
            else self.provider
        )
        worker_provider = (
            self._create_worker_provider(config)
            if config.orchestrator.use_multi_agent
            else self.provider
        )

        self.supervisor = SupervisorAgent(
            supervisor_provider,
            self.session_manager,
            self.repo_path,
            use_multi_agent=config.orchestrator.use_multi_agent,
            worker_provider=worker_provider,
        )

        # Initialize documentation generator
        self.doc_generator = DocumentationGenerator(self.provider, self.repo_path)

        # Context compressor for long conversations
        from .context_compressor import ContextCompressor

        self.context_compressor = ContextCompressor(self.provider)

    def _create_provider(self, config: Config):
        """Create appropriate provider based on configuration."""
        # Priority: explicit override > config active model
        model_config = (
            self._parse_model_override()
            or config_manager.get_active_model_config(config)
        )
        provider_type = model_config.get("provider", "litellm")

        # Validate model is specified
        model_name = model_config.get("model", "")
        if not model_name:
            raise ValueError(
                "No model specified. Please select a model using:\n"
                "1. Run 'EQUITR-coder models --discover' to see available models\n"
                "2. Use --model parameter with your chosen model\n"
                "3. Set model in configuration"
            )

        # Validate model supports function calling (required for EQUITR Coder)
        from ..utils.litellm_utils import check_function_calling_support

        if not check_function_calling_support(model_name):
            raise ValueError(
                f"Model '{model_name}' does not support function calling, which is required for EQUITR Coder.\n"
                f"Please select a model that supports function calling such as:\n"
                f"- OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo\n"
                f"- Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku\n"
                f"- Google: gemini-pro, gemini-1.5-pro\n"
                f"- Moonshot: moonshot/moonshot-v1-8k, moonshot/moonshot-v1-32k\n"
                f"Run 'EQUITR-coder models --discover' to see all available models."
            )

        if provider_type == "litellm":
            return LiteLLMProvider.from_config(model_config)
        elif provider_type == "openrouter":
            return OpenRouterProvider.from_env(model=model_name)
        else:
            # Default to LiteLLM for unknown providers
            return LiteLLMProvider.from_config(model_config)

    def _create_supervisor_provider(self, config: Config):
        """Create a provider specifically for the supervisor."""
        # Priority: supervisor override > config supervisor model > main model
        model_override = (
            self._supervisor_model_override
            or config.orchestrator.supervisor_model
            or self._model_override
        )

        if model_override:
            # Create temporary config with supervisor model
            temp_config = config.model_copy()
            temp_config.llm.model = model_override
            model_config = self._parse_model_override(
                model_override
            ) or config_manager.get_active_model_config(temp_config)
        else:
            model_config = config_manager.get_active_model_config(config)

        provider_type = model_config.get("provider", "litellm")
        model_name = model_config.get("model", "")

        if not model_name:
            raise ValueError("No supervisor model specified")

        # Validate supervisor model supports function calling
        from ..utils.litellm_utils import check_function_calling_support

        if not check_function_calling_support(model_name):
            raise ValueError(
                f"Supervisor model '{model_name}' does not support function calling, which is required for EQUITR Coder.\n"
                f"Please select a supervisor model that supports function calling."
            )

        if provider_type == "litellm":
            return LiteLLMProvider.from_config(model_config)
        elif provider_type == "openrouter":
            return OpenRouterProvider.from_env(model=model_name)
        else:
            return LiteLLMProvider.from_config(model_config)

    def _create_worker_provider(self, config: Config):
        """Create a provider specifically for worker agents."""
        # Priority: worker override > config worker model > main model
        model_override = (
            self._worker_model_override
            or config.orchestrator.worker_model
            or self._model_override
        )

        if model_override:
            # Create temporary config with worker model
            temp_config = config.model_copy()
            temp_config.llm.model = model_override
            model_config = self._parse_model_override(
                model_override
            ) or config_manager.get_active_model_config(temp_config)
        else:
            model_config = config_manager.get_active_model_config(config)

        provider_type = model_config.get("provider", "litellm")
        model_name = model_config.get("model", "")

        if not model_name:
            raise ValueError("No worker model specified")

        # Validate worker model supports function calling
        from ..utils.litellm_utils import check_function_calling_support

        if not check_function_calling_support(model_name):
            raise ValueError(
                f"Worker model '{model_name}' does not support function calling, which is required for EQUITR Coder.\n"
                f"Please select a worker model that supports function calling."
            )

        if provider_type == "litellm":
            return LiteLLMProvider.from_config(model_config)
        elif provider_type == "openrouter":
            return OpenRouterProvider.from_env(model=model_name)
        else:
            return LiteLLMProvider.from_config(model_config)

    def _check_model_compatibility(self):
        """Check if the current model supports function calling."""
        from ..utils.litellm_utils import get_model_compatibility, get_compatible_tools

        model_name = getattr(self.provider, "model", self.config.llm.model)
        validation = get_model_compatibility(model_name)

        if not validation["function_calling"]:
            if validation["warnings"]:
                print(f"⚠️  Warning: {validation['warnings'][0]}")
            print("   EQUITR Coder will continue without tool execution capabilities.")

        # Store compatibility info for later use
        self.model_compatibility = validation

    def _parse_model_override(
        self, model_override: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Return a model_config dict if a CLI / programmatic override was supplied."""
        override = model_override or self._model_override
        if not override:
            return None

        # If the override matches a named model profile, use it directly
        if override in self.config.llm.models:
            return self.config.llm.models[override]

        # Otherwise treat it as a provider/model string
        if "/" in override:
            _provider_type, _model_name = override.split("/", 1)
        else:
            _provider_type, _model_name = "openai", override

        return {
            "provider": "litellm",
            "model": override,
            "temperature": self.config.llm.temperature,
            "max_tokens": self.config.llm.max_tokens,
            "api_key": self.config.llm.api_key,
            "api_base": self.config.llm.api_base,
        }

    async def run(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        force_documentation: bool = True,
    ) -> dict:
        """Run the agent orchestrator loop with MANDATORY documentation context."""

        # Load or create session
        if session_id:
            session = self.session_manager.load_session(session_id)
            if not session:
                print(f"Session {session_id} not found, creating new session")
                session = self.session_manager.create_session(session_id)
        else:
            session = self.session_manager.create_session()

        # MANDATORY: Load or generate all three documentation files
        docs = self.doc_generator.get_existing_documents()

        # If documentation doesn't exist, generate it from the user input
        if not docs or not all(
            key in docs for key in ["requirements", "design", "todos"]
        ):
            print("📋 Generating mandatory documentation from user input...")

            # Create a planning conversation from the user input
            planning_conversation = [{"role": "user", "content": user_input}]

            # Generate documentation iteratively (without feedback callback for API usage)
            docs = await self.doc_generator.generate_documents_iteratively(
                planning_conversation,
                feedback_callback=None,  # No interactive feedback in orchestrator
            )

            if not docs:
                error_msg = "CRITICAL: Failed to generate mandatory documentation. Please provide a clearer description of what you want to build."
                return {
                    "content": error_msg,
                    "usage": {},
                    "cost": 0.0,
                    "error": "documentation_generation_failed",
                }

            print("✅ Documentation generated successfully!")

        # MANDATORY: Always include ALL documentation in context - NO EXCEPTIONS
        doc_context = f"""
MANDATORY PROJECT DOCUMENTATION CONTEXT:

===== REQUIREMENTS DOCUMENT =====
{docs['requirements']}

===== DESIGN DOCUMENT =====
{docs['design']}

===== TODO LIST =====
{docs['todos']}

===== USER REQUEST =====
{user_input}

INSTRUCTIONS:
- You MUST reference and follow the above documentation for ALL responses
- You MUST ensure your response aligns with the requirements, design, and todos
- You MUST update the todo list progress as you complete tasks
- You MUST maintain consistency with the documented architecture and design
"""

        # Always use documentation context - NO EXCEPTIONS
        contextualized_input = doc_context

        # Check if we should use multi-agent mode
        if self.supervisor.should_use_multiagent(contextualized_input):
            return {
                "content": await self._run_multiagent(contextualized_input, session),
                "usage": {},
                "cost": self.total_cost,
            }
        else:
            return await self._run_single_agent(contextualized_input, session)

    async def _run_multiagent(self, user_input: str, session) -> str:
        """Run in multi-agent mode with supervisor coordination and MANDATORY documentation context."""

        # CRITICAL VALIDATION: Ensure we have documentation context
        if "MANDATORY PROJECT DOCUMENTATION CONTEXT" not in user_input:
            return "EXECUTION BLOCKED: No mandatory documentation context found in user input. All multi-agent execution must include requirements, design, and todos."

        print(f"🤖 Using multi-agent mode with MANDATORY documentation context")

        # Add user message to session
        user_message = Message(role="user", content=user_input)
        self.session_manager.add_message(user_message)

        try:
            # Step 1: Break down the request into tasks
            task_list = await self.supervisor.break_into_tasks(user_input)

            print(f"📋 Created {len(task_list.tasks)} tasks for multi-agent execution")

            # Step 2: Execute tasks using worker agents
            results = await self.supervisor.spawn_workers(task_list)

            # Step 3: Compile results into a response
            response_parts = []
            response_parts.append("✅ Multi-agent execution completed!")
            response_parts.append(f"📊 Summary: {results['summary']}")

            if results["task_results"]:
                response_parts.append("\n🔍 Task Results:")
                for task_id, result in results["task_results"].items():
                    if result["success"]:
                        response_parts.append(f"  ✓ Task {task_id}: {result['result']}")
                    else:
                        response_parts.append(f"  ❌ Task {task_id}: {result['error']}")

            # Get message pool status for additional context
            pool_status = await self.supervisor.get_status()
            if pool_status["recent_messages"]:
                response_parts.append("\n💬 Agent Communication Summary:")
                response_parts.append(
                    f"  - {len(pool_status['recent_messages'])} messages exchanged"
                )
                response_parts.append(
                    f"  - Active agents: {', '.join(pool_status['active_workers'])}"
                )

            response = "\n".join(response_parts)

            # Add assistant response to session
            assistant_message = Message(role="assistant", content=response)
            self.session_manager.add_message(assistant_message)

            # Check if audit should be triggered for multi-agent mode
            await self._check_and_trigger_multiagent_audit()

            return response

        except Exception as e:
            error_message = f"❌ Error in multi-agent execution: {str(e)}"
            print(error_message)

            # Add error to session
            error_msg = Message(role="assistant", content=error_message)
            self.session_manager.add_message(error_msg)

            return error_message

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _call_llm_with_retry(
        self, messages: List[Message], tool_schemas: List[Dict[str, Any]]
    ):
        """Call LLM with retry logic."""
        # Only provide tools if model supports function calling
        tools_to_use = (
            tool_schemas
            if tool_schemas and self.model_compatibility["supported"]
            else None
        )

        # Debug: Print tool information
        print(f"DEBUG: Model compatibility: {self.model_compatibility}")
        print(
            f"DEBUG: Tool schemas provided: {len(tool_schemas) if tool_schemas else 0}"
        )
        print(f"DEBUG: Tools to use: {len(tools_to_use) if tools_to_use else 0}")
        if tools_to_use:
            print(
                f"DEBUG: Tool names: {[tool.get('name', 'unknown') for tool in tools_to_use]}"
            )

        # Context compression if needed
        if self.context_manager.should_truncate(messages, system_prompt="") and not any(
            m.content.startswith("COMPRESSED CONTEXT SUMMARY") for m in messages
        ):
            # Compress everything except last 8 messages to keep recent history
            older_messages = messages[:-8] if len(messages) > 8 else []
            if older_messages:
                summary_msg = await self.context_compressor.compress(older_messages)
                # keep last 8 messages + summary
                messages = [summary_msg] + messages[-8:]

        response = await self.provider.chat(
            messages=messages,
            tools=tools_to_use,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        )

        # Debug: Print response information
        print(f"DEBUG: Response has tool calls: {bool(response.tool_calls)}")
        if response.tool_calls:
            print(
                f"DEBUG: Tool calls: {[tc.function['name'] for tc in response.tool_calls]}"
            )

        # Debug mode: Show live LLM response
        if self.config.orchestrator.debug:
            print(f"\n🤖 LLM Response:")
            print(f"   Content: {response.content}")
            if response.tool_calls:
                print(f"   Tool calls ({len(response.tool_calls)}):")
                for i, tc in enumerate(response.tool_calls, 1):
                    print(
                        f"     {i}. {tc.function['name']}: {tc.function.get('arguments', {})}"
                    )
            print()

        return response

    async def _execute_tools(
        self,
        tool_calls: List[ToolCall],
        enabled_tools: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> List[Any]:
        """Execute tool calls concurrently with logging."""
        tasks = []
        start_times = []

        for tool_call in tool_calls:
            tool_name = tool_call.function["name"]
            tool_args = tool_call.function.get("arguments", {})

            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}

            # Debug mode: Show tool execution
            if self.config.orchestrator.debug:
                print(f"🔧 Executing tool: {tool_name}")
                print(f"   Args: {tool_args}")

            start_time = time.time()
            start_times.append(start_time)

            # safety: path validation helper
            def _path_safe(p: str) -> bool:
                try:
                    root = Path(self.repo_path).resolve()
                    return Path(p).resolve().is_relative_to(root)
                except Exception:
                    return False

            # Block any file-system tool call that tries to escape repo root
            dangerous = False
            for key in ("path", "target_file", "file", "filename"):
                if key in tool_args and isinstance(tool_args[key], str):
                    if not _path_safe(tool_args[key]):
                        dangerous = True
                        break

            if dangerous:
                from ..tools.base import ToolResult

                async def error_result():
                    return ToolResult(
                        success=False, error="Path outside workspace is not allowed"
                    )

                tasks.append(error_result())
            else:
                if tool_name in enabled_tools:
                    tool = enabled_tools[tool_name]
                    tasks.append(tool.run(**tool_args))
                else:

                    async def error_result():
                        from ..tools.base import ToolResult

                        return ToolResult(
                            success=False,
                            error=f"Tool '{tool_name}' not found or not enabled",
                        )

                    tasks.append(error_result())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results and log tool calls
        final_results = []
        for i, (tool_call, result) in enumerate(zip(tool_calls, results)):
            duration_ms = (time.time() - start_times[i]) * 1000
            tool_name = tool_call.function["name"]

            if isinstance(result, Exception):
                from ..tools.base import ToolResult

                tool_result = ToolResult(success=False, error=str(result))
                final_results.append(tool_result)
            else:
                tool_result = result
                final_results.append(result)

            # Debug mode: Show tool result
            if self.config.orchestrator.debug:
                status = "✅" if tool_result.success else "❌"
                print(f"   Result: {status} ({duration_ms:.1f}ms)")
                if tool_result.success:
                    result_str = str(tool_result)
                    print(f"   Output: {result_str[:100]}...")
                else:
                    print(f"   Error: {tool_result.error}")
                print()

            # Log the tool call
            if self.tool_logger.enabled:
                self.tool_logger.log_tool_call(
                    tool_call=tool_call,
                    result=tool_result,
                    duration_ms=duration_ms,
                    session_id=session_id,
                )

        return final_results

    def _build_system_prompt(self, repo_context: str) -> str:
        """Build the system prompt with repository context."""

        if self.model_compatibility["supported"]:
            prompt = """You are EQUITR Coder, an advanced AI assistant that can execute tools to help with software development and general tasks.

You have access to various tools for:
- File system operations (create, read, edit, list files)
- Git operations (commit, status, diff)
- Shell command execution (in a sandboxed environment)
- Web search
- And more depending on the current configuration

When responding:
1. Think step by step about what needs to be done
2. Use tools when appropriate to gather information or make changes
3. Provide clear explanations of what you're doing
4. If you encounter errors, try alternative approaches
5. Always prioritize security and safety

Current working directory: {}
Session configuration: {}
Available tools: {}""".format(
                self.repo_path,
                self.config.llm.model,
                ", ".join(self.config.tools.enabled),
            )
        else:
            prompt = """You are EQUITR Coder, an advanced AI assistant for software development and general tasks.

Note: The current model ({}) does not support function calling, so tool execution is disabled.
You can still provide guidance, code examples, and explanations, but cannot directly execute tools.

When responding:
1. Think step by step about what needs to be done
2. Provide clear code examples and explanations
3. Guide users on how to perform tasks manually
4. If you encounter limitations, explain them clearly
5. Always prioritize security and safety

Current working directory: {}
Session configuration: {}""".format(
                self.config.llm.model, self.repo_path, self.config.llm.model
            )

        if repo_context:
            prompt += f"\n\nRepository context:\n{repo_context}"

        return prompt

    async def _run_single_agent(self, user_input: str, session) -> dict:
        """Run in single-agent mode with MANDATORY documentation context validation."""

        # CRITICAL VALIDATION: Ensure we have documentation context
        if "MANDATORY PROJECT DOCUMENTATION CONTEXT" not in user_input:
            return {
                "content": "EXECUTION BLOCKED: No mandatory documentation context found in user input. All execution must include requirements, design, and todos.",
                "usage": {},
                "cost": 0.0,
                "error": "missing_documentation_context",
            }

        # Add user message to session
        user_message = Message(role="user", content=user_input)
        self.session_manager.add_message(user_message)

        # Get repository context
        repo_context = await self.repo_indexer.get_context(user_input)

        # Build system prompt
        system_prompt = self._build_system_prompt(repo_context)

        # Get conversation history
        messages = self.session_manager.get_messages()

        # Add system message if this is the first message
        if len(messages) == 1:  # Only user message exists
            messages.insert(0, Message(role="system", content=system_prompt))

        # Get enabled tools
        enabled_tools = {
            name: tool
            for name, tool in registry.get_all().items()
            if name in self.config.tools.enabled
            and name not in self.config.tools.disabled
        }

        # Filter tools if restrictions are set
        if self.available_tools:
            enabled_tools = {
                name: tool
                for name, tool in enabled_tools.items()
                if name in self.available_tools
            }

        # Build tool schemas
        tool_schemas = [tool.get_json_schema() for tool in enabled_tools.values()]

        # Initialize iteration tracking
        iteration = 0

        # Main iteration loop - continue until model indicates completion (no more tool calls)
        # Unlimited iterations - only stops when model decides task is complete
        while True:
            iteration += 1

            # Call LLM
            response = await self._call_llm_with_retry(messages, tool_schemas)

            # Update cost
            self.total_cost += response.cost or 0

            # Process response
            assistant_message = Message(role="assistant", content=response.content)

            # Handle tool calls if any
            if response.tool_calls:
                # Add assistant message with tool calls first
                assistant_message.tool_calls = response.tool_calls
                messages.append(assistant_message)

                tool_results = await self._execute_tools(
                    response.tool_calls,
                    enabled_tools,
                    session.session_id if session else None,
                )

                # Add tool results to messages
                for tool_call, result in zip(response.tool_calls, tool_results):
                    tool_message = Message(
                        role="tool", content=str(result), tool_call_id=tool_call.id
                    )
                    messages.append(tool_message)

                # Continue the iteration loop - the model will decide if more work is needed
                continue
            else:
                # No tool calls, task is complete
                break

        # Add final assistant response to session
        self.session_manager.add_message(assistant_message)

        # Check if audit should be triggered
        audit_triggered = await self._check_and_trigger_audit(messages, tool_schemas)

        response_data = {
            "content": assistant_message.content,
            "usage": response.usage or {},
            "cost": self.total_cost,
        }

        if audit_triggered:
            response_data["audit_triggered"] = True

        return response_data

    async def _check_and_trigger_audit(
        self, messages: List[Message], tool_schemas: List[Dict[str, Any]]
    ) -> bool:
        """Check if audit should be triggered and run it if needed."""
        try:
            # Import audit manager
            from ..tools.builtin.audit import audit_manager

            # Check if audit should be triggered
            if not audit_manager.should_trigger_audit():
                return False

            print("🔍 All todos completed! Triggering automatic audit...")

            # Get audit context
            audit_context = audit_manager.get_audit_context()

            # Create audit message
            audit_message = Message(
                role="user",
                content=f"""
🔍 AUTOMATIC AUDIT TRIGGERED - All todos completed!

{audit_context}

Please perform a comprehensive audit of the codebase:

1. Use list_files to see all files in the project
2. Use read_file to examine design documents, requirements, and key implementation files
3. Use grep_search to verify implementations match requirements
4. Check if all requirements from design documents are implemented
5. Verify code quality and completeness

Based on your audit:
- If everything is complete and faithful to requirements: Respond with "AUDIT PASSED"
- If issues are found: Respond with "AUDIT FAILED" and create new todos for fixes using create_todo

Begin audit now.
""",
            )

            # Add audit message to conversation
            messages.append(audit_message)

            # Start audit iteration loop
            audit_iteration = 0
            max_audit_iterations = 50  # Allow more thorough audits
            while audit_iteration < max_audit_iterations:
                audit_iteration += 1

                # Call LLM for audit
                response = await self._call_llm_with_retry(messages, tool_schemas)

                # Update cost
                self.total_cost += response.cost or 0

                # Handle audit response
                audit_response = Message(role="assistant", content=response.content)

                # If the model produced any tool call we treat that as the
                # final PASS / FAIL signal (the content should include the
                # explanation; we do not parse it).
                if response.tool_calls:
                    audit_response.tool_calls = response.tool_calls
                    messages.append(audit_response)

                    enabled_tools = {
                        name: tool
                        for name, tool in registry.get_all().items()
                        if name in self.config.tools.enabled
                        and name not in self.config.tools.disabled
                    }

                    await self._execute_tools(response.tool_calls, enabled_tools, None)
                    # One round of audit tool execution is enough – exit.
                    return True

                # No tool calls yet – record assistant message and continue.
                messages.append(audit_response)

            print("⚠️ Audit reached maximum iterations without producing a tool call")
            return False

        except Exception as e:
            print(f"⚠️ Audit trigger error: {e}")
            return False

    async def _check_and_trigger_multiagent_audit(self):
        """Check if audit should be triggered for multi-agent mode."""
        try:
            # Import audit manager
            from ..tools.builtin.audit import audit_manager

            # Check if audit should be triggered
            if not audit_manager.should_trigger_audit():
                return False

            print("🔍 All todos completed! Triggering automatic audit via supervisor...")

            # Delegate audit to supervisor
            if hasattr(self, "supervisor") and self.supervisor:
                await self.supervisor.trigger_audit()

            return True

        except Exception as e:
            print(f"⚠️ Multi-agent audit trigger error: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        await self.provider.close()
