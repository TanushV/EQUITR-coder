#!/usr/bin/env python3
"""
EQUITR Coder - Interactive CLI with Mandatory Documentation Generation

This CLI enforces an interactive workflow where:
1. User has a back-and-forth conversation with the LLM
2. Once satisfied, generates mandatory documentation (todo, requirements, design)
3. Uses generated docs as context for execution
4. Supports both single-agent and multi-agent modes
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text

from .core.config import config_manager
from .core.orchestrator import AgentOrchestrator
from .core.planning import ConversationalPlanner
from .core.documentation import DocumentationGenerator
from .tools.builtin.git_auto import GitAutoCommit

app = typer.Typer(
    name="equitrcoder",
    help="EQUITR Coder - Interactive AI coding assistant with mandatory documentation generation",
    add_completion=False,
)

console = Console()


def show_welcome():
    """Show welcome message and instructions."""
    welcome_text = Text()
    welcome_text.append("🚀 EQUITR Coder - Interactive Mode\n", style="bold green")
    welcome_text.append("\nWorkflow:\n", style="bold cyan")
    welcome_text.append(
        "1. Chat with the AI to discuss your requirements\n", style="dim"
    )
    welcome_text.append(
        "2. AI generates mandatory documentation (todo, requirements, design)\n",
        style="dim",
    )
    welcome_text.append("3. Review and approve documentation\n", style="dim")
    welcome_text.append(
        "4. AI executes tasks using documentation as context\n", style="dim"
    )
    welcome_text.append("\nCommands:\n", style="bold yellow")
    welcome_text.append("  /quit - Exit the session\n", style="dim")
    welcome_text.append("  /clear - Clear conversation history\n", style="dim")
    welcome_text.append("  /status - Show session status\n", style="dim")
    welcome_text.append("  /multi-agent - Toggle multi-agent mode\n", style="dim")
    welcome_text.append("  /help - Show this help\n", style="dim")

    console.print(Panel(welcome_text, title="EQUITR Coder", border_style="green"))


def show_session_status(orchestrator: AgentOrchestrator):
    """Show current session status."""
    messages = orchestrator.session_manager.get_messages()
    multi_agent_status = (
        "Enabled" if orchestrator.config.orchestrator.use_multi_agent else "Disabled"
    )

    status_text = Text()
    status_text.append(f"Messages: {len(messages)}\n", style="cyan")
    status_text.append(f"Total cost: ${orchestrator.total_cost:.4f}\n", style="cyan")
    status_text.append(f"Iterations: {orchestrator.iteration_count}\n", style="cyan")
    status_text.append(f"Multi-agent: {multi_agent_status}\n", style="cyan")
    status_text.append(f"Model: {orchestrator.config.llm.model}\n", style="cyan")

    console.print(Panel(status_text, title="Session Status", border_style="blue"))


async def conduct_planning_conversation(
    orchestrator: AgentOrchestrator, initial_request: str
) -> Optional[dict]:
    """Conduct the mandatory planning conversation."""
    console.print("\n[bold green]🎯 Starting Planning Conversation[/bold green]")
    console.print(
        "[dim]The AI will ask questions to understand your requirements...[/dim]\n"
    )

    # Initialize the planning conversation
    conversation_history = []
    conversation_history.append({"role": "user", "content": initial_request})

    # Planning conversation loop
    while True:
        # Get AI response/questions
        planning_prompt = f"""
You are EQUITR Coder, an AI assistant that helps with software development projects.

The user has made this initial request: "{initial_request}"

Your task is to conduct a thorough planning conversation to understand:
1. The exact requirements and scope
2. Technical constraints and preferences
3. Architecture and design decisions
4. Implementation details and priorities

Based on the conversation so far:
{conversation_history}

