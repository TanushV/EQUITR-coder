"""Simple ASCII TUI interface for EQUITR Coder."""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..core.config import Config, config_manager
from ..orchestrators.single_orchestrator import SingleAgentOrchestrator
from ..agents.base_agent import BaseAgent
from ..tools.discovery import discover_tools
from ..core.session import SessionManagerV2


class SimpleTUI:
    """Simple ASCII-based TUI for EQUITR Coder."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session_manager = SessionManagerV2(config.session.session_dir)
        self.current_session_id = "default"
        self.current_model = ""
        self.available_models = [
            "moonshot/kimi-k2-0711-preview",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo", 
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku"
        ]
        
    def print_header(self):
        """Print ASCII header."""
        print("\n" + "=" * 60)
        print("    EQUITR CODER - AI Coding Assistant")
        print("=" * 60)
        print(f"Session: {self.current_session_id}")
        print(f"Model: {self.current_model or 'Not selected'}")
        print("-" * 60)
        
    def print_menu(self):
        """Print main menu."""
        print("\nCommands:")
        print("  /help     - Show this help")
        print("  /model    - Change model")
        print("  /session  - Manage sessions") 
        print("  /quit     - Exit")
        print("  <task>    - Execute a coding task")
        print("-" * 60)
        
    def select_model(self):
        """Model selection interface."""
        print("\nAvailable models:")
        for i, model in enumerate(self.available_models, 1):
            print(f"  {i}. {model}")
        print("  0. Enter custom model")
        
        try:
            choice = input("\nSelect model (number): ").strip()
            if choice == "0":
                custom_model = input("Enter custom model: ").strip()
                if custom_model:
                    self.current_model = custom_model
                    print(f"Model set to: {custom_model}")
            elif choice.isdigit() and 1 <= int(choice) <= len(self.available_models):
                self.current_model = self.available_models[int(choice) - 1]
                print(f"Model set to: {self.current_model}")
            else:
                print("Invalid selection")
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
        """Execute a coding task."""
        if not self.current_model:
            print("❌ No model selected. Use /model to select one.")
            return
            
        try:
            # Create agent and orchestrator
            agent = BaseAgent(max_cost=5.0, max_iterations=20)
            
            # Add tools
            tools = discover_tools()
            for tool in tools:
                agent.add_tool(tool)
                
            orchestrator = SingleAgentOrchestrator(
                agent=agent,
                model=self.current_model,
                session_manager=self.session_manager
            )
            
            # Set up live callbacks
            def on_message(message_data):
                role = message_data['role'].upper()
                content = message_data['content']
                print(f"\n[{role}] {content}")
                if role == "ASSISTANT":
                    print("-" * 50)
            
            def on_iteration(iteration, status):
                print(f"\n>>> Iteration {iteration} | Cost: ${status['current_cost']:.4f}")
                
            def on_tool_call(tool_data):
                if tool_data.get('success', True):
                    tool_name = tool_data.get('tool_name', 'unknown')
                    print(f"🔧 Using tool: {tool_name}")
                else:
                    print(f"❌ Tool error: {tool_data.get('error', 'unknown')}")
            
            orchestrator.set_callbacks(
                on_message=on_message,
                on_iteration=on_iteration
            )
            agent.on_tool_call_callback = on_tool_call
            
            print(f"\n🤖 Executing task: {task}")
            print("=" * 60)
            
            # Execute
            result = await orchestrator.execute_task(
                task_description=task,
                session_id=self.current_session_id
            )
            
            print("=" * 60)
            if result["success"]:
                print(f"✅ Task completed!")
                print(f"💰 Cost: ${result['cost']:.4f}")
                print(f"🔄 Iterations: {result['iterations']}")
            else:
                print(f"❌ Task failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
    async def run(self):
        """Main TUI loop."""
        print("Welcome to EQUITR Coder!")
        
        while True:
            try:
                self.print_header()
                
                if not self.current_model:
                    print("\n⚠️  No model selected. Please select a model first.")
                    self.print_menu()
                    
                user_input = input("\nequitrcoder> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['/quit', '/exit', '/q']:
                    print("Goodbye!")
                    break
                elif user_input.lower() in ['/help', '/h']:
                    self.print_menu()
                elif user_input.lower() == '/model':
                    self.select_model()
                elif user_input.lower() == '/session':
                    self.manage_sessions()
                elif user_input.startswith('/'):
                    print(f"Unknown command: {user_input}")
                else:
                    # Execute as task
                    await self.execute_task(user_input)
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
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
