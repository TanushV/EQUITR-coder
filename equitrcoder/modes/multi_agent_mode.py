"""
Multi-Agent Modes - Combines CleanOrchestrator + Multiple CleanAgents
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..tools.builtin.todo import TodoManager, set_global_todo_file
from ..tools.discovery import discover_tools


class MultiAgentMode:
    """
    Multi-Agent Mode: Orchestrator creates docs, Multiple agents run with coordination.
    """

    def __init__(
        self,
        num_agents: int,
        agent_model: str = "moonshot/kimi-k2-0711-preview",
        orchestrator_model: str = "moonshot/kimi-k2-0711-preview",
        supervisor_model: str = "o3",
        audit_model: str = "o3",
        max_cost_per_agent: Optional[float] = None,
        max_iterations_per_agent: Optional[int] = None,
        run_parallel: bool = False,
    ):
        self.num_agents = num_agents
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.supervisor_model = supervisor_model
        self.audit_model = audit_model
        self.max_cost_per_agent = max_cost_per_agent
        self.max_iterations_per_agent = max_iterations_per_agent
        self.run_parallel = run_parallel

        print(
            f"🎭 Multi-Agent Mode ({num_agents} agents, {'parallel' if run_parallel else 'sequential'}):"
        )
        print(f"   Agent Model: {agent_model}")
        print(f"   Orchestrator Model: {orchestrator_model}")
        print(f"   Supervisor Model: {supervisor_model}")
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
        3. Each agent has built-in audit
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

            # Discover tools (same for all agents, but add supervisor tools)
            base_tools = discover_tools()

            # Add supervisor tool if available
            if self.supervisor_model != self.agent_model:
                # TODO: Add ask_supervisor tool to each agent
                pass

            agents = []
            agent_tasks = []

            for agent_id in range(1, self.num_agents + 1):
                # Get context for this specific agent
                context = orchestrator.get_context_for_agent(docs_result, agent_id)

                # Setup agent-specific todo file
                agent_todo_file = f".EQUITR_todos_agent_{agent_id}.json"

                # Create agent
                agent = CleanAgent(
                    agent_id=f"agent_{agent_id}",
                    model=self.agent_model,
                    tools=base_tools,
                    context=context,
                    max_cost=self.max_cost_per_agent,
                    max_iterations=self.max_iterations_per_agent,
                    audit_model=self.audit_model,
                )

                # Set callbacks if provided
                if callbacks:
                    agent.set_callbacks(
                        on_message=callbacks.get("on_message"),
                        on_iteration=callbacks.get("on_iteration"),
                        on_completion=callbacks.get("on_completion"),
                        on_audit=callbacks.get("on_audit"),
                    )

                agents.append(agent)

                # Create agent task description
                agent_task = f"""You are Agent {agent_id} of {self.num_agents} in a multi-agent system.

Original task: {task_description}

Shared Documentation:
- Requirements: {docs_result['requirements_path']}
- Design: {docs_result['design_path']}
- Your specific todos: {context.get('agent_todo_file', 'See main todos')}

INSTRUCTIONS:
1. Read the shared requirements and design documents
2. Use list_todos to see YOUR assigned tasks
3. Complete all YOUR todos systematically
4. Use communication tools to coordinate with other agents if needed
5. Mark todos complete with update_todo when finished
6. You are working {'in parallel' if self.run_parallel else 'sequentially'} with other agents

Start by using list_todos to see your assigned work!"""

                agent_tasks.append((agent, agent_task, agent_todo_file))

                print(f"✅ Agent {agent_id} setup complete")

            # Step 3: Run agents (parallel or sequential)
            if self.run_parallel:
                print("🚀 Step 3: Running agents in PARALLEL...")
                agent_results = await self._run_agents_parallel(agent_tasks)
            else:
                print("🚀 Step 3: Running agents SEQUENTIALLY...")
                agent_results = await self._run_agents_sequential(agent_tasks)

            # Calculate overall success
            overall_success = all(result["success"] for result in agent_results)
            total_cost = sum(result.get("cost", 0) for result in agent_results)
            total_iterations = sum(
                result.get("iterations", 0) for result in agent_results
            )

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
            return {
                "success": False,
                "error": str(e),
                "mode": f"multi_agent_{'parallel' if self.run_parallel else 'sequential'}",
            }

    async def _run_agents_parallel(
        self, agent_tasks: List[tuple]
    ) -> List[Dict[str, Any]]:
        """Run all agents in parallel."""

        async def run_single_agent(agent, task, todo_file):
            # Set the correct todo file for this agent
            set_global_todo_file(todo_file)
            return await agent.run(task)

        # Create tasks for parallel execution
        tasks = [
            run_single_agent(agent, task, todo_file)
            for agent, task, todo_file in agent_tasks
        ]

        # Run all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"success": False, "error": str(result), "agent_id": f"agent_{i+1}"}
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _run_agents_sequential(
        self, agent_tasks: List[tuple]
    ) -> List[Dict[str, Any]]:
        """Run agents one after another."""
        results = []

        for agent, task, todo_file in agent_tasks:
            print(f"🤖 Running {agent.agent_id}...")

            # Set the correct todo file for this agent
            set_global_todo_file(todo_file)

            # Run agent
            result = await agent.run(task)
            results.append(result)

            print(f"✅ {agent.agent_id} completed: Success={result['success']}")

            # If an agent fails in sequential mode, continue but note the failure
            if not result["success"]:
                print(
                    f"⚠️ {agent.agent_id} failed, but continuing with remaining agents"
                )

        return results


# Convenience functions for different modes


async def run_multi_agent_sequential(
    task_description: str,
    num_agents: int = 2,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    orchestrator_model: str = "moonshot/kimi-k2-0711-preview",
    supervisor_model: str = "o3",
    audit_model: str = "o3",
    project_path: str = ".",
    max_cost_per_agent: Optional[float] = None,
    max_iterations_per_agent: Optional[int] = None,
    callbacks: Optional[Dict[str, Callable]] = None,
) -> Dict[str, Any]:
    """Run multi-agent mode with sequential execution."""

    mode = MultiAgentMode(
        num_agents=num_agents,
        agent_model=agent_model,
        orchestrator_model=orchestrator_model,
        supervisor_model=supervisor_model,
        audit_model=audit_model,
        max_cost_per_agent=max_cost_per_agent,
        max_iterations_per_agent=max_iterations_per_agent,
        run_parallel=False,
    )

    return await mode.run(
        task_description=task_description,
        project_path=project_path,
        callbacks=callbacks,
    )


async def run_multi_agent_parallel(
    task_description: str,
    num_agents: int = 3,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    orchestrator_model: str = "moonshot/kimi-k2-0711-preview",
    supervisor_model: str = "o3",
    audit_model: str = "o3",
    project_path: str = ".",
    max_cost_per_agent: Optional[float] = None,
    max_iterations_per_agent: Optional[int] = None,
    callbacks: Optional[Dict[str, Callable]] = None,
) -> Dict[str, Any]:
    """Run multi-agent mode with parallel execution."""

    mode = MultiAgentMode(
        num_agents=num_agents,
        agent_model=agent_model,
        orchestrator_model=orchestrator_model,
        supervisor_model=supervisor_model,
        audit_model=audit_model,
        max_cost_per_agent=max_cost_per_agent,
        max_iterations_per_agent=max_iterations_per_agent,
        run_parallel=True,
    )

    return await mode.run(
        task_description=task_description,
        project_path=project_path,
        callbacks=callbacks,
    )
