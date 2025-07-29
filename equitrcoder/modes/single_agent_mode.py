"""
Single Agent Mode - Combines CleanOrchestrator + CleanAgent
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable

from ..core.clean_orchestrator import CleanOrchestrator
from ..core.clean_agent import CleanAgent
from ..tools.discovery import discover_tools
from ..tools.builtin.todo import set_global_todo_file


class SingleAgentMode:
    """
    Single Agent Mode: Orchestrator creates docs, Agent runs until completion with built-in audit.
    """
    
    def __init__(
        self,
        agent_model: str = "moonshot/kimi-k2-0711-preview",
        orchestrator_model: str = "moonshot/kimi-k2-0711-preview", 
        audit_model: str = "o3",
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None
    ):
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        
        print(f"🎭 Single Agent Mode:")
        print(f"   Agent Model: {agent_model}")
        print(f"   Orchestrator Model: {orchestrator_model}")
        print(f"   Audit Model: {audit_model}")
    
    async def run(
        self,
        task_description: str,
        project_path: str = ".",
        callbacks: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, Any]:
        """
        Run single agent mode:
        1. Orchestrator creates docs
        2. Agent runs until completion 
        3. Built-in audit runs automatically
        """
        try:
            # Step 1: Orchestrator creates docs
            print("📋 Step 1: Creating documentation...")
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            
            docs_result = await orchestrator.create_docs(
                task_description=task_description,
                project_path=project_path,
                num_agents=1
            )
            
            if not docs_result["success"]:
                return {
                    "success": False,
                    "error": f"Documentation creation failed: {docs_result['error']}",
                    "stage": "orchestrator"
                }
            
            print(f"✅ Documentation created: {docs_result['task_name']}")
            
            # Step 2: Setup agent with tools and context
            print("🤖 Step 2: Setting up agent...")
            
            # Discover tools
            tools = discover_tools()
            print(f"🔧 Discovered {len(tools)} tools")
            
            # Get context from docs
            context = orchestrator.get_context_for_agent(docs_result)
            
            # Ensure todo system uses correct file
            task_todo_file = f".EQUITR_todos_{docs_result['task_name']}.json"
            set_global_todo_file(task_todo_file)
            
            # Create agent
            agent = CleanAgent(
                agent_id="single_agent",
                model=self.agent_model,
                tools=tools,
                context=context,
                max_cost=self.max_cost,
                max_iterations=self.max_iterations,
                audit_model=self.audit_model
            )
            
            # Set callbacks if provided
            if callbacks:
                agent.set_callbacks(
                    on_message=callbacks.get('on_message'),
                    on_iteration=callbacks.get('on_iteration'),
                    on_completion=callbacks.get('on_completion'),
                    on_audit=callbacks.get('on_audit')
                )
            
            print("✅ Agent setup complete")
            
            # Step 3: Agent runs until completion (includes built-in audit)
            print("🚀 Step 3: Agent execution (includes automatic audit)...")
            
            enhanced_task = f"""Original task: {task_description}

Documentation has been created for this task:
- Requirements: {docs_result['requirements_path']}
- Design: {docs_result['design_path']}  
- Todos: {docs_result['todos_path']}

INSTRUCTIONS:
1. Read these documents for context
2. Use list_todos to see your assigned tasks
3. Complete all todos systematically
4. Mark todos complete with update_todo when finished
5. Create working, tested code that fulfills the requirements

Start by using list_todos to see what needs to be done!"""
            
            agent_result = await agent.run(enhanced_task)
            
            print(f"🎯 Agent completed: Success={agent_result['success']}")
            
            # Combine results
            return {
                "success": agent_result["success"],
                "mode": "single_agent",
                "docs_result": docs_result,
                "agent_result": agent_result,
                "cost": agent_result.get("cost", 0),
                "iterations": agent_result.get("iterations", 0),
                "audit_result": agent_result.get("audit_result", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": "single_agent"
            }


async def run_single_agent_mode(
    task_description: str,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    orchestrator_model: str = "moonshot/kimi-k2-0711-preview",
    audit_model: str = "o3",
    project_path: str = ".",
    max_cost: Optional[float] = None,
    max_iterations: Optional[int] = None,
    callbacks: Optional[Dict[str, Callable]] = None
) -> Dict[str, Any]:
    """Convenience function to run single agent mode."""
    
    mode = SingleAgentMode(
        agent_model=agent_model,
        orchestrator_model=orchestrator_model,
        audit_model=audit_model,
        max_cost=max_cost,
        max_iterations=max_iterations
    )
    
    return await mode.run(
        task_description=task_description,
        project_path=project_path,
        callbacks=callbacks
    )