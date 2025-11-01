# equitrcoder/modes/researcher_mode.py

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from ..core.clean_orchestrator import CleanOrchestrator
from ..modes.multi_agent_mode import MultiAgentMode
from ..providers.litellm import LiteLLMProvider, Message
from ..tools.builtin.todo import get_todo_manager, set_global_todo_file

# Tools used programmatically
from ..tools.custom.research_tools import HardwareInfo, RunExperiments
from ..utils.git_manager import GitManager


class ResearcherMode:
    """Researcher mode: conversational planning + multi-agent implementation + experiment execution."""

    def __init__(
        self,
        num_agents: int,
        agent_model: str,
        orchestrator_model: str,
        audit_model: str,
        max_cost_per_agent: Optional[float] = None,
        max_iterations_per_agent: Optional[int] = None,
        auto_commit: bool = True,
        team: Optional[List[str]] = None,
    ):
        self.num_agents = num_agents
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost_per_agent = max_cost_per_agent
        self.max_iterations_per_agent = max_iterations_per_agent
        self.auto_commit = auto_commit
        self.team = team or [
            "ml_researcher",
            "data_engineer",
            "experiment_runner",
        ]
        self.global_cost = 0.0
        print(
            f"🎭 Researcher Mode (Multi-Agent Parallel with Experiments): Auto-commit is {'ON' if self.auto_commit else 'OFF'}"
        )
        print(f"   Agent Model: {agent_model}, Audit Model: {audit_model}")

    async def run(
        self,
        task_description: str,
        project_path: str = ".",
        callbacks: Optional[Dict[str, Callable]] = None,
        research_context: Optional[Dict[str, Any]] = None,
        task_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main entry for researcher mode."""
        original_cwd = os.getcwd()
        try:
            project_dir = Path(project_path).resolve()

            # Step 0: Conversational planning with user (datasets, hardware, experiments)
            # If a research_context is provided (e.g., from TUI), use it to avoid interactive prompts.
            research_ctx = research_context
            if research_ctx is None:
                # Non-interactive fallback: create minimal, sane defaults so mode is guaranteed to proceed
                research_ctx = {
                    "datasets": [],
                    "hardware": {},
                    "experiments": [
                        {
                            "name": "lint",
                            "command": "python -m ruff check .",
                            "timeout": 300,
                        },
                        {"name": "tests", "command": "pytest -q", "timeout": 900},
                    ],
                }

            # Step 1: Create docs with orchestrator using augmented description
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            augmented_desc = self._augment_task_description(
                task_description, research_ctx
            )
            docs_result = await orchestrator.create_docs(
                task_description=augmented_desc,
                project_path=str(project_dir),
                task_name=task_name,
                team=self.team,
                is_research=True,
            )
            if not docs_result.get("success"):
                return {
                    "success": False,
                    "error": f"Documentation failed: {docs_result.get('error')}",
                    "stage": "planning",
                }

            # Persist research plan files alongside docs
            docs_dir = Path(docs_result["docs_dir"]).resolve()
            research_plan_path = docs_dir / "research_plan.yaml"
            experiments_path = docs_dir / "experiments.yaml"
            self._write_research_files(
                research_plan_path, experiments_path, research_ctx
            )

            # Ensure experiments.yaml is populated; if empty, auto-generate a sensible default
            try:
                exp_cfg = (
                    yaml.safe_load(experiments_path.read_text(encoding="utf-8")) or {}
                )
                experiments = exp_cfg.get("experiments", [])
                if not experiments:
                    default_exps = [
                        {
                            "name": "lint",
                            "command": "python -m ruff check .",
                            "timeout": 300,
                        },
                        {"name": "tests", "command": "pytest -q", "timeout": 900},
                    ]
                    experiments_path.write_text(
                        yaml.safe_dump(
                            {
                                "experiments": default_exps,
                                "created_at": datetime.now().isoformat(),
                            },
                            sort_keys=False,
                        ),
                        encoding="utf-8",
                    )
                    print(f"🧪 Auto-generated default experiments: {experiments_path}")
            except Exception as e:
                print(f"⚠️  Could not auto-generate experiments: {e}")

            # Step 2: Git init/ensure
            git_manager = GitManager(repo_path=str(project_dir))
            if self.auto_commit:
                git_manager.ensure_repo_is_ready()

            # Step 3: Execute task groups in parallel using MultiAgentMode helpers
            print(
                "🚀 Step 2: Starting phased execution of the plan (researcher mode)..."
            )
            set_global_todo_file(
                docs_result["todos_path"]
            )  # Use the session-local todo file

            # Change to project directory so tools work with correct relative paths
            os.chdir(str(project_dir))

            try:
                # Create helper multi-agent instance only for executing groups
                ma = MultiAgentMode(
                    num_agents=self.num_agents,
                    agent_model=self.agent_model,
                    orchestrator_model=self.orchestrator_model,
                    audit_model=self.audit_model,
                    max_cost_per_agent=self.max_cost_per_agent,
                    max_iterations_per_agent=self.max_iterations_per_agent,
                    run_parallel=True,
                    auto_commit=self.auto_commit,
                )

                # Ensure research mode uses multi-agent prompt with a research-specific suffix (simple approach)
                try:
                    from ..core.profile_manager import ProfileManager

                    pm = ProfileManager()
                    prompts_cfg = pm.system_prompt_config or {}
                    base_multi_prompt = ma.system_prompts.get(
                        "multi_agent_prompt",
                        "You are part of a team. Coordinate with other agents.",
                    )
                    research_suffix = prompts_cfg.get(
                        "research_multi_agent_suffix",
                        (
                            "\n\n[Research Mode Addendum]\n"
                            "- Prioritize experiment design and execution. If experiments fail, add fix todos and retry until pass or retry limit.\n"
                            "- Include datasets, hardware, and experiments context when available."
                        ),
                    )
                    ma.system_prompts["multi_agent_prompt"] = (
                        base_multi_prompt + "\n\n" + research_suffix
                    )
                except Exception:
                    pass

                phase_num = 1
                while not get_todo_manager().are_all_tasks_complete():
                    runnable_groups = get_todo_manager().get_next_runnable_groups()
                    if not runnable_groups:
                        break

                    print(
                        f"\n--- EXECUTING PHASE {phase_num} ({len(runnable_groups)} task groups in parallel) ---"
                    )

                    coros = [
                        ma._execute_task_group(
                            g, docs_result, callbacks, session_id=session_id
                        )
                        for g in runnable_groups
                    ]
                    phase_results = await asyncio.gather(*coros)

                    phase_cost = sum(r.get("cost", 0.0) for r in phase_results)
                    self.global_cost += phase_cost

                    if any(not r.get("success") for r in phase_results):
                        print(f"❌ PHASE {phase_num} FAILED. Halting execution.")
                        return {
                            "success": False,
                            "error": f"A task in phase {phase_num} failed.",
                            "stage": "execution",
                            "cost": self.global_cost,
                        }

                    # Commit after each group if enabled
                    if self.auto_commit:
                        for group in runnable_groups:
                            git_manager.commit_task_group_completion(group.model_dump())

                    print(
                        f"✅ PHASE {phase_num} COMPLETED | Phase cost: ${phase_cost:.4f}"
                    )
                    phase_num += 1

                print(
                    f"🎉 INITIAL PHASES COMPLETED! Global cost so far: ${self.global_cost:.4f}"
                )

                # Step 4: Execute the pre-injected experiment group (created by orchestrator in research mode)
                exp_groups = [
                    g
                    for g in get_todo_manager().get_next_runnable_groups()
                    if g.group_id == "experiment_execution"
                ]
                if exp_groups:
                    print(
                        f"\n--- EXECUTING EXPERIMENT PHASE ({len(exp_groups)} group) ---"
                    )
                    exp_results = await asyncio.gather(
                        *[
                            ma._execute_task_group(g, docs_result, callbacks)
                            for g in exp_groups
                        ]
                    )
                    phase_cost = sum(r.get("cost", 0.0) for r in exp_results)
                    self.global_cost += phase_cost
                    if any(not r.get("success") for r in exp_results):
                        print("❌ Experiment execution phase failed.")
                        return {
                            "success": False,
                            "error": "Experiment execution phase failed.",
                            "stage": "experiments",
                            "cost": self.global_cost,
                        }
                else:
                    # If no explicit experiment group is runnable (e.g., empty plan), attempt a direct experiments run
                    try:
                        exp_cfg_path = experiments_path
                        run_tool = RunExperiments()
                        run_res = await run_tool.run(config_path=str(exp_cfg_path))
                        if not run_res.success:
                            print(f"❌ Direct experiments run failed: {run_res.error}")
                            return {
                                "success": False,
                                "error": f"Direct experiments run failed: {run_res.error}",
                                "stage": "experiments",
                                "cost": self.global_cost,
                            }
                        # Try to generate a research report as a final artifact
                        try:
                            report_path = (
                                Path(docs_result["docs_dir"]) / "research_report.md"
                            )
                            await self._generate_report_with_supervisor(
                                report_path,
                                task_description,
                                research_ctx,
                                run_res,
                            )
                        except Exception:
                            pass
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Experiments fallback failed: {e}",
                            "stage": "experiments",
                            "cost": self.global_cost,
                        }

                final = {
                    "success": True,
                    "docs_result": docs_result,
                    "cost": self.global_cost,
                }
                # Report path will be part of artifacts written by the experiment_runner task
                # Final audit after phases (regardless of experiment outcomes)
                try:
                    # Reuse CleanAgent audit pathway directly for a single audit
                    from ..core.clean_agent import CleanAgent
                    from ..tools.discovery import discover_tools

                    audit_agent = CleanAgent(
                        agent_id="final_research_auditor",
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
                    audit_result = await audit_agent._run_audit()
                except Exception as e:
                    audit_result = {"success": False, "error": str(e)}
                final["final_audit"] = audit_result
                return final
            finally:
                # Restore working directory
                try:
                    os.chdir(original_cwd)
                except Exception:
                    pass

        except Exception as e:
            return {"success": False, "error": str(e), "mode": "researcher"}

    async def _collect_research_context(self, initial_task: str) -> Dict[str, Any]:
        """Interactive conversation to gather datasets, hardware, and experiments."""
        print("\n🧠 RESEARCHER CONVERSATION")
        print("=" * 60)
        print("Describe datasets (paths) you will use. Enter blank line when done.")
        datasets: List[Dict[str, str]] = []
        while True:
            path = input("Dataset path (blank to finish): ").strip()
            if not path:
                break
            desc = input("Short description: ").strip()
            datasets.append({"path": path, "description": desc})

        # Hardware detection + optional user notes
        hw_tool = HardwareInfo()
        hw_result = await hw_tool.run(detailed=True)
        hardware = (
            hw_result.data if hw_result.success else {"note": hw_result.error or "N/A"}
        )
        more_hw = input("Any additional hardware notes? (blank to skip): ").strip()
        if more_hw:
            hardware["user_notes"] = more_hw

        print(
            "\nDefine experiments to run (shell commands). Enter blank name to finish."
        )
        experiments: List[Dict[str, Any]] = []
        while True:
            name = input("Experiment name (blank to finish): ").strip()
            if not name:
                break
            command = input("Shell command to run: ").strip()
            experiments.append({"name": name, "command": command})

        return {
            "datasets": datasets,
            "hardware": hardware,
            "experiments": experiments,
        }

    def _augment_task_description(self, base: str, ctx: Dict[str, Any]) -> str:
        parts = [base.strip(), "\n\n=== Research Context ==="]
        if ctx.get("datasets"):
            parts.append("Datasets:")
            for d in ctx["datasets"]:
                parts.append(f"- {d.get('path')}: {d.get('description')}")
        if ctx.get("hardware"):
            parts.append("\nHardware:")
            parts.append(yaml.safe_dump(ctx["hardware"], sort_keys=False))
        if ctx.get("experiments"):
            parts.append("Experiments (to run after build):")
            for e in ctx["experiments"]:
                parts.append(f"- {e.get('name')}: {e.get('command')}")
        return "\n".join(parts)

    def _write_research_files(
        self, plan_path: Path, experiments_path: Path, ctx: Dict[str, Any]
    ) -> None:
        plan = {
            "datasets": ctx.get("datasets", []),
            "hardware": ctx.get("hardware", {}),
            "created_at": datetime.now().isoformat(),
        }
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
        exp_cfg = {
            "experiments": ctx.get("experiments", []),
            "created_at": datetime.now().isoformat(),
        }
        experiments_path.write_text(
            yaml.safe_dump(exp_cfg, sort_keys=False), encoding="utf-8"
        )
        print(f"🧾 Wrote research plan: {plan_path}")
        print(f"🧪 Wrote experiments config: {experiments_path}")

    async def _generate_report_with_supervisor(
        self,
        output_path: Path,
        task_description: str,
        research_ctx: Dict[str, Any],
        exp_result: Any,
    ) -> None:
        """Use the supervisor model to produce a Markdown report summarizing results (hardcoded flow)."""
        provider = LiteLLMProvider(model=self.orchestrator_model)

        # Prepare a compact summary for the supervisor
        datasets_txt = "\n".join(
            f"- {d.get('path')} — {d.get('description','')}"
            for d in research_ctx.get("datasets", [])
        )
        hardware_json = json.dumps(research_ctx.get("hardware", {}), indent=2)

        exp_summary = {"all_passed": None, "results": []}
        if getattr(exp_result, "success", False) and isinstance(
            getattr(exp_result, "data", None), dict
        ):
            exp_summary["all_passed"] = exp_result.data.get("all_passed")
            for r in exp_result.data.get("results", []):
                exp_summary["results"].append(
                    {
                        "name": r.get("name"),
                        "command": r.get("command"),
                        "return_code": r.get("return_code"),
                        "passed": r.get("passed"),
                        # Truncate outputs to avoid excessive tokens
                        "stdout_tail": (r.get("stdout") or "")[-1000:],
                        "stderr_tail": (r.get("stderr") or "")[-1000:],
                    }
                )

        system_prompt = (
            "You are a strict research supervisor. Produce a professional Markdown report summarizing "
            "the research task, datasets, hardware, experiments executed, and outcomes. Provide a clear "
            "Conclusion and a short Next Steps section. Keep the report concise, actionable, and accurate."
        )
        user_prompt = (
            f"TASK DESCRIPTION:\n{task_description}\n\n"
            f"DATASETS:\n{datasets_txt or 'N/A'}\n\n"
            f"HARDWARE (JSON):\n```json\n{hardware_json}\n```\n\n"
            f"EXPERIMENT SUMMARY (JSON):\n```json\n{json.dumps(exp_summary, indent=2)}\n```\n\n"
            "Please output ONLY valid GitHub-Flavored Markdown."
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]
        try:
            response = await provider.chat(messages=messages)
            md = response.content.strip()
            if not md.startswith("#"):
                md = f"# Research Report\n\n{md}"
        except Exception as e:
            # Fallback minimal report if model call fails
            md = (
                f"# Research Report\n\nTask: {task_description}\n\n"
                f"## Datasets\n{datasets_txt or 'N/A'}\n\n"
                f"## Hardware\n```json\n{hardware_json}\n```\n\n"
                f"## Experiments (Summary)\n```json\n{json.dumps(exp_summary, indent=2)}\n```\n\n"
                f"_Report generation failed with: {e}_\n"
            )

        output_path.write_text(md, encoding="utf-8")
        print(f"📝 Wrote research report via supervisor: {output_path}")


async def run_researcher_mode(**kwargs) -> Dict[str, Any]:
    # Separate runtime-only args from constructor kwargs
    task_desc = kwargs.pop("task_description", "")
    project_path = kwargs.pop("project_path", ".")
    callbacks = kwargs.pop("callbacks", None)

    # Defaults
    config = {
        "num_agents": kwargs.pop("num_agents", 3),
        # Enforce exact requested defaults
        "agent_model": kwargs.pop("agent_model", "gpt-5-mini"),
        "orchestrator_model": kwargs.pop("orchestrator_model", "gpt-5"),
        "audit_model": kwargs.pop("audit_model", "gpt-5"),
        "max_cost_per_agent": kwargs.pop("max_cost_per_agent", None),
        "max_iterations_per_agent": kwargs.pop("max_iterations_per_agent", 50),
        "auto_commit": kwargs.pop("auto_commit", True),
        "team": kwargs.pop(
            "team",
            ["ml_researcher", "data_engineer", "experiment_runner"],
        ),
    }

    mode = ResearcherMode(**config)
    return await mode.run(
        task_description=task_desc,
        project_path=project_path,
        callbacks=callbacks,
        research_context=kwargs.get("research_context"),
        task_name=kwargs.get("task_name"),
        session_id=kwargs.get("session_id"),
    )
