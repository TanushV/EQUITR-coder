"""
Ask Supervisor Tool - Allows weak agents to consult the strong reasoning model.

Updated to share the core audit-style loop: uses the same read-only tools and
iteration budget as audit, while keeping a distinct system prompt and accepting
explicit context (including full docs) for the supervisor.
"""

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from ...repository.indexer import RepositoryIndexer
from ..base import Tool, ToolResult


class AskSupervisorArgs(BaseModel):
    question: str = Field(
        ..., description="The question or problem to ask the supervisor"
    )
    context_files: Optional[List[str]] = Field(
        default=None, description="Optional list of file paths to include as context"
    )
    include_repo_tree: bool = Field(
        default=True, description="Include repository tree structure in context"
    )
    include_git_status: bool = Field(
        default=True, description="Include current git status in context"
    )


class AskSupervisor(Tool):
    """Tool for weak agents to consult the strong reasoning supervisor model.

    The tool now mirrors the audit loop: it exposes the same read-only tools
    (read_file, list_files, grep_search, git_status, git_diff, plus any MCP
    proxies `mcp:*`) to the supervisor and runs up to the same number of
    iterations as audit.
    """

    def __init__(
        self,
        provider,
        max_calls: int = 5,
        docs_context: Optional[Dict[str, Any]] = None,
    ):
        self.provider = provider
        self.call_count = 0
        self.max_calls = max_calls
        self.docs_context: Optional[Dict[str, Any]] = docs_context
        super().__init__()

    def get_name(self) -> str:
        return "ask_supervisor"

    def get_description(self) -> str:
        return """Ask the supervisor (strong reasoning model) for guidance on complex problems.

        Use this tool when:
        - You need help with architectural decisions
        - You're stuck on a complex problem
        - You need clarification on requirements
        - You want to verify your approach before proceeding

        The supervisor has access to read-only tools and can analyze the codebase."""

    def get_args_schema(self) -> Type[BaseModel]:
        return AskSupervisorArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)

        if self.call_count >= self.max_calls:
            return ToolResult(
                success=False,
                error=f"Maximum supervisor calls ({self.max_calls}) reached for this session",
            )

        self.call_count += 1

        # Build context for supervisor (explicit, labeled)
        context_parts: List[str] = []

        # Include full docs context if available
        try:
            if isinstance(self.docs_context, dict) and self.docs_context:
                import json as _json

                doc_payload: Dict[str, Any] = {}
                for key in (
                    "requirements_content",
                    "design_content",
                    "docs_dir",
                    "todos_path",
                ):
                    if key in self.docs_context:
                        doc_payload[key] = self.docs_context[key]
                if doc_payload:
                    context_parts.append(
                        "FULL DOCUMENTATION CONTEXT (read-only):\n"
                        + _json.dumps(doc_payload, indent=2)
                    )
        except Exception:
            # Non-fatal; continue without docs
            pass

        # Add repository tree if requested
        if args.include_repo_tree:
            try:
                indexer = RepositoryIndexer()
                tree = indexer.get_file_tree()
                tree_str = indexer._format_tree(tree)  # best-effort formatting
                context_parts.append(f"Repository Structure:\n{tree_str}")
            except Exception as e:
                context_parts.append(f"Could not get repository structure: {e}")

        # Add git status if requested
        if args.include_git_status:
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "status", "--porcelain"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    context_parts.append(f"Git Status:\n{result.stdout}")
            except Exception as e:
                context_parts.append(f"Could not get git status: {e}")

        # Add context files if provided
        if args.context_files:
            for file_path in args.context_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        context_parts.append(f"File: {file_path}\n{content}")
                except Exception as e:
                    context_parts.append(f"Could not read {file_path}: {e}")

        # Combine all context
        full_context = "\n\n".join(context_parts)

        # Create supervisor prompt (distinct from audit, but encourage MCP usage and tool loop)
        supervisor_prompt = (
            "You are a senior technical supervisor helping a development agent.\n\n"
            "INSTRUCTIONS:\n"
            "• At each turn, either CALL a read-only tool (read_file, list_files, grep_search, git_status, git_diff, and any MCP tools 'mcp:*') or, when satisfied, provide a final advisory answer.\n"
            "• Prefer calling tools to validate assumptions. MCP tools (mcp:*) may be used to fetch external information when helpful.\n"
            "• Provide clear, actionable guidance the agent can immediately act upon.\n\n"
            f"QUESTION: {args.question}\n\n"
            f"CONTEXT:\n{full_context}\n"
        )

        # Query supervisor model in a loop until it provides an answer
        from ...providers.litellm import Message

        # Available read-only tools for supervisor (match audit set + MCP proxies)
        tool_schemas: List[Dict[str, Any]] = []
        tools_by_name: Dict[str, Any] = {}
        try:
            from ...tools.discovery import (
                discover_tools as _discover_tools,  # type: ignore
            )
        except Exception:
            _discover_tools = None  # type: ignore

        allowed_base = {
            "read_file",
            "list_files",
            "grep_search",
            "git_status",
            "git_diff",
        }
        if _discover_tools:
            try:
                for t in _discover_tools():
                    name = getattr(t, "name", None) or t.get_name()
                    if not name:
                        continue
                    if name in {"ask_supervisor", "send_message", "receive_messages"}:
                        continue
                    if (name in allowed_base) or name.startswith("mcp:"):
                        tools_by_name[name] = t
                        try:
                            tool_schemas.append(t.get_json_schema())
                        except Exception:
                            pass
            except Exception:
                pass

        messages = [Message(role="system", content=supervisor_prompt)]

        # Supervisor reasoning loop (match audit iteration budget)
        max_iterations = 20
        total_cost = 0.0
        for _ in range(max_iterations):
            try:
                response = await self.provider.chat(
                    messages=messages, tools=tool_schemas if tool_schemas else None
                )
                try:
                    total_cost += float(getattr(response, "cost", 0.0) or 0.0)
                except Exception:
                    pass

                if response.tool_calls:
                    # Execute requested tools (read-only + MCP proxies)
                    import json as _json

                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function.get("name", "")
                        raw_args = tool_call.function.get("arguments", "{}")
                        try:
                            tool_args = (
                                _json.loads(raw_args)
                                if isinstance(raw_args, str)
                                else raw_args
                            )
                        except Exception:
                            tool_args = {}

                        if tool_name in tools_by_name:
                            try:
                                tool_obj = tools_by_name[tool_name]
                                result = await tool_obj.run(**(tool_args or {}))
                                content = (
                                    result.json()
                                    if hasattr(result, "json")
                                    else str(result.data or result.error)
                                )
                            except Exception as e:
                                content = f"Tool execution failed: {e}"
                        else:
                            # Fallback to limited built-in executor
                            content = await self._execute_read_only_tool(
                                tool_name, tool_args
                            )

                        messages.append(
                            Message(role="tool", content=content, name=tool_name)
                        )
                else:
                    # Supervisor provided final answer
                    return ToolResult(
                        success=True,
                        data=response.content,
                        metadata={
                            "cost": total_cost,
                            "usage": getattr(response, "usage", {}),
                        },
                    )

            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Supervisor consultation failed: {str(e)}",
                    metadata={"cost": total_cost},
                )

        return ToolResult(
            success=False,
            error="Supervisor did not provide a final answer within iteration limit",
            metadata={"cost": total_cost},
        )

    async def _execute_read_only_tool(self, tool_name: str, args: dict) -> str:
        """Execute read-only tools for the supervisor."""
        try:
            if tool_name == "read_file":
                with open(args.get("path", ""), "r", encoding="utf-8") as f:
                    return f.read()
            elif tool_name == "list_files":
                import os

                path = args.get("path", ".")
                files = os.listdir(path)
                return "\n".join(files)
            elif tool_name == "grep_search":
                import subprocess

                pattern = args.get("pattern", "")
                file_pattern = args.get("file_pattern", "*")
                result = subprocess.run(
                    ["grep", "-r", pattern, file_pattern],
                    capture_output=True,
                    text=True,
                )
                return result.stdout if result.returncode == 0 else "No matches found"
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool execution failed: {str(e)}"
