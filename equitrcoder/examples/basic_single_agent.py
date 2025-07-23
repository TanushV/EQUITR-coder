#!/usr/bin/env python3
"""
Basic Single Agent Examples

This file demonstrates simple usage patterns for equitrcoder's single-agent functionality.
These examples show how to create and use BaseAgent and SingleAgentOrchestrator for
basic coding tasks.
"""

import asyncio
import os
from typing import Dict, Any

# Import the main equitrcoder components
from equitrcoder.agents.base_agent import BaseAgent
from equitrcoder.orchestrators.single_orchestrator import SingleAgentOrchestrator
from equitrcoder.core.session import SessionManagerV2


async def basic_task_execution():
    """
    Example 1: Basic task execution with a single agent
    
    This shows the simplest way to use equitrcoder for a coding task.
    """
    print("=== Example 1: Basic Task Execution ===")
    
    # Create a base agent with cost and iteration limits
    agent = BaseAgent(
        max_cost=1.0,        # Limit spending to $1.00
        max_iterations=10    # Maximum 10 iterations
    )
    
    # Create a single-agent orchestrator
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Execute a simple task
    result = await orchestrator.execute_task(
        "Analyze the current directory structure and suggest improvements"
    )
    
    # Check results
    if result["success"]:
        print(f"✅ Task completed successfully!")
        print(f"💰 Cost: ${result['cost']:.4f}")
        print(f"🔄 Iterations used: {result['iterations']}")
        print(f"📝 Session ID: {result['session_id']}")
    else:
        print(f"❌ Task failed: {result['error']}")
    
    return result


async def task_with_monitoring():
    """
    Example 2: Task execution with progress monitoring
    
    This shows how to monitor the agent's progress during execution.
    """
    print("\n=== Example 2: Task with Monitoring ===")
    
    agent = BaseAgent(max_cost=0.5, max_iterations=5)
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Set up monitoring callbacks
    def on_message(message_data: Dict[str, Any]):
        role = message_data.get('role', 'unknown')
        content = message_data.get('content', '')[:100]  # First 100 chars
        print(f"[{role.upper()}] {content}...")
    
    def on_iteration(iteration: int, status: Dict[str, Any]):
        cost = status.get('current_cost', 0)
        print(f"🔄 Iteration {iteration}: Cost ${cost:.4f}")
    
    def on_completion(results: Dict[str, Any], final_status: Dict[str, Any]):
        final_cost = final_status.get('current_cost', 0)
        print(f"🏁 Task completed! Final cost: ${final_cost:.4f}")
    
    # Set callbacks on the orchestrator
    orchestrator.set_callbacks(
        on_message=on_message,
        on_iteration=on_iteration,
        on_completion=on_completion
    )
    
    # Execute task with monitoring
    result = await orchestrator.execute_task(
        "Check if there are any Python files in the current directory and list them"
    )
    
    return result


async def session_management_example():
    """
    Example 3: Using persistent sessions
    
    This shows how to create and reuse sessions for continuity across tasks.
    """
    print("\n=== Example 3: Session Management ===")
    
    # Create a session manager
    session_manager = SessionManagerV2()
    
    # Create agent and orchestrator with session management
    agent = BaseAgent(max_cost=2.0, max_iterations=15)
    orchestrator = SingleAgentOrchestrator(agent, session_manager=session_manager)
    
    # First task - creates a new session
    print("Starting first task...")
    result1 = await orchestrator.execute_task(
        "Start analyzing the equitrcoder project structure",
        session_id="project-analysis"
    )
    
    if result1["success"]:
        print(f"First task completed. Session: {result1['session_id']}")
    
    # Second task - continues in the same session
    print("\nContinuing with second task...")
    result2 = await orchestrator.execute_task(
        "Continue the analysis by focusing on the core modules",
        session_id="project-analysis"
    )
    
    if result2["success"]:
        print(f"Second task completed. Session: {result2['session_id']}")
    
    # Check session information
    session = session_manager.load_session("project-analysis")
    if session:
        print(f"\n📊 Session Statistics:")
        print(f"   Total cost: ${session.cost:.4f}")
        print(f"   Total iterations: {session.iteration_count}")
        print(f"   Messages in history: {len(session.messages)}")
    
    return result2


