"""
Advanced TUI for EQUITR Coder using Textual

Features:
- Bottom status bar showing mode, models, stage, agents, and current cost
- Left sidebar with todo list progress
- Center chat window with live agent outputs
- Window splitting for parallel agents
- Real-time updates and proper event handling
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.unified_config import get_config

from rich.syntax import Syntax
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)

try:
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from ..core.config import config_manager
from ..programmatic import (
    EquitrCoder,
    ExecutionResult,
    MultiAgentTaskConfiguration,
    TaskConfiguration,
    create_multi_agent_coder,
    create_single_agent_coder,
)
from ..tools.builtin.todo import todo_manager
from ..core.model_manager import model_manager


class TodoSidebar(Static):
    """Left sidebar showing todo list progress."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.todos: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("📋 Todo Progress", classes="sidebar-title")
            yield Container(id="todo-list")

    def update_todos(self, todos: List[Dict[str, Any]]):
        """Update the todo list display."""
        self.todos = todos
        todo_container = self.query_one("#todo-list")
        todo_container.remove_children()

        if not todos:
            todo_container.mount(Label("No todos found", classes="todo-empty"))
            return

        for todo in todos:
            status_icon = "✅" if todo.get("completed", False) else "⏳"
            priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(
                todo.get("priority", "medium"), "white"
            )

            todo_text = f"{status_icon} {todo.get('description', 'Unknown task')}"
            todo_label = Label(todo_text, classes=f"todo-item todo-{priority_color}")
            todo_container.mount(todo_label)


class ChatWindow(RichLog):
    """Center chat window showing live agent outputs."""

    def __init__(self, agent_id: str = "main", **kwargs):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.message_count = 0

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the chat window."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding for different roles
        role_colors = {
            "user": "blue",
            "assistant": "green",
            "tool": "yellow",
            "system": "gray",
            "supervisor": "magenta",
            "worker": "cyan",
        }

        role_color = role_colors.get(role.lower(), "white")
        role_text = Text(f"[{timestamp}] {role.upper()}", style=f"bold {role_color}")

        # Format content with syntax highlighting if it's code
        if metadata and metadata.get("is_code", False):
            content_renderable = Syntax(
                content, metadata.get("language", "python"), theme="monokai"
            )
        else:
            content_renderable = Text(content)

        self.write(role_text)
        self.write(content_renderable)
        self.write("")  # Empty line for spacing

        self.message_count += 1

    def add_tool_call(
        self, tool_name: str, args: Dict, result: Any, success: bool = True
    ):
        """Add a tool call to the chat window."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        status_icon = "🔧" if success else "❌"
        status_color = "green" if success else "red"

        tool_text = Text(
            f"[{timestamp}] {status_icon} TOOL: {tool_name}",
            style=f"bold {status_color}",
        )
        self.write(tool_text)

        # Show tool arguments if they exist
        if args:
            args_text = Text(f"  Args: {args}", style="dim")
            self.write(args_text)

        # Show result summary
        if isinstance(result, dict) and "error" in result:
            error_text = Text(f"  Error: {result['error']}", style="red")
            self.write(error_text)
        elif success:
            success_text = Text("  ✓ Success", style="green")
            self.write(success_text)

        self.write("")

    def add_status_update(self, message: str, level: str = "info"):
        """Add a status update message."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        level_colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }

        level_icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}

        color = level_colors.get(level, "white")
        icon = level_icons.get(level, "📝")

        status_text = Text(f"[{timestamp}] {icon} {message}", style=f"bold {color}")
        self.write(status_text)
        self.write("")


