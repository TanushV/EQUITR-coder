# equitrcoder/programmatic/interface.py

from dataclasses import dataclass
from typing import Optional, Union, List
from pathlib import Path
from datetime import datetime
from ..core.config import config_manager
from ..modes.single_agent_mode import run_single_agent_mode
from ..modes.multi_agent_mode import run_multi_agent_parallel
from ..utils.git_manager import GitManager
from ..core.session import SessionManagerV2

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
    max_iterations: int = 50  # New field with default 50
    supervisor_model: Optional[str] = None
    worker_model: Optional[str] = None
    auto_commit: bool = True # <-- ADDED THIS FLAG
    team: Optional[List[str]] = None  # List of agent profile names to use

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
    # New fields for LLM response visibility
    conversation_history: Optional[List[dict]] = None
    tool_call_history: Optional[List[dict]] = None
    llm_responses: Optional[List[dict]] = None

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
                supervisor_model = config.model or "moonshot/kimi-k2-0711-preview"
                result_data = await run_single_agent_mode(
                    task_description=task_description,
                    agent_model=config.model or "moonshot/kimi-k2-0711-preview",
                    orchestrator_model=supervisor_model,
                    audit_model=supervisor_model,  # Always use supervisor model for audit
                    project_path=self.repo_path,
                    max_cost=config.max_cost,
                    max_iterations=config.max_iterations,
                    auto_commit=config.auto_commit # Pass the flag
                )
            elif isinstance(config, MultiAgentTaskConfiguration):
                supervisor_model = config.supervisor_model or "gpt-4o-mini"
                result_data = await run_multi_agent_parallel(
                    task_description=task_description,
                    num_agents=config.num_agents,
                    agent_model=config.worker_model or "moonshot/kimi-k2-0711-preview",
                    orchestrator_model=supervisor_model,
                    audit_model=supervisor_model,  # Always use supervisor model for audit
                    project_path=self.repo_path,
                    max_cost_per_agent=config.max_cost / config.num_agents,
                    max_iterations_per_agent=config.max_iterations,
                    auto_commit=config.auto_commit, # Pass the flag
                    team=config.team  # Pass the team profiles
                )
            else:
                raise TypeError("Configuration must be TaskConfiguration or MultiAgentTaskConfiguration")
            
            # The commit hash would be returned from the mode runner if successful
            commit_hash = result_data.get("commit_hash")
            
            # Extract detailed LLM response data if available
            conversation_history = None
            tool_call_history = None
            llm_responses = None
            
            # For single agent mode, extract from execution_result
            if isinstance(config, TaskConfiguration) and "execution_result" in result_data:
                exec_result = result_data["execution_result"]
                if isinstance(exec_result, dict):
                    conversation_history = exec_result.get("messages", [])
                    tool_call_history = exec_result.get("tool_calls", [])
                    llm_responses = exec_result.get("llm_responses", [])
            
            # For multi-agent mode, we'd need to collect from all agents
            elif isinstance(config, MultiAgentTaskConfiguration):
                # TODO: Implement multi-agent response collection
                # This would require changes to the multi-agent mode to return agent details
                pass
            
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
                conversation_history=conversation_history,
                tool_call_history=tool_call_history,
                llm_responses=llm_responses
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