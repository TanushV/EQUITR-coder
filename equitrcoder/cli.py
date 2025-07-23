import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from .core.config import config_manager
from .core.orchestrator import AgentOrchestrator
from .ui.tui import run_tui

app = typer.Typer(
    name="EQUITR-coder",
    help="EQUITR Coder - An advanced AI coding assistant with intelligent tool execution and todo management",
)

console = Console()


def check_api_key():
    """Check if required API key is set based on configuration."""
    # This is now more flexible - we'll check during actual usage
    # since different providers have different key requirements
    pass


@app.command()
async def chat(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path to analyze"),
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Configuration profile to use"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model to use (overrides config)"
    ),
    budget: Optional[float] = typer.Option(
        None, "--budget", "-b", help="Budget limit in USD (overrides config)"
    ),
    session: Optional[str] = typer.Option(
        None, "--session", "-s", help="Session ID to resume"
    ),
    stream: bool = typer.Option(False, "--stream", help="Enable streaming responses"),
    multi_agent: bool = typer.Option(
        False,
        "--multi-agent",
        "-M",
        help="Enable strong/weak agent paradigm using supervisor + worker models",
    ),
    supervisor_model: Optional[str] = typer.Option(
        None, "--supervisor-model", help="Override supervisor model"
    ),
    worker_model: Optional[str] = typer.Option(
        None, "--worker-model", help="Override worker model"
    ),
):
    """Start a conversation with EQUITR Coder."""

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

    # Validate repository path
    repo_path = Path(repo).resolve()
    if not repo_path.exists():
        console.print(f"[red]❌ Repository path does not exist: {repo_path}[/red]")
        raise typer.Exit(1)

    # Show configuration with enhanced model information
    model_info = []

    # Main model
    main_model = model or config.llm.model
    model_info.append(f"[cyan]Main Model:[/cyan] {main_model}")

    # Show supervisor and worker models if multi-agent mode or different models specified
    if multi_agent or supervisor_model or worker_model:
        # Get the actual models that would be used
        from .core.orchestrator import AgentOrchestrator
        from .core.config import config_manager

        # Create temporary orchestrator to get model info
        temp_config = config.model_copy()
        if model:
            temp_config.llm.model = model

        temp_orchestrator = AgentOrchestrator(
            temp_config,
            str(repo_path),
            model=model,
            supervisor_model=supervisor_model,
            worker_model=worker_model,
        )

        # Get supervisor model
        try:
            supervisor_provider = temp_orchestrator._create_supervisor_provider(
                temp_config
            )
            supervisor_model_name = getattr(supervisor_provider, "model", "Unknown")
            if supervisor_model_name != main_model:
                model_info.append(
                    f"[cyan]Supervisor Model:[/cyan] {supervisor_model_name}"
                )
        except:
            if supervisor_model:
                model_info.append(f"[cyan]Supervisor Model:[/cyan] {supervisor_model}")

        # Get worker model
        try:
            worker_provider = temp_orchestrator._create_worker_provider(temp_config)
            worker_model_name = getattr(worker_provider, "model", "Unknown")
            if worker_model_name != main_model:
                model_info.append(f"[cyan]Worker Model:[/cyan] {worker_model_name}")
        except:
            if worker_model:
                model_info.append(f"[cyan]Worker Model:[/cyan] {worker_model}")

        # Close the temporary orchestrator
        await temp_orchestrator.close()

    # Build configuration panel content
    config_content = f"[green]🚀 EQUITR Coder[/green]\n\n"
    config_content += "\n".join(model_info) + "\n"
    config_content += f"[cyan]Profile:[/cyan] {profile}\n"
    config_content += f"[cyan]Repository:[/cyan] {repo_path}\n"
    config_content += f"[cyan]Budget:[/cyan] ${config.llm.budget}\n"
    config_content += f"[cyan]Session:[/cyan] {session or 'new'}"

    console.print(
        Panel(
            config_content,
            title="🛠️ Configuration",
            border_style="green",
        )
    )

    # Get user input
    console.print("\n[bold cyan]💬 Enter your request (Ctrl+D when done):[/bold cyan]")

    try:
        if sys.stdin.isatty():
            # Interactive mode
            lines = []
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break
            user_input = "\n".join(lines)
        else:
            # Pipe mode
            user_input = sys.stdin.read()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        raise typer.Exit(0)

    if not user_input.strip():
        console.print("[red]❌ No input provided[/red]")
        raise typer.Exit(1)

    # Update config for multi-agent mode
    if multi_agent:
        config.orchestrator.use_multi_agent = True
        console.print(
            "[yellow]🤖 Multi-agent mode enabled (strong/weak paradigm)[/yellow]"
        )

    # Run orchestrator
    async def run_chat():
        orchestrator = AgentOrchestrator(
            config,
            str(repo_path),
            model=model,
            supervisor_model=supervisor_model,
            worker_model=worker_model,
        )
        try:
            response = await orchestrator.run(user_input, session)
            # Extract content, usage, and cost
            content = response.get("content", "")
            usage = response.get("usage", {})
            cost = response.get("cost", 0.0)

            # Prepare cache stats
            cache_stats = ""
            prompt_tokens_details = usage.get("prompt_tokens_details", {})
            cached_tokens = prompt_tokens_details.get("cached_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Calculate cached price (approximate, using OpenAI/Anthropic rates as example)
            # You may want to refine this for each provider
            cached_price = 0.0
            if cached_tokens > 0:
                # Use OpenAI GPT-4 prompt price as default
                cached_price = (cached_tokens / 1000) * 0.03
                cache_stats = f"[green]Cached tokens:[/green] {cached_tokens}\n[green]Cached price:[/green] ${cached_price:.4f}"

            # Show usage stats
            usage_stats = f"[cyan]Prompt tokens:[/cyan] {prompt_tokens}\n[cyan]Completion tokens:[/cyan] {completion_tokens}\n[cyan]Total tokens:[/cyan] {total_tokens}\n[cyan]Total price:[/cyan] ${cost:.4f}"

            # Combine output
            output = f"{content}\n\n{cache_stats}\n{usage_stats}"
            console.print(
                Panel(output, title="🤖 EQUITR Coder Response", border_style="blue")
            )
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            raise typer.Exit(1)
        finally:
            await orchestrator.close()

    asyncio.run(run_chat())


@app.command()
def interactive(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path to analyze"),
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Configuration profile to use"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model to use (overrides config)"
    ),
    supervisor_model: Optional[str] = typer.Option(
        None, "--supervisor-model", help="Override supervisor model"
    ),
    worker_model: Optional[str] = typer.Option(
        None, "--worker-model", help="Override worker model"
    ),
):
    """Start an interactive conversation with EQUITR Coder."""

    check_api_key()

    # Load configuration
    try:
        config = config_manager.load_config(profile)
    except Exception as e:
        console.print(f"[red]❌ Failed to load config: {e}[/red]")
        raise typer.Exit(1)

    # Model override will be passed directly to orchestrator

    repo_path = Path(repo).resolve()
    if not repo_path.exists():
        console.print(f"[red]❌ Repository path does not exist: {repo_path}[/red]")
        raise typer.Exit(1)

    console.print(
        Panel(
            "[green]🤖 EQUITR Coder - Interactive Mode[/green]\n\n"
            "Type your messages and press Enter. Use '/quit' to exit.\n"
            "Commands:\n"
            "  /quit - Exit the session\n"
            "  /clear - Clear conversation history\n"
            "  /status - Show session status\n"
            "  /help - Show this help",
            title="Interactive Mode",
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
        session_id = None

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
                                "  /help - Show this help",
                                title="Help",
                                border_style="blue",
                            )
                        )
                        continue

                    if not user_input.strip():
                        continue

                    console.print("\n[dim]🤔 Thinking...[/dim]")

                    response = await orchestrator.run(user_input, session_id)

                    # Extract content, usage, and cost
                    content = response.get("content", "")
                    usage = response.get("usage", {})
                    cost = response.get("cost", 0.0)

                    # Prepare cache stats
                    cache_stats = ""
                    prompt_tokens_details = usage.get("prompt_tokens_details", {})
                    cached_tokens = prompt_tokens_details.get("cached_tokens", 0)
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

                    # Calculate cached price (approximate, using OpenAI/Anthropic rates as example)
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


