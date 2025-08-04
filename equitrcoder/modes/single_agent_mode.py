# equitrcoder/modes/single_agent_mode.py

from typing import Any, Callable, Dict, Optional
from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..tools.discovery import discover_tools
from ..tools.builtin.todo import todo_manager, set_global_todo_file
from ..utils.git_manager import GitManager # <-- NEW IMPORT

class SingleAgentMode:
    """Runs a single agent that executes task groups sequentially based on dependencies."""
    
    def __init__(self, agent_model: str, orchestrator_model: str, audit_model: str, max_cost: Optional[float], max_iterations: Optional[int], auto_commit: bool):
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        self.auto_commit = auto_commit # <-- NEW PROPERTY
        print(f"🎭 Single Agent Mode (Dependency-Aware): Auto-commit is {'ON' if self.auto_commit else 'OFF'}")
        print(f"   Agent Model: {agent_model}, Audit Model: {audit_model}")
    
    async def run(self, task_description: str, project_path: str = ".", callbacks: Optional[Dict[str, Callable]] = None) -> Dict[str, Any]:
        try:
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            docs_result = await orchestrator.create_docs(task_description=task_description, project_path=project_path)
            if not docs_result["success"]:
                return {"success": False, "error": f"Documentation failed: {docs_result['error']}", "stage": "planning"}
            
            # --- NEW GIT MANAGER INITIALIZATION ---
            git_manager = GitManager(repo_path=project_path)
            if self.auto_commit:
                git_manager.ensure_repo_is_ready()
            
            tools = discover_tools()
            agent = CleanAgent(
                agent_id="single_agent", model=self.agent_model, tools=tools, context=docs_result,
                max_cost=self.max_cost, max_iterations=self.max_iterations, audit_model=self.audit_model,
            )
            if callbacks: agent.set_callbacks(**callbacks)
            
            print("🚀 Step 3: Agent starting sequential execution of task groups...")
            set_global_todo_file(docs_result['todos_path'])
            
            while not todo_manager.are_all_tasks_complete():
                runnable_groups = todo_manager.get_next_runnable_groups()
                if not runnable_groups:
                    break
                
                group_to_run = runnable_groups[0]
                print(f"\n--- Starting Task Group: {group_to_run.group_id} ({group_to_run.specialization}) ---")
                
                todo_manager.update_task_group_status(group_to_run.group_id, 'in_progress')
                
                group_task_desc = f"""Your current objective is to complete all todos in the '{group_to_run.description}' task group.

Use the `list_todos_in_group` tool with group_id='{group_to_run.group_id}' to see your tasks.

Complete each task and mark it as 'completed' using the `update_todo_status` tool. When all todos in this group are done, the group will be marked as complete automatically, unlocking the next set of tasks.
"""
                
                agent_result = await agent.run(group_task_desc)
                
                if not agent_result.get("success"):
                    todo_manager.update_task_group_status(group_to_run.group_id, 'failed')
                    return {"success": False, "error": f"Agent failed on group {group_to_run.group_id}", "stage": "execution"}
                
                # --- NEW COMMIT LOGIC ---
                if self.auto_commit:
                    git_manager.commit_task_group_completion(group_to_run.model_dump())
            
            print("🎯 Agent has completed all task groups.")
            return {"success": True, "docs_result": docs_result, "agent_result": agent.get_status()}
        
        except Exception as e:
            return {"success": False, "error": str(e), "mode": "single_agent"}

async def run_single_agent_mode(**kwargs) -> Dict[str, Any]:
    # We now expect auto_commit to be passed in
    config = {
        "agent_model": "moonshot/kimi-k2-0711-preview",
        "orchestrator_model": "moonshot/kimi-k2-0711-preview",
        "audit_model": "o3",
        "max_cost": None,
        "max_iterations": None,
        "auto_commit": True,
        **kwargs
    }
    mode = SingleAgentMode(**config)
    return await mode.run(task_description=kwargs.get("task_description", ""), project_path=kwargs.get("project_path", "."))