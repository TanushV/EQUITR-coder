# equitrcoder/core/clean_orchestrator.py

import asyncio
import os
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
            "requirements_analyst_prompt": prompts.get(
                "requirements_analyst_prompt",
                "You are a requirements analyst. Create a clear requirements document.",
            ),
            "system_designer_prompt": prompts.get(
                "system_designer_prompt",
                "You are a system designer. Create a technical design document.",
            ),
            "task_group_planner_prompt": prompts.get(
                "task_group_planner_prompt",
                "You are a project manager. Create task groups for the project.",
            ),
            # Lightweight todos policy embedded in fallback to avoid overkill tasks
            "todo_generator_prompt": prompts.get(
                "todo_generator_prompt",
                (
                    "You are a technical lead. Create specific todos for a task group.\n\n"
                    "TODO CREATION GUIDELINES (no numeric caps):\n"
                    "- Use concise, imperative titles (e.g., 'Implement loader function').\n"
                    "- Avoid overly granular steps; focus on what needs to be delivered.\n"
                    "- Split only when tasks are truly independent; keep lists lean and reasonable.\n"
                    "- Prefer minimal filenames; at most one file path mention per todo.\n"
                    '- Return JSON array only: [{"title": "..."}]. No extra fields or prose.'
                ),
            ),
        }

    async def create_docs(
        self,
        task_description: str,
        project_path: str = ".",
        task_name: Optional[str] = None,
        team: Optional[List[str]] = None,
        is_research: bool = False,
    ) -> Dict[str, Any]:
        """Creates requirements, design, and a structured todo plan.
        Strict: any failure raises an exception (no fallbacks)."""
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
        # Allow longer time for GPT-5 planning on slow networks; configurable via env
        req_timeout = float(os.environ.get("EQUITR_ORCH_REQUIREMENTS_TIMEOUT", "900"))
        requirements_content, req_cost = await asyncio.wait_for(
            self._create_requirements(task_description, repo_context),
            timeout=req_timeout,
        )
        requirements_path = docs_dir / "requirements.md"
        requirements_path.write_text(requirements_content, encoding="utf-8")

        # 2. Create design document
        print("🏗️ Creating design document...")
        des_timeout = float(os.environ.get("EQUITR_ORCH_DESIGN_TIMEOUT", "900"))
        design_content, des_cost = await asyncio.wait_for(
            self._create_design(task_description, requirements_content, repo_context),
            timeout=des_timeout,
        )
        design_path = docs_dir / "design.md"
        design_path.write_text(design_content, encoding="utf-8")

        # 3. Create the structured todo plan (JSON) in same docs folder
        print("📝 Creating structured todo plan with dependencies...")
        todo_path = docs_dir / "todos.json"
        await self._setup_todo_system(
            task_description,
            requirements_content,
            design_content,
            task_name,
            todo_path,
            team,
            repo_context=repo_context,
            is_research=is_research,
        )

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
            "orchestrator_cost": float(req_cost or 0.0) + float(des_cost or 0.0),
        }

    async def _create_requirements(
        self, task_description: str, repo_context: str
    ) -> tuple[str, float]:
        system_prompt = self.prompts.get(
            "requirements_analyst_prompt", "You are a requirements analyst."
        )
        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"Task: {task_description}\n\nRepository Context (read-only):\n{repo_context}",
            ),
        ]
        # Strict: no fallbacks
        response = await asyncio.wait_for(
            self.provider.chat(messages=messages), timeout=300
        )
        return response.content, float(getattr(response, "cost", 0.0) or 0.0)

    async def _create_design(
        self, task_description: str, requirements: str, repo_context: str
    ) -> tuple[str, float]:
        system_prompt = self.prompts.get(
            "system_designer_prompt", "You are a system designer."
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nRepository Context (read-only):\n{repo_context}",
            ),
        ]
        # Strict: no fallbacks
        response = await asyncio.wait_for(
            self.provider.chat(messages=messages), timeout=300
        )
        return response.content, float(getattr(response, "cost", 0.0) or 0.0)

    async def _setup_todo_system(
        self,
        task_description: str,
        requirements: str,
        design: str,
        task_name: str,
        todo_file_path: Path,
        team: Optional[List[str]] = None,
        repo_context: Optional[str] = None,
        is_research: bool = False,
    ):
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
                    if profile_name == "default":
                        # Render default agent from default config
                        default_cfg = self.profile_manager.get_default_agent_config()
                        team_details.append(
                            f"- Profile: default\n  Name: {default_cfg['name']}\n  Description: {default_cfg['description']}"
                        )
                    else:
                        profile = self.profile_manager.get_profile(profile_name)
                        team_details.append(
                            f"- Profile: {profile_name}\n  Name: {profile['name']}\n  Description: {profile['description']}"
                        )
                except ValueError:
                    # Silently ignore if a profile is not found, or handle as an error
                    print(
                        f"Warning: Profile '{profile_name}' not found and will be ignored."
                    )

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
        task_group_planner_prompt = self.prompts.get(
            "task_group_planner_prompt", "You are a project manager."
        )
        system_prompt = _safe_format(
            task_group_planner_prompt,
            team_prompt_injection=team_prompt_injection,
            tools_context=tools_context,
            repo_context=repo_context or "",
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"Task: {task_description}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}\n\nRepository Context (read-only):\n{(repo_context or '')}",
            ),
        ]

        max_retries = 5
        task_groups_data = None
        for attempt in range(1, max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.provider.chat(messages=messages), timeout=180
                )
            except asyncio.TimeoutError:
                raise TimeoutError("Task group planning timed out")
            except Exception as e:
                raise e
            try:
                task_groups_data = json.loads(response.content)
                if not isinstance(task_groups_data, list):
                    raise ValueError("Expected an array of task groups")
                break  # Successfully parsed JSON
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == max_retries:
                    raise ValueError(
                        f"Failed to get valid task groups after retries: {e}"
                    )
                print(f"⚠️  Attempt {attempt} returned invalid task groups. Retrying...")
                continue
        print(f"✅ Created {len(task_groups_data)} task groups")

        # Set up the session-local todo file and manager
        set_global_todo_file(str(todo_file_path))
        manager = get_todo_manager()

        # Create task groups in the manager
        for group_data in task_groups_data:
            manager.create_task_group(
                group_id=group_data["group_id"],
                specialization=group_data["specialization"],
                description=group_data.get("description", ""),
                dependencies=group_data.get("dependencies", []),
            )

        # Inject experiment execution group ONLY in research mode so experiments are always run there
        try:
            if is_research:
                existing_ids = {g.group_id for g in manager.plan.task_groups}
                if "experiment_execution" not in existing_ids:
                    # Depend on all created groups
                    deps = [g_id for g_id in existing_ids]
                    manager.create_task_group(
                        group_id="experiment_execution",
                        specialization="experiment_runner",
                        description="Execute experiments from experiments.yaml and generate final research report.",
                        dependencies=deps,
                    )
        except Exception as e:
            print(f"⚠️  Could not inject experiment_execution group: {e}")

        # STAGE 2: Create todos for each task group
        print("📝 Stage 2: Creating todos for each task group...")
        todo_generator_prompt = self.prompts.get(
            "todo_generator_prompt", "You are a technical lead."
        )

        # Todo guidance: avoid hyperspecific micro-steps; allow any reasonable count
        todo_policy = (
            "\n\n[TODO GUIDANCE]\n"
            "- Avoid hyperspecific micro-steps; capture meaningful, deliverable tasks.\n"
            "- You may create as many todos as needed.\n"
            '- Return JSON array only: [{"title": "..."}]\n'
        )

        for group_data in task_groups_data + [
            {"group_id": "experiment_execution", "specialization": "experiment_runner"}
        ]:
            print(f"  📋 Creating todos for group: {group_data['group_id']}")

            system_prompt = _safe_format(
                todo_generator_prompt + todo_policy,
                group_id=group_data["group_id"],
                specialization=group_data["specialization"],
                description=group_data.get("description", ""),
                requirements=requirements,
                design=design,
                tools_context=tools_context,
                repo_context=repo_context or "",
            )

            messages = [
                Message(role="system", content=system_prompt),
                Message(
                    role="user",
                    content=(
                        f"Create specific todos for the '{group_data['group_id']}' task group.\n\n"
                        f"Repository Context (read-only):\n{(repo_context or '')}"
                    ),
                ),
            ]

            try:
                todos_data = None
                for attempt in range(1, max_retries + 1):
                    try:
                        response = await asyncio.wait_for(
                            self.provider.chat(messages=messages), timeout=180
                        )
                    except asyncio.TimeoutError:
                        raise TimeoutError(
                            f"Todo generation timed out for {group_data['group_id']}"
                        )
                    except Exception as e:
                        raise e
                    try:
                        todos_data_raw = json.loads(response.content)
                        if not isinstance(todos_data_raw, list):
                            raise ValueError("Expected an array of todo objects")
                        # Normalize todos into dicts with 'title'
                        normalized_todos: List[Dict[str, str]] = []
                        for todo in todos_data_raw:
                            title_val = None
                            if isinstance(todo, dict):
                                title_val = (
                                    todo.get("title")
                                    or todo.get("name")
                                    or todo.get("task")
                                )
                            elif isinstance(todo, str):
                                title_val = todo
                            if not title_val:
                                title_val = str(todo)
                            normalized_todos.append({"title": title_val})
                        todos_data = normalized_todos
                        break  # Successfully parsed JSON
                    except (json.JSONDecodeError, ValueError) as e:
                        if attempt == max_retries:
                            raise ValueError(
                                f"Failed to get valid todos for group {group_data['group_id']}: {e}"
                            )
                        print(
                            f"⚠️  Attempt {attempt} returned invalid todos for {group_data['group_id']}. Retrying..."
                        )
                        continue

                # Normalize titles only (no truncation of count)
                if isinstance(todos_data, list):
                    pass

                # Add todos to the group
                for todo_data in todos_data:
                    if isinstance(todo_data, dict):
                        t = (
                            todo_data.get("title")
                            or todo_data.get("name")
                            or todo_data.get("task")
                        )
                    else:
                        t = None
                    # Final sanitization: trim and enforce concise titles
                    title = (t or str(todo_data)).strip()
                    # Prefer concise titles; trim softly if extremely long
                    if len(title.split()) > 20:
                        title = " ".join(title.split()[:20])
                    try:
                        manager.add_todo_to_group(
                            group_id=group_data["group_id"], title=title
                        )
                    except Exception as e:
                        print(f"⚠️  Skipping todo due to error: {e}")
                        continue

                print(
                    f"    ✅ Added {len(todos_data)} lightweight todos to {group_data['group_id']}"
                )
            except Exception as e:
                # Strict: no silent fallbacks
                raise e
        # Ensure experiment execution has at least one mandatory todo to write and run the runner script
        try:
            manager = get_todo_manager()
            exp_group = manager.get_task_group("experiment_execution")
            if exp_group and not exp_group.todos:
                manager.add_todo_to_group(
                    "experiment_execution",
                    "Create and run experiment runner script; execute experiments and log results",
                )
                print("🧪 Ensured mandatory experiment runner todo exists")
        except Exception:
            pass

        print("✅ Two-stage todo creation completed successfully!")

    def _generate_live_repo_map(self, path=".", max_depth=None, max_tokens=None):
        max_depth = (
            max_depth
            or get_config_manager().get_cached_config().limits.get("max_depth", 3)
            if hasattr(get_config_manager().get_cached_config(), "limits")
            else 3
        )
        # Fallback tokens if not configured
        try:
            from .unified_config import (
                get_config,
            )  # local import to avoid cycle at module import time

            max_tokens = max_tokens or get_config("limits.context_max_tokens", 4000)
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
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                functions: List[str] = []
                if file_path.suffix == ".py":
                    func_pattern = r"^(def\s+\w+\([^)]*\):|class\s+\w+[^:]*:)"
                    for match in re.finditer(func_pattern, content, re.MULTILINE):
                        functions.append(match.group(1).strip())
                elif file_path.suffix in [".js", ".ts", ".jsx", ".tsx"]:
                    func_patterns = [
                        r"function\s+\w+\s*\([^)]*\)",
                        r"const\s+\w+\s*=\s*\([^)]*\)\s*=>",
                        r"class\s+\w+",
                        r"export\s+function\s+\w+\s*\([^)]*\)",
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

        def scan_directory(
            dir_path: _P, current_depth: int = 0, prefix: str = ""
        ) -> None:
            nonlocal current_tokens
            if current_depth > max_depth or current_tokens >= max_tokens:
                return
            try:
                items = sorted(dir_path.iterdir())
                for item in items:
                    if current_tokens >= max_tokens:
                        break
                    if item.name.startswith(".") and item.name not in [
                        ".gitignore",
                        ".env.example",
                    ]:
                        continue
                    if item.is_file():
                        try:
                            size = item.stat().st_size
                        except Exception:
                            size = 0
                        line = f"{prefix}📄 {item.name} ({size} bytes)"
                        if (
                            item.suffix in [".py", ".js", ".ts", ".jsx", ".tsx"]
                            and size < 50000
                        ):
                            funcs = extract_functions(item)
                            if funcs:
                                line += f" - Functions: {', '.join(funcs)}"
                        line_tokens = count_tokens(line + "\n")
                        if current_tokens + line_tokens > max_tokens - 100:
                            repo_map.append(
                                f"{prefix}... (truncated - token limit reached)"
                            )
                            return
                        repo_map.append(line)
                        current_tokens += line_tokens
                    elif item.is_dir():
                        dir_line = f"{prefix}📁 {item.name}/"
                        line_tokens = count_tokens(dir_line + "\n")
                        if current_tokens + line_tokens > max_tokens - 100:
                            repo_map.append(
                                f"{prefix}... (truncated - token limit reached)"
                            )
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
