# equitrcoder/core/clean_orchestrator.py

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..providers.litellm import LiteLLMProvider, Message
from ..tools.builtin.todo import set_global_todo_file, get_todo_manager
from ..tools.discovery import discover_tools
from .profile_manager import ProfileManager
from .unified_config import get_config_manager


def _safe_format(template: str, **kwargs) -> str:
    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"
    try:
        return template.format_map(_SafeDict(**kwargs))
    except Exception:
        # As a last resort, return template unformatted
        return template

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
        """Load orchestrator prompts from unified configuration."""
        config_manager = get_config_manager()
        config_data = config_manager.get_cached_config()
        
        # Get prompts from unified configuration
        prompts = config_data.prompts
        
        # Return orchestrator prompts with fallbacks
        return {
            'requirements_analyst_prompt': prompts.get('requirements_analyst_prompt', 'You are a requirements analyst. Create a clear requirements document.'),
            'system_designer_prompt': prompts.get('system_designer_prompt', 'You are a system designer. Create a technical design document.'),
            'task_group_planner_prompt': prompts.get('task_group_planner_prompt', 'You are a project manager. Create task groups for the project.'),
            'todo_generator_prompt': prompts.get('todo_generator_prompt', 'You are a technical lead. Create specific todos for a task group.')
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
            project_root = Path(project_path)
            if not task_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_name = f"task_{timestamp}"
            
            docs_dir = project_root / "docs" / task_name
            docs_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Creating documentation in: {docs_dir}")
            
            # Build a live repo map (with basic function signatures) for the target project folder
            repo_context = self._generate_live_repo_map(path=str(project_root))
            
            # 1. Create requirements document
            print("📋 Creating requirements document...")
            requirements_content = await self._create_requirements(task_description, repo_context)
            requirements_path = docs_dir / "requirements.md"
            requirements_path.write_text(requirements_content)
            
            # 2. Create design document
            print("🏗️ Creating design document...")
            design_content = await self._create_design(task_description, requirements_content, repo_context)
            design_path = docs_dir / "design.md"
            design_path.write_text(design_content)
            
            # 3. Create the structured todo plan (JSON) in same docs folder
            print("📝 Creating structured todo plan with dependencies...")
            todo_path = docs_dir / "todos.json"
            await self._setup_todo_system(task_description, requirements_content, design_content, task_name, todo_path, team, repo_context=repo_context)
            
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
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _create_requirements(self, task_description: str, repo_context: str) -> str:
        system_prompt = self.prompts.get('requirements_analyst_prompt', 'You are a requirements analyst.')
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRepository Context (read-only):\n{repo_context}"),
        ]
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _create_design(self, task_description: str, requirements: str, repo_context: str) -> str:
        system_prompt = self.prompts.get('system_designer_prompt', 'You are a system designer.')
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nRepository Context (read-only):\n{repo_context}"),
        ]
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _setup_todo_system(self, task_description: str, requirements: str, design: str, task_name: str, todo_file_path: Path, team: Optional[List[str]] = None, repo_context: Optional[str] = None):
        """Generates and saves the structured todo plan using a two-stage process."""
        
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
                    if profile_name == 'default':
                        # Render default agent from default config
                        default_cfg = self.profile_manager.get_default_agent_config()
                        team_details.append(f"- Profile: default\n  Name: {default_cfg['name']}\n  Description: {default_cfg['description']}")
                    else:
                        profile = self.profile_manager.get_profile(profile_name)
                        team_details.append(f"- Profile: {profile_name}\n  Name: {profile['name']}\n  Description: {profile['description']}")
                except ValueError:
                    # Silently ignore if a profile is not found, or handle as an error
                    print(f"Warning: Profile '{profile_name}' not found and will be ignored.")

            if team_details:
                team_prompt_injection = (
                    "You must delegate tasks to the following team of specialists. Assign each Task Group to the most appropriate specialist by setting the `specialization` field to their profile name (e.g., `backend_dev`).\n\n"
                    "Available Team:\n" + "\n".join(team_details) + "\n\n"
                    "Assignment policy:\n"
                    "- Prefer assigning each Task Group to the most relevant specialist.\n"
                    "- Use 'default' only when no clear specialist applies. Do NOT over-assign to 'default'.\n\n"
                )

        # STAGE 1: Create Task Groups
        print("🎯 Stage 1: Creating task groups...")
        task_group_planner_prompt = self.prompts.get('task_group_planner_prompt', 'You are a project manager.')
        system_prompt = _safe_format(
            task_group_planner_prompt,
            team_prompt_injection=team_prompt_injection,
            tools_context=tools_context,
            repo_context=repo_context or "",
        )
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}\n\nRepository Context (read-only):\n{(repo_context or '')}"),
        ]

        max_retries = 10
        for attempt in range(1, max_retries + 1):
            response = await self.provider.chat(messages=messages)
            try:
                task_groups_data = json.loads(response.content)
                if not isinstance(task_groups_data, list):
                    raise ValueError("Expected an array of task groups")
                break  # Successfully parsed JSON
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == max_retries:
                    raise ValueError(f"Failed to get valid task groups after multiple retries: {e}")
                print(f"⚠️  Attempt {attempt} returned invalid task groups. Retrying...")
                continue
        
        print(f"✅ Created {len(task_groups_data)} task groups")
        
        # Set up the session-local todo file and manager
        set_global_todo_file(str(todo_file_path))
        manager = get_todo_manager()
        
        # Create task groups in the manager
        for group_data in task_groups_data:
            manager.create_task_group(
                group_id=group_data['group_id'],
                specialization=group_data['specialization'],
                description=group_data.get('description', ''),
                dependencies=group_data.get('dependencies', [])
            )
        
        # STAGE 2: Create todos for each task group
        print("📝 Stage 2: Creating todos for each task group...")
        todo_generator_prompt = self.prompts.get('todo_generator_prompt', 'You are a technical lead.')
        
        for group_data in task_groups_data:
            print(f"  📋 Creating todos for group: {group_data['group_id']}")
            
            system_prompt = _safe_format(
                todo_generator_prompt,
                group_id=group_data['group_id'],
                specialization=group_data['specialization'],
                description=group_data.get('description', ''),
                requirements=requirements,
                design=design,
                tools_context=tools_context,
                repo_context=repo_context or "",
            )
            
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=(
                    f"Create specific todos for the '{group_data['group_id']}' task group.\n\n"
                    f"Repository Context (read-only):\n{(repo_context or '')}"
                )),
            ]
            
            try:
                for attempt in range(1, max_retries + 1):
                    response = await self.provider.chat(messages=messages)
                    try:
                        todos_data = json.loads(response.content)
                        if not isinstance(todos_data, list):
                            raise ValueError("Expected an array of todo objects")
                        
                        # Normalize todos into dicts with 'title'
                        normalized_todos: List[Dict[str, str]] = []
                        for todo in todos_data:
                            title_val = None
                            if isinstance(todo, dict):
                                title_val = todo.get('title') or todo.get('name') or todo.get('task')
                            elif isinstance(todo, str):
                                title_val = todo
                            
                            if not title_val:
                                # Could not extract title; coerce to string
                                title_val = str(todo)
                            normalized_todos.append({'title': title_val})
                        
                        todos_data = normalized_todos
                        break  # Successfully parsed JSON
                    except (json.JSONDecodeError, ValueError) as e:
                        if attempt == max_retries:
                            print(f"⚠️  Failed to get valid todos for group {group_data['group_id']} after multiple retries: {e}")
                            # Create a fallback todo
                            todos_data = [{"title": f"Implement {group_data['group_id']} functionality"}]
                            break
                        print(f"⚠️  Attempt {attempt} returned invalid todos for {group_data['group_id']}. Retrying...")
                        continue
                
                # Add todos to the group
                for todo_data in todos_data:
                    if isinstance(todo_data, dict):
                        t = todo_data.get('title') or todo_data.get('name') or todo_data.get('task')
                    else:
                        t = None
                    try:
                        manager.add_todo_to_group(
                            group_id=group_data['group_id'],
                            title=t or str(todo_data)
                        )
                    except Exception as e:
                        print(f"⚠️  Skipping todo due to error: {e}")
                        continue
                
                print(f"    ✅ Added {len(todos_data)} todos to {group_data['group_id']}")
            except Exception as e:
                print(f"⚠️  Failed to process todos for group {group_data.get('group_id')}: {e}")
                # Continue to next group without failing the whole operation
                continue
        
        print("✅ Two-stage todo creation completed successfully!")

    def _generate_live_repo_map(self, path=".", max_depth=None, max_tokens=None):
        max_depth = max_depth or get_config_manager().get_cached_config().limits.get('max_depth', 3) if hasattr(get_config_manager().get_cached_config(), 'limits') else 3
        # Fallback tokens if not configured
        try:
            from .unified_config import get_config  # local import to avoid cycle at module import time
            max_tokens = max_tokens or get_config('limits.context_max_tokens', 4000)
        except Exception:
            max_tokens = max_tokens or 4000
        """Generate a LIVE/dynamic repo map that reflects current file system state for the given path."""
        import re
        try:
            import tiktoken  # type: ignore
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            encoding = None
        from pathlib import Path as _P
        
        def count_tokens(text: str) -> int:
            if encoding:
                try:
                    return len(encoding.encode(text))
                except Exception:
                    pass
            return len(text) // 4
        
        def extract_functions(file_path: _P) -> List[str]:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                functions: List[str] = []
                if file_path.suffix == '.py':
                    func_pattern = r'^(def\s+\w+\([^)]*\):|class\s+\w+[^:]*:)'
                    for match in re.finditer(func_pattern, content, re.MULTILINE):
                        functions.append(match.group(1).strip())
                elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                    func_patterns = [
                        r'function\s+\w+\s*\([^)]*\)',
                        r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',
                        r'class\s+\w+',
                        r'export\s+function\s+\w+\s*\([^)]*\)'
                    ]
                    for pattern in func_patterns:
                        for match in re.finditer(pattern, content, re.MULTILINE):
                            functions.append(match.group(0).strip())
                return functions[:5]
            except Exception:
                return []
        
        repo_map: List[str] = []
        current_tokens = 0
        base = _P(path)
        
        def scan_directory(dir_path: _P, current_depth: int = 0, prefix: str = "") -> None:
            nonlocal current_tokens
            if current_depth > max_depth or current_tokens >= max_tokens:
                return
            try:
                items = sorted(dir_path.iterdir())
                for item in items:
                    if current_tokens >= max_tokens:
                        break
                    if item.name.startswith('.') and item.name not in ['.gitignore', '.env.example']:
                        continue
                    if item.is_file():
                        try:
                            size = item.stat().st_size
                        except Exception:
                            size = 0
                        line = f"{prefix}📄 {item.name} ({size} bytes)"
                        if item.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx'] and size < 50000:
                            funcs = extract_functions(item)
                            if funcs:
                                line += f" - Functions: {', '.join(funcs)}"
                        line_tokens = count_tokens(line + "\n")
                        if current_tokens + line_tokens > max_tokens - 100:
                            repo_map.append(f"{prefix}... (truncated - token limit reached)")
                            return
                        repo_map.append(line)
                        current_tokens += line_tokens
                    elif item.is_dir():
                        dir_line = f"{prefix}📁 {item.name}/"
                        line_tokens = count_tokens(dir_line + "\n")
                        if current_tokens + line_tokens > max_tokens - 100:
                            repo_map.append(f"{prefix}... (truncated - token limit reached)")
                            return
                        repo_map.append(dir_line)
                        current_tokens += line_tokens
                        scan_directory(item, current_depth + 1, prefix + "  ")
            except PermissionError:
                err = f"{prefix}❌ Permission denied"
                if current_tokens + count_tokens(err + "\n") <= max_tokens:
                    repo_map.append(err)
                    current_tokens += count_tokens(err + "\n")
        
        scan_directory(base)
        return "\n".join(repo_map)