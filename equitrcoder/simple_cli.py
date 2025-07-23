import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from .core.config import config_manager
from .core.orchestrator import AgentOrchestrator
from .core.planning import ConversationalPlanner
from .tools.builtin.git_auto import GitAutoCommit

app = typer.Typer(
    name="equitrcoder",
    help="EQUITR Coder - An advanced AI coding assistant that starts interactive sessions automatically",
    add_completion=False,
)

console = Console()


def check_api_key():
    """Check if required API key is set based on configuration."""
    pass


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
    session: Optional[str] = typer.Option(
        None, "--session", "-s", help="Session ID to resume"
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
    """Start EQUITR Coder - automatically begins an interactive session."""

    if version:
        from . import __version__

        console.print(f"[green]🚀 EQUITR Coder v{__version__}[/green]")
        return

    check_api_key()

    # Load configuration
    try:
        config = config_manager.load_config(profile)
    except Exception as e:
        console.print(f"[red]❌ Failed to load config: {e}[/red]")
        raise typer.Exit(1)

    # Apply CLI overrides
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

    # Show welcome message
    console.print(
        Panel(
            f"[green]🚀 EQUITR Coder - Interactive Mode[/green]\n\n"
            f"[cyan]Model:[/cyan] {model or config.llm.model}\n"
            f"[cyan]Profile:[/cyan] {profile}\n"
            f"[cyan]Repository:[/cyan] {repo_path}\n"
            f"[cyan]Budget:[/cyan] ${config.llm.budget}\n"
            f"[cyan]Session:[/cyan] {session or 'new'}\n\n"
            "Type your messages and press Enter. Use '/quit' to exit.\n"
            "Commands:\n"
            "  /quit - Exit the session\n"
            "  /clear - Clear conversation history\n"
            "  /status - Show session status\n"
            "  /help - Show this help",
            title="EQUITR Coder",
            border_style="green",
        )
    )

    async def run_interactive():
        orchestrator = AgentOrchestrator(
            config,
            str(repo_path),
            model=model,
            supervisor_model=supervisor_model,
            worker_model=worker_model,
        )
        git_auto = GitAutoCommit(str(repo_path))
        session_id = session

        # Initial git commit for planning start
        git_auto.commit_planning_start()

        try:
            while True:
                try:
                    user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")

                    if user_input.lower() in ["/quit", "/exit", "/q"]:
                        console.print("[yellow]👋 Goodbye![/yellow]")
                        break
                    elif user_input.lower() == "/clear":
                        orchestrator.session_manager.clear_current_session()
                        console.print("[green]✅ Conversation history cleared[/green]")
                        continue
                    elif user_input.lower() == "/status":
                        messages = orchestrator.session_manager.get_messages()
                        console.print("[cyan]📊 Session Status:[/cyan]")
                        console.print(f"  Messages: {len(messages)}")
                        console.print(f"  Total cost: ${orchestrator.total_cost:.4f}")
                        console.print(f"  Iterations: {orchestrator.iteration_count}")
                        continue
                    elif user_input.lower() == "/help":
                        console.print(
                            Panel(
                                "Commands:\n"
                                "  /quit - Exit the session\n"
                                "  /clear - Clear conversation history\n"
                                "  /status - Show session status\n"
                                "  /help - Show this help\n"
                                "  /skip - Skip planning conversation",
                                title="Help",
                                border_style="blue",
                            )
                        )
                        continue

                    if not user_input.strip():
                        continue

                    # Check if this is the first interaction - start planning
                    if not session_id and orchestrator.iteration_count == 0:
                        console.print(
                            "\n[green]🎯 Starting Conversational Planning Phase...[/green]"
                        )

                        # Initialize conversational planner
                        planner = ConversationalPlanner(
                            orchestrator.provider, str(repo_path)
                        )

                        # Start planning conversation
                        planning_success = await planner.start_planning_conversation(
                            user_input
                        )

                        if not planning_success:
                            console.print(
                                "[yellow]Planning cancelled. Exiting...[/yellow]"
                            )
                            break

                        # Generate planning documents
                        documents = await planner.generate_planning_documents()

                        if not documents:
                            console.print(
                                "[red]Failed to generate planning documents[/red]"
                            )
                            continue

                        # Display documents for approval
                        console.print(
                            "\n[green]📋 Planning Documents Generated:[/green]"
                        )
                        console.print(
                            Panel(
                                documents["requirements"],
                                title="Requirements Document",
                                border_style="green",
                            )
                        )
                        console.print(
                            Panel(
                                documents["design"],
                                title="Design Document",
                                border_style="blue",
                            )
                        )
                        console.print(
                            Panel(
                                documents["todos"],
                                title="Todo List",
                                border_style="yellow",
                            )
                        )

                        # User approval loop
                        while True:
                            approval = Prompt.ask(
                                "\n[bold cyan]Approve planning documents?[/bold cyan]",
                                choices=["y", "n", "edit"],
                                default="y",
                            )

                            if approval == "y":
                                console.print(
                                    "[green]✅ Planning approved - proceeding to implementation[/green]"
                                )
                                git_auto.commit_planning_complete()
                                break
                            elif approval == "n":
                                console.print(
                                    "[yellow]❌ Planning rejected - please provide new requirements[/yellow]"
                                )
                                continue
                            elif approval == "edit":
                                # Collect feedback for document revision
                                feedback = {
                                    "action": "revise",
                                    "changes": "",
                                    "specific_feedback": {},
                                }

                                general_feedback = Prompt.ask(
                                    "[cyan]What general changes would you like?[/cyan]",
                                    default="",
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
                                        feedback["specific_feedback"][
                                            doc_type
                                        ] = doc_feedback

                                # Regenerate documents with feedback
                                console.print(
                                    "[yellow]📝 Regenerating documents with your feedback...[/yellow]"
                                )

                                # Create a simple feedback callback that returns the collected feedback
                                def simple_feedback_callback(docs):
                                    return feedback

                                # Regenerate with feedback
                                revised_docs = (
                                    await doc_generator.generate_documents_iteratively(
                                        planning_conversation,
                                        feedback_callback=simple_feedback_callback,
                                    )
                                )

                                if revised_docs:
                                    documents = revised_docs
                                    console.print(
                                        "[green]✅ Documents revised successfully![/green]"
                                    )
                                else:
                                    console.print(
                                        "[red]❌ Failed to revise documents[/red]"
                                    )
                                continue

                        # Add planning context to session
                        planning_context = f"""
Planning completed successfully.
Requirements: {documents["requirements"][:500]}...
Design: {documents["design"][:500]}...
Todos: {documents["todos"][:300]}...
                        """

                        # Continue with implementation using planning context
                        response = await orchestrator.run(planning_context, session_id)
                    else:
                        # Regular execution
                        console.print("\n[dim]🤔 Thinking...[/dim]")
                        response = await orchestrator.run(user_input, session_id)

                    # Extract content, usage, and cost
                    content = response.get("content", "")
                    usage = response.get("usage", {})
                    cost = response.get("cost", 0.0)

                    # Auto-commit after task completion
                    if "completed" in content.lower() or "✅" in content:
                        git_auto.commit_checkpoint("Task completion")

                    # Prepare cache stats
                    cache_stats = ""
                    prompt_tokens_details = usage.get("prompt_tokens_details", {})
                    cached_tokens = prompt_tokens_details.get("cached_tokens", 0)
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

                    # Calculate cached price (approximate)
                    cached_price = 0.0
                    if cached_tokens > 0:
                        cached_price = (cached_tokens / 1000) * 0.03
                        cache_stats = f"[green]Cached tokens:[/green] {cached_tokens}\n[green]Cached price:[/green] ${cached_price:.4f}"

                    # Show usage stats
                    usage_stats = f"[cyan]Prompt tokens:[/cyan] {prompt_tokens}\n[cyan]Completion tokens:[/cyan] {completion_tokens}\n[cyan]Total tokens:[/cyan] {total_tokens}\n[cyan]Total price:[/cyan] ${cost:.4f}"

                    # Combine output
                    output = f"{content}\n\n{cache_stats}\n{usage_stats}"
                    console.print(
                        Panel(output, title="🤖 EQUITR Coder", border_style="blue")
                    )

                    # Store session ID for continuity
                    if orchestrator.session_manager.current_session:
                        session_id = (
                            orchestrator.session_manager.current_session.session_id
                        )

                except KeyboardInterrupt:
                    console.print("\n[yellow]Use /quit to exit properly[/yellow]")
                    continue
                except Exception as e:
                    console.print(f"[red]❌ Error: {e}[/red]")
                    continue

        finally:
            await orchestrator.close()

    asyncio.run(run_interactive())


# Make it work as a single command
def run():
    """Entry point for the simplified CLI."""
    app()


if __name__ == "__main__":
    run()
