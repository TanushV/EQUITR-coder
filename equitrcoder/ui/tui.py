"""Textual TUI interface for EQUITR Coder."""

from datetime import datetime
from typing import Dict, List, Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)
from textual.reactive import reactive
from textual.binding import Binding
from rich.console import RenderableType
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config, config_manager
from ..core.orchestrator import AgentOrchestrator
from ..core.session import SessionManagerV2


class ChatMessage(Static):
    """A single chat message widget."""

    def __init__(self, role: str, content: str, timestamp: datetime, **kwargs):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Compose the message widget."""
        role_color = "blue" if self.role == "user" else "green"
        time_str = self.timestamp.strftime("%H:%M:%S")

        with Container(classes="message"):
            yield Label(
                f"[{role_color}]{self.role.upper()}[/] [{time_str}]",
                classes="message-header",
            )
            yield Static(self.content, classes="message-content")


class TaskProgress(Static):
    """Widget to display task progress."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress_data = None

    def update_progress(self, progress_data: Dict[str, Any]):
        """Update the progress display."""
        self.progress_data = progress_data
        self.refresh()

    def render(self) -> RenderableType:
        """Render the task progress."""
        if not self.progress_data:
            return Panel("No active tasks", title="Task Progress")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Task ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Agent", style="yellow")
        table.add_column("Progress", style="blue")

        for task in self.progress_data.get("tasks", []):
            status_emoji = {
                "todo": "⏳",
                "in_progress": "🔄",
                "done": "✅",
                "failed": "❌",
            }.get(task["status"], "❓")

            table.add_row(
                task["id"],
                f"{status_emoji} {task['status']}",
                task.get("assigned_agent", "N/A"),
                f"{task.get('progress', 0):.1f}%",
            )

        summary = self.progress_data.get("summary", {})
        progress_text = f"Overall: {summary.get('progress', 0):.1f}% ({summary.get('completed', 0)}/{summary.get('total', 0)} tasks)"

        return Panel(
            table, title=f"Task Progress - {progress_text}", border_style="bright_blue"
        )


