"""
Ask Supervisor Tool - Allows weak agents to consult the strong reasoning model.
"""

from typing import List, Optional, Type

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
    """Tool for weak agents to consult the strong reasoning supervisor model."""

    def __init__(self, provider, max_calls: int = 5):
        self.provider = provider
        self.call_count = 0
        self.max_calls = max_calls
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
                error=f"Maximum supervisor calls ({self.max_calls}) reached for this session"
            )
        
        self.call_count += 1
        
        # Build context for supervisor
        context_parts = []
        
        # Add repository tree if requested
        if args.include_repo_tree:
            try:
                indexer = RepositoryIndexer()
                tree = indexer.get_tree_structure()
                context_parts.append(f"Repository Structure:\n{tree}")
            except Exception as e:
                context_parts.append(f"Could not get repository structure: {e}")
        
        # Add git status if requested
        if args.include_git_status:
            try:
                import subprocess
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    context_parts.append(f"Git Status:\n{result.stdout}")
            except Exception as e:
                context_parts.append(f"Could not get git status: {e}")
        
        # Add context files if provided
        if args.context_files:
            for file_path in args.context_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_parts.append(f"File: {file_path}\n{content}")
                except Exception as e:
                    context_parts.append(f"Could not read {file_path}: {e}")
        
        # Combine all context
        full_context = "\n\n".join(context_parts)
        
        # Create supervisor prompt
        supervisor_prompt = f"""You are a senior technical supervisor helping a development agent. 
The agent has asked for your guidance on the following question:

QUESTION: {args.question}

CONTEXT:
{full_context}

Please provide clear, actionable guidance. You can use read-only tools like grep_search, read_file, and list_files to investigate further if needed. 

Respond with specific, practical advice that the agent can immediately act upon."""

        # Query supervisor model in a loop until it provides an answer
        from ...providers.litellm import LiteLLMProvider, Message
        
        # Available read-only tools for supervisor
        read_only_tools = []
        try:
            from . import search, fs
            # Add read-only tools that supervisor can use
            read_only_tools = [
                {
                    "name": "grep_search",
                    "description": "Search for text patterns in files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string"},
                            "file_pattern": {"type": "string", "default": "*"}
                        },
                        "required": ["pattern"]
                    }
                },
                {
                    "name": "read_file", 
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "list_files",
                    "description": "List files in a directory", 
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "default": "."}
                        }
                    }
                }
            ]
        except ImportError:
            pass
        
        messages = [Message(role="system", content=supervisor_prompt)]
        
        # Supervisor reasoning loop
        max_iterations = 5
        for iteration in range(max_iterations):
            try:
                response = await self.provider.chat(
                    messages=messages,
                    tools=read_only_tools if read_only_tools else None
                )
                
                if response.tool_calls:
                    # Execute read-only tools for supervisor
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.function["name"]
                        tool_args = tool_call.function.get("arguments", {})
                        
                        # Execute the tool and add result to conversation
                        tool_result = await self._execute_read_only_tool(tool_name, tool_args)
                        messages.append(Message(
                            role="tool",
                            content=tool_result,
                            name=tool_name
                        ))
                else:
                    # Supervisor provided final answer
                    return ToolResult(
                        success=True,
                        data=response.content
                    )
                    
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Supervisor consultation failed: {str(e)}"
                )
        
        return ToolResult(
            success=False,
            error="Supervisor did not provide a final answer within iteration limit"
        )
    
    async def _execute_read_only_tool(self, tool_name: str, args: dict) -> str:
        """Execute read-only tools for the supervisor."""
        try:
            if tool_name == "read_file":
                with open(args.get("path", ""), 'r', encoding='utf-8') as f:
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
                    ['grep', '-r', pattern, file_pattern],
                    capture_output=True, text=True
                )
                return result.stdout if result.returncode == 0 else "No matches found"
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool execution failed: {str(e)}"