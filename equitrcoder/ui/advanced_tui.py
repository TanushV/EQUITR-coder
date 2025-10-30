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
import shlex
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from litellm import get_valid_models
except ImportError:
    def get_valid_models(*args, **kwargs):
        return []

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
    Footer,
    Select,
)

class StartupScreen(Static):
    """Initial startup screen with model selection and welcome message."""

    def __init__(self, available_models: List[str], **kwargs):
        super().__init__(**kwargs)
        self.available_models = available_models

    def compose(self) -> ComposeResult:
        with Vertical(classes="startup-container"):
            yield Label("🤖 EQUITR Coder - Multi-Agent AI Assistant", classes="startup-title")
            yield Label("Select your models to get started:", classes="startup-subtitle")
            
            with Horizontal(classes="model-selectors"):
                with Vertical():
                    yield Label("Supervisor Model:", classes="model-label")
                    yield Select(
                        options=[(model, model) for model in self.available_models],
                        value=self.available_models[0] if self.available_models else None,
                        id="supervisor-select"
                    )
                with Vertical():
                    yield Label("Worker Model:", classes="model-label")
                    yield Select(
                        options=[(model, model) for model in self.available_models],
                        value=self.available_models[0] if self.available_models else None,
                        id="worker-select"
                    )
                with Vertical():
                    yield Label("Mode:", classes="model-label")
                    yield Select(
                        options=[
                            ("Single Agent", "single"),
                            ("Multi-Agent Parallel", "multi-parallel"),
                            ("Multi-Agent Sequential", "multi-seq"),
                            ("Research Mode", "research")
                        ],
                        value="single",
                        id="mode-select"
                    )
            # New session/task selection controls
            yield Label("Previous tasks handling:", classes="model-label")
            yield Select(
                options=[
                    ("Ignore previous tasks (start fresh)", "ignore"),
                    ("Include selected previous tasks on top", "include"),
                    ("Only work on selected previous tasks", "only"),
                ],
                value="ignore",
                id="prev-task-mode"
            )
            yield Input(placeholder="Comma-separated task group IDs to include (optional)", id="prev-task-ids")
            
            yield Label("Type your first task below to begin:", classes="startup-instruction")
            yield Input(placeholder="Describe what you want to build...", id="startup-input")
            yield Button("Start Coding", variant="primary", id="btn-start")

class MainScreen(Static):
    """Main TUI screen with sidebars and chat."""
    
    def __init__(self, todo_sidebar, agent_grid, agents_sidebar, command_bar, **kwargs):
        super().__init__(**kwargs)
        self.todo_sidebar = todo_sidebar
        self.agent_grid = agent_grid
        self.agents_sidebar = agents_sidebar
        self.command_bar = command_bar

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield self.todo_sidebar
            with Vertical(classes="main-content"):
                yield self.agent_grid
            yield self.agents_sidebar
        yield self.command_bar


try:
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from ..core.unified_config import get_config_manager as _get_cm
config_manager = _get_cm()
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
        with Vertical(classes="sidebar-pad"):
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
    elapsed_seconds: reactive[float] = reactive(0.0)
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
            yield Label(
                f"Time: {self.elapsed_seconds:.1f}s",
                id="status-time",
                classes="status-item",
            )

    def _safe_update(self, selector: str, text: str) -> None:
        """Safely update a label if present (ignore if not yet mounted)."""
        try:
            self.query_one(selector).update(text)
        except Exception:
            # Widget not mounted yet or selector not present; ignore
            pass

    def watch_mode(self, mode: str):
        """Update mode display."""
        self._safe_update("#status-mode", f"Mode: {mode}")

    def watch_models(self, models: str):
        """Update models display."""
        self._safe_update("#status-models", f"Models: {models}")

    def watch_profiles(self, profiles: str):
        self._safe_update("#status-profiles", f"Profiles: {profiles}")

    def watch_pricing(self, pricing: str):
        self._safe_update("#status-pricing", f"Prices: {pricing}")

    def watch_stage(self, stage: str):
        """Update stage display."""
        self._safe_update("#status-stage", f"Stage: {stage}")

    def watch_agent_count(self, count: int):
        """Update agent count display."""
        self._safe_update("#status-agents", f"Agents: {count}")

    def watch_current_cost(self, cost: float):
        """Update cost display."""
        self._safe_update("#status-cost", f"Cost: ${cost:.4f}/${self.max_cost:.2f}")

    def update_cost_limit(self, max_cost: float):
        """Update the maximum cost limit."""
        self.max_cost = max_cost
        self._safe_update(
            "#status-cost", f"Cost: ${self.current_cost:.4f}/${max_cost:.2f}"
        )

    def update_elapsed(self, seconds: float):
        """Update elapsed time display."""
        self.elapsed_seconds = seconds
        self._safe_update("#status-time", f"Time: {seconds:.1f}s")


