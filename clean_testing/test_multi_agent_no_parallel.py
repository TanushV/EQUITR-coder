#!/usr/bin/env python3
"""
Test multi-agent orchestrator in NO PARALLEL mode (supervisor + single worker).
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig
from equitrcoder.providers.litellm import LiteLLMProvider


async def test_multi_agent_no_parallel():
    """Test multi-agent orchestrator with supervisor + single worker (no parallel)."""
    
    print("🧪 TESTING MULTI-AGENT NO PARALLEL MODE")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print("Mode: Supervisor (o3) + Single Worker (moonshot) - No parallel execution")
    print()
    
    try:
        print("📝 Setting up multi-agent orchestrator...")
        
        # Create providers with correct models
        supervisor_provider = LiteLLMProvider(model="o3")  # OpenAI API key
        worker_provider = LiteLLMProvider(model="moonshot/kimi-k2-0711-preview")  # Moonshot API key
        
        print(f"✅ Created supervisor provider: o3")
        print(f"✅ Created worker provider: moonshot/kimi-k2-0711-preview")
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(
            supervisor_provider=supervisor_provider,
            worker_provider=worker_provider,
            max_concurrent_workers=1,  # Only 1 worker (no parallel)
            global_cost_limit=5.0,  # Reasonable limit
            max_total_iterations=50  # Reasonable limit
        )
        print(f"🎭 Created multi-agent orchestrator (no parallel)")
        
        # Create a single worker
        worker_config = WorkerConfig(
            worker_id="main_worker",
            scope_paths=["."],
            allowed_tools=["create_file", "edit_file", "read_file", "list_files", "run_command", 
                          "create_todo", "update_todo", "list_todos", "ask_supervisor"],
            max_cost=2.0,
            max_iterations=None  # Unlimited for worker
        )
        
        worker = orchestrator.create_worker(worker_config, worker_provider)
        print(f"🤖 Created worker: {worker_config.worker_id}")
        print(f"   Tools: {len(worker_config.allowed_tools)} tools including ask_supervisor")
        
        # Set up callbacks for monitoring
        def on_task_start(task_id, worker_id, description):
            print(f"\n🎯 TASK START: {task_id} -> Worker {worker_id}")
            print(f"   Description: {description[:100]}{'...' if len(description) > 100 else ''}")
        
        def on_task_complete(task_result):
            print(f"\n✅ TASK COMPLETE: {task_result.task_id}")
            print(f"   Success: {task_result.success}")
            print(f"   Cost: ${task_result.cost:.4f}")
            print(f"   Iterations: {task_result.iteration_count}")
            if not task_result.success:
                print(f"   Error: {task_result.error}")
        
        def on_worker_message(msg):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if role == 'tool' and msg.get('tool_name') in ['ask_supervisor', 'create_file', 'update_todo']:
                print(f"🔧 {msg.get('tool_name')}: {content[:150]}{'...' if len(content) > 150 else ''}")
            elif role == 'assistant':
                print(f"💬 WORKER: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        def on_cost_update(total_cost, delta):
            print(f"💰 Cost update: +${delta:.4f} (total: ${total_cost:.4f})")
        
        orchestrator.set_callbacks(
            on_task_start=on_task_start,
            on_task_complete=on_task_complete,
            on_worker_message=on_worker_message,
            on_cost_update=on_cost_update
        )
        
        print("✅ Setup complete!\n")
        
        # Task that benefits from supervisor guidance
        coordination_task = """Create a simple task management system with the following components:
1. A Task class to represent individual tasks
2. A TaskManager class to handle CRUD operations
3. Save tasks to a JSON file for persistence
4. Include a simple CLI interface to add/list/complete tasks
5. Make it clean, well-structured, and follow good practices

This requires architectural decisions that the supervisor can help with."""
        
        # Single worker task (no parallel)
        worker_tasks = [{
            "task_id": "task_manager_system",
            "worker_id": "main_worker",
            "task_description": coordination_task,
            "context": {"mode": "no_parallel", "use_supervisor": True}
        }]
        
        print(f"🎯 COORDINATION TASK: {coordination_task}")
        print("=" * 70)
        
        # Execute using coordinate_workers (which handles document creation)
        result = await orchestrator.coordinate_workers(
            coordination_task=coordination_task,
            worker_tasks=worker_tasks
        )
        
        print("\n" + "=" * 70)
        print("📊 COORDINATION RESULT:")
        print(f"✅ Success: {result['success']}")
        print(f"💰 Total Cost: ${result.get('total_cost', 0):.4f}")
        print(f"⏱️ Total Time: {result.get('total_time', 0):.2f}s")
        print(f"👥 Worker Results: {len(result.get('worker_results', []))}")
        print(f"📁 Task Name: {result.get('task_name', 'N/A')}")
        
        if result.get('worker_results'):
            for i, worker_result in enumerate(result['worker_results']):
                print(f"   Worker {i+1}: Success={worker_result.success}, Cost=${worker_result.cost:.4f}")
        
        if not result['success']:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Check what files were created
        print("\n📁 FILES CREATED:")
        created_files = []
        for file_path in Path(".").glob("**/*"):
            if (file_path.is_file() and 
                not file_path.name.startswith('.') and 
                file_path.suffix in ['.py', '.json', '.md', '.txt'] and
                'test_multi_agent' not in file_path.name):
                created_files.append(file_path)
                print(f"  📄 {file_path} ({file_path.stat().st_size} bytes)")
        
        # Test any Python files created
        python_files = [f for f in created_files if f.suffix == '.py']
        for py_file in python_files:
            print(f"\n🧪 TESTING {py_file.name}:")
            try:
                code = py_file.read_text()
                compile(code, str(py_file), 'exec')
                print(f"   ✅ {py_file.name} compiles successfully!")
                
                # Check for expected patterns
                if 'class ' in code:
                    print(f"   ✅ Contains classes!")
                if 'def ' in code:
                    print(f"   ✅ Contains functions!")
                if 'json' in code.lower():
                    print(f"   ✅ Uses JSON for persistence!")
                    
            except SyntaxError as e:
                print(f"   ❌ {py_file.name} has syntax error: {e}")
        
        # Check docs folder
        docs_path = Path("docs")
        if docs_path.exists():
            print(f"\n📚 DOCS FOLDER:")
            for doc_file in docs_path.rglob("*.md"):
                print(f"  📄 {doc_file}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_multi_agent_no_parallel())
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)