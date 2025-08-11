# equitrcoder/modes/multi_agent_mode.py

import asyncio
# import yaml  # Unused
from datetime import datetime
# from pathlib import Path  # Unused
from typing import Any, Callable, Dict, List, Optional
from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..tools.discovery import discover_tools
from ..core.global_message_pool import global_message_pool
from ..tools.builtin.communication import create_communication_tools_for_agent
from ..tools.builtin.todo import set_global_todo_file, get_todo_manager
from ..utils.git_manager import GitManager
from ..core.profile_manager import ProfileManager
from ..core.unified_config import get_config_manager

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
        self.system_prompts = self._load_system_prompts()
        self.global_cost = 0.0  # Track total cost across all agents
        print(f"🎭 Multi-Agent Mode ({'Parallel Phased' if run_parallel else 'Sequential Group'}): Auto-commit is {'ON' if self.auto_commit else 'OFF'}")
        print(f"   Agent Model: {agent_model}, Audit Model: {audit_model}")
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts from unified configuration."""
        config_manager = get_config_manager()
        config_data = config_manager.get_cached_config()
        
        # Get prompts from unified configuration
        prompts = config_data.prompts
        
        # Return prompts with fallbacks
        return {
            'single_agent_prompt': prompts.get('single_agent_prompt', 'You are working on a single task group. Complete all todos systematically.'),
            'multi_agent_prompt': prompts.get('multi_agent_prompt', 'You are part of a team. Coordinate with other agents.')
        }
    
    async def run(self, task_description: str, project_path: str = ".", callbacks: Optional[Dict[str, Callable]] = None, team: Optional[List[str]] = None, task_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            docs_result = await orchestrator.create_docs(
                task_description=task_description,
                project_path=project_path,
                task_name=task_name,
                team=team,
            )
            if not docs_result["success"]:
                return {"success": False, "error": f"Documentation failed: {docs_result['error']}", "stage": "planning"}
            
            # --- NEW GIT MANAGER INITIALIZATION ---
            git_manager = GitManager(repo_path=project_path)
            if self.auto_commit:
                git_manager.ensure_repo_is_ready()
            
            print("🚀 Step 2: Starting phased execution of the plan...")
            set_global_todo_file(docs_result['todos_path'])
            
            # Change to project directory so tools work with correct relative paths
            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            phase_num = 1
            while not get_todo_manager().are_all_tasks_complete():
                runnable_groups = get_todo_manager().get_next_runnable_groups()
                if not runnable_groups:
                    break
                
                print(f"\n--- EXECUTING PHASE {phase_num} ({len(runnable_groups)} task groups in parallel) ---")
                print(f"💰 Global cost so far: ${self.global_cost:.4f}")
                
                agent_coroutines = [self._execute_task_group(group, docs_result, callbacks) for group in runnable_groups]
                phase_results = await asyncio.gather(*agent_coroutines)
                
                # Calculate phase cost and add to global cost
                phase_cost = sum(result.get("cost", 0.0) for result in phase_results)
                self.global_cost += phase_cost
                
                if any(not result.get("success") for result in phase_results):
                    print(f"❌ PHASE {phase_num} FAILED. Halting execution.")
                    print(f"💰 Phase {phase_num} cost: ${phase_cost:.4f} | Global cost: ${self.global_cost:.4f}")
                    return {"success": False, "error": f"A task in phase {phase_num} failed.", "stage": "execution", "cost": self.global_cost}
                
                # --- COMMIT AFTER EACH TASK GROUP ---
                if self.auto_commit:
                    for group in runnable_groups:
                        git_manager.commit_task_group_completion(group.model_dump())
                
                print(f"✅ PHASE {phase_num} COMPLETED SUCCESSFULLY")
                print(f"💰 Phase {phase_num} cost: ${phase_cost:.4f} | Global cost: ${self.global_cost:.4f}")
                phase_num += 1
            
            print(f"🎉 ALL PHASES COMPLETED! Global cost: ${self.global_cost:.4f}")
            return {"success": True, "docs_result": docs_result, "total_phases": phase_num - 1, "cost": self.global_cost}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except OSError as e:
                # Failed to change back to original directory, log but continue
                print(f"Warning: Failed to change back to original directory: {e}")
    
    async def _execute_task_group(self, group, docs_result, callbacks):
        specialization = group.specialization or 'default'
        agent_id = f"{specialization}_agent_{group.group_id}"
        await global_message_pool.register_agent(agent_id)

        # --- Profile-based Agent Configuration ---
        # Use the new ProfileManager method that handles both default and profile agents
        agent_config = self.profile_manager.get_agent_config(specialization)
        allowed_tool_names = agent_config.get('allowed_tools', [])
        
        if specialization == 'default':
            print("   Using default agent configuration")
        else:
            print(f"   Using profile: {specialization}")

        # Filter tools based on the agent configuration
        all_available_tools = discover_tools()
        agent_tools = [tool for tool in all_available_tools if tool.name in allowed_tool_names]
        
        # Add communication tools, as they are essential for coordination
        communication_tools = create_communication_tools_for_agent(agent_id)
        agent_tools.extend(communication_tools)
        
        # --- Instantiate Agent with Context ---
        # The CleanAgent will automatically build enhanced context from docs_result
        agent = CleanAgent(
            agent_id=agent_id,
            model=self.agent_model,
            tools=agent_tools,
            context=docs_result,
            max_cost=self.max_cost_per_agent,
            max_iterations=self.max_iterations_per_agent,
            audit_model=self.orchestrator_model  # Always use supervisor model for audit
        )
        if callbacks:
            agent.set_callbacks(**callbacks)
        
        # Get multi-agent prompt from config and format it
        multi_agent_prompt = self.system_prompts.get('multi_agent_prompt', 'You are part of a team. Coordinate with other agents.')
        group_task_desc = multi_agent_prompt.format(
            agent_id=agent_id,
            model=self.agent_model,
            group_description=group.description,
            group_id=group.group_id,
            specialization=group.specialization,
            available_tools=', '.join([tool.name for tool in agent_tools]),
            mandatory_context_json="{{mandatory_context_json}}",
            task_description="{{task_description}}"
        )
        print(f"\n🤖 Starting agent {agent_id} for group '{group.group_id}' ({group.specialization})")
        print(f"   Group Description: {group.description}")
        print(f"   Dependencies: {group.dependencies}")
        print(f"   Available Tools: {[tool.name for tool in agent_tools]}")
        
        start_time = datetime.now()
        result = await agent.run(group_task_desc)
        end_time = datetime.now()
        
        # Log detailed agent completion with comprehensive metrics
        agent_cost = result.get("cost", 0.0)
        agent_iterations = result.get("iterations", 0)
        execution_time = (end_time - start_time).total_seconds()
        success_icon = "✅" if result.get("success") else "❌"
        
        print(f"\n{success_icon} Agent {agent_id} COMPLETED:")
        print(f"   Cost: ${agent_cost:.4f}")
        print(f"   Iterations: {agent_iterations}")
        print(f"   Execution Time: {execution_time:.1f}s")
        print(f"   Success: {result.get('success', False)}")
        
        # Log communication tool usage
        tool_calls = result.get("tool_calls", [])
        ask_supervisor_calls = [tc for tc in tool_calls if tc.get("tool_name") == "ask_supervisor"]
        send_message_calls = [tc for tc in tool_calls if tc.get("tool_name") == "send_message"]
        
        print("   Communication Stats:")
        print(f"     ask_supervisor calls: {len(ask_supervisor_calls)}")
        print(f"     send_message calls: {len(send_message_calls)}")
        
        if len(ask_supervisor_calls) == 0:
            print(f"   ⚠️  WARNING: Agent {agent_id} made NO supervisor consultations!")
        if len(send_message_calls) == 0:
            print(f"   ⚠️  WARNING: Agent {agent_id} made NO inter-agent communications!")
        
        audit_res = result.get("audit_result", {})
        if audit_res and not audit_res.get("audit_passed", True):
            # Log audit issues and convert them into actionable todos (placeholder)
            print("🚨 Audit reported issues:\n", audit_res.get("audit_content", "No details"))
            # In future we could parse and add new todos. For now, continue execution.
            result["success"] = True
        # Note: We no longer mark task groups as "failed" - agents must persist until completion
        return result

async def run_multi_agent_sequential(**kwargs) -> Dict[str, Any]:
    # Separate runtime-only args from constructor kwargs
    task_desc = kwargs.pop("task_description", "")
    project_path = kwargs.pop("project_path", ".")
    team = kwargs.pop("team", None)
    config = {"run_parallel": False, "auto_commit": True, **kwargs}
    mode = MultiAgentMode(**config)
    return await mode.run(task_description=task_desc, project_path=project_path, team=team, task_name=kwargs.get("task_name"))

async def run_multi_agent_parallel(**kwargs) -> Dict[str, Any]:
    # Separate runtime-only args from constructor kwargs
    task_desc = kwargs.pop("task_description", "")
    project_path = kwargs.pop("project_path", ".")
    team = kwargs.pop("team", None)
    config = {"run_parallel": True, "auto_commit": True, **kwargs}
    mode = MultiAgentMode(**config)
    return await mode.run(task_description=task_desc, project_path=project_path, team=team, task_name=kwargs.get("task_name"))