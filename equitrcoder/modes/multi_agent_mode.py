# equitrcoder/modes/multi_agent_mode.py

import asyncio
from typing import Any, Callable, Dict, List, Optional
from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..tools.discovery import discover_tools
from ..core.global_message_pool import global_message_pool
from ..tools.builtin.communication import create_communication_tools_for_agent
from ..tools.builtin.todo import set_global_todo_file, todo_manager
from ..utils.git_manager import GitManager
from ..core.profile_manager import ProfileManager

class MultiAgentMode:
    """Manages multi-agent execution with dependency-aware phasing and auto-commits."""
    
    def __init__(self, num_agents: int, agent_model: str, orchestrator_model: str, audit_model: str, max_cost_per_agent: Optional[float], max_iterations_per_agent: Optional[int], run_parallel: bool, auto_commit: bool):
        self.num_agents = num_agents
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost_per_agent = max_cost_per_agent
        self.max_iterations_per_agent = max_iterations_per_agent
        self.run_parallel = run_parallel
        self.auto_commit = auto_commit # <-- NEW PROPERTY
        self.profile_manager = ProfileManager()
        print(f"🎭 Multi-Agent Mode ({'Parallel Phased' if run_parallel else 'Sequential Group'}): Auto-commit is {'ON' if self.auto_commit else 'OFF'}")
        print(f"   Agent Model: {agent_model}, Audit Model: {audit_model}")
    
    async def run(self, task_description: str, project_path: str = ".", callbacks: Optional[Dict[str, Callable]] = None, team: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            docs_result = await orchestrator.create_docs(
                task_description=task_description, 
                project_path=project_path,
                team=team
            )
            if not docs_result["success"]:
                return {"success": False, "error": f"Documentation failed: {docs_result['error']}", "stage": "planning"}
            
            # --- NEW GIT MANAGER INITIALIZATION ---
            git_manager = GitManager(repo_path=project_path)
            if self.auto_commit:
                git_manager.ensure_repo_is_ready()
            
            print("🚀 Step 2: Starting phased execution of the plan...")
            set_global_todo_file(docs_result['todos_path'])
            
            phase_num = 1
            while not todo_manager.are_all_tasks_complete():
                runnable_groups = todo_manager.get_next_runnable_groups()
                if not runnable_groups:
                    break
                
                print(f"\n--- EXECUTING PHASE {phase_num} ({len(runnable_groups)} task groups in parallel) ---")
                
                agent_coroutines = [self._execute_task_group(group, docs_result, callbacks) for group in runnable_groups]
                phase_results = await asyncio.gather(*agent_coroutines)
                
                if any(not result.get("success") for result in phase_results):
                    print(f"❌ PHASE {phase_num} FAILED. Halting execution.")
                    return {"success": False, "error": f"A task in phase {phase_num} failed.", "stage": "execution"}
                
                # --- NEW COMMIT LOGIC ---
                if self.auto_commit:
                    group_data = [g.model_dump() for g in runnable_groups]
                    git_manager.commit_phase_completion(phase_num, group_data)
                
                print(f"✅ PHASE {phase_num} COMPLETED SUCCESSFULLY ---")
                phase_num += 1
            
            return {"success": True, "docs_result": docs_result, "total_phases": phase_num - 1}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_task_group(self, group, docs_result, callbacks):
        agent_id = f"{group.specialization}_agent_{group.group_id}"
        await global_message_pool.register_agent(agent_id)

        # --- Profile-based Agent Configuration ---
        try:
            profile = self.profile_manager.get_profile(group.specialization)
            system_prompt = profile.get('system_prompt', "You are a helpful assistant.")
            allowed_tool_names = profile.get('allowed_tools', [])
        except ValueError:
            print(f"Warning: Profile '{group.specialization}' not found. Using default agent configuration.")
            system_prompt = "You are a helpful assistant."
            allowed_tool_names = [t.name for t in discover_tools()] # Default to all tools

        # Filter tools based on the profile
        all_available_tools = discover_tools()
        agent_tools = [tool for tool in all_available_tools if tool.name in allowed_tool_names]
        
        # Add communication tools, as they are essential for coordination
        communication_tools = create_communication_tools_for_agent(agent_id)
        agent_tools.extend(communication_tools)
        
        # --- Instantiate Agent with Profile ---
        agent = CleanAgent(
            agent_id=agent_id,
            model=self.agent_model,
            tools=agent_tools,
            context=docs_result,
            max_cost=self.max_cost_per_agent,
            max_iterations=self.max_iterations_per_agent,
            audit_model=self.audit_model
        )
        if callbacks:
            agent.set_callbacks(**callbacks)
        
        # The task description now supplements the base system prompt from the profile
        group_task_desc = f"""{system_prompt}

Your current mission is to complete your part of a larger project.
Your specific objective is to complete all todos in the '{group.description}' task group.
Use `list_todos_in_group` with group_id='{group.group_id}' to see your tasks.
Coordinate with other agents using `send_message` if you need information or need to signal completion of a dependency.
Complete each todo and mark it done with `update_todo_status`.
Make sure to only use the tools you have been given.
"""
        result = await agent.run(group_task_desc)
        if not result.get("success"):
            todo_manager.update_task_group_status(group.group_id, "failed")
        return result

async def run_multi_agent_sequential(**kwargs) -> Dict[str, Any]:
    config = {'run_parallel': False, 'auto_commit': True, **kwargs}
    mode = MultiAgentMode(**config)
    return await mode.run(task_description=kwargs.get("task_description", ""), team=kwargs.get("team"))

async def run_multi_agent_parallel(**kwargs) -> Dict[str, Any]:
    config = {'run_parallel': True, 'auto_commit': True, **kwargs}
    mode = MultiAgentMode(**config)
    return await mode.run(task_description=kwargs.get("task_description", ""), team=kwargs.get("team"))