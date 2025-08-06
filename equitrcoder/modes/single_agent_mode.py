# equitrcoder/modes/single_agent_mode.py

from datetime import datetime
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
                max_cost=self.max_cost, max_iterations=self.max_iterations, audit_model=self.orchestrator_model,
            )
            if callbacks:
                agent.set_callbacks(**callbacks)
            
            print("🚀 Step 3: Agent starting sequential execution of task groups...")
            set_global_todo_file(docs_result['todos_path'])
            
            total_cost = 0.0
            group_num = 1
            while not todo_manager.are_all_tasks_complete():
                runnable_groups = todo_manager.get_next_runnable_groups()
                if not runnable_groups:
                    break
                
                group_to_run = runnable_groups[0]
                print(f"\n--- TASK GROUP {group_num}: {group_to_run.group_id} ({group_to_run.specialization}) ---")
                print(f"💰 Total cost so far: ${total_cost:.4f}")
                
                todo_manager.update_task_group_status(group_to_run.group_id, 'in_progress')
                
                group_task_desc = f"""🎯 SINGLE-AGENT MISSION: Complete the '{group_to_run.description}' task group with supervisor guidance.

🚨 CRITICAL RULES FOR SUCCESS (FOLLOW RELIGIOUSLY):
1. **YOUR SPECIFIC OBJECTIVE**: Complete ALL todos in this task group
2. **MANDATORY SUPERVISOR CONSULTATION**: You MUST use `ask_supervisor` tool frequently - at least once every 3-5 iterations
3. **ASK BEFORE MAJOR DECISIONS**: When in doubt, ask supervisor FIRST before making architectural choices
4. **SYSTEMATIC APPROACH**: Work through each todo methodically with supervisor guidance
5. **COMPLETE IMPLEMENTATION**: Create actual working code, not just plans
6. **PERSISTENT EFFORT**: Keep trying different approaches until you succeed
7. **VERIFY WITH SUPERVISOR**: Ask supervisor to verify your work before marking todos complete

🔧 MANDATORY WORKFLOW (Follow this exactly):
1. **ALWAYS START**: Use `ask_supervisor` to confirm your understanding of the task group
2. **GET YOUR TODOS**: Use `list_todos_in_group` with group_id='{group_to_run.group_id}'
3. **ASK FOR GUIDANCE**: Use `ask_supervisor` for ANY unclear requirements or technical decisions
4. **IMPLEMENT WITH VERIFICATION**: Work on todos while regularly asking supervisor for feedback
5. **ASK WHEN STUCK**: Use `ask_supervisor` immediately when encountering any blocker
6. **CONFIRM COMPLETION**: Use `ask_supervisor` to verify your work before marking todos complete

🚨 SUPERVISOR CONSULTATION REQUIREMENTS (NON-NEGOTIABLE):
- Use `ask_supervisor` at least once every 3-5 iterations
- NEVER make major architectural decisions without asking supervisor
- ALWAYS ask supervisor when encountering technical challenges
- Ask supervisor for help with complex code, design decisions, or integration issues
- Verify your understanding of requirements with supervisor before starting

💡 WHEN TO USE `ask_supervisor`:
- Technical questions and design decisions
- Clarification of requirements or specifications
- When stuck on implementation details
- Before making major code changes
- To verify your work is on the right track
- When choosing between different approaches

🏆 SUCCESS METRIC: ALL todos completed through ACTIVE supervisor consultation and guidance.

Group ID: {group_to_run.group_id}
Specialization: {group_to_run.specialization}
Description: {group_to_run.description}

⚠️ REMEMBER: Silent agents who don't ask for guidance will struggle unnecessarily!
"""
                
                print(f"\n🤖 Starting work on group '{group_to_run.group_id}' ({group_to_run.specialization})")
                print(f"   Group Description: {group_to_run.description}")
                print(f"   Dependencies: {group_to_run.dependencies}")
                
                start_time = datetime.now()
                agent_result = await agent.run(group_task_desc)
                end_time = datetime.now()
                
                # Log detailed group completion with comprehensive metrics
                group_cost = agent_result.get("cost", 0.0)
                group_iterations = agent_result.get("iterations", 0)
                execution_time = (end_time - start_time).total_seconds()
                total_cost += group_cost
                success_icon = "✅" if agent_result.get("success") else "❌"
                
                print(f"\n{success_icon} Group '{group_to_run.group_id}' COMPLETED:")
                print(f"   Cost: ${group_cost:.4f}")
                print(f"   Iterations: {group_iterations}")
                print(f"   Execution Time: {execution_time:.1f}s")
                print(f"   Success: {agent_result.get('success', False)}")
                
                # Log communication tool usage
                tool_calls = agent_result.get("tool_calls", [])
                ask_supervisor_calls = [tc for tc in tool_calls if tc.get("tool_name") == "ask_supervisor"]
                
                print(f"   Communication Stats:")
                print(f"     ask_supervisor calls: {len(ask_supervisor_calls)}")
                
                if len(ask_supervisor_calls) == 0:
                    print(f"   ⚠️  WARNING: Agent made NO supervisor consultations for this group!")
                
                if not agent_result.get("success"):
                    print(f"❌ Agent encountered issues with group {group_to_run.group_id} but will continue (no 'failed' status)")
                    print(f"💰 Total cost: ${total_cost:.4f}")
                    return {"success": False, "error": f"Agent had issues with group {group_to_run.group_id}", "stage": "execution", "cost": total_cost}
                
                # --- NEW COMMIT LOGIC ---
                if self.auto_commit:
                    git_manager.commit_task_group_completion(group_to_run.model_dump())
                
                group_num += 1
            
            print(f"🎉 Agent has completed all task groups! Total cost: ${total_cost:.4f}")
            return {"success": True, "docs_result": docs_result, "cost": total_cost}
        
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