"""
Task class representing individual tasks in the task management system.
"""
from datetime import datetime
from typing import Optional
import uuid


class Task:
    """Represents a single task with properties and methods for task management."""
    
    def __init__(self, title: str, description: str = "", due_date: Optional[str] = None):
        """
        Initialize a new task.
        
        Args:
            title: The task title
            description: Optional task description
            due_date: Optional due date in YYYY-MM-DD format
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date
        self.completed = False
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
    
    def mark_completed(self):
        """Mark the task as completed."""
        self.completed = True
        self.completed_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date,
            'completed': self.completed,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create a Task instance from dictionary data."""
        task = cls(data['title'], data.get('description', ''), data.get('due_date'))
        task.id = data['id']
        task.completed = data.get('completed', False)
        task.created_at = data.get('created_at', datetime.now().isoformat())
        task.completed_at = data.get('completed_at')
        return task
    
    def __str__(self) -> str:
        """String representation of the task."""
        status = "✓" if self.completed else "○"
        due_str = f" (Due: {self.due_date})" if self.due_date else ""
        return f"{status} {self.title}{due_str}"
    
    def __repr__(self) -> str:
        return f"Task(id='{self.id}', title='{self.title}', completed={self.completed})"