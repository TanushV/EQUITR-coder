# equitrcoder/tools/builtin/todo.py

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
import uuid

# --- NEW DATA STRUCTURES ---
# This defines the new, hierarchical structure for your todo plans.

class TodoItem(BaseModel):
    """Represents a single, actionable sub-task within a Task Group."""
    id: str = Field(default_factory=lambda: f"todo_{uuid.uuid4().hex[:8]}")
    title: str
    status: str = "pending"  # Can be 'pending' or 'completed'

class TaskGroup(BaseModel):
    """A self-contained group of related todos that can have dependencies."""
    group_id: str
    specialization: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # Can be 'pending', 'in_progress', 'completed', or 'failed'
    todos: List[TodoItem] = Field(default_factory=list)

class TodoPlan(BaseModel):
    """The root object of a session-local todo file, containing the entire plan."""
    task_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    task_groups: List[TaskGroup] = Field(default_factory=list)

# --- REBUILT, DEPENDENCY-AWARE TODO MANAGER ---

class TodoManager:
    """Manages a structured list of Task Groups with dependencies for a single session."""

    def __init__(self, todo_file: str = ".EQUITR_todos.json"):
        self.todo_file = Path(todo_file)
        self._load_plan()

    def _load_plan(self):
        """Loads the entire structured plan from a session-local JSON file."""
        if self.todo_file.exists() and self.todo_file.stat().st_size > 0:
            try:
                data = json.loads(self.todo_file.read_text(encoding="utf-8"))
                self.plan = TodoPlan(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not load or parse todo plan from {self.todo_file}: {e}")
                self.plan = TodoPlan(task_name="default_task")
        else:
            self.plan = TodoPlan(task_name="default_task")

    def _save_plan(self):
        """Saves the entire plan to the JSON file."""
        try:
            self.todo_file.write_text(self.plan.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not save todo plan to {self.todo_file}: {e}")
    
    def create_task_group(self, group_id: str, specialization: str, description: str, dependencies: List[str]) -> TaskGroup:
        """Adds a new Task Group to the plan. Used by the orchestrator during planning."""
        group = TaskGroup(group_id=group_id, specialization=specialization, description=description, dependencies=dependencies)
        self.plan.task_groups.append(group)
        self._save_plan()
        return group

    def add_todo_to_group(self, group_id: str, title: str) -> Optional[TodoItem]:
        """Adds a specific sub-task (todo) to an existing group. Used by the orchestrator."""
        for group in self.plan.task_groups:
            if group.group_id == group_id:
                todo = TodoItem(title=title)
                group.todos.append(todo)
                self._save_plan()
                return todo
        return None

    def get_task_group(self, group_id: str) -> Optional[TaskGroup]:
        """Retrieves a specific task group by its ID."""
        for group in self.plan.task_groups:
            if group.group_id == group_id:
                return group
        return None

    def update_task_group_status(self, group_id: str, status: str) -> bool:
        """Updates the status of an entire task group. Used by the execution loop."""
        group = self.get_task_group(group_id)
        if group:
            group.status = status
            self._save_plan()
            return True
        return False

    def update_todo_status(self, todo_id: str, status: str) -> Optional[TaskGroup]:
        """Updates a single todo's status and checks if the parent group is now complete."""
        target_group = self._find_group_by_todo_id(todo_id)
        if not target_group:
            return None
        
        self._update_todo_in_group(target_group, todo_id, status)
        self._check_group_completion(target_group)
        self._save_plan()
        return target_group
    
    def _find_group_by_todo_id(self, todo_id: str) -> Optional[TaskGroup]:
        """Find the group containing the specified todo ID"""
        for group in self.plan.task_groups:
            if any(todo.id == todo_id for todo in group.todos):
                return group
        return None
    
    def _update_todo_in_group(self, group: TaskGroup, todo_id: str, status: str) -> None:
        """Update the status of a specific todo in a group"""
        for todo in group.todos:
            if todo.id == todo_id:
                todo.status = status
                break
    
    def _check_group_completion(self, group: TaskGroup) -> None:
        """Check if all todos in a group are completed and update group status"""
        all_done = all(t.status == 'completed' for t in group.todos)
        if all_done and group.status != 'completed':
            group.status = 'completed'
            print(f"🎉 Task Group '{group.group_id}' has been completed!")

    def get_next_runnable_groups(self) -> List[TaskGroup]:
        """Key method for dependency management: Finds all pending groups whose dependencies are met."""
        completed_group_ids = {g.group_id for g in self.plan.task_groups if g.status == 'completed'}
        runnable_groups = []
        for group in self.plan.task_groups:
            if group.status == 'pending':
                # A group is runnable if the set of its dependencies is a subset of the completed groups
                if set(group.dependencies).issubset(completed_group_ids):
                    runnable_groups.append(group)
        return runnable_groups

    def are_all_tasks_complete(self) -> bool:
        """Checks if the entire plan is finished."""
        if not self.plan.task_groups: return False
        return all(g.status == 'completed' for g in self.plan.task_groups)

# --- UPDATED TOOLS FOR THE NEW SYSTEM ---
# These are the tools the agents will use to interact with the plan.

from ..base import Tool, ToolResult

class ListTaskGroups(Tool):
    def get_name(self) -> str: return "list_task_groups"
    def get_description(self) -> str: return "Lists the high-level task groups, their specializations, dependencies, and statuses. This is the main way to see the overall project plan."
    def get_args_schema(self) -> Type[BaseModel]: return type('ListTaskGroupsArgs', (BaseModel,), {})
    async def run(self, **kwargs) -> ToolResult:
        manager = get_todo_manager()
        groups_summary = [g.model_dump() for g in manager.plan.task_groups]
        return ToolResult(success=True, data=groups_summary)

class ListAllTodos(Tool):
    def get_name(self) -> str: return "list_all_todos"
    def get_description(self) -> str: return "Lists ALL todos across ALL task groups with their statuses. Use this to see the complete project todo list."
    def get_args_schema(self) -> Type[BaseModel]: return type('ListAllTodosArgs', (BaseModel,), {})
    async def run(self, **kwargs) -> ToolResult:
        manager = get_todo_manager()
        all_todos = []
        for group in manager.plan.task_groups:
            for todo in group.todos:
                todo_data = todo.model_dump()
                todo_data['group_id'] = group.group_id
                todo_data['group_description'] = group.description
                todo_data['specialization'] = group.specialization
                all_todos.append(todo_data)
        return ToolResult(success=True, data=all_todos)

class ListTodosInGroup(Tool):
    class Args(BaseModel):
        group_id: str = Field(..., description="The ID of the task group to inspect.")
    def get_name(self) -> str: return "list_todos_in_group"
    def get_description(self) -> str: return "Lists the detailed sub-tasks (todos) within a specific task group. Use this to see your work for your current assignment."
    def get_args_schema(self) -> Type[BaseModel]: return self.Args
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        manager = get_todo_manager()
        group = manager.get_task_group(args.group_id)
        if not group:
            return ToolResult(success=False, error=f"Task group '{args.group_id}' not found.")
        
        todos_summary = [t.model_dump() for t in group.todos]
        return ToolResult(success=True, data=todos_summary)

class UpdateTodoStatus(Tool):
    class Args(BaseModel):
        todo_id: str = Field(..., description="The ID of the todo to update.")
        status: str = Field(..., description="The new status, typically 'completed'.")
    def get_name(self) -> str: return "update_todo_status"
    def get_description(self) -> str: return "Updates the status of a specific todo item. Marking all todos in a group as 'completed' will automatically complete the entire group."
    def get_args_schema(self) -> Type[BaseModel]: return self.Args
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        manager = get_todo_manager()
        updated_group = manager.update_todo_status(args.todo_id, args.status)
        if not updated_group:
            return ToolResult(success=False, error=f"Todo with ID '{args.todo_id}' not found.")
        return ToolResult(success=True, data=f"Todo '{args.todo_id}' updated. Parent group '{updated_group.group_id}' is now '{updated_group.status}'.")

class BulkUpdateTodoStatus(Tool):
    class Args(BaseModel):
        todo_ids: List[str] = Field(..., description="List of todo IDs to update.")
        status: str = Field(..., description="The new status to apply to all todos, typically 'completed'.")
    def get_name(self) -> str: return "bulk_update_todo_status"
    def get_description(self) -> str: return "Updates the status of multiple todo items at once. Efficient for marking several completed todos simultaneously."
    def get_args_schema(self) -> Type[BaseModel]: return self.Args
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        manager = get_todo_manager()
        updated_groups = set()
        updated_todos = []
        failed_todos = []
        
        for todo_id in args.todo_ids:
            updated_group = manager.update_todo_status(todo_id, args.status)
            if updated_group:
                updated_groups.add(updated_group.group_id)
                updated_todos.append(todo_id)
            else:
                failed_todos.append(todo_id)
        
        result_data = {
            "updated_todos": updated_todos,
            "failed_todos": failed_todos,
            "affected_groups": list(updated_groups),
            "total_updated": len(updated_todos),
            "total_failed": len(failed_todos)
        }
        
        if failed_todos:
            return ToolResult(
                success=False, 
                error=f"Failed to update {len(failed_todos)} todos: {failed_todos}",
                data=result_data
            )
        
        return ToolResult(
            success=True, 
            data=f"Successfully updated {len(updated_todos)} todos. Affected groups: {list(updated_groups)}"
        )

# --- GLOBAL INSTANCE AND SESSION MANAGEMENT ---

todo_manager = TodoManager()

def get_todo_manager():
    """Get the current global todo manager instance."""
    return todo_manager

def set_global_todo_file(todo_file: str):
    """Crucial function to ensure each run uses its own isolated todo file."""
    global todo_manager
    todo_manager = TodoManager(todo_file=todo_file)
    print(f"📋 Set global todo manager to use session-local file: {todo_file}")