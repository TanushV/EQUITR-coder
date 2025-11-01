"""
Todo Parser for EQUITR Coder

This module handles parsing todos from documents and integrating them
with the todo management system. Single responsibility: todo parsing and creation.
"""

from typing import List, Dict, Any, Optional
from ..tools.builtin.todo import TodoManager


class TodoParser:
    """Parses todos from documents and creates them in the todo system"""

    def __init__(self, todo_manager: TodoManager):
        self.todo_manager = todo_manager

    async def parse_and_create_todos(
        self, todos_content: str, task_folder: Optional[str] = None
    ) -> int:
        """Parse the todos document and create todos only for this specific task.
        Uses a single group derived from task_folder or 'general'."""
        print(f"📝 Parsing todos content (length: {len(todos_content)} chars)")
        lines = todos_content.split("\n")
        print(f"📝 Found {len(lines)} lines in todos document")

        # Create or get a group for this task
        group_id = (task_folder or "general").replace(" ", "_")
        existing_group = self.todo_manager.get_task_group(group_id)
        if existing_group is None:
            self.todo_manager.create_task_group(
                group_id=group_id,
                specialization="general",
                description=f"Todos for {task_folder or 'general'}",
                dependencies=[],
            )
            print(f"🧹 Initialized group '{group_id}'")
        else:
            # Reset group todos by re-creating an empty group with same metadata
            self.todo_manager.update_task_group_status(group_id, "pending")
            # Simply proceed; adding new todos will represent the current state

        todo_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for checkbox format: - [ ] Task description
            if line.startswith("- [ ]"):
                task_description = line[5:].strip()  # Remove '- [ ] '
                if task_description:
                    try:
                        self.todo_manager.add_todo_to_group(
                            group_id=group_id, title=task_description
                        )
                        print(f"✅ Created todo {todo_count + 1}: {task_description}")
                        todo_count += 1
                    except Exception as e:
                        print(
                            f"❌ Warning: Could not create todo '{task_description}': {e}"
                        )
                else:
                    print(f"⚠️ Empty task description on line {i + 1}: '{line}'")

        print(f"📝 Total todos created for this isolated task: {todo_count}")
        return todo_count

    def parse_categories(self, todos_content: str) -> List[Dict[str, Any]]:
        """Parse todos content into categories for parallel agent distribution."""
        categories: List[Dict[str, Any]] = []
        current_category: Optional[str] = None
        current_todos: List[str] = []

        for line in todos_content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                # Save previous category
                if current_category and current_todos:
                    categories.append(
                        {"name": current_category, "todos": current_todos.copy()}
                    )
                # Start new category
                current_category = line[3:].strip()  # Remove '## '
                current_todos = []
            elif line.startswith("- [ ]"):
                if current_category:
                    current_todos.append(line)

        # Save last category
        if current_category and current_todos:
            categories.append({"name": current_category, "todos": current_todos.copy()})

        return categories

    def create_agent_todos_content(
        self, categories: List[Dict[str, Any]], agent_idx: int, num_agents: int
    ) -> str:
        """Create todos content for a specific agent based on category distribution."""
        # Assign categories to this agent (round-robin distribution)
        agent_categories: List[Dict[str, Any]] = []
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
            for todo in category["todos"]:
                content += f"{todo}\n"
            content += "\n"

        return content
