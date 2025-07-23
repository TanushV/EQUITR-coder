import json
from datetime import datetime
from pathlib import Path
from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..base import Tool, ToolResult


class TodoItem(BaseModel):
    id: str
    title: str
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, cancelled
    priority: str = "medium"  # low, medium, high, urgent
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None


class TodoList(BaseModel):
    todos: List[TodoItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateTodoArgs(BaseModel):
    title: str = Field(..., description="Title of the todo item")
    description: str = Field(default="", description="Detailed description of the todo")
    priority: str = Field(
        default="medium", description="Priority: low, medium, high, urgent"
    )
    due_date: Optional[str] = Field(
        default=None, description="Due date in ISO format (YYYY-MM-DD)"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    assignee: Optional[str] = Field(
        default=None, description="Person assigned to this todo"
    )


class UpdateTodoArgs(BaseModel):
    todo_id: str = Field(..., description="ID of the todo to update")
    title: Optional[str] = Field(default=None, description="New title")
    description: Optional[str] = Field(default=None, description="New description")
    status: Optional[str] = Field(
        default=None,
        description="New status: pending, in_progress, completed, cancelled",
    )
    priority: Optional[str] = Field(
        default=None, description="New priority: low, medium, high, urgent"
    )
    due_date: Optional[str] = Field(
        default=None, description="New due date in ISO format"
    )
    tags: Optional[List[str]] = Field(default=None, description="New tags")
    assignee: Optional[str] = Field(default=None, description="New assignee")


class DeleteTodoArgs(BaseModel):
    todo_id: str = Field(..., description="ID of the todo to delete")


class ListTodosArgs(BaseModel):
    status: Optional[str] = Field(default=None, description="Filter by status")
    priority: Optional[str] = Field(default=None, description="Filter by priority")
    assignee: Optional[str] = Field(default=None, description="Filter by assignee")
    tag: Optional[str] = Field(default=None, description="Filter by tag")


class TodoManager:
    """Manages todo lists with persistence."""

    def __init__(self, todo_file: str = ".EQUITR_todos.json"):
        self.todo_file = Path(todo_file)
        self._load_todos()

    def _load_todos(self):
        """Load todos from file."""
        if self.todo_file.exists():
            try:
                with open(self.todo_file, "r") as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    for todo_data in data.get("todos", []):
                        todo_data["created_at"] = datetime.fromisoformat(
                            todo_data["created_at"]
                        )
                        todo_data["updated_at"] = datetime.fromisoformat(
                            todo_data["updated_at"]
                        )
                        if todo_data.get("due_date"):
                            todo_data["due_date"] = datetime.fromisoformat(
                                todo_data["due_date"]
                            )
                    self.todo_list = TodoList(**data)
            except Exception as e:
                print(f"Warning: Could not load todos: {e}")
                self.todo_list = TodoList()
        else:
            self.todo_list = TodoList()

    def _save_todos(self):
        """Save todos to file."""
        try:
            # Convert datetime objects to strings for JSON serialization
            data = self.todo_list.model_dump()
            for todo_data in data["todos"]:
                todo_data["created_at"] = todo_data["created_at"].isoformat()
                todo_data["updated_at"] = todo_data["updated_at"].isoformat()
                if todo_data.get("due_date"):
                    todo_data["due_date"] = todo_data["due_date"].isoformat()

            with open(self.todo_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save todos: {e}")

    def create_todo(self, **kwargs) -> TodoItem:
        """Create a new todo item."""
        now = datetime.now()

        # Generate ID
        todo_id = f"todo_{now.strftime('%Y%m%d_%H%M%S')}_{len(self.todo_list.todos)}"

        # Parse due date if provided
        due_date = None
        if kwargs.get("due_date"):
            try:
                due_date = datetime.fromisoformat(kwargs["due_date"])
            except ValueError:
                pass

        todo = TodoItem(
            id=todo_id,
            title=kwargs["title"],
            description=kwargs.get("description", ""),
            priority=kwargs.get("priority", "medium"),
            created_at=now,
            updated_at=now,
            due_date=due_date,
            tags=kwargs.get("tags", []),
            assignee=kwargs.get("assignee"),
        )

        self.todo_list.todos.append(todo)
        self._save_todos()
        return todo

    def update_todo(self, todo_id: str, **kwargs) -> Optional[TodoItem]:
        """Update an existing todo item."""
        todo = self.get_todo(todo_id)
        if not todo:
            return None

        now = datetime.now()

        # Update fields
        for field, value in kwargs.items():
            if value is not None:
                if field == "due_date" and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value)
                    except ValueError:
                        continue
                setattr(todo, field, value)

        todo.updated_at = now
        self._save_todos()
        return todo

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo item."""
        for i, todo in enumerate(self.todo_list.todos):
            if todo.id == todo_id:
                del self.todo_list.todos[i]
                self._save_todos()
                return True
        return False

    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """Get a specific todo by ID."""
        for todo in self.todo_list.todos:
            if todo.id == todo_id:
                return todo
        return None

    def list_todos(self, **filters) -> List[TodoItem]:
        """List todos with optional filters."""
        todos = self.todo_list.todos

        if filters.get("status"):
            todos = [t for t in todos if t.status == filters["status"]]
        if filters.get("priority"):
            todos = [t for t in todos if t.priority == filters["priority"]]
        if filters.get("assignee"):
            todos = [t for t in todos if t.assignee == filters["assignee"]]
        if filters.get("tag"):
            todos = [t for t in todos if filters["tag"] in t.tags]

        return todos


# Global todo manager instance
todo_manager = TodoManager()


class CreateTodo(Tool):
    def get_name(self) -> str:
        return "create_todo"

    def get_description(self) -> str:
        return "Create a new todo item"

    def get_args_schema(self) -> Type[BaseModel]:
        return CreateTodoArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            todo = todo_manager.create_todo(**args.model_dump())

            return ToolResult(
                success=True,
                data={
                    "todo": {
                        "id": todo.id,
                        "title": todo.title,
                        "description": todo.description,
                        "status": todo.status,
                        "priority": todo.priority,
                        "created_at": todo.created_at.isoformat(),
                        "due_date": todo.due_date.isoformat()
                        if todo.due_date
                        else None,
                        "tags": todo.tags,
                        "assignee": todo.assignee,
                    }
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class UpdateTodo(Tool):
    def get_name(self) -> str:
        return "update_todo"

    def get_description(self) -> str:
        return "Update an existing todo item"

    def get_args_schema(self) -> Type[BaseModel]:
        return UpdateTodoArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Extract todo_id and remove it from kwargs for update
            todo_id = args.todo_id
            update_data = {
                k: v
                for k, v in args.model_dump().items()
                if k != "todo_id" and v is not None
            }

            todo = todo_manager.update_todo(todo_id, **update_data)

            if not todo:
                return ToolResult(
                    success=False, error=f"Todo with ID '{todo_id}' not found"
                )

            return ToolResult(
                success=True,
                data={
                    "todo": {
                        "id": todo.id,
                        "title": todo.title,
                        "description": todo.description,
                        "status": todo.status,
                        "priority": todo.priority,
                        "updated_at": todo.updated_at.isoformat(),
                        "due_date": todo.due_date.isoformat()
                        if todo.due_date
                        else None,
                        "tags": todo.tags,
                        "assignee": todo.assignee,
                    }
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteTodo(Tool):
    def get_name(self) -> str:
        return "delete_todo"

    def get_description(self) -> str:
        return "Delete a todo item"

    def get_args_schema(self) -> Type[BaseModel]:
        return DeleteTodoArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            success = todo_manager.delete_todo(args.todo_id)

            if not success:
                return ToolResult(
                    success=False, error=f"Todo with ID '{args.todo_id}' not found"
                )

            return ToolResult(
                success=True,
                data={"message": f"Todo '{args.todo_id}' deleted successfully"},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListTodos(Tool):
    def get_name(self) -> str:
        return "list_todos"

    def get_description(self) -> str:
        return "List todos with optional filters"

    def get_args_schema(self) -> Type[BaseModel]:
        return ListTodosArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            filters = {k: v for k, v in args.model_dump().items() if v is not None}
            todos = todo_manager.list_todos(**filters)

            todo_list = []
            for todo in todos:
                todo_list.append(
                    {
                        "id": todo.id,
                        "title": todo.title,
                        "description": todo.description,
                        "status": todo.status,
                        "priority": todo.priority,
                        "created_at": todo.created_at.isoformat(),
                        "updated_at": todo.updated_at.isoformat(),
                        "due_date": todo.due_date.isoformat()
                        if todo.due_date
                        else None,
                        "tags": todo.tags,
                        "assignee": todo.assignee,
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "todos": todo_list,
                    "count": len(todo_list),
                    "filters_applied": filters,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
