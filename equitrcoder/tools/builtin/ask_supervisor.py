"""
Ask Supervisor Tool - Allows weak agents to consult the strong reasoning model.
"""

from typing import Type, Optional, List
from pydantic import BaseModel, Field
from ..base import Tool, ToolResult
from ...repository.indexer import RepositoryIndexer


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
        - Facing complex architectural decisions
        - Need deep analysis of code relationships
        - Encountering difficult bugs or edge cases
        - Planning complex refactoring or system design
        - Need strategic guidance on project direction
        - Unsure about optimal implementation approaches

        The supervisor will analyze your question with full context including repository structure,
        current state, and any specified files. This is your primary tool for leveraging the
        strong model's reasoning capabilities."""

    def get_args_schema(self) -> Type[BaseModel]:
        return AskSupervisorArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            # Check call limit
            if self.call_count >= self.max_calls:
                return ToolResult(
                    success=False,
                    error=f"Maximum supervisor calls ({self.max_calls}) exceeded. "
                          "Try to proceed independently or request manual intervention."
                )
            
            self.call_count += 1
            args = self.validate_args(kwargs)

            # Build comprehensive context
            context_parts = []

            # Add repository context
            if args.include_repo_tree:
                try:
                    # Use current directory as fallback

                    repo_path = "."
                    indexer = RepositoryIndexer(repo_path=repo_path)
                    tree = indexer.get_directory_tree()
                    if tree:
                        context_parts.append(f"Repository structure:\n{tree}")
                except Exception:
                    pass

            # Add git status
            if args.include_git_status:
                try:
                    from .git import GitStatus

                    git_tool = GitStatus()
                    git_result = await git_tool.run()
                    if git_result.success:
                        context_parts.append(f"Git status:\n{git_result.data}")
                except Exception:
                    pass

            # Add file contents if specified
            if args.context_files:
                from .fs import ReadFile

                read_tool = ReadFile()

                for file_path in args.context_files:
                    try:
                        file_result = await read_tool.run(path=file_path)
                        if file_result.success:
                            context_parts.append(
                                f"File: {file_path}\n```\n{file_result.data}\n```"
                            )
                    except Exception:
                        pass

            # Build full context
            full_context = "\n\n".join(context_parts) if context_parts else ""

            # Create supervisor prompt
            supervisor_prompt = f"""You are the supervisor (strong reasoning model) helping a worker agent with a complex problem. Your role is to provide strategic, high-level guidance that the worker agent can act upon.

WORKER AGENT QUESTION:
{args.question}

AVAILABLE CONTEXT:
{full_context}

SUPERVISOR GUIDANCE FRAMEWORK:
As the supervisor, provide structured guidance that includes:

1. **STRATEGIC ANALYSIS** (2-3 sentences)
   - What's the core challenge or opportunity?
   - What are the key trade-offs to consider?

2. **RECOMMENDED APPROACH** (specific and actionable)
   - Clear step-by-step plan
   - Specific tools or techniques to use
   - Priority order for implementation

3. **ARCHITECTURAL CONSIDERATIONS**
   - How does this fit into the broader codebase?
   - What patterns or conventions should be followed?
   - Potential impact on existing code

4. **RISK ASSESSMENT**
   - What could go wrong?
   - How to validate the approach?
   - When to escalate back to supervisor

5. **NEXT STEPS**
   - Immediate next action for worker agent
   - Success criteria to check

FORMAT YOUR RESPONSE:
Use clear markdown sections with headers. Be concise but comprehensive. Focus on actionable guidance that the worker agent can implement immediately."""

            # Use the provider to get supervisor response
            response = await self.provider.chat(
                messages=[{"role": "user", "content": supervisor_prompt}],
                temperature=0.1,
                max_tokens=2000,
            )

            return ToolResult(
                success=True,
                data={
                    "question": args.question,
                    "response": response.content,
                    "context_provided": {
                        "repo_tree": args.include_repo_tree,
                        "git_status": args.include_git_status,
                        "files": args.context_files or [],
                    },
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


def create_ask_supervisor_tool(provider) -> AskSupervisor:
    """Factory function to create ask_supervisor tool."""
    return AskSupervisor(provider)
