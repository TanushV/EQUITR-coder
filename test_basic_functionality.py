#!/usr/bin/env python3
"""
Basic functionality test for the merged equitrcoder package.
"""
import asyncio
from equitrcoder import (
    BaseAgent, 
    WorkerAgent, 
    create_single_orchestrator,
    create_multi_orchestrator,
    WorkerConfig
)


async def test_base_agent():
    """Test BaseAgent functionality."""
    print("🧪 Testing BaseAgent...")
    
    agent = BaseAgent(max_cost=1.0, max_iterations=5)
    
    # Test basic properties
    assert agent.agent_id is not None
    assert agent.max_cost == 1.0
    assert agent.max_iterations == 5
    assert agent.current_cost == 0.0
    assert agent.iteration_count == 0
    
    # Test message handling
    agent.add_message("user", "Hello, agent!")
    messages = agent.get_messages()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello, agent!"
    
    # Test status
    status = agent.get_status()
    assert status["agent_id"] == agent.agent_id
    assert status["current_cost"] == 0.0
    
    print("✅ BaseAgent tests passed!")


async def test_worker_agent():
    """Test WorkerAgent functionality."""
    print("🧪 Testing WorkerAgent...")
    
    worker = WorkerAgent(
        worker_id="test_worker",
        scope_paths=["."],
        allowed_tools=["read_file", "edit_file"],
        max_cost=0.5
    )
    
    # Test basic properties
    assert worker.agent_id == "test_worker"
    assert worker.max_cost == 0.5
    assert "." in [str(p) for p in worker.scope_paths]
    assert "read_file" in worker.allowed_tools
    assert "edit_file" in worker.allowed_tools
    
    # Test file access
    assert worker.can_access_file("test_basic_functionality.py")
    
    # Test scope stats
    stats = worker.get_scope_stats()
    assert "scope_paths" in stats
    assert "allowed_tools" in stats
    
    print("✅ WorkerAgent tests passed!")


async def test_single_orchestrator():
    """Test SingleAgentOrchestrator functionality."""
    print("🧪 Testing SingleAgentOrchestrator...")
    
    agent = BaseAgent(max_cost=0.1, max_iterations=2)
    orchestrator = create_single_orchestrator(agent=agent)
    
    # Test basic properties
    status = orchestrator.get_status()
    assert status["orchestrator_type"] == "single_agent"
    assert "agent_status" in status
    
    # Test task execution (simplified)
    result = await orchestrator.execute_task("Test task")
    assert "success" in result
    assert "session_id" in result
    
    print("✅ SingleAgentOrchestrator tests passed!")


async def test_multi_orchestrator():
    """Test MultiAgentOrchestrator functionality."""
    print("🧪 Testing MultiAgentOrchestrator...")
    
    orchestrator = create_multi_orchestrator(
        max_concurrent_workers=2,
        global_cost_limit=1.0
    )
    
    # Create a worker
    config = WorkerConfig(
        worker_id="test_worker",
        scope_paths=["."],
        allowed_tools=["read_file"],
        max_cost=0.5
    )
    
    worker = orchestrator.create_worker(config)
    assert worker.agent_id == "test_worker"
    
    # Test orchestrator status
    status = orchestrator.get_orchestrator_status()
    assert status["orchestrator_type"] == "multi_agent"
    assert status["total_workers"] == 1
    
    # Test task execution
    result = await orchestrator.execute_task(
        task_id="test_task",
        worker_id="test_worker", 
        task_description="Test multi-agent task"
    )
    
    assert result.task_id == "test_task"
    assert result.worker_id == "test_worker"
    
    print("✅ MultiAgentOrchestrator tests passed!")


async def main():
    """Run all tests."""
    print("🚀 Starting equitrcoder functionality tests...\n")
    
    try:
        await test_base_agent()
        await test_worker_agent()
        await test_single_orchestrator()
        await test_multi_orchestrator()
        
        print("\n🎉 All tests passed! The merged equitrcoder package is working correctly.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 