class StatusBar(Static):
    """Bottom status bar showing mode, models, stage, agents, and cost."""

    mode: reactive[str] = reactive("single")
    models: reactive[str] = reactive("Not set")
    profiles: reactive[str] = reactive("default")
    pricing: reactive[str] = reactive("$0.000/1K")
    stage: reactive[str] = reactive("ready")
    agent_count: reactive[int] = reactive(0)
    current_cost: reactive[float] = reactive(0.0)
    max_cost: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"Mode: {self.mode}", id="status-mode", classes="status-item")
            yield Label(
                f"Models: {self.models}", id="status-models", classes="status-item"
            )
            yield Label(
                f"Profiles: {self.profiles}", id="status-profiles", classes="status-item"
            )
            yield Label(
                f"Prices: {self.pricing}", id="status-pricing", classes="status-item"
            )
            yield Label(
                f"Stage: {self.stage}", id="status-stage", classes="status-item"
            )
            yield Label(
                f"Agents: {self.agent_count}", id="status-agents", classes="status-item"
            )
            yield Label(
                f"Cost: ${self.current_cost:.4f}/${self.max_cost:.2f}",
                id="status-cost",
                classes="status-item",
            )

    def watch_mode(self, mode: str):
        """Update mode display."""
        self.query_one("#status-mode").update(f"Mode: {mode}")

    def watch_models(self, models: str):
        """Update models display."""
        self.query_one("#status-models").update(f"Models: {models}")

    def watch_profiles(self, profiles: str):
        self.query_one("#status-profiles").update(f"Profiles: {profiles}")

    def watch_pricing(self, pricing: str):
        self.query_one("#status-pricing").update(f"Prices: {pricing}")

    def watch_stage(self, stage: str):
        """Update stage display."""
        self.query_one("#status-stage").update(f"Stage: {stage}")

    def watch_agent_count(self, count: int):
        """Update agent count display."""
        self.query_one("#status-agents").update(f"Agents: {count}")

    def watch_current_cost(self, cost: float):
        """Update cost display."""
        self.query_one("#status-cost").update(f"Cost: ${cost:.4f}/${self.max_cost:.2f}")

    def update_cost_limit(self, max_cost: float):
        """Update the maximum cost limit."""
        self.max_cost = max_cost
        self.query_one("#status-cost").update(
            f"Cost: ${self.current_cost:.4f}/${max_cost:.2f}"
        )


class TaskInputPanel(Static):
    """Panel for task input and configuration."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Task Input", classes="panel-title")
            yield Input(placeholder="Enter your task description...", id="task-input")
            yield Input(placeholder="Comma-separated dataset paths (optional)", id="datasets-input")
            yield Input(placeholder="Experiments (name:command; name:command; ...)", id="experiments-input")
            with Horizontal():
                yield Button("Execute Single", variant="primary", id="btn-single")
                yield Button("Execute Multi", variant="success", id="btn-multi")
                yield Button("Execute Research", variant="success", id="btn-research")
                yield Button("Clear", variant="warning", id="btn-clear")


class AgentPanelGrid(Static):
    """Equal-split grid for agent chat windows."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_windows: Dict[str, ChatWindow] = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            for agent_id, window in self.agent_windows.items():
                yield window

    def add_agent_window(self, agent_id: str, agent_name: Optional[str] = None):
        if agent_id in self.agent_windows:
            return
        chat_window = ChatWindow(agent_id=agent_id, classes="agent-window")
        self.agent_windows[agent_id] = chat_window
        self.refresh()

    def get_agent_window(self, agent_id: str) -> Optional[ChatWindow]:
        return self.agent_windows.get(agent_id)

    def remove_agent_window(self, agent_id: str):
        if agent_id in self.agent_windows:
            del self.agent_windows[agent_id]
            self.refresh()


