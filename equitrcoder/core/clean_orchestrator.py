# equitrcoder/core/clean_orchestrator.py

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..providers.litellm import LiteLLMProvider, Message
from ..tools.builtin.todo import set_global_todo_file, get_todo_manager
from ..tools.discovery import discover_tools
from .profile_manager import ProfileManager

class CleanOrchestrator:
    """Orchestrates the creation of the three mandatory project documents."""
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        from ..utils.env_loader import auto_load_environment
        auto_load_environment()
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self.profile_manager = ProfileManager()
        self.prompts = self._load_orchestrator_prompts()
    
    def _load_orchestrator_prompts(self) -> Dict[str, str]:
        """Load orchestrator prompts from unified system_prompt.yaml config."""
        config_path = Path('equitrcoder/config/system_prompt.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {
                    'requirements_analyst_prompt': config.get('requirements_analyst_prompt', ''),
                    'system_designer_prompt': config.get('system_designer_prompt', ''),
                    'project_manager_prompt': config.get('project_manager_prompt', '')
                }
        
        # Fallback prompts if config file not found
        return {
            'requirements_analyst_prompt': 'You are a requirements analyst. Create a clear requirements document.',
            'system_designer_prompt': 'You are a system designer. Create a technical design document.',
            'project_manager_prompt': 'You are a project manager. Create a structured execution plan.'
        }
    
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
            
            # 3. Create the structured todo plan (JSON) in same docs folder
            print("📝 Creating structured todo plan with dependencies...")
            todo_path = docs_dir / "todos.json"
            await self._setup_todo_system(task_description, requirements_content, design_content, task_name, todo_path, team)
            
            print("✅ Documentation and plan created successfully!")
            return {
                "success": True,
                "task_name": task_name,
                "requirements_path": str(requirements_path),
                "design_path": str(design_path),
                "todos_path": str(todo_path),
                "docs_dir": str(docs_dir),
                # Include actual content for agent context
                "requirements_content": requirements_content,
                "design_content": design_content,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_requirements(self, task_description: str) -> str:
        system_prompt = self.prompts.get('requirements_analyst_prompt', 'You are a requirements analyst.')
        
        messages = [Message(role="system", content=system_prompt), Message(role="user", content=f"Task: {task_description}")]
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _create_design(self, task_description: str, requirements: str) -> str:
        system_prompt = self.prompts.get('system_designer_prompt', 'You are a system designer.')
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}"),
        ]
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _setup_todo_system(self, task_description: str, requirements: str, design: str, task_name: str, todo_file_path: Path, team: Optional[List[str]] = None):
        """Generates and saves the structured todo plan."""
        
        # Get available tools context
        available_tools = discover_tools()
        tools_context = "Available tools that agents will have access to:\n"
        for tool in available_tools:
            tools_context += f"- {tool.get_name()}: {tool.get_description()}\n"
        
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

        # Get project manager prompt from config and format it
        project_manager_prompt = self.prompts.get('project_manager_prompt', 'You are a project manager.')
        system_prompt = project_manager_prompt.format(
            team_prompt_injection=team_prompt_injection,
            tools_context=tools_context
        )
        
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
        manager = get_todo_manager()
        for group_data in task_groups_data:
            manager.create_task_group(
                group_id=group_data['group_id'],
                specialization=group_data['specialization'],
                description=group_data.get('description', ''),
                dependencies=group_data.get('dependencies', [])
            )
            for todo_data in group_data.get('todos', []):
                manager.add_todo_to_group(
                    group_id=group_data['group_id'],
                    title=todo_data['title']
                )