async def error_handling_example():
    """
    Example 4: Error handling and limits
    
    This shows how to handle errors and limit violations gracefully.
    """
    print("\n=== Example 4: Error Handling and Limits ===")
    
    # Create an agent with very strict limits to demonstrate limit handling
    agent = BaseAgent(
        max_cost=0.01,       # Very low cost limit
        max_iterations=2     # Very low iteration limit
    )
    
    orchestrator = SingleAgentOrchestrator(agent)
    
    try:
        # This task might exceed our limits
        result = await orchestrator.execute_task(
            "Perform a comprehensive analysis of the entire codebase and create detailed documentation"
        )
        
        if not result["success"]:
            print(f"❌ Task failed: {result['error']}")
            
            # Get detailed status information
            status = agent.get_status()
            limits = status.get("limits_status", {})
            
            # Check what limits were exceeded
            if limits.get("cost_exceeded", False):
                print("💰 Cost limit was exceeded!")
                print(f"   Current cost: ${status.get('current_cost', 0):.4f}")
                print(f"   Max cost: ${agent.max_cost:.4f}")
            
            if limits.get("iterations_exceeded", False):
                print("🔄 Iteration limit was exceeded!")
                print(f"   Current iterations: {status.get('current_iterations', 0)}")
                print(f"   Max iterations: {agent.max_iterations}")
        else:
            print("✅ Task completed within limits!")
            
    except Exception as e:
        print(f"💥 Execution error: {e}")
        print("This might happen due to API issues, network problems, etc.")
    
    return None


async def custom_configuration_example():
    """
    Example 5: Custom agent configuration
    
    This shows how to configure agents with different settings.
    """
    print("\n=== Example 5: Custom Configuration ===")
    
    # Create agents with different configurations
    
    # Budget-conscious agent
    budget_agent = BaseAgent(
        max_cost=0.5,
        max_iterations=5,
        model="gpt-3.5-turbo"  # Assuming this is cheaper
    )
    
    # High-performance agent
    performance_agent = BaseAgent(
        max_cost=5.0,
        max_iterations=50,
        model="gpt-4"  # Assuming this is more capable
    )
    
    # Create orchestrators
    budget_orchestrator = SingleAgentOrchestrator(budget_agent)
    performance_orchestrator = SingleAgentOrchestrator(performance_agent)
    
    # Simple task for budget agent
    print("Budget agent working on simple task...")
    budget_result = await budget_orchestrator.execute_task(
        "List the main Python files in this project"
    )
    
    if budget_result["success"]:
        print(f"Budget agent: ${budget_result['cost']:.4f} spent")
    
    # Complex task for performance agent
    print("\nPerformance agent working on complex task...")
    performance_result = await performance_orchestrator.execute_task(
        "Analyze the architecture of this project and suggest optimizations"
    )
    
    if performance_result["success"]:
        print(f"Performance agent: ${performance_result['cost']:.4f} spent")
    
    return budget_result, performance_result


async def main():
    """
    Main function that runs all examples
    """
    print("🚀 equitrcoder Basic Single Agent Examples")
    print("=" * 50)
    
    # Check if we have API keys configured
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: No API keys found in environment variables.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run these examples.")
        print("   Examples will show the structure but may not execute successfully.")
        print()
    
    try:
        # Run all examples
        await basic_task_execution()
        await task_with_monitoring()
        await session_management_example()
        await error_handling_example()
        await custom_configuration_example()
        
        print("\n🎉 All examples completed!")
        print("\nNext steps:")
        print("- Try modifying the tasks to suit your needs")
        print("- Experiment with different cost and iteration limits")
        print("- Check out multi_agent_coordination.py for advanced examples")
        
    except Exception as e:
        print(f"\n💥 Error running examples: {e}")
        print("This might be due to missing API keys or network issues.")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 