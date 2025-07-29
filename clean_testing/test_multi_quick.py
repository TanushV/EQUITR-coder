#!/usr/bin/env python3
"""
Quick test to see what happens with multi-agent orchestrator.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig
from equitrcoder.providers.litellm import LiteLLMProvider


async def test_multi_quick():
    """Quick test of multi-agent orchestrator to see what happens."""
    
    print("🧪 QUICK MULTI-AGENT TEST")
    print("=" * 40)
    
    try:
        print("📝 Setting up...")
        
        # Create providers
        supervisor_provider = LiteLLMProvider(model="o3")
        worker_provider = LiteLLMProvider(model="moonshot/kimi-k2-0711-preview")
        
        print(f"✅ Providers created")
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(
            supervisor_provider=supervisor_provider,
            worker_provider=worker_provider,
            max_concurrent_workers=1,
            global_cost_limit=2.0,
            max_total_iterations=20
        )
        print(f"✅ Orchestrator created")
        
        # Create one worker
        worker_config = WorkerConfig(
            worker_id="test_worker",
            scope_paths=["."],
            allowed_tools=["create_file", "edit_file", "read_file", "list_files", 
                          "create_todo", "update_todo", "list_todos", "ask_supervisor"],
            max_cost=1.0,
            max_iterations=15
        )
        
        worker = orchestrator.create_worker(worker_config, worker_provider)
        print(f"✅ Worker created: {worker_config.worker_id}")
        
        # Simple task
        task = "Create a simple Python function called 'greet' that takes a name and returns 'Hello, [name]!' in a file called 'greet.py'"
        
        print(f"🎯 Task: {task}")
        print("-" * 40)
        
        # Execute single task
        result = await orchestrator.execute_task(
            task_id="greet_task",
            worker_id="test_worker",  
            task_description=task,
            context={"quick_test": True}
        )
        
        print("-" * 40)
        print("📊 RESULT:")
        print(f"Success: {result.success}")
        print(f"Cost: ${result.cost:.4f}")
        print(f"Iterations: {result.iteration_count}")
        print(f"Time: {result.execution_time:.2f}s")
        if not result.success:
            print(f"Error: {result.error}")
        
        # Check files
        greet_file = Path("greet.py")
        if greet_file.exists():
            print(f"\n✅ greet.py created ({greet_file.stat().st_size} bytes)")
            code = greet_file.read_text()
            print(f"Code: {code[:200]}...")
            
            # Test it
            try:
                exec(code)
                print("✅ Code executes without errors")
            except Exception as e:
                print(f"❌ Code error: {e}")
        else:
            print("❌ greet.py not created")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_multi_quick())
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)