class TaskInputPanel(Static):
    """Removed - using startup screen instead."""
    pass


class CommandBar(Static):
    """Bottom command bar with a single always-visible input for slash-commands."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="commandbar-pad"):
            yield Label("/>", classes="commandbar-prompt")
            yield Input(placeholder="Type /help for commands...", id="command-input")


class AgentPanelGrid(Static):
    """Equal-split grid for agent chat windows."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_windows: Dict[str, ChatWindow] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(classes="main-pad"):
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
        with Vertical(classes="sidebar-pad"):
            yield Label("👥 Running Agents", classes="sidebar-title")
            yield Container(id="agents-list")

    def update_agents(self, agents: List[str]):
        self.agents = agents
        try:
            container = self.query_one("#agents-list")
            container.remove_children()
            if not agents:
                container.mount(Label("No active agents", classes="todo-empty"))
                return
            for name in agents:
                container.mount(Label(f"• {name}"))
        except Exception:
            # Component not mounted yet, ignore
            pass


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
    /* Global look (black background, white text) */
    Screen {
        background: #000000;
        color: #ffffff;
    }

    Header {
        background: #000000;
        color: #ffffff;
        border-bottom: solid #444444;
    }

    Footer {
        background: #000000;
        color: #ffffff;
        border-top: solid #444444;
    }

    RichLog {
        background: #000000;
        color: #ffffff;
        border: none #000000;
    }

    Input {
        background: #000000;
        color: #ffffff;
        border: solid #666666;
    }

    Button {
        background: #111111;
        color: #ffffff;
        border: solid #666666;
    }

    /* Utility */
    .hidden { display: none; }

    /* Startup screen */
    .startup-container {
        align: center top;
        width: 100%;
        height: 1fr;
        background: #000000;
        color: #ffffff;
        padding: 1 2;
        border: solid #444444;
    }
    .startup-title {
        text-align: center;
        text-style: bold;
        color: #00ff00;
        margin: 1 0;
        height: 3;
    }
    .startup-subtitle, .startup-instruction {
        text-align: center;
        margin: 1 0;
        color: #cccccc;
        height: 2;
    }
    .model-selectors {
        width: 100%;
        height: 6;
        margin: 1 0;
        layout: horizontal;
    }
    .model-label {
        text-align: center;
        margin: 0 0 1 0;
        color: #ffffff;
        height: 1;
    }
    .model-selectors > Vertical {
        width: 1fr;
        margin: 0 1;
        height: 1fr;
    }
    #startup-input {
        width: 100%;
        margin: 1 0;
        height: 3;
    }
    #btn-start {
        width: 100%;
        margin: 1 0;
        height: 3;
    }

    .sidebar {
        width: 20%;
        background: #000000;
        color: #ffffff;
        border-right: solid #444444;
    }

    .rightbar {
        width: 15%;
        background: #000000;
        color: #ffffff;
        border-left: solid #444444;
    }

    .main-content {
        width: 65%;
        background: #000000;
        color: #ffffff;
    }

    .sidebar-pad {
        padding: 1;
    }

    .panel-pad {
        padding: 1;
    }

    .main-pad {
        padding: 1;
    }

    .sidebar-title {
        background: #111111;
        color: #ffffff;
        padding: 1;
        text-align: center;
        text-style: bold;
        border: solid #444444;
    }

    .panel-title {
        background: #111111;
        color: #ffffff;
        padding: 1;
        text-align: center;
        text-style: bold;
        border: solid #444444;
    }

    .todo-item {
        padding: 0 1;
        margin: 1 0;
        border: solid #666666;
        color: #ffffff;
        background: #000000;
    }

    .todo-red {
        color: #ffffff;
    }

    .todo-yellow {
        color: #ffffff;
    }

    .todo-green {
        color: #ffffff;
    }

    .todo-empty {
        color: #cccccc;
        text-align: center;
        padding: 2;
    }

    .status-item {
        padding: 0 2;
        background: #111111;
        color: #ffffff;
        border-right: solid #444444;
        text-style: bold;
    }

    #task-input {
        margin: 1 0;
        border: solid #666666;
    }

    StatusBar {
        height: 1;
        background: #000000;
        border-bottom: solid #444444;
        color: #ffffff;
    }

    TodoSidebar {
        border-right: solid #444444;
    }

    TaskInputPanel {
        height: 2;
        border-bottom: solid #444444;
        background: #000000;
        color: #ffffff;
    }

    AgentPanelGrid {
        height: 1fr;
        border: solid #444444;
        layout: horizontal;
        background: #000000;
        color: #ffffff;
    }

    .agent-window {
        width: 1fr;
        border-right: solid #333333;
        background: #000000;
        color: #ffffff;
    }

    .model-suggestions {
        background: #000000;
        color: #ffffff;
        border: solid #444444;
        max-height: 20;
        overflow: auto;
    }

    ModelSuggestion {
        padding: 1;
        background: #111111;
        color: #ffffff;
        border: solid #444444;
    }

    /* Bottom command bar */
    CommandBar {
        dock: bottom;
        height: 1;
        border-top: solid #444444;
        background: #000000;
        color: #ffffff;
    }
    .commandbar-pad { padding: 0; }
    .commandbar-prompt { width: 3; text-align: center; color: #888888; }
    #command-input { width: 1fr; }

    /* Status bar should be visible */
    StatusBar {
        height: 1;
        dock: top;
    }

    /* Header should be visible */
    Header {
        height: 1;
        dock: top;
    }
    """

    TITLE = "EQUITR Coder - Advanced TUI"
    SUB_TITLE = "Multi-Agent AI Coding Assistant"
    BINDINGS = [
        ("h", "show_help", "Help"),
    ]

    COMMANDS_HELP = (
        "Commands:\n"
        "  /help                               Show this help\n"
        "  /mode [single|multi-parallel|multi-seq|research]  Switch mode (multi-parallel is default)\n"
        "  /models                             Open model selector\n"
        "  /set supervisor <model>             Set supervisor model\n"
        "  /set worker <model>                 Set worker model\n"
        "  /set mode <mode>                    Set execution mode\n"
        "  /run <task description>             Execute a task in current mode\n"
        "  /status                             Show current status\n"
        "  /agents                             List active agents\n"
        "  /profiles list                      List available profiles\n"
        "  /profiles select <name>             Select a profile (multi/research)\n"
        "  /session list                       List saved sessions\n"
        "  /session current                    Show current session\n"
        "  /session new [id]                   Start/use a new session id\n"
        "  /session resume <id>                Resume an existing session id\n"
        "  /session pause                      Mark current session paused and cancel running task\n"
        "  /tasks mode [ignore|include|only]   Control handling of previous tasks\n"
        "  /tasks select <groupIdsCsv>         Select task group IDs for include/only\n"
        "  /clear                              Clear chat windows\n"
        "  /quit                               Exit the TUI\n"
    )

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
        self.model_selected: bool = False
        self.multi_run_parallel: bool = True
        self.startup_mode: bool = True
        self.available_models: List[str] = []
        self.active_agent_names: List[str] = []
        self.command_bar = CommandBar()
        self.startup_screen: Optional[StartupScreen] = None
        self.main_screen: Optional[MainScreen] = None
        self.custom_header: Optional[Static] = None
        self.session_cost: float = 0.0
        self.current_session_id: Optional[str] = None
        self._task_handle: Optional[Any] = None
        self._paused: bool = False
        self.status_bar: StatusBar = StatusBar()
        self.project_root: Optional[str] = None
        self.prev_task_mode: str = "ignore"
        self.prev_task_ids: List[str] = []

        # Initialize components
        self.todo_sidebar = TodoSidebar(classes="sidebar")
        self.agent_grid = AgentPanelGrid()
        self.agents_sidebar = AgentsSidebar(classes="rightbar")
        self.command_bar = CommandBar()
        self.active_agent_names: List[str] = []
        self.startup_screen: Optional[StartupScreen] = None
        self.main_screen: Optional[MainScreen] = None
        self.custom_header: Optional[Static] = None

        # Do not set status labels here; wait until after mount

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        # Custom header with time and models
        self.custom_header = Static(classes="custom-header")
        yield self.custom_header
        # Status bar (docked via CSS)
        yield self.status_bar

        # Container for switching between startup and main screens
        yield Container(id="screen-container", classes="screen-container")

    async def on_mount(self):
        """Initialize TUI after mounting."""
        # Get available models from litellm
        try:
            self.available_models = get_valid_models(check_provider_endpoint=True)
            if not self.available_models:
                # Fallback to common models if API detection fails
                self.available_models = [
                    "gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku",
                    "moonshot/kimi-k2-0711-preview"
                ]
        except Exception:
            self.available_models = [
                "gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku",
                "moonshot/kimi-k2-0711-preview"
            ]

        # Show startup screen initially
        await self.show_startup_screen()
        
        # Update header with current time
        self.update_header()
        self.set_interval(1.0, self.update_header)  # Update every second

        # Initialize main agent window
        self.agent_grid.add_agent_window("main")
        self.active_agent_names = ["Main Agent"]
        
        # Load todos
        await self.update_todos()

        # Initialize coder
        if self.mode == "single":
            self.coder = create_single_agent_coder()
        else:
            self.coder = create_multi_agent_coder()

        # Set up callbacks
        self.coder.on_task_start = self.on_task_start
        self.coder.on_task_complete = self.on_task_complete
        self.coder.on_tool_call = self.on_tool_call
        self.coder.on_message = self.on_message
        self.coder.on_iteration = self.on_iteration

    def action_show_help(self) -> None:
        self.show_help()

    def show_help(self) -> None:
        main_window = self.agent_grid.get_agent_window("main")
        if main_window:
            main_window.add_status_update(self.COMMANDS_HELP, "info")

    def set_mode(self, mode: str) -> None:
        normalized = mode.lower()
        if normalized in ("single",):
            self.mode = "single"
        elif normalized in ("multi", "multi-parallel", "multi_parallel", "parallel"):
            self.mode = "multi"
            self.multi_run_parallel = True
        elif normalized in ("multi-seq", "multi_sequential", "sequential", "multi-sequential"):
            self.mode = "multi"
            self.multi_run_parallel = False
        elif normalized in ("research",):
            self.mode = "research"
        else:
            main_window = self.agent_grid.get_agent_window("main")
            if main_window:
                main_window.add_status_update(f"Unknown mode: {mode}", "error")
            return
        self.status_bar.mode = self.mode if self.mode != "multi" else ("multi-seq" if not self.multi_run_parallel else "multi-parallel")
        main_window = self.agent_grid.get_agent_window("main")
        if main_window:
            mode_label = self.status_bar.mode
            main_window.add_status_update(f"Mode set to {mode_label}. Use /run <task description> to execute.", "info")
        # Recreate coder per mode to ensure identical backend as programmatic interface
        try:
            if self.mode == "single":
                self.coder = create_single_agent_coder()
            elif self.mode == "multi":
                self.coder = create_multi_agent_coder()
            else:  # research
                self.coder = EquitrCoder(mode="research")
            self.coder.on_task_start = self.on_task_start
            self.coder.on_task_complete = self.on_task_complete
            self.coder.on_tool_call = self.on_tool_call
            self.coder.on_message = self.on_message
            self.coder.on_iteration = self.on_iteration
        except Exception:
            pass
        try:
            self.query_one("#command-input", Input).focus()
        except Exception:
            pass

    async def execute_command(self, line: str) -> None:
        line = line.strip()
        main_window = self.agent_grid.get_agent_window("main")
        if not line:
            return
        if not line.startswith("/"):
            if main_window:
                main_window.add_status_update("Use /help to see available commands.", "warning")
            return
        try:
            parts = shlex.split(line[1:])
        except Exception:
            parts = line[1:].split()
        if not parts:
            self.show_help()
            return
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("help", "h"):
            self.show_help()
            return
        if cmd == "mode":
            if not args:
                self.show_help()
                return
            self.set_mode(args[0].lower())
            return
        if cmd == "models":
            self.select_model()
            return
        if cmd == "set" and args:
            if args[0] in ("supervisor", "sup") and len(args) >= 2:
                model = " ".join(args[1:])
                self.supervisor_model = model
                self.model_selected = True
            elif args[0] in ("worker", "wrk") and len(args) >= 2:
                model = " ".join(args[1:])
                self.worker_model = model
                self.model_selected = True
            elif args[0] in ("mode", "m") and len(args) >= 2:
                new_mode = args[1].lower()
                self.set_mode(new_mode)
                return
            else:
                if main_window:
                    main_window.add_status_update("Usage: /set supervisor <model> | /set worker <model> | /set mode <mode>", "warning")
                return
            models_display = f"Supervisor: {self.supervisor_model or 'Default'} | Worker: {self.worker_model or 'Default'}"
            self.status_bar.models = models_display
            self.update_pricing_display()
            if main_window:
                main_window.add_status_update(f"Models updated: Supervisor={self.supervisor_model}, Worker={self.worker_model}", "success")
            try:
                self.query_one("#command-input", Input).focus()
            except Exception:
                pass
            return
        if cmd == "run":
            if not args:
                if main_window:
                    main_window.add_status_update("Usage: /run <task description>", "warning")
                return
            if not self.model_selected:
                if main_window:
                    main_window.add_status_update("Select models first with /models or /set", "warning")
                self.select_model()
                return
            task_text = " ".join(args)
            await self.execute_task(self.mode, task_text)
            return
        if cmd == "status":
            status = (
                f"Mode: {self.mode} | Supervisor: {self.supervisor_model or 'Not set'} | "
                f"Worker: {self.worker_model or 'Not set'} | Profiles: {', '.join(self.selected_profiles) or 'default'}"
            )
            if main_window:
                main_window.add_status_update(status, "info")
            return
        if cmd == "agents":
            if main_window:
                main_window.add_status_update(f"Agents: {', '.join(self.active_agent_names) or 'None'}", "info")
            return
        if cmd == "profiles":
            if not args:
                self.show_help()
                return
            sub = args[0]
            if sub == "list":
                cfg = config_manager.load_config()
                if main_window:
                    main_window.add_status_update(f"Profiles: {', '.join(cfg.profiles.available)}", "info")
                return
            if sub == "select" and len(args) >= 2:
                name = args[1]
                self.selected_profiles = [name]
                self.status_bar.profiles = name
                if main_window:
                    main_window.add_status_update(f"Profile selected: {name}", "success")
                return
            self.show_help()
            return
        if cmd == "clear":
            await self.clear_chat()
            return
        if cmd in ("quit", "exit"):
            self.exit()
            return
        if cmd == "session":
            if not args:
                self.show_help()
                return
            sub = args[0].lower()
            if sub == "list":
                try:
                    sessions = self.coder.list_sessions() if self.coder else []
                    if main_window:
                        if not sessions:
                            main_window.add_status_update("No sessions found", "info")
                        else:
                            lines = [f"{s['session_id']} | msgs={s['message_count']} | updated={s['updated_at']} | cost=${s.get('cost',0.0):.2f}" for s in sessions]
                            main_window.add_status_update("Sessions:\n" + "\n".join(lines), "info")
                except Exception as e:
                    if main_window:
                        main_window.add_status_update(f"Failed to list sessions: {e}", "error")
                return
            if sub == "current":
                sid = self.current_session_id or "None"
                if main_window:
                    main_window.add_status_update(f"Current session: {sid}", "info")
                return
            if sub == "new":
                import uuid
                sid = args[1] if len(args) >= 2 else str(uuid.uuid4())[:8]
                self.current_session_id = sid
                try:
                    # Ensure session exists
                    if self.coder:
                        sm = self.coder.session_manager
                        sm.get_session_data(sid)
                except Exception:
                    pass
                if main_window:
                    main_window.add_status_update(f"Using new session: {sid}", "success")
                return
            if sub == "resume" and len(args) >= 2:
                sid = args[1]
                try:
                    if self.coder and self.coder.session_manager.load_session(sid):
                        self.current_session_id = sid
                        # Mark unpaused
                        sess = self.coder.session_manager.get_session_data(sid)
                        sess.metadata["paused"] = False
                        self.coder.session_manager.save_session(sess)
                        if main_window:
                            main_window.add_status_update(f"Resumed session: {sid}", "success")
                    else:
                        if main_window:
                            main_window.add_status_update(f"Session not found: {sid}", "error")
                except Exception as e:
                    if main_window:
                        main_window.add_status_update(f"Failed to resume session: {e}", "error")
                return
            if sub == "pause":
                if not self.current_session_id:
                    if main_window:
                        main_window.add_status_update("No current session to pause. Use /session new or /session resume <id>.", "warning")
                    return
                try:
                    if self._task_handle and not self._task_handle.done():
                        self._task_handle.cancel()
                    if self.coder:
                        sess = self.coder.session_manager.get_session_data(self.current_session_id)
                        sess.metadata["paused"] = True
                        self.coder.session_manager.save_session(sess)
                    self._paused = True
                    if main_window:
                        main_window.add_status_update(f"Paused session: {self.current_session_id}", "success")
                except Exception as e:
                    if main_window:
                        main_window.add_status_update(f"Failed to pause: {e}", "error")
                return
            self.show_help()
            return
        if cmd == "tasks":
            if not args:
                self.show_help()
                return
            sub = args[0].lower()
            if sub == "mode" and len(args) >= 2:
                mode_val = args[1].lower()
                if mode_val in ("ignore", "include", "only"):
                    self.prev_task_mode = mode_val
                    if main_window:
                        main_window.add_status_update(f"Previous tasks mode set to: {mode_val}", "success")
                else:
                    if main_window:
                        main_window.add_status_update("Usage: /tasks mode [ignore|include|only]", "warning")
                return
            if sub == "select" and len(args) >= 2:
                ids_csv = args[1]
                self.prev_task_ids = [x.strip() for x in ids_csv.split(',') if x.strip()]
                if main_window:
                    main_window.add_status_update(f"Selected task groups: {', '.join(self.prev_task_ids) if self.prev_task_ids else '(none)'}", "success")
                return
            self.show_help()
            return
        # Unknown command
        if main_window:
            main_window.add_status_update(f"Unknown command: {cmd}. Use /help.", "error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-start":
            # Get selected models
            try:
                supervisor_select = self.query_one("#supervisor-select", Select)
                worker_select = self.query_one("#worker-select", Select)
                mode_select = self.query_one("#mode-select", Select)
                startup_input = self.query_one("#startup-input", Input)
                prev_task_mode = self.query_one("#prev-task-mode", Select)
                prev_ids_input = self.query_one("#prev-task-ids", Input)
                
                self.supervisor_model = supervisor_select.value
                self.worker_model = worker_select.value
                
                # Set mode based on selection
                selected_mode = mode_select.value
                self.set_mode(selected_mode)
                
                self.model_selected = True
                self.prev_task_mode = prev_task_mode.value or "ignore"
                self.prev_task_ids = [x.strip() for x in (prev_ids_input.value or "").split(',') if x.strip()]
                # Reflect selected models immediately
                models_display = f"Supervisor: {self.supervisor_model or 'Default'} | Worker: {self.worker_model or 'Default'}"
                self.status_bar.models = models_display
                self.update_pricing_display()
                
                first_task = startup_input.value.strip()
                if not first_task:
                    return
                
                # Switch to main screen
                await self.show_main_screen()
                
                # Execute the first task
                await self.execute_task(self.mode, first_task)
                
            except Exception as e:
                print(f"Error starting: {e}")

    async def on_key(self, event: Key) -> None:
        """Handle key presses."""
        if event.key == "ctrl+c":
            await self.quit()
        elif event.key == "enter":
            if self.startup_mode:
                # Handle startup screen enter
                try:
                    btn_start = self.query_one("#btn-start", Button)
                    await self.on_button_pressed(Button.Pressed(btn_start))
                except Exception:
                    pass
            else:
                # Handle main screen enter
                try:
                    cmd_input = self.query_one("#command-input", Input)
                    line = cmd_input.value.strip()
                    cmd_input.value = ""
                    await self.execute_command(line)
                except Exception:
                    pass

    async def execute_task(self, mode: str, task_text: Optional[str] = None):
        """Execute a task using the specified mode."""
        if self.task_running:
            return
        if not self.model_selected:
            main_window = self.agent_grid.get_agent_window("main")
            if main_window:
                main_window.add_status_update("Select models first with /models or /set", "warning")
            self.select_model()
            return

        task_description = (task_text or "").strip()
        if not task_description:
            main_window = self.agent_grid.get_agent_window("main")
            main_window.add_status_update(
                "Please enter a task description", "warning"
            )
            return

        # Ensure we have a session id
        if not self.current_session_id:
            import uuid
            self.current_session_id = str(uuid.uuid4())[:8]
        self._paused = False

        # Ensure isolated project directory per run
        try:
            from datetime import datetime as _dt
            from pathlib import Path as _Path
            ts = _dt.now().strftime("%Y%m%d_%H%M%S")
            proj_dir = _Path(f"generated_projects/tui_run_{ts}").resolve()
            proj_dir.mkdir(parents=True, exist_ok=True)
            self.project_root = str(proj_dir)
        except Exception:
            self.project_root = "."

        async def _run():
            self.task_running = True
            self.current_task = task_description
            self.status_bar.stage = "executing"
            try:
                main_window = self.agent_grid.get_agent_window("main")
                main_window.add_message("user", task_description)
                # Clear any previous worker windows so UI reflects current mode
                try:
                    for _agent_id in list(self.agent_grid.agent_windows.keys()):
                        if _agent_id != "main":
                            self.agent_grid.remove_agent_window(_agent_id)
                except Exception:
                    pass

                # Configure and execute task
                if mode == "single":
                    config = TaskConfiguration(
                        description=task_description,
                        max_cost=get_config('limits.max_cost', 5.0),
                        max_iterations=get_config('limits.max_iterations', 20),
                        auto_commit=True,
                        model=self.supervisor_model or self.worker_model,
                        session_id=self.current_session_id,
                    )
                    self.status_bar.update_cost_limit(5.0)
                    self.status_bar.agent_count = 1
                    self.active_agent_names = ["Main Agent"]
                elif mode == "multi":
                    _workers = get_config('limits.max_workers', 3)
                    config = MultiAgentTaskConfiguration(
                        description=task_description,
                        max_workers=_workers,
                        max_cost=get_config('limits.max_cost', 15.0),
                        supervisor_model=self.supervisor_model or get_config('orchestrator.supervisor_model', "gpt-4"),
                        worker_model=self.worker_model or get_config('orchestrator.worker_model', "gpt-3.5-turbo"),
                        auto_commit=True,
                        run_parallel=self.multi_run_parallel,
                        session_id=self.current_session_id,
                    )
                    self.status_bar.update_cost_limit(15.0)
                    self.status_bar.agent_count = 1 + int(_workers)
                    self.active_agent_names = ["Supervisor"]
                    for i in range(_workers):
                        agent_id = f"worker_{i+1}"
                        self.agent_grid.add_agent_window(agent_id)
                        self.active_agent_names.append(f"Worker {i+1}")
                else:  # research
                    from ..programmatic.interface import ResearchTaskConfiguration
                    _workers = get_config('limits.max_workers', 3)
                    config = ResearchTaskConfiguration(
                        description=task_description,
                        max_workers=_workers,
                        max_cost=get_config('limits.max_cost', 15.0),
                        supervisor_model=self.supervisor_model or get_config('orchestrator.supervisor_model', "gpt-4"),
                        worker_model=self.worker_model or get_config('orchestrator.worker_model', "gpt-3.5-turbo"),
                        auto_commit=True,
                        team=["ml_researcher", "data_engineer", "experiment_runner"],
                        session_id=self.current_session_id,
                        research_context={},
                    )
                    self.status_bar.update_cost_limit(15.0)
                    self.status_bar.agent_count = 1 + int(_workers)
                    self.active_agent_names = ["Supervisor"]
                    for i in range(_workers):
                        agent_id = f"worker_{i+1}"
                        self.agent_grid.add_agent_window(agent_id)
                        self.active_agent_names.append(f"Worker {i+1}")
                self.agents_sidebar.update_agents(self.active_agent_names)

                # Apply previous task handling before execution
                if self.prev_task_mode != "ignore":
                    try:
                        from ..tools.builtin.todo import get_todo_manager
                        mgr = get_todo_manager()
                        if self.prev_task_mode == "only":
                            # Mark all groups not selected as completed to focus on selected ones
                            select = set(self.prev_task_ids or [])
                            for g in mgr.plan.task_groups:
                                if g.group_id not in select:
                                    g.status = 'completed'
                            mgr._save_plan()
                        elif self.prev_task_mode == "include":
                            # Leave existing groups; they will be included. Optionally mark selected as pending explicitly
                            select = set(self.prev_task_ids or [])
                            for g in mgr.plan.task_groups:
                                if g.group_id in select:
                                    g.status = 'pending'
                            mgr._save_plan()
                    except Exception:
                        pass

                # Execute task using programmatic interface in isolated project path
                if not self.coder:
                    if mode == "single":
                        self.coder = create_single_agent_coder()
                    elif mode == "multi":
                        self.coder = create_multi_agent_coder()
                    else:
                        self.coder = EquitrCoder(mode="research")
                    self.coder.on_task_start = self.on_task_start
                    self.coder.on_task_complete = self.on_task_complete
                    self.coder.on_tool_call = self.on_tool_call
                    self.coder.on_message = self.on_message
                    self.coder.on_iteration = self.on_iteration
                self.coder.repo_path = __import__('pathlib').Path(self.project_root).resolve()
                result = await self.coder.execute_task(task_description, config)

                if result.success:
                    # Update status bar elapsed and cost
                    try:
                        self.status_bar.update_elapsed(float(getattr(result, "execution_time", 0.0) or 0.0))
                        self.status_bar.current_cost = float(getattr(result, "cost", 0.0) or 0.0)
                    except Exception:
                        pass
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

        import asyncio as _asyncio
        self._task_handle = _asyncio.create_task(_run())
        # Do not await here to keep UI responsive

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
            try:
                self.todo_sidebar.update_todos([])
            except Exception:
                # Component not mounted yet, ignore
                pass

    # Callback methods
    def on_task_start(self, description: str, mode: str):
        """Called when a task starts."""
        main_window = self.agent_grid.get_agent_window("main")
        main_window.add_status_update(f"Starting {mode} mode task", "info")

    def on_task_complete(self, result: ExecutionResult):
        """Called when a task completes."""
        self.session_cost += result.cost
        main_window = self.agent_grid.get_agent_window("main")

        if result.success:
            main_window.add_status_update("Task execution completed", "success")
        else:
            main_window.add_status_update("Task execution failed", "error")

    def on_iteration(self, iteration: int, cost: float):
        """Called on each iteration to update live cost."""
        self.session_cost += cost
        main_window = self.agent_grid.get_agent_window("main")
        main_window.add_status_update(
            f"Iteration {iteration} | Session Cost: ${self.session_cost:.4f}", "info"
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

    def update_header(self) -> None:
        """Update header with current time and models."""
        current_time = datetime.now().strftime("%H:%M:%S")
        supervisor_text = f"Supervisor: {self.supervisor_model or 'Not set'}"
        worker_text = f"Worker: {self.worker_model or 'Not set'}"
        mode_label = getattr(self.status_bar, "mode", self.mode)
        mode_text = f"Mode: {mode_label}"
        cost_text = f"Session Cost: ${self.session_cost:.4f}"
        agent_text = f"Agents: {self.status_bar.agent_count}"

        header_text = f"⏰ {current_time} | {supervisor_text} | {worker_text} | {mode_text} | {agent_text} | {cost_text}"
        
        if self.custom_header:
            try:
                self.custom_header.update(header_text)
            except Exception:
                pass

    async def show_startup_screen(self) -> None:
        """Show the startup screen with model selection."""
        container = self.query_one("#screen-container")
        container.remove_children()
        
        self.startup_screen = StartupScreen(self.available_models)
        container.mount(self.startup_screen)
        
        # Focus the startup input
        try:
            self.query_one("#startup-input", Input).focus()
        except Exception:
            pass

    async def show_main_screen(self) -> None:
        """Show the main TUI screen."""
        container = self.query_one("#screen-container")
        container.remove_children()
        
        self.main_screen = MainScreen(
            self.todo_sidebar, self.agent_grid, self.agents_sidebar, self.command_bar
        )
        container.mount(self.main_screen)
        
        # Add welcome messages
        main_window = self.agent_grid.get_agent_window("main")
        if main_window:
            main_window.add_status_update("All actions are via slash-commands in the bottom input. Type /help or press 'h' for a command list.", "info")
        
        # Update agents sidebar now that it's mounted
        self.agents_sidebar.update_agents(self.active_agent_names)
        
        # Focus bottom command input
        try:
            self.query_one("#command-input", Input).focus()
        except Exception:
            pass
        
        self.startup_mode = False

    def select_model(self) -> None:
        """Show model selection info since we use startup screen."""
        main_window = self.agent_grid.get_agent_window("main")
        if main_window:
            main_window.add_status_update(f"Current setup: Mode={self.mode}, Supervisor={self.supervisor_model}, Worker={self.worker_model}. Use /set to change.", "info")
            main_window.add_status_update("Available models: " + ", ".join(self.available_models[:10]) + ("..." if len(self.available_models) > 10 else ""), "info")

    def update_pricing_display(self) -> None:
        """Update pricing info (shown in header now)."""
        self.update_header()


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
