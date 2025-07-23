"""
Single Agent Orchestrator - Simple wrapper around BaseAgent for single-agent tasks.
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ..core.session import SessionData, SessionManagerV2
from ..tools.discovery import discover_tools
from ..providers.openrouter import Message


class SingleAgentOrchestrator:
    """Orchestrator for single-agent tasks with session management and cost tracking."""
    
    def __init__(
        self,
        agent: BaseAgent,
        session_manager: Optional[SessionManagerV2] = None,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None
    ):
        self.agent = agent
        self.session_manager = session_manager or SessionManagerV2()
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        
        # Set limits on agent if provided
        if max_cost:
            self.agent.max_cost = max_cost
        if max_iterations:
            self.agent.max_iterations = max_iterations
        
        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_iteration_callback: Optional[Callable] = None
        self.on_completion_callback: Optional[Callable] = None
    
    async def execute_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a single task using the agent."""
        
        # Create or load session
        if session_id:
            session = self.session_manager.load_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
        else:
            session = self.session_manager.create_session()
        
        self.agent.session = session
        
        # Add initial task message
        self.agent.add_message("user", task_description, {"context": context})
        
        try:
            # Execute task
            result = await self._execute_task_loop(task_description, context)
            
            # Update session
            session.cost += self.agent.current_cost
            session.total_tokens += result.get("total_tokens", 0)
            session.iteration_count = self.agent.iteration_count
            
            # Save session
            await self.session_manager._save_session_to_disk(session)
            
            return {
                "success": True,
                "result": result,
                "session_id": session.session_id,
                "cost": self.agent.current_cost,
                "iterations": self.agent.iteration_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session.session_id if session else None,
                "cost": self.agent.current_cost,
                "iterations": self.agent.iteration_count
            }
    
    async def _execute_task_loop(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main task execution loop."""
        
        iteration_results = []
        
        while True:
            # Check limits
            limits = self.agent.check_limits()
            if not limits["can_continue"]:
                break
            
            # Increment iteration
            self.agent.increment_iteration()
            
            # Call iteration callback
            if self.on_iteration_callback:
                self.on_iteration_callback(self.agent.iteration_count, self.agent.get_status())
            
            # For now, this is a simple implementation
            # In a real scenario, this would involve LLM calls and tool usage
            iteration_result = {
                "iteration": self.agent.iteration_count,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "message": f"Processed task: {task_description}"
            }
            
            iteration_results.append(iteration_result)
            
            # Add completion message
            self.agent.add_message(
                "assistant",
                f"Completed iteration {self.agent.iteration_count}",
                {"iteration_result": iteration_result}
            )
            
            # For demo purposes, complete after one iteration
            break
        
        # Call completion callback
        if self.on_completion_callback:
            self.on_completion_callback(iteration_results, self.agent.get_status())
        
        return {
            "task_description": task_description,
            "iterations": iteration_results,
            "total_iterations": len(iteration_results),
            "final_status": self.agent.get_status()
        }
    
    async def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Use a tool through the agent."""
        return await self.agent.call_tool(tool_name, **kwargs)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.agent.get_available_tools()
    
    def add_tool(self, tool):
        """Add a tool to the agent."""
        self.agent.add_tool(tool)
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from the agent."""
        return self.agent.get_messages(limit)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "orchestrator_type": "single_agent",
            "agent_status": self.agent.get_status(),
            "session_id": self.agent.session.session_id if self.agent.session else None,
            "limits": {
                "max_cost": self.max_cost,
                "max_iterations": self.max_iterations
            }
        }
    
    def reset(self):
        """Reset the orchestrator and agent state."""
        self.agent.reset()
    
    def set_callbacks(
        self,
        on_message: Optional[Callable] = None,
        on_iteration: Optional[Callable] = None,
        on_completion: Optional[Callable] = None
    ):
        """Set callback functions for monitoring."""
        if on_message:
            self.on_message_callback = on_message
            self.agent.on_message_callback = on_message
        
        if on_iteration:
            self.on_iteration_callback = on_iteration
        
        if on_completion:
            self.on_completion_callback = on_completion 