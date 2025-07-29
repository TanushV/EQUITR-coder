"""
Clean Orchestrator Implementation - ONLY creates docs (requirements, design, todos).
Nothing else.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import uuid

from ..providers.litellm import LiteLLMProvider, Message
from ..tools.builtin.todo import set_global_todo_file


class CleanOrchestrator:
    """
    Simple orchestrator that ONLY creates documentation.
    Creates requirements.md, design.md, todos.md and sets up todo system.
    """
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        # Auto-load environment variables
        from ..utils.env_loader import auto_load_environment
        auto_load_environment()
        
        self.model = model
        self.provider = LiteLLMProvider(model=model)
    
    async def create_docs(
        self,
        task_description: str,
        project_path: str = ".",
        task_name: Optional[str] = None,
        num_agents: int = 1
    ) -> Dict[str, Any]:
        """
        Create all required documentation for a task.
        
        Args:
            task_description: The user's task description
            project_path: Where to create the docs
            task_name: Optional task name (will generate if not provided)
            num_agents: Number of agents (affects todo splitting)
            
        Returns:
            Dict with success status and file paths
        """
        try:
            project_path = Path(project_path)
            
            # Generate unique task name if not provided
            if not task_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_name = f"task_{timestamp}"
            
            # Create task-specific docs directory
            docs_dir = project_path / "docs" / task_name
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Creating documentation in: {docs_dir}")
            
            # Step 1: Create requirements document
            print("📋 Creating requirements document...")
            requirements_content = await self._create_requirements(task_description)
            requirements_path = docs_dir / "requirements.md"
            requirements_path.write_text(requirements_content)
            
            # Step 2: Create design document
            print("🏗️ Creating design document...")
            design_content = await self._create_design(task_description, requirements_content)
            design_path = docs_dir / "design.md"
            design_path.write_text(design_content)
            
            # Step 3: Create todos document
            print("📝 Creating todos document...")
            if num_agents > 1:
                todos_result = await self._create_todos_for_multiple_agents(
                    task_description, requirements_content, design_content, num_agents, docs_dir
                )
            else:
                todos_content = await self._create_todos(task_description, requirements_content, design_content)
                todos_path = docs_dir / "todos.md"
                todos_path.write_text(todos_content)
                
                # Setup todo system for single agent
                await self._setup_todo_system(todos_content, task_name)
                
                todos_result = {
                    "todos_path": str(todos_path),
                    "agent_todo_files": []
                }
            
            print(f"✅ Documentation created successfully!")
            
            return {
                "success": True,
                "task_name": task_name,
                "requirements_path": str(requirements_path),
                "design_path": str(design_path),
                "todos_path": todos_result["todos_path"],
                "agent_todo_files": todos_result.get("agent_todo_files", []),
                "docs_dir": str(docs_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_requirements(self, task_description: str) -> str:
        """Create requirements.md document."""
        system_prompt = """You are a requirements analyst. Create a clear, structured requirements document.

Create a requirements.md that includes:
1. Project Overview - What needs to be built
2. Functional Requirements - What the system should do  
3. Technical Requirements - How it should be built
4. Success Criteria - How to know when complete

Be specific and actionable. Use markdown format."""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}")
        ]
        
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _create_design(self, task_description: str, requirements: str) -> str:
        """Create design.md document."""
        system_prompt = """You are a system designer. Create a technical design document.

Create a design.md that includes:
1. System Architecture - High-level structure
2. Components - What parts need to be built
3. Data Flow - How information moves
4. Implementation Plan - Step-by-step approach
5. File Structure - What files/directories will be created

Be technical and specific. Use markdown format."""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}")
        ]
        
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _create_todos(self, task_description: str, requirements: str, design: str) -> str:
        """Create todos.md document for single agent."""
        system_prompt = """You are a project manager creating a task breakdown.

Create a todos.md with checkboxes (- [ ]) format that includes:
1. 5-20 specific, actionable tasks
2. Each task should be completable independently
3. Tasks should build towards the final goal
4. Use clear, descriptive titles
5. Order tasks logically

Format: Use markdown with checkbox syntax: - [ ] Task description"""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}")
        ]
        
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _create_todos_for_multiple_agents(
        self,
        task_description: str,
        requirements: str,
        design: str,
        num_agents: int,
        docs_dir: Path
    ) -> Dict[str, Any]:
        """Create todos for multiple agents with proper categorization."""
        system_prompt = f"""You are a project manager creating tasks for {num_agents} parallel agents.

