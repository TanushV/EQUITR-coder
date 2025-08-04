# equitrcoder/programmatic/interface.py

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
from ..core.config import config_manager
from ..modes.single_agent_mode import run_single_agent_mode
from ..modes.multi_agent_mode import run_multi_agent_sequential, run_multi_agent_parallel
from ..utils.git_manager import GitManager
from ..core.session import SessionData, SessionManagerV2

@dataclass
class TaskConfiguration:
    """Configuration for a single task execution."""
    description: str
    max_cost: float = 2.0
    max_iterations: int = 20
    session_id: Optional[str] = None
    model: Optional[str] = None
    auto_commit: bool = True # <-- ADDED THIS FLAG

@dataclass
class MultiAgentTaskConfiguration:
    """Configuration for multi-agent task execution."""
    description: str
    num_agents: int = 3
    max_cost: float = 10.0
    supervisor_model: Optional[str] = None
    worker_model: Optional[str] = None
    auto_commit: bool = True # <-- ADDED THIS FLAG

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

class EquitrCoder:
    """Main programmatic interface for EQUITR Coder."""
    
    def __init__(self, repo_path: str = ".", git_enabled: bool = True):
        self.repo_path = Path(repo_path).resolve()
        self.git_enabled = git_enabled
        self.config = config_manager.load_config()
        self.session_manager = SessionManagerV2(self.config.session.session_dir)
        if self.git_enabled:
            self.git_manager = GitManager(str(self.repo_path))
            self.git_manager.ensure_repo_is_ready()
    
    async def execute_task(self, task_description: str, config: Union[TaskConfiguration, MultiAgentTaskConfiguration]) -> ExecutionResult:
        start_time = datetime.now()
        
        try:
            if isinstance(config, TaskConfiguration):
                result_data = await run_single_agent_mode(
                    task_description=task_description,
                    agent_model=config.model or "moonshot/kimi-k2-0711-preview",
                    orchestrator_model=config.model or "moonshot/kimi-k2-0711-preview",
                    audit_model=config.model or "o3",
                    project_path=self.repo_path,
                    max_cost=config.max_cost,
                    max_iterations=config.max_iterations,
                    auto_commit=config.auto_commit # Pass the flag
                )
            elif isinstance(config, MultiAgentTaskConfiguration):
                result_data = await run_multi_agent_parallel(
                    task_description=task_description,
                    num_agents=config.num_agents,
                    agent_model=config.worker_model or "moonshot/kimi-k2-0711-preview",
                    orchestrator_model=config.worker_model or "moonshot/kimi-k2-0711-preview",
                    audit_model=config.supervisor_model or "o3",
                    project_path=self.repo_path,
                    max_cost_per_agent=config.max_cost / config.num_agents,
                    auto_commit=config.auto_commit # Pass the flag
                )
            else:
                raise TypeError("Configuration must be TaskConfiguration or MultiAgentTaskConfiguration")
            
            # The commit hash would be returned from the mode runner if successful
            commit_hash = result_data.get("commit_hash")
            
            return ExecutionResult(
                success=result_data.get("success", False),
                content=str(result_data),
                cost=result_data.get("cost", 0.0),
                iterations=result_data.get("iterations", 0),
                session_id=result_data.get("session_id", "N/A"),
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=result_data.get("error"),
                git_committed=bool(commit_hash),
                commit_hash=commit_hash
            )
        except Exception as e:
            return ExecutionResult(
                success=False, content="", cost=0.0, iterations=0, session_id="error",
                execution_time=(datetime.now() - start_time).total_seconds(), error=str(e)
            )

# Convenience factory functions (remain unchanged)
def create_single_agent_coder(**kwargs) -> EquitrCoder:
    return EquitrCoder(**kwargs)

def create_multi_agent_coder(**kwargs) -> EquitrCoder:
    return EquitrCoder(**kwargs)