class AgentsSidebar(Static):
    """Right sidebar listing running agents."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agents: List[str] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("👥 Running Agents", classes="sidebar-title")
            yield Container(id="agents-list")

    def update_agents(self, agents: List[str]):
        self.agents = agents
        container = self.query_one("#agents-list")
        container.remove_children()
        if not agents:
            container.mount(Label("No active agents", classes="todo-empty"))
            return
        for name in agents:
            container.mount(Label(f"• {name}"))


class ModelSuggestion(ListItem):
    """Custom list item for model suggestions."""

    def __init__(self, model_name: str, provider: str):
        super().__init__()
        self.model_name = model_name
        self.provider = provider

    def compose(self) -> ComposeResult:
        yield Label(f"{self.model_name} ({self.provider})")


class EquitrTUI(App):
    """Main TUI application for EQUITR Coder."""

    CSS = """
    .sidebar {
        width: 25%;
        background: $surface;
        border-right: solid $accent;
    }
    
    .rightbar {
        width: 20%;
        background: $surface;
        border-left: solid $accent;
    }
    
    .main-content {
        width: 55%;
    }
    
    .sidebar-title {
        background: $accent;
        color: $text;
        padding: 1;
        text-align: center;
        font-weight: bold;
    }
    
    .panel-title {
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        font-weight: bold;
    }
    
    .todo-item {
        padding: 0 1;
        margin: 1 0;
        border: thin $accent;
        border-radius: 4;
    }
    
    .todo-red {
        background: $error 20%;
        color: $error;
    }
    
    .todo-yellow {
        background: $warning 20%;
        color: $warning;
    }
    
    .todo-green {
        background: $success 20%;
        color: $success;
    }
    
    .todo-empty {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    
    .status-item {
        padding: 0 2;
        background: $surface-dark;
        color: $text;
        border-right: solid $accent;
    }
    
    #task-input {
        margin: 1 0;
        border: thin $primary;
    }
    
    StatusBar {
        height: 1;
        background: $surface;
        border-bottom: solid $accent;
    }
    
    TodoSidebar {
        border-right: solid $accent;
    }
    
    TaskInputPanel {
        height: 8;
        border-bottom: solid $accent;
        background: $surface-light;
    }
    
    AgentPanelGrid {
        border: solid $accent;
        layout: horizontal;
    }
    
    .agent-window {
        width: 1fr;
        border-right: solid $accent 50%;
    }
    
    .model-suggestions {
        background: $surface;
        border: thin $accent;
        max-height: 20;
        overflow: auto;
    }
    
    ModelSuggestion {
        padding: 1;
        background: $boost;
        hover-background: $primary 20%;
    }
    """

    TITLE = "EQUITR Coder - Advanced TUI"
    SUB_TITLE = "Multi-Agent AI Coding Assistant"

    def __init__(self, mode: str = "single", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.config = config_manager.load_config()
        self.coder: Optional[EquitrCoder] = None
        self.current_task: Optional[str] = None
        self.task_running = False
        self.supervisor_model: Optional[str] = None
        self.worker_model: Optional[str] = None
        self.selected_profiles: List[str] = []

        # Initialize components
        self.todo_sidebar = TodoSidebar(classes="sidebar")
        self.status_bar = StatusBar()
        self.task_input = TaskInputPanel()
        self.agent_grid = AgentPanelGrid()
        self.agents_sidebar = AgentsSidebar(classes="rightbar")
        self.model_suggestions = ListView(classes="model-suggestions hidden")
        self.available_models: Dict[str, List[str]] = self.get_available_models()
        self.active_agent_names: List[str] = []

        # Set initial status
        self.status_bar.mode = mode
        self.status_bar.stage = "ready"

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()
        yield self.status_bar

        with Horizontal():
            yield self.todo_sidebar

            with Vertical(classes="main-content"):
                yield self.task_input
                yield self.agent_grid
                with Container(id="model-selector", classes="hidden"):
                    yield Label("Select Models", classes="panel-title")
                    yield Input(
                        placeholder="Supervisor model...", id="supervisor-input"
                    )
                    yield Input(placeholder="Worker model...", id="worker-input")
                    yield self.model_suggestions
                    yield Button("Confirm", variant="primary", id="btn-model-confirm")
                    yield Button("Cancel", variant="warning", id="btn-model-cancel")

            yield self.agents_sidebar

    async def on_mount(self):
        """Initialize TUI after mounting."""
        # Initialize main agent window
        self.agent_grid.add_agent_window("main")
        self.active_agent_names = ["Main Agent"]
        self.agents_sidebar.update_agents(self.active_agent_names)

        # Load todos
        await self.update_todos()

        # Initialize coder
        if self.mode == "single":
            self.coder = create_single_agent_coder()
            self.status_bar.models = "Default Single Model"
            self.status_bar.agent_count = 1
            self.status_bar.profiles = "default"
        else:
            self.coder = create_multi_agent_coder()
            self.status_bar.models = "Supervisor + Workers"
            self.status_bar.agent_count = 3
            self.status_bar.profiles = ", ".join(self.selected_profiles or ["default"]) or "default"

        # Set up callbacks
        self.coder.on_task_start = self.on_task_start
        self.coder.on_task_complete = self.on_task_complete
        self.coder.on_tool_call = self.on_tool_call
        self.coder.on_message = self.on_message
        self.coder.on_iteration = self.on_iteration

    def update_pricing_display(self):
        """Compute and update pricing string from selected models."""
        parts = []
        if self.supervisor_model:
            sup = self.supervisor_model
            c = model_manager.cost_cache.get(sup) or {"prompt": 0.0, "completion": 0.0}
            avg = (c.get("prompt", 0.0) + c.get("completion", 0.0)) / 2.0
            parts.append(f"sup ${avg:.4f}/1K")
        if self.worker_model:
            w = self.worker_model
            c = model_manager.cost_cache.get(w) or {"prompt": 0.0, "completion": 0.0}
            avg = (c.get("prompt", 0.0) + c.get("completion", 0.0)) / 2.0
            parts.append(f"wrk ${avg:.4f}/1K")
        self.status_bar.pricing = ", ".join(parts) if parts else "$0.0000/1K"

    def get_available_models(self) -> Dict[str, List[str]]:
        """Detect available providers and their models using environment variables and Litellm."""
        models = {}

        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            models["openai"] = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            models["anthropic"] = ["claude-3-sonnet", "claude-3-haiku", "claude-2"]

        # Azure
        if os.getenv("AZURE_API_KEY"):
            models["azure"] = ["azure/gpt-4", "azure/gpt-3.5-turbo"]

        # AWS Sagemaker/Bedrock
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            # Use Litellm to get supported models (example; expand as needed)
            models["aws"] = [
                f"sagemaker/{m}"
                for m in [
                    "jumpstart-dft-meta-textgeneration-llama-2-7b",
                    "bedrock/anthropic.claude-v2",
                ]
            ]

        # Add more providers based on env vars (e.g., COHERE_API_KEY, etc.)
        if os.getenv("COHERE_API_KEY"):
            models["cohere"] = ["command-nightly"]

        # Flatten for easier searching
        all_models = []
        for provider, model_list in models.items():
            for model in model_list:
                all_models.append((model, provider))

        return {"all": sorted(all_models), "by_provider": models}

    def select_model(self):
        """Show model selector with dynamic suggestions for both models."""
        selector = self.query_one("#model-selector")
        selector.remove_class("hidden")

        supervisor_input = self.query_one("#supervisor-input", Input)
        self.query_one("#worker-input", Input)
        supervisor_input.focus()

        # Initial update
        self.update_model_suggestions("")

    def update_model_suggestions(self, query: str):
        """Update the list of model suggestions based on user input."""
        self.model_suggestions.clear()

        matched = [
            (model, provider)
            for model, provider in self.available_models["all"]
            if query.lower() in model.lower() or query.lower() in provider.lower()
        ]

        if not matched:
            self.model_suggestions.mount(
                Label("No matching models found", classes="todo-empty")
            )
            return

        for model, provider in matched[:10]:  # Limit to top 10 suggestions
            self.model_suggestions.mount(ModelSuggestion(model, provider))

        self.model_suggestions.add_class("visible")

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle changes in the model input fields."""
        if event.input.id in ["supervisor-input", "worker-input"]:
            self.update_model_suggestions(event.value)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Auto-select highlighted suggestion into the focused input."""
        if event.item and isinstance(event.item, ModelSuggestion):
            if self.query_one("#supervisor-input").has_focus:
                self.query_one("#supervisor-input", Input).value = event.item.model_name
            elif self.query_one("#worker-input").has_focus:
                self.query_one("#worker-input", Input).value = event.item.model_name

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-single":
            await self.execute_task("single")
        elif event.button.id == "btn-multi":
            await self.execute_task("multi")
        elif event.button.id == "btn-research":
            await self.execute_task("research")
        elif event.button.id == "btn-clear":
            await self.clear_chat()
        elif event.button.id == "btn-model-confirm":
            supervisor_input = self.query_one("#supervisor-input", Input).value.strip()
            worker_input = self.query_one("#worker-input", Input).value.strip()
            if supervisor_input:
                self.supervisor_model = supervisor_input
            if worker_input:
                self.worker_model = worker_input
            models_display = f"Supervisor: {self.supervisor_model or 'Default'} | Worker: {self.worker_model or 'Default'}"
            self.status_bar.models = models_display
            self.update_pricing_display()
            main_window = self.agent_grid.get_agent_window("main")
            main_window.add_status_update(f"Models set: {models_display}", "success")
            self.hide_model_selector()
        elif event.button.id == "btn-model-cancel":
            self.hide_model_selector()

    async def on_key(self, event: Key) -> None:
        """Handle key presses."""
        if event.key == "ctrl+c":
            await self.quit()
        elif event.key == "enter":
            task_input = self.query_one("#task-input", Input)
            if task_input.value and not self.task_running:
                await self.execute_task(self.mode)
        elif event.key == "m" and not self.task_running:  # Example: 'm' for model
            self.select_model()

    async def execute_task(self, mode: str):
        """Execute a task using the specified mode."""
        if self.task_running:
            return

        task_input = self.query_one("#task-input", Input)
        datasets_input = self.query_one("#datasets-input", Input)
        experiments_input = self.query_one("#experiments-input", Input)
        task_description = task_input.value.strip()

        if not task_description:
            main_window = self.agent_grid.get_agent_window("main")
            main_window.add_status_update(
                "Please enter a task description", "warning"
            )
            return

        self.task_running = True
        self.current_task = task_description
        self.status_bar.stage = "executing"

        try:
            # Clear input
            task_input.value = ""

            # Add user message to main window
            main_window = self.agent_grid.get_agent_window("main")
            main_window.add_message("user", task_description)

            # Configure and execute task
            if mode == "single":
                config = TaskConfiguration(
                    description=task_description,
                    max_cost=get_config('limits.max_cost', 5.0),
                    max_iterations=get_config('limits.max_iterations', 20),
                    auto_commit=True,
                )
                self.status_bar.update_cost_limit(5.0)
                self.status_bar.agent_count = 1
                self.active_agent_names = ["Main Agent"]
            elif mode == "multi":
                config = MultiAgentTaskConfiguration(
                    description=task_description,
                    max_workers=get_config('limits.max_workers', 3),
                    max_cost=get_config('limits.max_cost', 15.0),
                    supervisor_model=self.supervisor_model or get_config('orchestrator.supervisor_model', "gpt-4"),
                    worker_model=self.worker_model or get_config('orchestrator.worker_model', "gpt-3.5-turbo"),
                    auto_commit=True,
                )
                self.status_bar.update_cost_limit(15.0)
                # Add worker windows for multi-agent mode (equal split)
                self.active_agent_names = ["Supervisor"]
                # Ensure at least 2 workers for demo split equal
                workers = get_config('limits.max_workers', 3)
                for i in range(workers):
                    agent_id = f"worker_{i+1}"
                    self.agent_grid.add_agent_window(agent_id)
                    self.active_agent_names.append(f"Worker {i+1}")
            else:  # research
                from ..programmatic.interface import ResearchTaskConfiguration
                config = ResearchTaskConfiguration(
                    description=task_description,
                    max_workers=get_config('limits.max_workers', 3),
                    max_cost=get_config('limits.max_cost', 15.0),
                    supervisor_model=self.supervisor_model or get_config('orchestrator.supervisor_model', "gpt-4"),
                    worker_model=self.worker_model or get_config('orchestrator.worker_model', "gpt-3.5-turbo"),
                    auto_commit=True,
                    team=["ml_researcher", "data_engineer", "experiment_runner", "report_writer"],
                )
                self.status_bar.update_cost_limit(15.0)
                self.active_agent_names = ["Supervisor"]
                workers = get_config('limits.max_workers', 3)
                for i in range(workers):
                    agent_id = f"worker_{i+1}"
                    self.agent_grid.add_agent_window(agent_id)
                    self.active_agent_names.append(f"Worker {i+1}")
            self.agents_sidebar.update_agents(self.active_agent_names)

            # Execute task
            # For research mode, synthesize a non-interactive research_context from inputs
            if mode == "research":
                datasets_raw = datasets_input.value.strip()
                experiments_raw = experiments_input.value.strip()
                datasets = []
                if datasets_raw:
                    for p in [s.strip() for s in datasets_raw.split(",") if s.strip()]:
                        datasets.append({"path": p, "description": ""})
                experiments = []
                if experiments_raw:
                    # parse name:command; name:command
                    for part in [s.strip() for s in experiments_raw.split(";") if s.strip()]:
                        if ":" in part:
                            name, cmd = part.split(":", 1)
                            experiments.append({"name": name.strip(), "command": cmd.strip()})
                        else:
                            experiments.append({"name": f"exp_{len(experiments)+1}", "command": part})
                # We call researcher mode indirectly via EquitrCoder; embed context by temporarily monkey-patching
                # the programmatic call through config (EquitrCoder passes through to mode).
                # We use a private attr on config to pass through.
                setattr(config, "research_context", {"datasets": datasets, "experiments": experiments})
            result = await self.coder.execute_task(task_description, config)

            # Show result
            if result.success:
                main_window.add_status_update(
                    f"Task completed successfully! Cost: ${result.cost:.4f}, Time: {result.execution_time:.2f}s",
                    "success",
                )
                if result.git_committed:
                    main_window.add_status_update(
                        f"Changes committed: {result.commit_hash}", "info"
                    )
            else:
                main_window.add_status_update(f"Task failed: {result.error}", "error")

        except Exception as e:
            main_window = self.agent_grid.get_agent_window("main")
            main_window.add_status_update(f"Execution error: {str(e)}", "error")

        finally:
            self.task_running = False
            self.status_bar.stage = "ready"
            await self.update_todos()

    async def clear_chat(self):
        """Clear all chat windows."""
        for window in self.agent_grid.agent_windows.values():
            window.clear()

    async def update_todos(self):
        """Update the todo list display."""
        try:
            # Build grouped todos view from manager
            groups = []
            for group in todo_manager.plan.task_groups:
                group_entry = {
                    "group_id": group.group_id,
                    "description": group.description,
                    "status": group.status,
                    "todos": [{"title": t.title, "status": t.status} for t in group.todos],
                }
                groups.append(group_entry)
            self.todo_sidebar.update_todos(groups)
        except Exception:
            self.todo_sidebar.update_todos([])

    # Callback methods
    def on_task_start(self, description: str, mode: str):
        """Called when a task starts."""
        main_window = self.agent_grid.get_agent_window("main")
        main_window.add_status_update(f"Starting {mode} mode task", "info")

    def on_task_complete(self, result: ExecutionResult):
        """Called when a task completes."""
        self.status_bar.current_cost = result.cost
        main_window = self.agent_grid.get_agent_window("main")

        if result.success:
            main_window.add_status_update("Task execution completed", "success")
        else:
            main_window.add_status_update("Task execution failed", "error")

    def on_iteration(self, iteration: int, cost: float):
        """Called on each iteration to update live cost."""
        self.status_bar.current_cost = cost
        main_window = self.agent_grid.get_agent_window("main")
        main_window.add_status_update(
            f"Iteration {iteration} | Current Cost: ${cost:.4f}", "info"
        )

    def on_tool_call(self, tool_data: Dict[str, Any]):
        """Called when a tool is executed."""
        agent_id = tool_data.get("agent_id", "main")
        window = self.agent_grid.get_agent_window(agent_id)

        if window:
            window.add_tool_call(
                tool_name=tool_data.get("tool_name", "unknown"),
                args=tool_data.get("arguments", {}),
                result=tool_data.get("result", {}),
                success=tool_data.get("success", True),
            )

    def on_message(self, message_data: Dict[str, Any]):
        """Called when a message is generated."""
        agent_id = message_data.get("agent_id", "main")
        window = self.agent_grid.get_agent_window(agent_id)

        if window:
            window.add_message(
                role=message_data.get("role", "assistant"),
                content=message_data.get("content", ""),
                metadata=message_data.get("metadata", {}),
            )

    async def on_shutdown(self):
        """Clean up resources on shutdown."""
        if self.coder:
            await self.coder.cleanup()

    def hide_model_selector(self):
        selector = self.query_one("#model-selector")
        selector.add_class("hidden")
        self.model_suggestions.clear()
        self.model_suggestions.add_class("hidden")


def launch_advanced_tui(mode: str = "single") -> int:
    """Launch the advanced TUI application."""
    if not TEXTUAL_AVAILABLE:
        print("❌ Advanced TUI requires 'textual' and 'rich' packages. Please install them with: pip install textual rich")
        return 1

    try:
        app = EquitrTUI(mode=mode)
        app.run()
        return 0
    except Exception as e:
        print(f"❌ Failed to launch TUI: {e}")
        return 1


def launch_tui(mode: str = "single") -> int:
    """Launch the unified TUI (advanced only)."""
    return launch_advanced_tui(mode)


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "single"
    exit(launch_tui(mode))
