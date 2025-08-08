"""
Todo Parser for EQUITR Coder

This module handles parsing todos from documents and integrating them
with the todo management system. Single responsibility: todo parsing and creation.
"""

from typing import List, Dict, Any
from ..tools.builtin.todo import TodoManager


class TodoParser:
    """Parses todos from documents and creates them in the todo system"""
    
    def __init__(self, todo_manager: TodoManager):
        self.todo_manager = todo_manager
    
    async def parse_and_create_todos(self, todos_content: str, task_folder: str = None) -> int:
        """Parse the todos document and create todos only for this specific task."""
        print(f"📝 Parsing todos content (length: {len(todos_content)} chars)")
        lines = todos_content.split("\n")
        print(f"📝 Found {len(lines)} lines in todos document")

        # Clear ALL existing todos in this isolated todo file
        existing_todos = self.todo_manager.list_todos()
        for todo in existing_todos:
            self.todo_manager.delete_todo(todo.id)
        print(f"🧹 Cleared {len(existing_todos)} existing todos from isolated todo file")

        todo_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for checkbox format: - [ ] Task description
            if line.startswith("- [ ]"):
                task_description = line[5:].strip()  # Remove '- [ ] '
                if task_description:
                    try:
                        tags = ["auto-generated"]
                        if task_folder:
                            tags.append(f"task-{task_folder}")

                        todo = self.todo_manager.create_todo(
                            title=task_description,
                            description=f"Auto-generated from todos document for task: {task_folder or 'unknown'}",
                            priority="medium",
                            tags=tags,
                            assignee=None,
                        )
                        print(f"✅ Created todo {todo_count + 1}: {todo.id} - {task_description}")
                        todo_count += 1
                    except Exception as e:
                        print(f"❌ Warning: Could not create todo '{task_description}': {e}")
                else:
                    print(f"⚠️ Empty task description on line {i + 1}: '{line}'")

        print(f"📝 Total todos created for this isolated task: {todo_count}")

        # Show all todos in this isolated file
        all_todos = self.todo_manager.list_todos()
        print(f"📝 Todos in isolated file: {len(all_todos)}")
        for todo in all_todos:
            print(f"  - {todo.status}: {todo.title}")
        
        return todo_count
    
    def parse_categories(self, todos_content: str) -> List[Dict[str, Any]]:
        """Parse todos content into categories for parallel agent distribution."""
        categories = []
        current_category = None
        current_todos = []

        for line in todos_content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                # Save previous category
                if current_category and current_todos:
                    categories.append({
                        "name": current_category, 
                        "todos": current_todos.copy()
                    })
                # Start new category
                current_category = line[3:].strip()  # Remove '## '
                current_todos = []
            elif line.startswith("- [ ]"):
                if current_category:
                    current_todos.append(line)

        # Save last category
        if current_category and current_todos:
            categories.append({
                "name": current_category, 
                "todos": current_todos.copy()
            })

        return categories
    
    def create_agent_todos_content(self, categories: List[Dict[str, Any]], agent_idx: int, num_agents: int) -> str:
        """Create todos content for a specific agent based on category distribution."""
        # Assign categories to this agent (round-robin distribution)
        agent_categories = []
        for cat_idx, category in enumerate(categories):
            if cat_idx % num_agents == agent_idx:
                agent_categories.append(category)

        if not agent_categories:
            # If no categories assigned, create a coordination category
            return f"# Agent {agent_idx + 1} Tasks\n\n## Coordination\n- [ ] Coordinate with other agents\n- [ ] Review and integrate work from other agents\n"

        # Generate content for assigned categories
        content = f"# Agent {agent_idx + 1} Tasks\n\n"
        content += f"**Assigned Categories:** {', '.join([cat['name'] for cat in agent_categories])}\n\n"

        for category in agent_categories:
            content += f"## {category['name']}\n"
            for todo in category['todos']:
                content += f"{todo}\n"
            content += "\n"

        return content