@app.command()
def sessions(
    action: Optional[str] = typer.Argument(
        None, help="Action: list, delete, or switch"
    ),
    session_id: Optional[str] = typer.Argument(
        None, help="Session ID for delete/switch actions"
    ),
):
    """List and manage conversation sessions."""

    from .core.session import SessionManagerV2

    session_manager = SessionManagerV2()

    if action == "delete" and session_id:
        if session_manager.delete_session(session_id):
            console.print(f"[green]✅ Session {session_id} deleted[/green]")
        else:
            console.print(f"[red]❌ Failed to delete session {session_id}[/red]")
        return

    if action == "switch" and session_id:
        if session_manager.switch_session(session_id):
            console.print(f"[green]✅ Switched to session {session_id}[/green]")
        else:
            console.print(f"[red]❌ Session {session_id} not found[/red]")
        return

    # Default action: list sessions
    sessions = session_manager.list_sessions()

    if not sessions:
        console.print("[yellow]📭 No sessions found[/yellow]")
        return

    # Create a rich table for session display
    from rich.table import Table

    table = Table(title="Available Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Created", style="green")
    table.add_column("Updated", style="yellow")
    table.add_column("Messages", justify="right", style="blue")
    table.add_column("Tasks", justify="right", style="magenta")
    table.add_column("Cost", justify="right", style="red")
    table.add_column("Status", style="dim")

    for session in sessions:
        table.add_row(
            session["session_id"],
            session["created_at"].strftime("%Y-%m-%d %H:%M"),
            session["updated_at"].strftime("%Y-%m-%d %H:%M"),
            str(session["message_count"]),
            str(session["task_count"]),
            f"${session['cost']:.3f}",
            session["status"],
        )

    console.print(table)


