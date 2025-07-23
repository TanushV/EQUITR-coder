#!/usr/bin/env python3
"""
EQUITR Coder - Ultra-simple CLI with no flags

This is the simplest possible CLI that starts an interactive session
with sensible defaults and no command-line arguments.
"""

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from .core.config import config_manager
from .core.orchestrator import AgentOrchestrator
from .core.planning import ConversationalPlanner
from .tools.builtin.git_auto import GitAutoCommit

console = Console()


def main():
    """
    Main entry point for the ultra-simple CLI.
    Runs with no arguments and starts an interactive session.
    """
    try:
        # Load default configuration
        config = config_manager.load_config("default")

        # Use current directory as repository
        repo_path = Path.cwd().resolve()

        # Show welcome message
        console.print(
            Panel(
                f"[green]🚀 EQUITR Coder - Interactive Mode[/green]\n\n"
                f"[cyan]Model:[/cyan] {config.llm.model}\n"
                f"[cyan]Repository:[/cyan] {repo_path}\n"
                f"[cyan]Budget:[/cyan] ${config.llm.budget}\n\n"
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
            orchestrator = AgentOrchestrator(config, str(repo_path))
            git_auto = GitAutoCommit(str(repo_path))
            session_id = None

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
                            console.print(
                                "[green]✅ Conversation history cleared[/green]"
                            )
                            continue
                        elif user_input.lower() == "/status":
                            messages = orchestrator.session_manager.get_messages()
                            console.print("[cyan]📊 Session Status:[/cyan]")
                            console.print(f"  Messages: {len(messages)}")
                            console.print(
                                f"  Total cost: ${orchestrator.total_cost:.4f}"
                            )
                            console.print(
                                f"  Iterations: {orchestrator.iteration_count}"
                            )
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
                            planning_success = (
                                await planner.start_planning_conversation(user_input)
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
                                    _edit_feedback = Prompt.ask(
                                        "[bold cyan]What changes would you like?[/bold cyan]"
                                    )
                                    console.print(
                                        "[yellow]Document editing not yet implemented - please restart planning[/yellow]"
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
                            response = await orchestrator.run(
                                planning_context, session_id
                            )
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

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
