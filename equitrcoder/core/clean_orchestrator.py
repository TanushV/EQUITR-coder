# equitrcoder/core/clean_orchestrator.py

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..providers.litellm import LiteLLMProvider, Message
from ..tools.builtin.todo import set_global_todo_file, todo_manager
from .profile_manager import ProfileManager

class CleanOrchestrator:
    """Orchestrates the creation of the three mandatory project documents."""
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        from ..utils.env_loader import auto_load_environment
        auto_load_environment()
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self.profile_manager = ProfileManager()
    
    async def create_docs(
        self,
        task_description: str,
        project_path: str = ".",
        task_name: Optional[str] = None,
        team: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Creates requirements, design, and a structured todo plan."""
        try:
            project_path = Path(project_path)
            if not task_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_name = f"task_{timestamp}"
            
            docs_dir = project_path / "docs" / task_name
            docs_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Creating documentation in: {docs_dir}")
            
            # 1. Create requirements document
            print("📋 Creating requirements document...")
            requirements_content = await self._create_requirements(task_description)
            requirements_path = docs_dir / "requirements.md"
            requirements_path.write_text(requirements_content)
            
            # 2. Create design document
            print("🏗️ Creating design document...")
            design_content = await self._create_design(task_description, requirements_content)
            design_path = docs_dir / "design.md"
            design_path.write_text(design_content)
            
            # 3. Create the structured todo plan (JSON)
            print("📝 Creating structured todo plan with dependencies...")
            task_todo_file = f".EQUITR_todos_{task_name}.json"
            await self._setup_todo_system(task_description, requirements_content, design_content, task_name, project_path / task_todo_file, team)
            
            print("✅ Documentation and plan created successfully!")
            return {
                "success": True,
                "task_name": task_name,
                "requirements_path": str(requirements_path),
                "design_path": str(design_path),
                "todos_path": str(project_path / task_todo_file), # Path to the JSON plan
                "docs_dir": str(docs_dir),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_requirements(self, task_description: str) -> str:
        system_prompt = """You are a requirements analyst. Create a clear, structured requirements document.

Create a requirements.md that includes:
1. Project Overview - What needs to be built
2. Functional Requirements - What the system should do  
3. Technical Requirements - How it should be built
4. Success Criteria - How to know when complete

Be specific and actionable. Use markdown format."""
        
        messages = [Message(role="system", content=system_prompt), Message(role="user", content=f"Task: {task_description}")]
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _create_design(self, task_description: str, requirements: str) -> str:
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
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}"),
        ]
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _setup_todo_system(self, task_description: str, requirements: str, design: str, task_name: str, todo_file_path: Path, team: Optional[List[str]] = None):
        """Generates and saves the structured todo plan."""
        
        team_prompt_injection = ""
        if team:
            team_details = []
            for profile_name in team:
                try:
                    profile = self.profile_manager.get_profile(profile_name)
                    team_details.append(f"- Profile: {profile_name}\n  Name: {profile['name']}\n  Description: {profile['description']}")
                except ValueError:
                    # Silently ignore if a profile is not found, or handle as an error
                    print(f"Warning: Profile '{profile_name}' not found and will be ignored.")

            if team_details:
                team_prompt_injection = (
                    "You must delegate tasks to the following team of specialists. Assign each Task Group to the most appropriate specialist by setting the `specialization` field to their profile name (e.g., `backend_dev`).\n\n"
                    "Available Team:\n" + "\n".join(team_details) + "\n\n"
                )

        system_prompt = f"""You are a senior project manager and team lead. Based on the provided requirements and design, decompose the project into a structured JSON execution plan.
{team_prompt_injection}
The plan must consist of an array of "Task Groups".

Each Task Group must have:
1. `group_id`: A unique, descriptive ID (e.g., `backend_api`, `frontend_ui`).
2. `specialization`: The profile name of the specialist assigned to this group (e.g., `backend_dev`, `frontend_dev`). If no specific team is provided, use a general role (e.g., `backend`, `frontend`).
3. `description`: A one-sentence summary of the group's objective.
4. `dependencies`: A list of `group_id`s that must be completed before this group can start. The first group(s) should have an empty list.
5. `todos`: An array of 2-8 specific, actionable sub-tasks (as `{{ "title": "..." }}` objects) for this group.

Analyze the project to identify logical dependencies. For example, the `frontend_ui` group must depend on the `backend_api` group.

Generate only the raw JSON object and nothing else."""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}"),
        ]

        max_retries = 10
        for attempt in range(1, max_retries + 1):
            response = await self.provider.chat(messages=messages)
            try:
                plan_data = json.loads(response.content)
                if isinstance(plan_data, list):
                    task_groups_data = plan_data
                else:
                    task_groups_data = plan_data.get("task_groups", plan_data)
                break  # Successfully parsed JSON
            except json.JSONDecodeError:
                if attempt == max_retries:
                    raise ValueError("Failed to decode the JSON plan from the language model after multiple retries.")
                print(f"⚠️  Attempt {attempt} returned invalid JSON. Retrying...")
                continue
        
        # Set up the session-local todo file and manager
        set_global_todo_file(str(todo_file_path))
        
        # Populate the new TodoManager with the structured plan
        for group_data in task_groups_data:
            todo_manager.create_task_group(
                group_id=group_data['group_id'],
                specialization=group_data['specialization'],
                description=group_data.get('description', ''),
                dependencies=group_data.get('dependencies', [])
            )
            for todo_data in group_data.get('todos', []):
                todo_manager.add_todo_to_group(
                    group_id=group_data['group_id'],
                    title=todo_data['title']
                )