@app.command()
def tui(
    repo: str = typer.Option(".", "--repo", "-r", help="Repository path to analyze"),
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Configuration profile to use"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model to use (overrides config)"
    ),
    supervisor_model: Optional[str] = typer.Option(
        None, "--supervisor-model", help="Override supervisor model"
    ),
    worker_model: Optional[str] = typer.Option(
        None, "--worker-model", help="Override worker model"
    ),
):
    """Launch the beautiful terminal user interface."""

    check_api_key()

    # Load configuration
    try:
        config = config_manager.load_config(profile)
    except Exception as e:
        console.print(f"[red]❌ Failed to load config: {e}[/red]")
        raise typer.Exit(1)

    # Apply model override before launching TUI (initial selection)
    if model:
        if model in config.llm.models:
            config = config_manager.switch_model(config, model)
        else:
            # Treat as provider/model string and inject new profile 'cli'
            config = config_manager.add_model_config(
                config,
                "cli_override",
                {
                    "provider": "litellm",
                    "model": model,
                    "temperature": config.llm.temperature,
                    "max_tokens": config.llm.max_tokens,
                },
            )
            config.llm.active_model = "cli_override"

    # Validate repository path
    repo_path = Path(repo).resolve()
    if not repo_path.exists():
        console.print(f"[red]❌ Repository path does not exist: {repo_path}[/red]")
        raise typer.Exit(1)

    # Launch TUI
    try:
        asyncio.run(
            run_tui(
                config, supervisor_model=supervisor_model, worker_model=worker_model
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]❌ TUI Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config_cmd(
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Configuration profile to show"
    ),
    edit: bool = typer.Option(False, "--edit", help="Open config in editor"),
):
    """Show or edit configuration."""

    try:
        config = config_manager.load_config(profile)

        if edit:
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                import yaml

                yaml.dump(config.model_dump(), f, default_flow_style=False)
                temp_file = f.name

            editor = os.getenv("EDITOR", "nano")
            result = subprocess.run([editor, temp_file])

            if result.returncode == 0:
                try:
                    # Load the edited configuration
                    with open(temp_file, "r") as f:
                        edited_config_data = yaml.safe_load(f)

                    # Validate the edited configuration by creating a Config object
                    from .core.config import Config

                    edited_config = Config(**edited_config_data)

                    # Save the validated configuration
                    config_manager.save_user_config(edited_config)

                    console.print(
                        "[green]✅ Configuration updated successfully![/green]"
                    )

                    # Display the updated configuration
                    console.print(
                        Panel(
                            f"[cyan]LLM Model:[/cyan] {edited_config.llm.model}\n"
                            f"[cyan]Budget:[/cyan] ${edited_config.llm.budget}\n"
                            f"[cyan]Tools:[/cyan] {', '.join(edited_config.tools.enabled)}\n"
                            f"[cyan]Session Persistence:[/cyan] {edited_config.session.persist}\n"
                            f"[cyan]Repository Indexing:[/cyan] {edited_config.repository.index_on_start}",
                            title=f"Updated Configuration - {profile}",
                            border_style="green",
                        )
                    )

                except yaml.YAMLError as e:
                    console.print(f"[red]❌ Invalid YAML format: {e}[/red]")
                    console.print("[yellow]Configuration not saved[/yellow]")
                except Exception as e:
                    console.print(f"[red]❌ Invalid configuration: {e}[/red]")
                    console.print("[yellow]Configuration not saved[/yellow]")
            else:
                console.print(
                    "[yellow]⚠️ Editor exited with error, configuration not saved[/yellow]"
                )

            # Clean up temporary file
            os.unlink(temp_file)
        else:
            console.print(
                Panel(
                    f"[cyan]LLM Model:[/cyan] {config.llm.model}\n"
                    f"[cyan]Budget:[/cyan] ${config.llm.budget}\n"
                    f"[cyan]Tools:[/cyan] {', '.join(config.tools.enabled)}\n"
                    f"[cyan]Session Persistence:[/cyan] {config.session.persist}\n"
                    f"[cyan]Repository Indexing:[/cyan] {config.repository.index_on_start}",
                    title=f"Configuration - {profile}",
                    border_style="cyan",
                )
            )

    except Exception as e:
        console.print(f"[red]❌ Failed to load config: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def models(
    api_base: str = typer.Option(
        "http://localhost:4000", "--api-base", help="LiteLLM proxy base URL"
    ),
    discover: bool = typer.Option(
        False, "--discover", help="Discover available models"
    ),
):
    """List and discover available models."""

    from equitrcoder.providers.model_discovery import LiteLLMModelDiscovery
    from rich.table import Table

    if discover:
        console.print(f"[cyan]🔍 Discovering models from {api_base}...[/cyan]")
        discovery = LiteLLMModelDiscovery(api_base)

        try:
            models = discovery.get_available_models_sync()

            if not models:
                console.print(
                    "[yellow]📭 No models found or LiteLLM proxy not accessible[/yellow]"
                )
                console.print(
                    "[dim]Make sure LiteLLM proxy is running at the specified URL[/dim]"
                )
                return

            # Import function calling discovery
            from equitrcoder.providers.function_calling_discovery import (
                FunctionCallingModelDiscovery,
            )

            fc_discovery = FunctionCallingModelDiscovery()

            table = Table(title="Available Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Function Calling", style="magenta")
            table.add_column("Parallel FC", style="blue")
            table.add_column("Created", style="yellow")

            for model in models:
                model_id = model.get("id", "unknown")
                owned_by = model.get("owned_by", "unknown")
                created = model.get("created", 0)

                # Check function calling support
                try:
                    import asyncio

                    model_info = asyncio.run(fc_discovery.validate_model(model_id))
                    fc_support = "✅" if model_info["supports_function_calling"] else "❌"
                    pfc_support = (
                        "✅" if model_info["supports_parallel_function_calling"] else "❌"
                    )
                except Exception:
                    fc_support = "❓"
                    pfc_support = "❓"

                # Convert Unix timestamp to readable format
                from datetime import datetime

                created_date = (
                    datetime.fromtimestamp(created).strftime("%Y-%m-%d")
                    if created
                    else "unknown"
                )

                table.add_row(model_id, owned_by, fc_support, pfc_support, created_date)

            console.print(table)
            console.print(f"[green]✅ Found {len(models)} models[/green]")
            console.print(
                "\n[dim]Legend: ✅ = Supported, ❌ = Not Supported, ❓ = Unknown[/dim]"
            )

        except Exception as e:
            console.print(f"[red]❌ Error discovering models: {e}[/red]")
            console.print(
                "[dim]Make sure LiteLLM proxy is running and accessible[/dim]"
            )
    else:
        # Show current configuration
        config = config_manager.load_config()

        # Check function calling support for current model
        from equitrcoder.providers.function_calling_discovery import (
            FunctionCallingModelDiscovery,
        )

        fc_discovery = FunctionCallingModelDiscovery()

        model_status = "Unknown"
        fc_status = "Unknown"
        if config.llm.model:
            try:
                import asyncio

                model_info = asyncio.run(fc_discovery.validate_model(config.llm.model))
                model_status = (
                    "✅ Compatible" if model_info["valid"] else "❌ Incompatible"
                )
                fc_status = (
                    "✅ Supported"
                    if model_info["supports_function_calling"]
                    else "❌ Not Supported"
                )
            except Exception:
                model_status = "❓ Unknown"
                fc_status = "❓ Unknown"

        console.print(
            Panel(
                f"[cyan]Current Model:[/cyan] {config.llm.model or 'Not selected'}\n"
                f"[cyan]Model Status:[/cyan] {model_status}\n"
                f"[cyan]Function Calling:[/cyan] {fc_status}\n"
                f"[cyan]API Base:[/cyan] {config.llm.api_base or 'Not configured'}\n"
                f"[cyan]Provider:[/cyan] {config.llm.provider}\n\n"
                f"Use [bold]--discover[/bold] to discover models from LiteLLM proxy\n"
                f"Use [bold]--api-base[/bold] to specify a different LiteLLM proxy URL",
                title="Model Configuration",
                border_style="cyan",
            )
        )


@app.command()
def version():
    """Show version information."""
    from . import __version__

    console.print(f"[green]🚀 EQUITR Coder v{__version__}[/green]")


if __name__ == "__main__":
    app()