class ModelSelector(Static):
    """Widget for selecting models."""

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the model selector."""
        with Vertical():
            yield Label("Model Selection", classes="panel-title")

            # Current model display
            current_model = self.config.llm.active_model
            model_info = self.config.llm.models.get(current_model, {})
            current_display = f"{current_model}: {model_info.get('model', 'Unknown')}"
            yield Label(
                f"Current: {current_display}",
                id="current-model",
                classes="current-model",
            )

            # Model selector
            model_options = [(name, name) for name in self.config.llm.models.keys()]
            yield Select(
                options=model_options,
                value=current_model,
                id="model-select",
                classes="model-select",
            )

            # Model details
            yield Label("Details:", classes="details-label")
            yield Static(
                self._format_model_details(current_model),
                id="model-details",
                classes="model-details",
            )

    def _format_model_details(self, model_name: str) -> str:
        """Format model details for display."""
        if model_name not in self.config.llm.models:
            return "Model not found"

        model_config = self.config.llm.models[model_name]
        details = []
        details.append(f"Provider: {model_config.get('provider', 'Unknown')}")
        details.append(f"Model: {model_config.get('model', 'Unknown')}")
        details.append(f"Temperature: {model_config.get('temperature', 'N/A')}")
        details.append(f"Max Tokens: {model_config.get('max_tokens', 'N/A')}")

        return "\n".join(details)

    def update_model_info(self, model_name: str) -> None:
        """Update the displayed model information."""
        if model_name in self.config.llm.models:
            model_info = self.config.llm.models[model_name]
            current_display = f"{model_name}: {model_info.get('model', 'Unknown')}"

            self.query_one("#current-model", Label).update(
                f"Current: {current_display}"
            )
            self.query_one("#model-details", Static).update(
                self._format_model_details(model_name)
            )


class SessionPanel(Static):
    """Panel for session management."""

    def __init__(self, session_manager: SessionManagerV2, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = session_manager

    def compose(self) -> ComposeResult:
        """Compose the session panel."""
        with Vertical():
            yield Label("Sessions", classes="panel-title")
            yield Button("New Session", id="new-session", classes="session-button")
            yield Button("Load Session", id="load-session", classes="session-button")
            yield Button(
                "Delete Session", id="delete-session", classes="session-button"
            )

            with ScrollableContainer(classes="session-list"):
                yield DataTable(id="session-table")

    def on_mount(self) -> None:
        """Initialize the session table."""
        table = self.query_one("#session-table", DataTable)
        table.add_columns("ID", "Created", "Tasks", "Cost")
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        """Refresh the session list."""
        table = self.query_one("#session-table", DataTable)
        table.clear()

        sessions = self.session_manager.list_sessions()
        for session in sessions:
            table.add_row(
                session["session_id"][:8],
                session["created_at"].strftime("%m/%d %H:%M"),
                str(session["task_count"]),
                f"${session['cost']:.2f}",
            )


class EquitrTUI(App):
    """Main TUI application for EQUITR Coder."""

    CSS = """
    .message {
        margin: 1 0;
        padding: 1;
        border: solid $primary;
    }

    .message-header {
        text-style: bold;
        margin-bottom: 1;
    }

    .message-content {
        margin-left: 2;
        color: $text;
    }

    .input-container {
        height: 4;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
    }

    .chat-container {
        height: 1fr;
        border: solid $primary;
        margin: 1;
    }

    .sidebar {
        width: 30;
        dock: left;
        background: $surface;
        border-right: solid $primary;
    }

    .panel-title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }

    .session-button {
        width: 100%;
        margin: 0 0 1 0;
    }

    .session-list {
        height: 1fr;
        border: solid $primary;
        margin: 1 0;
    }

    .status-bar {
        height: 3;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
    }

    .progress-panel {
        height: 1fr;
        margin: 1 0;
    }

    .model-panel {
        height: auto;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
    }

    .current-model {
        color: $accent;
        margin: 0 0 1 0;
    }

    .model-select {
        margin: 0 0 1 0;
    }

    .details-label {
        text-style: bold;
        margin: 1 0 0 0;
    }

    .model-details {
        color: $text-muted;
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_session", "New Session", show=True),
        Binding("ctrl+l", "load_session", "Load Session", show=True),
        Binding("ctrl+s", "save_session", "Save Session", show=True),
        Binding("ctrl+m", "focus_model_selector", "Select Model", show=True),
        Binding("f1", "toggle_sidebar", "Toggle Sidebar", show=True),
    ]

    current_session_id: reactive[str] = reactive("default")
    is_processing: reactive[bool] = reactive(False)
    sidebar_visible: reactive[bool] = reactive(True)

    def __init__(
        self,
        config: Config,
        supervisor_model: Optional[str] = None,
        worker_model: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.config = config
        self.supervisor_model = supervisor_model
        self.worker_model = worker_model
        self.session_manager = SessionManagerV2(config.session.session_dir)
        self.orchestrator = AgentOrchestrator(
            config=config,
            session_manager=self.session_manager,
            supervisor_model=supervisor_model,
            worker_model=worker_model,
        )
        self.messages: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        """Compose the main UI."""
        yield Header(show_clock=True)

        with Horizontal():
            # Sidebar
            with Container(classes="sidebar", id="sidebar"):
                yield SessionPanel(self.session_manager, id="session-panel")
                yield ModelSelector(
                    self.config, id="model-selector", classes="model-panel"
                )
                yield TaskProgress(id="task-progress", classes="progress-panel")

            # Main content area
            with Vertical():
                # Chat area with tabs
                with TabbedContent(id="main-tabs"):
                    with TabPane("Chat", id="chat-tab"):
                        with ScrollableContainer(
                            classes="chat-container", id="chat-log"
                        ):
                            yield Static(
                                "Welcome to EQUITR Coder! Type your message below.",
                                classes="welcome-message",
                            )

                    with TabPane("Session Info", id="session-tab"):
                        yield Static(
                            "Session information will appear here.", id="session-info"
                        )

                # Input area
                with Container(classes="input-container"):
                    with Horizontal():
                        yield Input(
                            placeholder="Type your message...", id="message-input"
                        )
                        yield Button("Send", id="send-button", variant="primary")
                        yield Button("Clear", id="clear-button", variant="error")

        # Status bar
        with Container(classes="status-bar"):
            yield Label(f"Session: {self.current_session_id}", id="status-session")
            yield Label("Ready", id="status-message")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app."""
        self.query_one("#message-input", Input).focus()
        self.load_session_messages()

    def watch_current_session_id(self, session_id: str) -> None:
        """Update UI when session changes."""
        self.query_one("#status-session", Label).update(f"Session: {session_id}")
        self.load_session_messages()

    def watch_is_processing(self, processing: bool) -> None:
        """Update UI when processing state changes."""
        status_label = self.query_one("#status-message", Label)
        send_button = self.query_one("#send-button", Button)
        message_input = self.query_one("#message-input", Input)

        if processing:
            status_label.update("Processing...")
            send_button.disabled = True
            message_input.disabled = True
        else:
            status_label.update("Ready")
            send_button.disabled = False
            message_input.disabled = False

    def watch_sidebar_visible(self, visible: bool) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        if visible:
            sidebar.styles.display = "block"
        else:
            sidebar.styles.display = "none"

    def load_session_messages(self) -> None:
        """Load messages from current session."""
        chat_log = self.query_one("#chat-log", ScrollableContainer)
        chat_log.remove_children()

        # Load session data
        session_data = self.session_manager.get_session_data(self.current_session_id)
        if session_data and session_data.messages:
            for msg in session_data.messages:
                timestamp = datetime.fromisoformat(
                    msg.get("timestamp", datetime.now().isoformat())
                )
                chat_message = ChatMessage(
                    role=msg["role"], content=msg["content"], timestamp=timestamp
                )
                chat_log.mount(chat_message)
        else:
            chat_log.mount(
                Static("No messages in this session.", classes="welcome-message")
            )

        # Scroll to bottom
        chat_log.scroll_end()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send-button":
            await self.send_message()
        elif event.button.id == "clear-button":
            await self.clear_chat()
        elif event.button.id == "new-session":
            await self.action_new_session()
        elif event.button.id == "load-session":
            await self.action_load_session()
        elif event.button.id == "delete-session":
            await self.action_delete_session()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "message-input":
            await self.send_message()

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle model selection changes."""
        if event.select.id == "model-select":
            new_model = event.value
            if new_model and new_model in self.config.llm.models:
                # Switch to the new model
                self.config = config_manager.switch_model(self.config, new_model)

                # Update the model selector display
                model_selector = self.query_one("#model-selector", ModelSelector)
                model_selector.update_model_info(new_model)

                # Recreate the orchestrator with the new model
                self.orchestrator = AgentOrchestrator(
                    config=self.config,
                    session_manager=self.session_manager,
                    supervisor_model=self.supervisor_model,
                    worker_model=self.worker_model,
                )

                # Update status
                self.query_one("#status-message", Label).update(
                    f"Switched to model: {new_model}"
                )

                # Save the configuration
                config_manager.save_user_config(self.config)

    async def send_message(self) -> None:
        """Send a message and get response."""
        message_input = self.query_one("#message-input", Input)
        message = message_input.value.strip()

        if not message:
            return

        # Clear input
        message_input.value = ""

        # Add user message to chat
        self.add_message("user", message)

        # Set processing state
        self.is_processing = True

        try:
            # Get response from orchestrator
            response = await self.orchestrator.run(message, self.current_session_id)

            # Add assistant response
            self.add_message("assistant", response)

            # Update task progress if available
            if (
                hasattr(self.orchestrator, "supervisor")
                and self.orchestrator.supervisor
            ):
                progress = await self.orchestrator.supervisor.get_status()
                task_progress = self.query_one("#task-progress", TaskProgress)
                task_progress.update_progress(progress)

        except Exception as e:
            self.add_message("assistant", f"Error: {str(e)}")

        finally:
            self.is_processing = False

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat log."""
        chat_log = self.query_one("#chat-log", ScrollableContainer)
        timestamp = datetime.now()

        chat_message = ChatMessage(role=role, content=content, timestamp=timestamp)
        chat_log.mount(chat_message)
        chat_log.scroll_end()

    async def clear_chat(self) -> None:
        """Clear the chat log."""
        chat_log = self.query_one("#chat-log", ScrollableContainer)
        chat_log.remove_children()
        chat_log.mount(Static("Chat cleared.", classes="welcome-message"))

    async def action_new_session(self) -> None:
        """Create a new session."""
        new_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_manager.create_session(new_session_id)
        self.current_session_id = new_session_id

        # Refresh session panel
        session_panel = self.query_one("#session-panel", SessionPanel)
        session_panel.refresh_sessions()

    async def action_load_session(self) -> None:
        """Load an existing session."""
        # For now, just switch to the first available session
        sessions = self.session_manager.list_sessions()
        if sessions:
            self.current_session_id = sessions[0]["session_id"]

            # Refresh session panel
            session_panel = self.query_one("#session-panel", SessionPanel)
            session_panel.refresh_sessions()

    async def action_delete_session(self) -> None:
        """Delete the current session."""
        if self.current_session_id != "default":
            self.session_manager.delete_session(self.current_session_id)
            self.current_session_id = "default"

            # Refresh session panel
            session_panel = self.query_one("#session-panel", SessionPanel)
            session_panel.refresh_sessions()

    async def action_save_session(self) -> None:
        """Save the current session."""
        # Session is auto-saved, but we can force a save
        await self.session_manager.save_session(self.current_session_id)

    async def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.sidebar_visible = not self.sidebar_visible

    async def action_focus_model_selector(self) -> None:
        """Focus the model selector."""
        model_select = self.query_one("#model-select", Select)
        model_select.focus()

    async def action_quit(self) -> None:
        """Quit the application."""
        # Ensure session is saved before quitting
        await self.session_manager.save_session(self.current_session_id)
        self.exit()


async def run_tui(
    config: Config,
    supervisor_model: Optional[str] = None,
    worker_model: Optional[str] = None,
) -> None:
    """Run the TUI application."""
    app = EquitrTUI(
        config, supervisor_model=supervisor_model, worker_model=worker_model
    )
    await app.run_async()


def launch_tui(mode: str = "single") -> int:
    """Launch the TUI interface."""
    try:
        import asyncio
        from ..core.config import config_manager

        # Load default config
        config = config_manager.load_config()

        # Run the TUI
        asyncio.run(run_tui(config))
        return 0

    except ImportError:
        print(
            "TUI dependencies not available. Install with: pip install equitrcoder[tui]"
        )
        return 1
    except Exception as e:
        print(f"TUI error: {e}")
        return 1
