# equitrcoder/modes/single_agent_mode.py

import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..core.unified_config import get_config_manager
from ..tools.builtin.todo import get_todo_manager, set_global_todo_file
from ..tools.discovery import discover_tools
from ..utils.git_manager import GitManager


class SingleAgentMode:
    """Runs a single agent that executes task groups sequentially based on dependencies."""

    def __init__(
        self,
        agent_model: str,
        orchestrator_model: str,
        audit_model: str,
        max_cost: Optional[float],
        max_iterations: Optional[int],
        auto_commit: bool,
    ):
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        self.auto_commit = auto_commit  # <-- NEW PROPERTY
        self.system_prompts = self._load_system_prompts()
        print(
            f"🎭 Single Agent Mode (Dependency-Aware): Auto-commit is {'ON' if self.auto_commit else 'OFF'}"
        )
        print(f"   Agent Model: {agent_model}, Audit Model: {audit_model}")

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts from unified configuration."""
        config_manager = get_config_manager()
        config_data = config_manager.get_cached_config()

        # Get prompts from unified configuration
        prompts = config_data.prompts

        # Return prompts with fallbacks
        return {
            "single_agent_prompt": prompts.get(
                "single_agent_prompt",
                "You are working on a single task group. Complete all todos systematically.",
            ),
            "multi_agent_prompt": prompts.get(
                "multi_agent_prompt",
                "You are part of a team. Coordinate with other agents.",
            ),
        }

    async def run(
        self,
        task_description: str,
        project_path: str = ".",
        callbacks: Optional[Dict[str, Callable]] = None,
        task_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        original_cwd = os.getcwd()
        try:
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            docs_result = await orchestrator.create_docs(
                task_description=task_description,
                project_path=project_path,
                task_name=task_name,
            )
            if not docs_result["success"]:
                return {
                    "success": False,
                    "error": f"Documentation failed: {docs_result['error']}",
                    "stage": "planning",
                }

            # --- NEW GIT MANAGER INITIALIZATION ---
            git_manager = GitManager(repo_path=project_path)
            if self.auto_commit:
                git_manager.ensure_repo_is_ready()

            tools = discover_tools()
            # Ensure read-only audit tools are always present
            by_name = {t.get_name(): t for t in tools}
            required = [
                "read_file",
                "list_files",
                "grep_search",
                "git_status",
                "git_diff",
            ]
            for r in required:
                if r not in by_name:
                    # find in discovery again to avoid duplication
                    extra = [t for t in discover_tools() if t.get_name() == r]
                    tools.extend(extra)
            agent = CleanAgent(
                agent_id="single_agent",
                model=self.agent_model,
                tools=tools,
                context=docs_result,
                max_cost=self.max_cost,
                max_iterations=self.max_iterations,
                audit_model=self.orchestrator_model,
            )
            if callbacks:
                agent.set_callbacks(**callbacks)

            print("🚀 Step 3: Agent starting sequential execution of task groups...")
            set_global_todo_file(docs_result["todos_path"])

            # Change to project directory so tools work with correct relative paths
            os.chdir(project_path)

            total_cost = 0.0
            group_num = 1
            while not get_todo_manager().are_all_tasks_complete():
                runnable_groups = get_todo_manager().get_next_runnable_groups()
                if not runnable_groups:
                    break

                group_to_run = runnable_groups[0]
                print(
                    f"\n--- TASK GROUP {group_num}: {group_to_run.group_id} ({group_to_run.specialization}) ---"
                )
                print(f"💰 Total cost so far: ${total_cost:.4f}")

                get_todo_manager().update_task_group_status(
                    group_to_run.group_id, "in_progress"
                )

                # Get single-agent prompt from config and format it
                single_agent_prompt = self.system_prompts.get(
                    "single_agent_prompt", "Complete the task group systematically."
                )
                group_task_desc = single_agent_prompt.format(
                    agent_id="single_agent",
                    model=self.agent_model,
                    group_description=group_to_run.description,
                    group_id=group_to_run.group_id,
                    specialization=group_to_run.specialization,
                    available_tools=", ".join([tool.get_name() for tool in tools]),
                    mandatory_context_json="{{mandatory_context_json}}",
                    task_description="{{task_description}}",
                )

                print(
                    f"\n🤖 Starting work on group '{group_to_run.group_id}' ({group_to_run.specialization})"
                )
                print(f"   Group Description: {group_to_run.description}")
                print(f"   Dependencies: {group_to_run.dependencies}")

                start_time = datetime.now()
                agent_result = await agent.run(group_task_desc, session_id=session_id)
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
                ask_supervisor_calls = [
                    tc for tc in tool_calls if tc.get("tool_name") == "ask_supervisor"
                ]

                print("   Communication Stats:")
                print(f"     ask_supervisor calls: {len(ask_supervisor_calls)}")

                if len(ask_supervisor_calls) == 0:
                    print(
                        "   ⚠️  WARNING: Agent made NO supervisor consultations for this group!"
                    )

                if not agent_result.get("success"):
                    print(
                        f"❌ Agent encountered issues with group {group_to_run.group_id} but will continue (no 'failed' status)"
                    )
                    print(f"💰 Total cost: ${total_cost:.4f}")
                    return {
                        "success": False,
                        "error": f"Agent had issues with group {group_to_run.group_id}",
                        "stage": "execution",
                        "cost": total_cost,
                    }

                # --- NEW COMMIT LOGIC ---
                if self.auto_commit:
                    git_manager.commit_task_group_completion(group_to_run.model_dump())

                group_num += 1

            print(
                f"🎉 Agent has completed all task groups! Total cost: ${total_cost:.4f}"
            )
            # Final audit after all todos complete (single-agent mode)
            try:
                auditor = CleanAgent(
                    agent_id="final_auditor_single",
                    model=self.orchestrator_model,
                    tools=[
                        t
                        for t in discover_tools()
                        if t.get_name()
                        in (
                            "read_file",
                            "list_files",
                            "grep_search",
                            "git_status",
                            "git_diff",
                        )
                    ],
                    context=docs_result,
                    audit_model=self.orchestrator_model,
                )
                audit_result = await auditor._run_audit()
            except Exception as e:
                audit_result = {"success": False, "error": str(e)}

            return {
                "success": True,
                "docs_result": docs_result,
                "cost": total_cost,
                "final_audit": audit_result,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "mode": "single_agent"}
        finally:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except OSError as e:
                # Failed to change back to original directory, log but continue
                print(f"Warning: Failed to change back to original directory: {e}")


async def run_single_agent_mode(**kwargs) -> Dict[str, Any]:
    # We now expect auto_commit to be passed in
    config = {
        "agent_model": "moonshot/kimi-k2-0711-preview",
        "orchestrator_model": "moonshot/kimi-k2-0711-preview",
        "audit_model": "o3",
        "max_cost": None,
        "max_iterations": None,
        "auto_commit": True,
        **kwargs,
    }
    mode = SingleAgentMode(**config)
    return await mode.run(
        task_description=kwargs.get("task_description", ""),
        project_path=kwargs.get("project_path", "."),
        task_name=kwargs.get("task_name"),
        session_id=kwargs.get("session_id"),
    )