Ask ONE specific, clarifying question to better understand the requirements.
If you have enough information to create comprehensive documentation, respond with "READY_TO_DOCUMENT".
Be conversational and helpful.
"""

        response = await orchestrator.run(planning_prompt)
        ai_response = response.get("content", "")

        if "READY_TO_DOCUMENT" in ai_response:
            console.print("\n[green]✅ Planning conversation complete![/green]")
            break

        # Show AI's question
        console.print(Panel(ai_response, title="🤖 EQUITR Coder", border_style="blue"))

        # Get user's response
        user_response = Prompt.ask("\n[bold cyan]Your response[/bold cyan]")

        if user_response.lower() in ["/quit", "/exit"]:
            return None

        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_history.append({"role": "user", "content": user_response})

    return {"conversation": conversation_history}


async def generate_documentation(
    orchestrator: AgentOrchestrator, conversation_data: dict
) -> Optional[dict]:
    """Generate mandatory documentation based on conversation with iterative feedback."""
    console.print("\n[bold green]📋 Generating Documentation...[/bold green]")

    # Create documentation generator
    doc_generator = DocumentationGenerator(orchestrator.provider, str(Path.cwd()))

    # Create feedback callback for interactive revision
    feedback_callback = create_feedback_callback()

    # Generate documents iteratively with user feedback
    docs = await doc_generator.generate_documents_iteratively(
        conversation_data["conversation"], feedback_callback=feedback_callback
    )

    if not docs:
        console.print("[red]❌ Failed to generate documentation[/red]")
        return None

    return docs


async def review_and_approve_documentation(docs: dict) -> bool:
    """Review and approve generated documentation."""
    console.print("\n[bold green]📋 Generated Documentation[/bold green]")

    # Display all documents
    console.print(
        Panel(
            docs["requirements"], title="📄 Requirements Document", border_style="green"
        )
    )
    console.print(
        Panel(docs["design"], title="🏗️ Design Document", border_style="blue")
    )
    console.print(Panel(docs["todos"], title="✅ Todo List", border_style="yellow"))

    # Approval loop
    while True:
        choice = Prompt.ask(
            "\n[bold cyan]Review documentation[/bold cyan]",
            choices=["approve", "revise", "quit"],
            default="approve",
        )

        if choice == "approve":
            console.print("[green]✅ Documentation approved![/green]")
            return True
        elif choice == "revise":
            # Collect specific feedback for each document
            feedback = {"action": "revise", "changes": "", "specific_feedback": {}}

            console.print(
                "\n[bold cyan]Please provide feedback for revision:[/bold cyan]"
            )

            # General changes
            general_feedback = Prompt.ask(
                "[cyan]What general changes would you like?[/cyan]", default=""
            )
            if general_feedback:
                feedback["changes"] = general_feedback

            # Document-specific feedback
            for doc_type in ["requirements", "design", "todos"]:
                doc_feedback = Prompt.ask(
                    f"[cyan]Any specific changes for {doc_type}?[/cyan]", default=""
                )
                if doc_feedback:
                    feedback["specific_feedback"][doc_type] = doc_feedback

            return feedback
        elif choice == "quit":
            return False


def create_feedback_callback():
    """Create a feedback callback function for iterative documentation."""

    def feedback_callback(docs: dict):
        console.print("\n[bold green]📋 Generated Documentation[/bold green]")

        # Display all documents with truncation for readability
        for doc_type, content in docs.items():
            title_map = {
                "requirements": "📄 Requirements Document",
                "design": "🏗️ Design Document",
                "todos": "✅ Todo List",
            }
            border_map = {"requirements": "green", "design": "blue", "todos": "yellow"}

            # Show first 1000 chars with option to see more
            display_content = content
            if len(content) > 1000:
                display_content = (
                    content[:1000]
                    + "\n\n[dim]... (truncated, full content will be saved)[/dim]"
                )

            console.print(
                Panel(
                    display_content,
                    title=title_map[doc_type],
                    border_style=border_map[doc_type],
                )
            )

        # Get user choice
        choice = Prompt.ask(
            "\n[bold cyan]Review documentation[/bold cyan]",
            choices=["approve", "revise", "quit"],
            default="approve",
        )

        if choice == "approve":
            return {"action": "approve"}
        elif choice == "revise":
            feedback = {"action": "revise", "changes": "", "specific_feedback": {}}

            console.print(
                "\n[bold cyan]Please provide feedback for revision:[/bold cyan]"
            )

            # General changes
            general_feedback = Prompt.ask(
                "[cyan]What general changes would you like?[/cyan]", default=""
            )
            if general_feedback:
                feedback["changes"] = general_feedback

            # Document-specific feedback
            for doc_type in ["requirements", "design", "todos"]:
                doc_feedback = Prompt.ask(
                    f"[cyan]Any specific changes for {doc_type}? (optional)[/cyan]",
                    default="",
                )
                if doc_feedback:
                    feedback["specific_feedback"][doc_type] = doc_feedback

            return feedback
        else:  # quit
            return {"action": "quit"}

    return feedback_callback


async def execute_with_documentation(
    orchestrator: AgentOrchestrator, docs: dict
) -> dict:
    """Execute tasks using MANDATORY documentation as context."""
    console.print(
        "\n[bold green]🚀 Starting Implementation with MANDATORY Documentation Context[/bold green]"
    )

    # VALIDATION: Ensure ALL three documents exist before execution
    required_docs = ["requirements", "design", "todos"]
    missing_docs = [
        doc for doc in required_docs if doc not in docs or not docs[doc].strip()
    ]

    if missing_docs:
        error_msg = f"EXECUTION BLOCKED: Missing mandatory documentation: {', '.join(missing_docs)}"
        console.print(f"[red]❌ {error_msg}[/red]")
        return {
            "content": error_msg,
            "usage": {},
            "cost": 0.0,
            "error": "missing_mandatory_documentation",
        }

    # Create execution context with ALL MANDATORY documentation
    execution_context = f"""
