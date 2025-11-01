# equitrcoder/programmatic/interface.py

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.model_manager import model_manager
from ..core.session import SessionManagerV2
from ..core.unified_config import get_config_manager
from ..modes.multi_agent_mode import (
    run_multi_agent_parallel,
    run_multi_agent_sequential,
)
from ..modes.researcher_mode import run_researcher_mode
from ..modes.single_agent_mode import run_single_agent_mode
from ..utils.git_manager import GitManager


@dataclass
class TaskConfiguration:
    """Configuration for a single task execution."""

    description: str
    max_cost: float = 2.0
    max_iterations: int = 20
    session_id: Optional[str] = None
    model: Optional[str] = None
    auto_commit: bool = True


@dataclass
class MultiAgentTaskConfiguration:
    """Configuration for multi-agent task execution."""

    description: str
    max_workers: int = 3
    max_cost: float = 10.0
    max_iterations: int = 50
    supervisor_model: Optional[str] = None
    worker_model: Optional[str] = None
    auto_commit: bool = True
    team: Optional[List[str]] = None
    run_parallel: bool = True
    session_id: Optional[str] = None


@dataclass
class ResearchTaskConfiguration:
    """Configuration for researcher mode execution."""

    description: str
    max_workers: int = 3
    max_cost: float = 12.0
    max_iterations: int = 50
    supervisor_model: Optional[str] = None
    worker_model: Optional[str] = None
    auto_commit: bool = True
    team: Optional[List[str]] = None
    # Optional pre-filled research context (for TUI to avoid interactive prompts)
    research_context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of task execution."""

    success: bool
    content: str
    cost: float
    iterations: int
    session_id: str
    execution_time: float
    error: Optional[str] = None
    git_committed: bool = False
    commit_hash: Optional[str] = None
    conversation_history: Optional[List[dict]] = None
    tool_call_history: Optional[List[dict]] = None
    llm_responses: Optional[List[dict]] = None


class EquitrCoder:
    """Main programmatic interface for EQUITR Coder."""

    def __init__(
        self,
        repo_path: str = ".",
        git_enabled: bool = True,
        mode: str = "single",
        max_workers: int = 2,
        supervisor_model: Optional[str] = None,
        worker_model: Optional[str] = None,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.git_enabled = git_enabled
        self.mode = mode
        self.max_workers = max_workers
        self.supervisor_model = supervisor_model
        self.worker_model = worker_model
        self.config = get_config_manager().get_cached_config()
        # Resolve session dir from unified config dicts
        try:
            session_dir = (
                self.config.session.get("session_dir")
                if isinstance(self.config.session, dict)
                else None
            )
        except Exception:
            session_dir = None
        session_dir = session_dir or "~/.EQUITR-coder/sessions"
        self.session_manager = SessionManagerV2(session_dir)
        if self.git_enabled:
            self.git_manager = GitManager(str(self.repo_path))
            self.git_manager.ensure_repo_is_ready()

    # --- Convenience getters expected by tests ---
    def check_available_api_keys(self) -> Dict[str, bool]:
        providers = [
            ("openai", "OPENAI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("moonshot", "MOONSHOT_API_KEY"),
            ("openrouter", "OPENROUTER_API_KEY"),
            ("groq", "GROQ_API_KEY"),
        ]
        import os

        return {name: bool(os.getenv(env)) for name, env in providers}

    async def check_model_availability(
        self, model: str, test_call: bool = False
    ) -> bool:
        result = await model_manager.validate_model(model, test_call=test_call)
        return result.is_valid

    def list_sessions(self) -> List[Dict[str, Any]]:
        return self.session_manager.list_sessions()

    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.session_manager.load_session(session_id)
        if not session:
            return None
        return {
            "session_id": session.session_id,
            "messages": [
                (
                    m.model_dump()
                    if hasattr(m, "model_dump")
                    else getattr(m, "__dict__", {})
                )
                for m in session.messages
            ],
            "cost": session.cost,
            "iterations": session.iteration_count,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    def get_git_status(self) -> Dict[str, Any]:
        if not self.git_enabled:
            return {"error": "Git is disabled"}
        try:
            import subprocess

            out = subprocess.run(
                ["git", "status", "--porcelain", "-b"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            branch = "HEAD"
            lines = out.stdout.splitlines()
            if lines and lines[0].startswith("## "):
                branch = lines[0][3:]
            return {
                "branch": branch,
                "dirty": any(line and not line.startswith("## ") for line in lines),
                "raw": out.stdout,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_recent_commits(self, n: int = 5) -> List[str]:
        if not self.git_enabled:
            return []
        try:
            import subprocess

            out = subprocess.run(
                ["git", "--no-pager", "log", f"-{n}", "--pretty=%h %s"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            return [line for line in out.stdout.splitlines() if line.strip()]
        except Exception:
            return []

    async def cleanup(self) -> None:
        await self.session_manager.cleanup()

    async def _execute_single_task(
        self, task_description: str, config: Optional[TaskConfiguration]
    ) -> ExecutionResult:
        start_time = datetime.now()
        try:
            cfg = config or TaskConfiguration(description=task_description)
            supervisor_model = cfg.model or "moonshot/kimi-k2-0711-preview"
            result_data = await run_single_agent_mode(
                task_description=task_description,
                agent_model=cfg.model or "moonshot/kimi-k2-0711-preview",
                orchestrator_model=supervisor_model,
                audit_model=supervisor_model,
                project_path=self.repo_path,
                max_cost=cfg.max_cost,
                max_iterations=cfg.max_iterations,
                auto_commit=cfg.auto_commit,
            )
            commit_hash = result_data.get("commit_hash")
            exec_result = (
                result_data.get("execution_result", {})
                if isinstance(result_data.get("execution_result"), dict)
                else {}
            )
            return ExecutionResult(
                success=result_data.get("success", False),
                content=str(result_data),
                cost=result_data.get("cost", 0.0),
                iterations=result_data.get("iterations", 0),
                session_id=result_data.get("session_id", "N/A"),
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=result_data.get("error"),
                git_committed=bool(commit_hash),
                commit_hash=commit_hash,
                conversation_history=exec_result.get("messages", []),
                tool_call_history=exec_result.get("tool_calls", []),
                llm_responses=exec_result.get("llm_responses", []),
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=str(e),
            )

    async def execute_task(
        self,
        task_description: str,
        config: Union[
            TaskConfiguration,
            MultiAgentTaskConfiguration,
            ResearchTaskConfiguration,
            None,
        ] = None,
    ) -> ExecutionResult:
        start_time = datetime.now()

        try:
            # Route testable path: when no config is provided, delegate based on mode
            if config is None:
                if self.mode == "single":
                    return await self._execute_single_task(task_description, None)
                elif self.mode == "multi":
                    # Build default multi-agent config
                    config = MultiAgentTaskConfiguration(
                        description=task_description,
                        max_workers=self.max_workers,
                        supervisor_model=self.supervisor_model,
                        worker_model=self.worker_model,
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        content="",
                        cost=0.0,
                        iterations=0,
                        session_id="error",
                        execution_time=0.0,
                        error=f"Invalid mode: {self.mode}",
                    )

            if isinstance(config, TaskConfiguration):
                return await self._execute_single_task(task_description, config)

            elif isinstance(config, MultiAgentTaskConfiguration):
                supervisor_model = config.supervisor_model or "gpt-4o-mini"
                runner = (
                    run_multi_agent_parallel
                    if config.run_parallel
                    else run_multi_agent_sequential
                )
                # Ensure 'default' profile is always part of the team for planning
                effective_team = list(config.team) if config.team else []
                if "default" not in effective_team:
                    effective_team.append("default")
                result_data = await runner(
                    task_description=task_description,
                    num_agents=config.max_workers,
                    agent_model=config.worker_model or "moonshot/kimi-k2-0711-preview",
                    orchestrator_model=supervisor_model,
                    audit_model=supervisor_model,
                    project_path=self.repo_path,
                    max_cost_per_agent=config.max_cost / max(1, config.max_workers),
                    max_iterations_per_agent=config.max_iterations,
                    auto_commit=config.auto_commit,
                    team=effective_team,
                    session_id=config.session_id,
                )
            elif isinstance(config, ResearchTaskConfiguration):
                supervisor_model = (
                    config.supervisor_model or "moonshot/kimi-k2-0711-preview"
                )
                # Ensure 'default' profile is always part of the team for planning
                effective_team = list(config.team) if config.team else []
                if "default" not in effective_team:
                    effective_team.append("default")
                result_data = await run_researcher_mode(
                    task_description=task_description,
                    num_agents=config.max_workers,
                    agent_model=config.worker_model or "moonshot/kimi-k2-0711-preview",
                    orchestrator_model=supervisor_model,
                    audit_model=supervisor_model,
                    project_path=self.repo_path,
                    max_cost_per_agent=config.max_cost / max(1, config.max_workers),
                    max_iterations_per_agent=config.max_iterations,
                    auto_commit=config.auto_commit,
                    team=effective_team,
                    research_context=config.research_context,
                    session_id=config.session_id,
                )
            else:
                raise TypeError(
                    "Configuration must be TaskConfiguration or MultiAgentTaskConfiguration"
                )

            commit_hash = result_data.get("commit_hash")
            conversation_history = None
            tool_call_history = None
            llm_responses = None
            return ExecutionResult(
                success=result_data.get("success", False),
                content=str(result_data),
                cost=float(result_data.get("cost", 0.0) or 0.0),
                iterations=result_data.get("iterations", 0),
                session_id=result_data.get("session_id", "N/A"),
                execution_time=float(
                    result_data.get("execution_time")
                    or (datetime.now() - start_time).total_seconds()
                ),
                error=result_data.get("error"),
                git_committed=bool(commit_hash),
                commit_hash=commit_hash,
                conversation_history=conversation_history,
                tool_call_history=tool_call_history,
                llm_responses=llm_responses,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=str(e),
            )


# Convenience factory functions updated per tests
def create_single_agent_coder(**kwargs) -> EquitrCoder:
    return EquitrCoder(mode="single", **kwargs)


def create_multi_agent_coder(**kwargs) -> EquitrCoder:
    mapped = dict(kwargs)
    mapped["mode"] = "multi"
    return EquitrCoder(**mapped)


def create_research_coder(**kwargs) -> EquitrCoder:
    mapped = dict(kwargs)
    mapped["mode"] = "research"
    return EquitrCoder(**mapped)
