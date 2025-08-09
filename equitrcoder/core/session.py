import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel

from ..providers.openrouter import Message


class TaskItem(BaseModel):
    """Individual task in a project checklist."""

    id: str
    description: str
    status: str = "todo"  # todo, in_progress, done, failed
    files: List[str] = []
    created_at: datetime
    updated_at: datetime


class SessionData(BaseModel):
    """Enhanced session data with checklist and cost tracking."""

    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []
    metadata: Dict[str, Any] = {}

    # New v1.1 fields
    checklist: List[TaskItem] = []
    cost: float = 0.0
    total_tokens: int = 0
    iteration_count: int = 0


class SessionManagerV2:
    """Enhanced session manager with multi-session support and caching."""

    def __init__(self, session_dir: str = "~/.EQUITR-coder/sessions"):
        self.session_dir = Path(session_dir).expanduser()
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionData] = None

        # Memory cache for sessions
        self._session_cache: Dict[str, SessionData] = {}
        self._dirty_sessions: Set[str] = set()

        # Background task for periodic saves
        self._save_task: Optional[asyncio.Task] = None
        self._start_periodic_save()

    def _start_periodic_save(self):
        """Start background task for periodic session saves."""
        try:
            if self._save_task is None or self._save_task.done():
                self._save_task = asyncio.create_task(self._periodic_save_loop())
        except RuntimeError:
            # No event loop running, skip background task
            pass

    async def _periodic_save_loop(self):
        """Background loop to save dirty sessions every 30 seconds."""
        while True:
            try:
                await asyncio.sleep(30)  # Save every 30 seconds
                await self._flush_dirty_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in periodic save: {e}")

    async def _flush_dirty_sessions(self):
        """Save all dirty sessions to disk."""
        for session_id in list(self._dirty_sessions):
            if session_id in self._session_cache:
                session = self._session_cache[session_id]
                await self._save_session_to_disk(session)
                self._dirty_sessions.discard(session_id)

    def create_session(self, session_id: Optional[str] = None) -> SessionData:
        """Create a new session with optional custom ID."""
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]  # Short UUID for readability

        now = datetime.now()
        session = SessionData(session_id=session_id, created_at=now, updated_at=now)

        self.current_session = session
        self._session_cache[session_id] = session
        self._dirty_sessions.add(session_id)
        return session

    def load_session(self, session_id: str) -> Optional[SessionData]:
        """Load an existing session with caching."""
        # Check cache first
        if session_id in self._session_cache:
            session = self._session_cache[session_id]
            self.current_session = session
            return session

        # Load from disk
        session_file = self.session_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            with open(session_file, "r") as f:
                data = json.load(f)

            # Convert message dicts back to Message objects
            messages = [Message(**msg) for msg in data.get("messages", [])]
            data["messages"] = messages

            # Convert checklist items back to TaskItem objects
            checklist = [TaskItem(**item) for item in data.get("checklist", [])]
            data["checklist"] = checklist

            # Convert datetime strings back to datetime objects
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

            session = SessionData(**data)

            # Cache the session
            self._session_cache[session_id] = session
            self.current_session = session
            return session

        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return None

    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session."""
        session = self.load_session(session_id)
        if session:
            self.current_session = session
            return True
        return False

    async def _save_session_to_disk(self, session: SessionData):
        """Save session to disk (async version)."""
        session.updated_at = datetime.now()
        session_file = self.session_dir / f"{session.session_id}.json"

        try:
            # Convert to dict for JSON serialization
            data = session.model_dump()

            # Convert datetime objects to ISO strings
            data["created_at"] = session.created_at.isoformat()
            data["updated_at"] = session.updated_at.isoformat()

            # Convert checklist items to dicts
            checklist_data = []
            for item in session.checklist:
                item_dict = item.model_dump()
                item_dict["created_at"] = item.created_at.isoformat()
                item_dict["updated_at"] = item.updated_at.isoformat()
                checklist_data.append(item_dict)
            data["checklist"] = checklist_data

            # Use aiofiles for async file operations
            import aiofiles

            async with aiofiles.open(session_file, "w") as f:
                await f.write(json.dumps(data, indent=2))

        except Exception as e:
            print(f"Failed to save session {session.session_id}: {e}")

    def save_session(self, session: SessionData):
        """Save session (sync version - marks as dirty for later save)."""
        session.updated_at = datetime.now()
        self._session_cache[session.session_id] = session
        self._dirty_sessions.add(session.session_id)

        # If no background task is running, save immediately
        if self._save_task is None:
            self._save_session_sync(session)

    def _save_session_sync(self, session: SessionData):
        """Save session to disk synchronously."""
        session_file = self.session_dir / f"{session.session_id}.json"

        try:
            # Convert to dict for JSON serialization
            data = session.model_dump()

            # Convert datetime objects to ISO strings
            data["created_at"] = session.created_at.isoformat()
            data["updated_at"] = session.updated_at.isoformat()

            # Convert checklist items to dicts
            checklist_data = []
            for item in session.checklist:
                item_dict = item.model_dump()
                item_dict["created_at"] = item.created_at.isoformat()
                item_dict["updated_at"] = item.updated_at.isoformat()
                checklist_data.append(item_dict)
            data["checklist"] = checklist_data

            with open(session_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Failed to save session {session.session_id}: {e}")

    def add_message(self, message: Message):
        """Add a message to the current session."""
        if self.current_session is None:
            self.create_session()
        assert self.current_session is not None

        self.current_session.messages.append(message)
        self.save_session(self.current_session)

    def get_messages(self) -> List[Message]:
        """Get all messages from the current session."""
        if self.current_session is None:
            return []
        return self.current_session.messages.copy()

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions with metadata."""
        sessions = []

        # Get sessions from cache
        for session_id, session in self._session_cache.items():
            sessions.append(
                {
                    "session_id": session_id,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": len(session.messages),
                    "cost": session.cost,
                    "task_count": len(session.checklist),
                    "status": "cached",
                }
            )

        # Get sessions from disk that aren't cached
        for file in self.session_dir.glob("*.json"):
            session_id = file.stem
            if session_id not in self._session_cache:
                try:
                    with open(file, "r") as f:
                        data = json.load(f)

                    sessions.append(
                        {
                            "session_id": session_id,
                            "created_at": datetime.fromisoformat(
                                data.get("created_at", "")
                            ),
                            "updated_at": datetime.fromisoformat(
                                data.get("updated_at", "")
                            ),
                            "message_count": len(data.get("messages", [])),
                            "cost": data.get("cost", 0.0),
                            "task_count": len(data.get("checklist", [])),
                            "status": "on_disk",
                        }
                    )
                except Exception as e:
                    print(f"Error reading session {session_id}: {e}")

        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from both cache and disk."""
        # Remove from cache
        if session_id in self._session_cache:
            del self._session_cache[session_id]

        if session_id in self._dirty_sessions:
            self._dirty_sessions.remove(session_id)

        # Remove from disk
        session_file = self.session_dir / f"{session_id}.json"
        try:
            if session_file.exists():
                session_file.unlink()
            return True
        except Exception as e:
            print(f"Failed to delete session {session_id}: {e}")
            return False

    # ---------------------------------------------------------------------
    # Backwards-compatibility helpers (older UI expected these)
    # ---------------------------------------------------------------------
    def get_session_data(self, session_id: str):  # noqa: D401
        """Return the SessionData for *session_id* (create if not exists)."""
        session = self.load_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session

    def clear_current_session(self):
        """Clear the current session messages."""
        if self.current_session:
            self.current_session.messages.clear()
            self.save_session(self.current_session)

    # New methods for v1.1 features
    def add_task(self, description: str, files: Optional[List[str]] = None) -> str:
        """Add a task to the current session's checklist."""
        if self.current_session is None:
            self.create_session()
        assert self.current_session is not None

        task_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        task = TaskItem(
            id=task_id,
            description=description,
            files=files or [],
            created_at=now,
            updated_at=now,
        )

        self.current_session.checklist.append(task)
        self.save_session(self.current_session)
        return task_id

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update the status of a task in the current session."""
        if self.current_session is None:
            return False

        for task in self.current_session.checklist:
            if task.id == task_id:
                task.status = status
                task.updated_at = datetime.now()
                self.save_session(self.current_session)
                return True
        return False

    def get_checklist(self) -> List[TaskItem]:
        """Get the current session's checklist."""
        if self.current_session is None:
            return []
        return self.current_session.checklist.copy()

    def update_cost(self, additional_cost: float, additional_tokens: int = 0):
        """Update the cost and token count for the current session."""
        if self.current_session is None:
            self.create_session()
        assert self.current_session is not None

        self.current_session.cost += additional_cost
        self.current_session.total_tokens += additional_tokens
        self.save_session(self.current_session)

    def increment_iteration(self):
        """Increment the iteration count for the current session."""
        if self.current_session is None:
            self.create_session()
        assert self.current_session is not None

        self.current_session.iteration_count += 1
        self.save_session(self.current_session)

    async def cleanup(self):
        """Cleanup method to save all dirty sessions and stop background tasks."""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass

        await self._flush_dirty_sessions()


# Backward compatibility alias
SessionManager = SessionManagerV2
