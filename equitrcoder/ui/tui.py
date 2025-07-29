"""Simple ASCII TUI interface for EQUITR Coder."""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..agents.base_agent import BaseAgent
from ..core.config import Config, config_manager
from ..core.session import SessionManagerV2
from ..modes.multi_agent_mode import run_multi_agent_sequential
from ..modes.single_agent_mode import run_single_agent_mode
from ..tools.discovery import discover_tools

HEADER_COLOR = "\033[94m"  # Bright blue
SUCCESS_COLOR = "\033[92m"  # Green
ERROR_COLOR = "\033[91m"  # Red
WARNING_COLOR = "\033[93m"  # Yellow
INFO_COLOR = "\033[96m"  # Cyan for info
AGENT_COLOR = "\033[95m"  # Magenta for agent messages
RESET = "\033[0m"


class SimpleTUI:
    """Simple ASCII-based TUI for EQUITR Coder."""

    def __init__(self, config: Config):
        self.config = config
        self.session_manager = SessionManagerV2(config.session.session_dir)
        self.current_session_id = "default"
        self.supervisor_model = ""
        self.worker_model = ""
        self.available_models = [
            "moonshot/kimi-k2-0711-preview",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
        ]

        # Auto-load environment and set default model
        from ..utils.env_loader import auto_load_environment

        env_status = auto_load_environment()

        # Set default model if moonshot is available
        if env_status.get("providers", {}).get("moonshot", {}).get("available"):
            self.worker_model = "moonshot/kimi-k2-0711-preview"
            self.supervisor_model = "moonshot/kimi-k2-0711-preview"

    def print_header(self):
        """Print ASCII header."""
        print(f"{HEADER_COLOR}\n" + "=" * 60)
        print(f"{HEADER_COLOR}    EQUITR CODER - AI Coding Assistant{RESET}")
        print(f"{HEADER_COLOR}" + "=" * 60)
        print(f"{INFO_COLOR}Mode: Single Agent{RESET}")
        print(f"{HEADER_COLOR}Available API Keys:{RESET}")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key:
            print(f"  {SUCCESS_COLOR}OpenAI: ****{openai_key[-4:]}{RESET}")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            print(f"  {SUCCESS_COLOR}Anthropic: ****{anthropic_key[-4:]}{RESET}")
        # Add other providers if needed
        print(
            f"{HEADER_COLOR}Selected Supervisor: {self.supervisor_model or 'Not selected'}{RESET}"
        )
        print(
            f"{HEADER_COLOR}Selected Worker: {self.worker_model or 'Not selected'}{RESET}"
        )
        print(f"{HEADER_COLOR}Session: {self.current_session_id}{RESET}")
        print(f"{HEADER_COLOR}-" * 60 + RESET)

    def print_menu(self):
        """Print main menu."""
        print(f"{HEADER_COLOR}\nCommands:{RESET}")
        print(f"  {INFO_COLOR}/help     - Show this help{RESET}")
        print(f"  {INFO_COLOR}/model    - Change model{RESET}")
        print(f"  {INFO_COLOR}/session  - Manage sessions{RESET}")
        print(f"  {INFO_COLOR}/quit     - Exit{RESET}")
        print(f"  {INFO_COLOR}<task>    - Execute a coding task{RESET}")
        print(f"{HEADER_COLOR}-" * 60 + RESET)

    def select_model(self):
        """Model selection interface."""
        print("\nAvailable models:")
        for i, model in enumerate(self.available_models, 1):
            print(f"  {i}. {model}")
        print("  0. Enter custom model")

        try:
            # Select supervisor
            choice = input("\nSelect supervisor model (number): ").strip()
            if choice == "0":
                custom_model = input("Enter custom supervisor model: ").strip()
                if custom_model:
                    self.supervisor_model = custom_model
                    print(f"Supervisor model set to: {custom_model}")
            elif choice.isdigit() and 1 <= int(choice) <= len(self.available_models):
                self.supervisor_model = self.available_models[int(choice) - 1]
                print(f"Supervisor model set to: {self.supervisor_model}")
            else:
                print("Invalid selection for supervisor")

            # Select worker
            choice = input("\nSelect worker model (number): ").strip()
            if choice == "0":
                custom_model = input("Enter custom worker model: ").strip()
                if custom_model:
                    self.worker_model = custom_model
                    print(f"Worker model set to: {custom_model}")
            elif choice.isdigit() and 1 <= int(choice) <= len(self.available_models):
                self.worker_model = self.available_models[int(choice) - 1]
                print(f"Worker model set to: {self.worker_model}")
            else:
                print("Invalid selection for worker")
        except (ValueError, KeyboardInterrupt):
            print("Selection cancelled")

    def manage_sessions(self):
        """Session management interface."""
        print("\nSession Management:")
        print("  1. New session")
        print("  2. List sessions")
        print("  3. Switch session")

        try:
            choice = input("Select option: ").strip()
            if choice == "1":
                session_name = input("Enter session name: ").strip()
                if session_name:
                    self.current_session_id = session_name
                    print(f"Created session: {session_name}")
            elif choice == "2":
                sessions = self.session_manager.list_sessions()
                print("\nExisting sessions:")
                for session in sessions[:10]:  # Show last 10
                    print(f"  - {session['session_id']} (Cost: ${session['cost']:.2f})")
            elif choice == "3":
                session_name = input("Enter session name: ").strip()
                if session_name:
                    self.current_session_id = session_name
                    print(f"Switched to session: {session_name}")
        except KeyboardInterrupt:
            print("Operation cancelled")

    async def execute_task(self, task: str):
        """Execute a coding task with mandatory 3-document creation workflow."""
        if not self.worker_model and not self.supervisor_model:
            print(f"{WARNING_COLOR}❌ No models selected. Use /model to select.{RESET}")
            return

        try:
            # MANDATORY: Create the 3 documents first through interactive discussion
            print(f"{HEADER_COLOR}\n🚀 Starting EQUITR Coder Workflow{RESET}")
            print(
                f"{INFO_COLOR}Before we begin coding, we need to create 3 mandatory documents:{RESET}"
            )
            print(f"{INFO_COLOR}1. Requirements (what to build){RESET}")
            print(f"{INFO_COLOR}2. Design (how to build it){RESET}")
            print(f"{INFO_COLOR}3. Todos (task breakdown){RESET}")
            print(f"{HEADER_COLOR}=" * 60 + RESET)

            # Import document workflow
            from ..core.document_workflow import DocumentWorkflowManager

            # Create document workflow manager
            doc_manager = DocumentWorkflowManager(
                model=self.worker_model or self.supervisor_model
            )

            # Interactive callback for user discussion
            async def interaction_callback(speaker, message):
                print(f"\n{AGENT_COLOR}[{speaker}] {message}{RESET}")
                print(f"{HEADER_COLOR}-" * 50 + RESET)

                user_response = input(
                    f"\n{INFO_COLOR}Your response (or 'done' to finish): {RESET}"
                ).strip()
                return (
                    user_response
                    if user_response.lower() not in ["done", "quit", "exit"]
                    else None
                )

            # Create documents through interactive discussion
            doc_result = await doc_manager.create_documents_interactive(
                user_prompt=task,
                project_path=".",
                interaction_callback=interaction_callback,
            )

            if not doc_result.success:
                print(
                    f"{ERROR_COLOR}❌ Failed to create documents: {doc_result.error}{RESET}"
                )
                return

            print(f"{SUCCESS_COLOR}\n✅ Documents created successfully!{RESET}")
            print(
                f"{SUCCESS_COLOR}📄 Requirements: {doc_result.requirements_path}{RESET}"
            )
            print(f"{SUCCESS_COLOR}🏗️ Design: {doc_result.design_path}{RESET}")
            print(f"{SUCCESS_COLOR}📋 Todos: {doc_result.todos_path}{RESET}")

            # Ask user if they want to proceed with execution
            proceed = (
                input(f"\n{INFO_COLOR}Proceed with task execution? (y/n): {RESET}")
                .strip()
                .lower()
            )
            if proceed not in ["y", "yes"]:
                print(f"{WARNING_COLOR}Task execution cancelled by user.{RESET}")
                return

            # Now execute the actual task with the created documents as context
            print(
                f"{HEADER_COLOR}\n🤖 Starting task execution with created documents...{RESET}"
            )
            print(f"{HEADER_COLOR}=" * 60 + RESET)

            # Set up live callbacks for clean architecture
            def on_message(message_data):
                role = message_data["role"].upper()
                content = message_data["content"]
                color = AGENT_COLOR if role == "ASSISTANT" else INFO_COLOR
                print(f"\n{color}[{role}] {content}{RESET}")
                if role == "ASSISTANT":
                    print(f"{HEADER_COLOR}-" * 50 + RESET)

            def on_iteration(iteration, status):
                print(
                    f"{HEADER_COLOR}\n>>> Iteration {iteration} | Cost: ${status.get('cost', 0):.4f}{RESET}"
                )

            def on_tool_call(tool_data):
                if tool_data.get("success", True):
                    tool_name = tool_data.get("tool_name", "unknown")
                    print(f"{SUCCESS_COLOR}🔧 Using tool: {tool_name}{RESET}")
                    if tool_name in ["edit_file", "create_file"]:
                        try:
                            import subprocess

                            diff_output = subprocess.run(
                                ["git", "diff", "HEAD"], capture_output=True, text=True
                            ).stdout
                            for line in diff_output.splitlines():
                                if line.startswith("+"):
                                    print(f"{SUCCESS_COLOR}{line}{RESET}")
                                elif line.startswith("-"):
                                    print(f"{ERROR_COLOR}{line}{RESET}")
                                else:
                                    print(line)
                        except Exception as e:
                            print(f"{WARNING_COLOR}⚠️ Could not show diff: {e}{RESET}")
                else:
                    print(
                        f"{ERROR_COLOR}❌ Tool error: {tool_data.get('error', 'unknown')}{RESET}"
                    )

            # Set up callbacks dictionary
            callbacks = {
                "on_message": on_message,
                "on_iteration": on_iteration,
                "on_tool_call": on_tool_call,
            }

            # Enhanced task description with document context
            enhanced_task = f"""
Original task: {task}

You have access to the following planning documents that were created:
- Requirements: {doc_result.requirements_path}
- Design: {doc_result.design_path}  
- Todos: {doc_result.todos_path}

Please read these documents first, then execute the task according to the plan.
Focus on completing the todos one by one, following the design specifications.
"""

            # Execute using clean single agent mode
            model = (
                self.worker_model
                or self.supervisor_model
                or "moonshot/kimi-k2-0711-preview"
            )
            result = await run_single_agent_mode(
                task_description=enhanced_task,
                agent_model=model,
                audit_model=model,
                max_cost=5.0,
                max_iterations=20,
                session_id=self.current_session_id,
                callbacks=callbacks,
            )

            print(f"{HEADER_COLOR}=" * 60 + RESET)
            if result["success"]:
                print(f"{SUCCESS_COLOR}✅ Task completed!{RESET}")
                print(f"{SUCCESS_COLOR}💰 Cost: ${result['cost']:.4f}{RESET}")
                print(f"{SUCCESS_COLOR}🔄 Iterations: {result['iterations']}{RESET}")
                print(
                    f"{SUCCESS_COLOR}📋 Check todos.md for task completion status{RESET}"
                )
            else:
                print(f"{ERROR_COLOR}❌ Task failed: {result['error']}{RESET}")

        except Exception as e:
            print(f"{ERROR_COLOR}❌ Error: {e}{RESET}")

    async def run(self):
        """Main TUI loop."""
        print("Welcome to EQUITR Coder!")

        while True:
            try:
                self.print_header()

                if not self.worker_model and not self.supervisor_model:
                    print(
                        f"\n{WARNING_COLOR}⚠️  No models selected. Please select a model first.{RESET}"
                    )
                    self.print_menu()

                user_input = input(f"\nequitrcoder> {RESET}").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["/quit", "/exit", "/q"]:
                    print("Goodbye!")
                    break
                elif user_input.lower() in ["/help", "/h"]:
                    self.print_menu()
                elif user_input.lower() == "/model":
                    self.select_model()
                elif user_input.lower() == "/session":
                    self.manage_sessions()
                elif user_input.startswith("/"):
                    print(f"Unknown command: {user_input}")
                else:
                    # Execute as task
                    await self.execute_task(user_input)

            except KeyboardInterrupt:
                print(f"\n{RESET}Goodbye!")
                break
            except EOFError:
                print(f"\n{RESET}Goodbye!")
                break


async def run_tui(config: Config) -> None:
    """Run the simple TUI application."""
    tui = SimpleTUI(config)
    await tui.run()


# --- Convenience wrapper expected by CLI ---
import asyncio as _asyncio

from ..core.config import config_manager as _cfg_mgr


def launch_tui(mode: str = "single") -> int:
    """Blocking wrapper so `equitrcoder tui` works."""
    try:
        cfg = _cfg_mgr.load_config()
        _asyncio.run(run_tui(cfg))
        return 0
    except Exception as exc:
        print(f"❌ Failed to launch TUI: {exc}")
        return 1