MANDATORY PROJECT DOCUMENTATION - ALL THREE REQUIRED:

REQUIREMENTS DOCUMENT:
{docs["requirements"]}

DESIGN DOCUMENT:
{docs["design"]}

TODO LIST:
{docs["todos"]}

EXECUTION INSTRUCTIONS:
- You MUST implement based on the above three documents
- You MUST follow the design specifications exactly
- You MUST complete the todo items in order
- You MUST reference all three documents in your implementation
- You MUST maintain consistency across all documentation

Begin implementation now using ALL the above documentation as context.
"""

    # Execute with MANDATORY documentation context - NO EXCEPTIONS
    response = await orchestrator.run(execution_context)
    return response


@app.command()
def main(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path to analyze"),
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Configuration profile to use"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model to use (overrides config)"
    ),
    supervisor_model: Optional[str] = typer.Option(
        None, "--supervisor-model", help="Model for supervisor in multi-agent mode"
    ),
    worker_model: Optional[str] = typer.Option(
        None, "--worker-model", help="Model for workers in multi-agent mode"
    ),
    budget: Optional[float] = typer.Option(
        None, "--budget", "-b", help="Budget limit in USD (overrides config)"
    ),
    multi_agent: bool = typer.Option(
        False, "--multi-agent", "-M", help="Enable multi-agent mode"
    ),
    log_tool_calls: bool = typer.Option(
        False, "--log-tool-calls", help="Enable tool call logging"
    ),
    tool_log_file: str = typer.Option(
        "tool_calls.log", "--tool-log-file", help="Tool call log file path"
    ),
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version information"
    ),
):
    """Start EQUITR Coder interactive session with mandatory documentation generation."""

    if version:
        console.print("[green]EQUITR Coder v0.1.0[/green]")
        return

    try:
        # Load configuration
        config = config_manager.load_config(profile)

        # Apply CLI overrides
        if model:
            config.llm.model = model
        if budget:
            config.llm.budget = budget
        if multi_agent:
            config.orchestrator.use_multi_agent = True
        if supervisor_model:
            config.orchestrator.supervisor_model = supervisor_model
        if worker_model:
            config.orchestrator.worker_model = worker_model
        if log_tool_calls:
            config.orchestrator.log_tool_calls = True
            config.orchestrator.tool_log_file = tool_log_file

        # Validate repository path
        repo_path = Path(repo).resolve()
        if not repo_path.exists():
            console.print(f"[red]❌ Repository path does not exist: {repo_path}[/red]")
            raise typer.Exit(1)

        # Show welcome
        show_welcome()

        # Show configuration
        config_text = Text()
        config_text.append(f"Model: {config.llm.model}\n", style="cyan")
        if config.orchestrator.use_multi_agent:
            if config.orchestrator.supervisor_model:
                config_text.append(
                    f"Supervisor Model: {config.orchestrator.supervisor_model}\n",
                    style="cyan",
                )
            if config.orchestrator.worker_model:
                config_text.append(
                    f"Worker Model: {config.orchestrator.worker_model}\n", style="cyan"
                )
        config_text.append(f"Profile: {profile}\n", style="cyan")
        config_text.append(f"Repository: {repo_path}\n", style="cyan")
        config_text.append(f"Budget: ${config.llm.budget}\n", style="cyan")
        config_text.append(
            f"Multi-agent: {'Enabled' if config.orchestrator.use_multi_agent else 'Disabled'}\n",
            style="cyan",
        )
        if config.orchestrator.log_tool_calls:
            config_text.append(
                f"Tool Logging: Enabled ({config.orchestrator.tool_log_file})\n",
                style="cyan",
            )

        console.print(
            Panel(config_text, title="🛠️ Configuration", border_style="green")
        )

        async def run_interactive():
            orchestrator = AgentOrchestrator(
                config,
                str(repo_path),
                supervisor_model=supervisor_model,
                worker_model=worker_model,
            )
            git_auto = GitAutoCommit(str(repo_path))
            session_id = None

            # Initial git commit
            git_auto.commit_planning_start()

            try:
                while True:
                    try:
                        # Get initial user request
                        user_input = Prompt.ask(
                            "\n[bold cyan]What would you like to build?[/bold cyan]"
                        )

                        # Handle special commands
                        if user_input.lower() in ["/quit", "/exit", "/q"]:
                            console.print("[yellow]👋 Goodbye![/yellow]")
                            break
                        elif user_input.lower() == "/clear":
                            orchestrator.session_manager.clear_current_session()
                            console.print(
                                "[green]✅ Conversation history cleared[/green]"
                            )
                            continue
                        elif user_input.lower() == "/status":
                            show_session_status(orchestrator)
                            continue
                        elif user_input.lower() == "/multi-agent":
                            config.orchestrator.use_multi_agent = (
                                not config.orchestrator.use_multi_agent
                            )
                            status = (
                                "enabled"
                                if config.orchestrator.use_multi_agent
                                else "disabled"
                            )
                            console.print(f"[green]✅ Multi-agent mode {status}[/green]")
                            continue
                        elif user_input.lower() == "/help":
                            show_welcome()
                            continue

                        if not user_input.strip():
                            continue

                        # Step 1: Conduct planning conversation
                        conversation_data = await conduct_planning_conversation(
                            orchestrator, user_input
                        )
                        if not conversation_data:
                            console.print("[yellow]Planning cancelled[/yellow]")
                            continue

                        # Step 2: Generate MANDATORY documentation - ALL THREE REQUIRED
                        docs = await generate_documentation(
                            orchestrator, conversation_data
                        )
                        if not docs:
                            console.print(
                                "[red]❌ CRITICAL: Failed to generate MANDATORY documentation[/red]"
                            )
                            continue

                        # VALIDATION: Ensure ALL three documents exist - NO EXCEPTIONS
                        missing_docs = []
                        for doc_type in ["requirements", "design", "todos"]:
                            if doc_type not in docs or not docs[doc_type].strip():
                                missing_docs.append(doc_type)

                        if missing_docs:
                            console.print(
                                f"[red]❌ CRITICAL: Missing MANDATORY documentation: {', '.join(missing_docs)}[/red]"
                            )
                            console.print(
                                "[red]All three documents (requirements, design, todos) MUST be generated before proceeding[/red]"
                            )
                            continue

                        # Step 3: Review and approve documentation
                        approved = await review_and_approve_documentation(docs)
                        if not approved:
                            console.print(
                                "[yellow]Documentation not approved - starting over[/yellow]"
                            )
                            continue

                        # Commit planning completion
                        git_auto.commit_planning_complete()

                        # Step 4: Execute with documentation context
                        response = await execute_with_documentation(orchestrator, docs)

                        # Display result
                        content = response.get("content", "")
                        usage = response.get("usage", {})
                        cost = response.get("cost", 0.0)

                        # Show usage stats
                        usage_text = Text()
                        usage_text.append(
                            f"Total tokens: {usage.get('total_tokens', 0)}\n",
                            style="cyan",
                        )
                        usage_text.append(f"Cost: ${cost:.4f}\n", style="cyan")

                        # Show result
                        console.print(
                            Panel(
                                content,
                                title="🤖 Implementation Complete",
                                border_style="green",
                            )
                        )
                        console.print(
                            Panel(
                                usage_text, title="📊 Usage Stats", border_style="blue"
                            )
                        )

                        # Auto-commit completion
                        git_auto.commit_checkpoint("Implementation complete")

                        # Ask if user wants to continue
                        if not Confirm.ask(
                            "\n[bold cyan]Start another project?[/bold cyan]"
                        ):
                            break

                    except KeyboardInterrupt:
                        console.print("\n[yellow]Use /quit to exit properly[/yellow]")
                        continue
                    except Exception as e:
                        console.print(f"[red]❌ Error: {e}[/red]")
                        import traceback

                        traceback.print_exc()
                        continue

            finally:
                await orchestrator.close()

        asyncio.run(run_interactive())

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    app()
