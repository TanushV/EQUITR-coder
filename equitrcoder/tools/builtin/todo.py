# equitrcoder/tools/builtin/todo.py

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
import uuid

# --- NEW DATA STRUCTURES ---

class TodoItem(BaseModel):
    id: str = Field(default_factory=lambda: f"todo_{uuid.uuid4().hex[:8]}")
    title: str
    status: str = "pending"  # pending, in_progress, completed, cancelled

class TaskGroup(BaseModel):
    group_id: str
    specialization: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    todos: List[TodoItem] = Field(default_factory=list)

class TodoList(BaseModel):
    task_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    task_groups: List[TaskGroup] = Field(default_factory=list)

# --- REBUILT TODO MANAGER ---

class TodoManager:
    """Manages a structured list of Task Groups with dependencies."""
    
    def __init__(self, todo_file: str = ".EQUITR_todos.json"):
        self.todo_file = Path(todo_file)
        self._load_todos()
    
    def _load_todos(self):
        if self.todo_file.exists() and self.todo_file.stat().st_size > 0:
            try:
                data = json.loads(self.todo_file.read_text())
                self.todo_list = TodoList(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not load or parse todos from {self.todo_file}: {e}")
                self.todo_list = TodoList(task_name="default_task")
        else:
            self.todo_list = TodoList(task_name="default_task")
    
    def _save_todos(self):
        try:
            self.todo_file.write_text(self.todo_list.model_dump_json(indent=2))
        except Exception as e:
            print(f"Warning: Could not save todos to {self.todo_file}: {e}")
    
    def create_task_group(self, group_id: str, specialization: str, description: str, dependencies: List[str]) -> TaskGroup:
        group = TaskGroup(group_id=group_id, specialization=specialization, description=description, dependencies=dependencies)
        self.todo_list.task_groups.append(group)
        self._save_todos()
        return group
    
    def add_todo_to_group(self, group_id: str, title: str) -> Optional[TodoItem]:
        for group in self.todo_list.task_groups:
            if group.group_id == group_id:
                todo = TodoItem(title=title)
                group.todos.append(todo)
                self._save_todos()
                return todo
        return None
    
    def get_task_group(self, group_id: str) -> Optional[TaskGroup]:
        for group in self.todo_list.task_groups:
            if group.group_id == group_id:
                return group
        return None
    
    def update_task_group_status(self, group_id: str, status: str) -> bool:
        group = self.get_task_group(group_id)
        if group:
            group.status = status
            self._save_todos()
            return True
        return False
    
    def update_todo_status(self, todo_id: str, status: str) -> Optional[TaskGroup]:
        for group in self.todo_list.task_groups:
            for todo in group.todos:
                if todo.id == todo_id:
                    todo.status = status
                    
                    # Check if the parent group is now completed
                    all_done = all(t.status == 'completed' for t in group.todos)
                    if all_done and group.status != 'completed':
                        group.status = 'completed'
                        print(f"🎉 Task Group '{group.group_id}' completed!")
                    
                    self._save_todos()
                    return group
        return None
    
    def get_next_runnable_groups(self) -> List[TaskGroup]:
        """Finds all pending groups whose dependencies are met."""
        completed_group_ids = {g.group_id for g in self.todo_list.task_groups if g.status == 'completed'}
        runnable_groups = []
        for group in self.todo_list.task_groups:
            if group.status == 'pending':
                if set(group.dependencies).issubset(completed_group_ids):
                    runnable_groups.append(group)
        return runnable_groups
    
    def are_all_tasks_complete(self) -> bool:
        return all(g.status in ['completed', 'failed'] for g in self.todo_list.task_groups)

# --- UPDATED TOOLS ---

from ..base import Tool, ToolResult

class ListTaskGroupsArgs(BaseModel):
    pass

class ListTaskGroups(Tool):
    def get_name(self) -> str: return "list_task_groups"
    def get_description(self) -> str: return "Lists the high-level task groups, their specializations, dependencies, and statuses."
    def get_args_schema(self) -> Type[BaseModel]: return ListTaskGroupsArgs
    async def run(self, **kwargs) -> ToolResult:
        groups_summary = [
            {
                "group_id": g.group_id,
                "specialization": g.specialization,
                "description": g.description,
                "status": g.status,
                "dependencies": g.dependencies,
                "todo_count": len(g.todos)
            }
            for g in todo_manager.todo_list.task_groups
        ]
        return ToolResult(success=True, data=groups_summary)

class ListTodosInGroupArgs(BaseModel):
    group_id: str = Field(..., description="The ID of the task group to inspect.")

class ListTodosInGroup(Tool):
    def get_name(self) -> str: return "list_todos_in_group"
    def get_description(self) -> str: return "Lists the detailed sub-tasks (todos) within a specific task group."
    def get_args_schema(self) -> Type[BaseModel]: return ListTodosInGroupArgs
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        group = todo_manager.get_task_group(args.group_id)
        if not group:
            return ToolResult(success=False, error=f"Task group '{args.group_id}' not found.")
        
        todos_summary = [{"id": t.id, "title": t.title, "status": t.status} for t in group.todos]
        return ToolResult(success=True, data=todos_summary)

class UpdateTodoStatusArgs(BaseModel):
    todo_id: str = Field(..., description="The ID of the todo to update.")
    status: str = Field(..., description="The new status, typically 'completed'.")

class UpdateTodoStatus(Tool):
    def get_name(self) -> str: return "update_todo_status"
    def get_description(self) -> str: return "Updates the status of a specific todo item. Marking all todos in a group as 'completed' will complete the group."
    def get_args_schema(self) -> Type[BaseModel]: return UpdateTodoStatusArgs
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        updated_group = todo_manager.update_todo_status(args.todo_id, args.status)
        if not updated_group:
            return ToolResult(success=False, error=f"Todo with ID '{args.todo_id}' not found.")
        return ToolResult(success=True, data=f"Todo '{args.todo_id}' updated. Parent group '{updated_group.group_id}' is now '{updated_group.status}'.")

# Global instance and manager function
todo_manager = TodoManager()

def set_global_todo_file(todo_file: str):
    global todo_manager
    todo_manager = TodoManager(todo_file=todo_file)
    print(f"📋 Set global todo manager to use session-local file: {todo_file}")