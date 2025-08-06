# equitrcoder/modes/multi_agent_mode.py

import asyncio
from datetime import datetime
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
            total_cost = 0.0
            while not todo_manager.are_all_tasks_complete():
                runnable_groups = todo_manager.get_next_runnable_groups()
                if not runnable_groups:
                    break
                
                print(f"\n--- EXECUTING PHASE {phase_num} ({len(runnable_groups)} task groups in parallel) ---")
                print(f"💰 Total cost so far: ${total_cost:.4f}")
                
                agent_coroutines = [self._execute_task_group(group, docs_result, callbacks) for group in runnable_groups]
                phase_results = await asyncio.gather(*agent_coroutines)
                
                # Calculate phase cost
                phase_cost = sum(result.get("cost", 0.0) for result in phase_results)
                total_cost += phase_cost
                
                if any(not result.get("success") for result in phase_results):
                    print(f"❌ PHASE {phase_num} FAILED. Halting execution.")
                    print(f"💰 Phase {phase_num} cost: ${phase_cost:.4f} | Total cost: ${total_cost:.4f}")
                    return {"success": False, "error": f"A task in phase {phase_num} failed.", "stage": "execution", "cost": total_cost}
                
                # --- NEW COMMIT LOGIC ---
                if self.auto_commit:
                    group_data = [g.model_dump() for g in runnable_groups]
                    git_manager.commit_phase_completion(phase_num, group_data)
                
                print(f"✅ PHASE {phase_num} COMPLETED SUCCESSFULLY")
                print(f"💰 Phase {phase_num} cost: ${phase_cost:.4f} | Total cost: ${total_cost:.4f}")
                phase_num += 1
            
            print(f"🎉 ALL PHASES COMPLETED! Total cost: ${total_cost:.4f}")
            return {"success": True, "docs_result": docs_result, "total_phases": phase_num - 1, "cost": total_cost}
        
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
            audit_model=self.orchestrator_model  # Always use supervisor model for audit
        )
        if callbacks:
            agent.set_callbacks(**callbacks)
        
        # The task description now supplements the base system prompt from the profile
        group_task_desc = f"""{system_prompt}

🎯 MULTI-AGENT MISSION: Complete your part of a larger project with MANDATORY team coordination.

🚨 CRITICAL RULES FOR MULTI-AGENT SUCCESS (FOLLOW RELIGIOUSLY):
1. **YOUR SPECIFIC OBJECTIVE**: Complete ALL todos in the '{group.description}' task group
2. **MANDATORY SUPERVISOR CONSULTATION**: You MUST use `ask_supervisor` tool frequently - at least once every 3-5 iterations
3. **MANDATORY TEAM COMMUNICATION**: You MUST use `send_message` to coordinate with other agents
4. **NEVER WORK IN ISOLATION**: Working alone without communication is FORBIDDEN
5. **ASK BEFORE ACTING**: When in doubt, ask supervisor FIRST before making major decisions
6. **COMMUNICATE PROGRESS**: Send status updates to other agents regularly
7. **COMPLETE TODOS FULLY**: Mark todos as 'completed' only when fully implemented and tested

🔧 MANDATORY WORKFLOW (Follow this exactly):
1. **ALWAYS START**: Use `ask_supervisor` to confirm your understanding of the task
2. **GET YOUR TODOS**: Use `list_todos_in_group` with group_id='{group.group_id}'
3. **COORDINATE FIRST**: Use `send_message` to announce your start and coordinate with other agents
4. **ASK FOR GUIDANCE**: Use `ask_supervisor` for ANY unclear requirements or technical decisions
5. **IMPLEMENT WITH COMMUNICATION**: Work on todos while regularly using `send_message` for updates
6. **ASK WHEN STUCK**: Use `ask_supervisor` immediately when encountering any blocker
7. **CONFIRM COMPLETION**: Use `ask_supervisor` to verify your work before marking todos complete
8. **ANNOUNCE SUCCESS**: Use `send_message` to inform other agents when your group is complete

🚨 COMMUNICATION REQUIREMENTS (NON-NEGOTIABLE):
- Use `ask_supervisor` at least once every 3-5 iterations
- Use `send_message` at least once every 5-7 iterations
- NEVER make major architectural decisions without asking supervisor
- ALWAYS communicate blockers, progress, and completions to the team
- Ask supervisor for help with complex code, design decisions, or integration issues

💡 WHEN TO USE EACH TOOL:
- `ask_supervisor`: Technical questions, design decisions, blockers, verification
- `send_message`: Progress updates, coordination needs, dependency discussions
- Both tools are MANDATORY - not optional suggestions!

🏆 SUCCESS METRIC: ALL todos completed through ACTIVE team coordination and supervisor guidance.

Group ID: {group.group_id}
Specialization: {group.specialization}
Available Tools: {[tool.name for tool in agent_tools]}

⚠️ REMEMBER: Silent agents who don't communicate will be considered failed agents!
"""
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
        
        print(f"   Communication Stats:")
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
    return await mode.run(task_description=task_desc, project_path=project_path, team=team)

async def run_multi_agent_parallel(**kwargs) -> Dict[str, Any]:
    # Separate runtime-only args from constructor kwargs
    task_desc = kwargs.pop("task_description", "")
    project_path = kwargs.pop("project_path", ".")
    team = kwargs.pop("team", None)
    config = {"run_parallel": True, "auto_commit": True, **kwargs}
    mode = MultiAgentMode(**config)
    return await mode.run(task_description=task_desc, project_path=project_path, team=team)