Create categorized todos that can be split among {num_agents} agents:
1. Create {min(num_agents, 6)} logical categories 
2. Each category should be independent and self-contained
3. 3-8 tasks per category
4. Use clear category headers (## Category Name)
5. Use checkbox format: - [ ] Task description

Format:
## Category 1 Name
- [ ] Task 1
- [ ] Task 2

## Category 2 Name  
- [ ] Task 3
- [ ] Task 4"""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}")
        ]
        
        response = await self.provider.chat(messages=messages)
        todos_content = response.content
        
        # Save main todos file
        todos_path = docs_dir / "todos.md"
        todos_path.write_text(todos_content)
        
        # Parse into categories and create agent-specific files
        agent_todo_files = await self._split_todos_for_agents(todos_content, num_agents, docs_dir)
        
        return {
            "todos_path": str(todos_path),
            "agent_todo_files": agent_todo_files
        }
    
    async def _split_todos_for_agents(self, todos_content: str, num_agents: int, docs_dir: Path) -> List[str]:
        """Split categorized todos among agents."""
        # Parse categories
        categories = []
        current_category = None
        current_todos = []
        
        for line in todos_content.split('\n'):
            line = line.strip()
            if line.startswith('## '):
                # Save previous category
                if current_category and current_todos:
                    categories.append({
                        'name': current_category,
                        'todos': current_todos.copy()
                    })
                # Start new category
                current_category = line[3:].strip()
                current_todos = []
            elif line.startswith('- [ ]'):
                if current_category:
                    current_todos.append(line)
        
        # Save last category
        if current_category and current_todos:
            categories.append({
                'name': current_category,
                'todos': current_todos.copy()
            })
        
        if not categories:
            print("⚠️ No categories found, creating simple split")
            return []
        
        print(f"📋 Found {len(categories)} categories: {[cat['name'] for cat in categories]}")
        
        # Distribute categories among agents
        agent_todo_files = []
        
        for agent_idx in range(num_agents):
            # Assign categories to this agent (round-robin)
            agent_categories = []
            for cat_idx, category in enumerate(categories):
                if cat_idx % num_agents == agent_idx:
                    agent_categories.append(category)
            
            if not agent_categories:
                # Fallback if no categories assigned
                agent_categories = [{
                    'name': 'General Tasks',
                    'todos': ['- [ ] Coordinate with other agents and integrate work']
                }]
            
            # Create agent-specific todos file
            agent_content = f"# Todos for Agent {agent_idx + 1}\n\n"
            agent_content += f"**Agent {agent_idx + 1} of {num_agents}**\n\n"
            
            for category in agent_categories:
                agent_content += f"## {category['name']}\n"
                for todo in category['todos']:
                    agent_content += f"{todo}\n"
                agent_content += "\n"
            
            agent_content += f"""## Instructions
- Complete ALL todos in your assigned categories
- Each category is self-contained
- Use communication tools to coordinate with other agents
- Mark todos complete with update_todo when finished
"""
            
            # Save agent file
            agent_file_path = docs_dir / f"todos_agent_{agent_idx + 1}.md"
            agent_file_path.write_text(agent_content)
            agent_todo_files.append(str(agent_file_path))
            
            print(f"📋 Agent {agent_idx + 1} assigned: {[cat['name'] for cat in agent_categories]}")
            
            # Setup todo system for this agent
            agent_todo_file = f".EQUITR_todos_agent_{agent_idx + 1}.json"
            await self._setup_todo_system_for_agent(agent_categories, agent_todo_file, agent_idx + 1)
        
        return agent_todo_files
    
    async def _setup_todo_system(self, todos_content: str, task_name: str):
        """Setup the todo system with todos from the document."""
        # Create isolated todo file for this task
        task_todo_file = f".EQUITR_todos_{task_name}.json"
        set_global_todo_file(task_todo_file)
        
        # Parse and create todos
        from ..tools.builtin.todo import todo_manager
        
        # Clear existing todos in isolated file
        existing_todos = todo_manager.list_todos()
        for todo in existing_todos:
            todo_manager.delete_todo(todo.id)
        
        # Parse todos from markdown
        todo_count = 0
        for line in todos_content.split('\n'):
            line = line.strip()
            if line.startswith('- [ ]'):
                task_text = line[5:].strip()
                if task_text:
                    todo_manager.create_todo(
                        title=task_text,
                        description=f"Auto-generated from todos document for task: {task_name}",
                        priority="medium",
                        tags=["auto-generated", f"task-{task_name}"]
                    )
                    todo_count += 1
        
        print(f"📝 Created {todo_count} todos in isolated file: {task_todo_file}")
    
    async def _setup_todo_system_for_agent(self, categories: List[Dict], todo_file: str, agent_id: int):
        """Setup todos for a specific agent."""
        from ..tools.builtin.todo import TodoManager
        
        # Create agent-specific todo manager
        agent_todo_manager = TodoManager(todo_file=todo_file)
        
        # Clear existing todos
        existing_todos = agent_todo_manager.list_todos()
        for todo in existing_todos:
            agent_todo_manager.delete_todo(todo.id)
        
        # Create todos from categories
        todo_count = 0
        for category in categories:
            for todo_line in category['todos']:
                if todo_line.startswith('- [ ]'):
                    task_text = todo_line[5:].strip()
                    if task_text:
                        agent_todo_manager.create_todo(
                            title=task_text,
                            description=f"Category: {category['name']} - Assigned to Agent {agent_id}",
                            priority="medium",
                            tags=["auto-generated", f"agent-{agent_id}", category['name'].lower().replace(' ', '-')],
                            assignee=f"agent_{agent_id}"
                        )
                        todo_count += 1
        
        print(f"📝 Created {todo_count} todos for Agent {agent_id} in: {todo_file}")
    
    def get_context_for_agent(self, docs_result: Dict[str, Any], agent_id: Optional[int] = None) -> Dict[str, Any]:
        """Get context information for an agent based on created docs."""
        context = {
            "task_name": docs_result.get("task_name"),
            "docs_dir": docs_result.get("docs_dir"),
            "requirements_path": docs_result.get("requirements_path"),
            "design_path": docs_result.get("design_path"),
            "todos_path": docs_result.get("todos_path")
        }
        
        # Add agent-specific info for multi-agent mode
        if agent_id is not None and docs_result.get("agent_todo_files"):
            agent_files = docs_result["agent_todo_files"]
            if agent_id <= len(agent_files):
                context["agent_todo_file"] = agent_files[agent_id - 1]
                context["agent_id"] = agent_id
                context["total_agents"] = len(agent_files)
        
        return context