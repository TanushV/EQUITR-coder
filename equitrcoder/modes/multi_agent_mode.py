# equitrcoder/modes/multi_agent_mode.py

import asyncio
from typing import Any, Callable, Dict, List, Optional

from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..tools.builtin.todo import TodoManager, set_global_todo_file
from ..tools.discovery import discover_tools

# --- NEW IMPORTS ---
from ..core.global_message_pool import global_message_pool
from ..tools.builtin.communication import create_communication_tools_for_agent

class MultiAgentMode:
    """
    Multi-Agent Mode: Orchestrator creates docs, Multiple agents run with coordination.
    """

    def __init__(
        self,
        num_agents: int,
        agent_model: str,
        orchestrator_model: str,
        audit_model: str,
        max_cost_per_agent: Optional[float] = None,
        max_iterations_per_agent: Optional[int] = None,
        run_parallel: bool = False,
    ):
        self.num_agents = num_agents
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost_per_agent = max_cost_per_agent
        self.max_iterations_per_agent = max_iterations_per_agent
        self.run_parallel = run_parallel

        print(
            f"🎭 Multi-Agent Mode ({num_agents} agents, {'parallel' if run_parallel else 'sequential'}):"
        )
        print(f"   Agent Model: {agent_model}")
        print(f"   Orchestrator Model: {orchestrator_model}")
        print(f"   Audit Model: {audit_model}")

    async def run(
        self,
        task_description: str,
        project_path: str = ".",
        callbacks: Optional[Dict[str, Callable]] = None,
    ) -> Dict[str, Any]:
        """
        Run multi-agent mode:
        1. Orchestrator creates docs with agent-specific todos
        2. Multiple agents run (parallel or sequential)
        3. Each agent has built-in audit and communication tools
        """
        try:
            # Step 1: Orchestrator creates docs for multiple agents
            print("📋 Step 1: Creating documentation for multiple agents...")
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)

            docs_result = await orchestrator.create_docs(
                task_description=task_description,
                project_path=project_path,
                num_agents=self.num_agents,
            )

            if not docs_result["success"]:
                return {
                    "success": False,
                    "error": f"Documentation creation failed: {docs_result['error']}",
                    "stage": "orchestrator",
                }

            print(
                f"✅ Documentation created for {self.num_agents} agents: {docs_result['task_name']}"
            )

            # Step 2: Setup multiple agents
            print(f"🤖 Step 2: Setting up {self.num_agents} agents...")

            base_tools = discover_tools()
            agents = []
            agent_tasks = []

            for agent_id_num in range(1, self.num_agents + 1):
                agent_id = f"agent_{agent_id_num}"
                
                # --- MODIFICATION START ---
                # Register agent with the message pool
                await global_message_pool.register_agent(agent_id)
                
                # Create communication tools for this specific agent
                communication_tools = create_communication_tools_for_agent(agent_id)
                
                # Combine base tools and communication tools
                all_tools = base_tools + communication_tools
                # --- MODIFICATION END ---
                
                context = orchestrator.get_context_for_agent(docs_result, agent_id_num)
                agent_todo_file = f".EQUITR_todos_agent_{agent_id_num}.json"

                agent = CleanAgent(
                    agent_id=agent_id,
                    model=self.agent_model,
                    tools=all_tools, # Use combined tools
                    context=context,
                    max_cost=self.max_cost_per_agent,
                    max_iterations=self.max_iterations_per_agent,
                    audit_model=self.audit_model,
                )

                if callbacks:
                    agent.set_callbacks(**callbacks)

                agents.append(agent)

                agent_task_desc = f"""You are {agent_id} in a {self.num_agents}-agent team.

Original task: {task_description}

Your team has created shared documentation:
- Requirements: {docs_result['requirements_path']}
- Design: {docs_result['design_path']}
- Your specific todos are in: {context.get('agent_todo_file', 'See main todos')}

Your mission:
1. Read the shared documentation for context.
2. Use the `receive_messages` tool to check for instructions from other agents.
3. Use the `list_todos` tool to see YOUR assigned tasks.
4. Complete your tasks.
5. Use `send_message` to coordinate with other agents (e.g., when you finish a key part they depend on).
6. Use `update_todo` to mark your tasks as completed.

Start by listing your todos and checking for messages.
"""
                agent_tasks.append((agent, agent_task_desc, agent_todo_file))
                print(f"✅ {agent_id} setup complete with communication tools.")

            # Step 3: Run agents
            if self.run_parallel:
                print("🚀 Step 3: Running agents in PARALLEL...")
                agent_results = await self._run_agents_parallel(agent_tasks)
            else:
                print("🚀 Step 3: Running agents SEQUENTIALLY...")
                agent_results = await self._run_agents_sequential(agent_tasks)

            overall_success = all(result.get("success", False) for result in agent_results)
            total_cost = sum(result.get("cost", 0) for result in agent_results)
            total_iterations = sum(result.get("iterations", 0) for result in agent_results)

            print(f"🎯 All agents completed: Success={overall_success}")

            return {
                "success": overall_success,
                "mode": f"multi_agent_{'parallel' if self.run_parallel else 'sequential'}",
                "num_agents": self.num_agents,
                "docs_result": docs_result,
                "agent_results": agent_results,
                "total_cost": total_cost,
                "total_iterations": total_iterations,
                "audit_results": [
                    result.get("audit_result", {}) for result in agent_results
                ],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_agents_parallel(self, agent_tasks: List[tuple]) -> List[Dict[str, Any]]:
        async def run_single_agent(agent, task, todo_file):
            set_global_todo_file(todo_file)
            return await agent.run(task)

        tasks = [run_single_agent(agent, task, todo_file) for agent, task, todo_file in agent_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"success": False, "error": str(result), "agent_id": f"agent_{i+1}"})
            else:
                processed_results.append(result)
        return processed_results

    async def _run_agents_sequential(self, agent_tasks: List[tuple]) -> List[Dict[str, Any]]:
        results = []
        for agent, task, todo_file in agent_tasks:
            print(f"🤖 Running {agent.agent_id}...")
            set_global_todo_file(todo_file)
            result = await agent.run(task)
            results.append(result)
            print(f"✅ {agent.agent_id} completed: Success={result['success']}")
            if not result["success"]:
                print(f"⚠️ {agent.agent_id} failed, but continuing with remaining agents.")
        return results


async def run_multi_agent_sequential(**kwargs) -> Dict[str, Any]:
    mode = MultiAgentMode(run_parallel=False, **kwargs)
    return await mode.run(task_description=kwargs.get("task_description", ""))


async def run_multi_agent_parallel(**kwargs) -> Dict[str, Any]:
    mode = MultiAgentMode(run_parallel=True, **kwargs)
    return await mode.run(task_description=kwargs.get("task_description", ""))