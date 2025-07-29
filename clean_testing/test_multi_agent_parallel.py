#!/usr/bin/env python3
"""
Test multi-agent orchestrator in PARALLEL mode (supervisor + multiple parallel workers).
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig
from equitrcoder.providers.litellm import LiteLLMProvider


async def test_multi_agent_parallel():
    """Test multi-agent orchestrator with supervisor + multiple parallel workers."""
    
    print("🧪 TESTING MULTI-AGENT PARALLEL MODE")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print("Mode: Supervisor (o3) + Multiple Workers (moonshot) - Parallel execution")
    print()
    
    try:
        print("📝 Setting up multi-agent orchestrator...")
        
        # Create providers with correct models
        supervisor_provider = LiteLLMProvider(model="o3")  # OpenAI API key
        worker_provider = LiteLLMProvider(model="moonshot/kimi-k2-0711-preview")  # Moonshot API key
        
        print(f"✅ Created supervisor provider: o3")
        print(f"✅ Created worker provider: moonshot/kimi-k2-0711-preview")
        
        # Create orchestrator for parallel execution
        orchestrator = MultiAgentOrchestrator(
            supervisor_provider=supervisor_provider,
            worker_provider=worker_provider,
            max_concurrent_workers=3,  # Allow 3 parallel workers
            global_cost_limit=8.0,  # Higher limit for parallel
            max_total_iterations=100  # Higher limit for parallel
        )
        print(f"🎭 Created multi-agent orchestrator (parallel mode)")
        
        # Create multiple workers for parallel execution
        worker_configs = [
            WorkerConfig(
                worker_id="frontend_worker",
                scope_paths=["./frontend", "./static", "./templates"],
                allowed_tools=["create_file", "edit_file", "read_file", "list_files", 
                              "create_todo", "update_todo", "list_todos", "ask_supervisor"],
                max_cost=2.0,
                max_iterations=None
            ),
            WorkerConfig(
                worker_id="backend_worker", 
                scope_paths=["./backend", "./api", "./models"],
                allowed_tools=["create_file", "edit_file", "read_file", "list_files",
                              "create_todo", "update_todo", "list_todos", "ask_supervisor"],
                max_cost=2.0,
                max_iterations=None
            ),
            WorkerConfig(
                worker_id="config_worker",
                scope_paths=["./config", "."],
                allowed_tools=["create_file", "edit_file", "read_file", "list_files",
                              "create_todo", "update_todo", "list_todos", "ask_supervisor"],
                max_cost=1.5,
                max_iterations=None
            )
        ]
        
        # Create all workers
        workers = []
        for config in worker_configs:
            worker = orchestrator.create_worker(config, worker_provider)
            workers.append(worker)
            print(f"🤖 Created worker: {config.worker_id} (scope: {config.scope_paths[0]})")
        
        # Set up callbacks for monitoring
        def on_task_start(task_id, worker_id, description):
            print(f"\n🎯 TASK START: {task_id} -> Worker {worker_id}")
        
        def on_task_complete(task_result):
            print(f"✅ TASK COMPLETE: {task_result.task_id} (Worker: {task_result.worker_id})")
            print(f"   Success: {task_result.success}, Cost: ${task_result.cost:.4f}")
        
        def on_worker_message(msg):
            if msg.get('role') == 'tool' and msg.get('tool_name') in ['ask_supervisor', 'create_file']:
                print(f"🔧 {msg.get('tool_name')}: {msg.get('content', '')[:100]}...")
        
        orchestrator.set_callbacks(
            on_task_start=on_task_start,
            on_task_complete=on_task_complete,
            on_worker_message=on_worker_message
        )
        
        print("✅ Setup complete!\n")
        
        # Complex task that benefits from parallel execution
        coordination_task = """Create a simple web application with the following structure:
1. Frontend: HTML templates and CSS styling
2. Backend: Python Flask API with routes
3. Configuration: Requirements file and basic config
4. Each component should be modular and well-structured
5. The app should have a simple "Hello World" functionality with a form

This task is designed to be split among multiple parallel agents."""
        
        # Create tasks for parallel workers (will be automatically distributed)
        worker_tasks = [
            {
                "task_id": "frontend_task",
                "worker_id": "frontend_worker", 
                "task_description": "Handle frontend components - HTML templates and CSS styling",
                "context": {"component": "frontend", "parallel": True}
            },
            {
                "task_id": "backend_task",
                "worker_id": "backend_worker",
                "task_description": "Handle backend components - Flask API and routes", 
                "context": {"component": "backend", "parallel": True}
            },
            {
                "task_id": "config_task",
                "worker_id": "config_worker",
                "task_description": "Handle configuration - requirements and setup files",
                "context": {"component": "config", "parallel": True}
            }
        ]
        
        print(f"🎯 COORDINATION TASK: {coordination_task}")
        print(f"👥 Parallel Workers: {len(worker_tasks)}")
        print("=" * 70)
        
        # Execute using coordinate_workers with automatic todo splitting
        result = await orchestrator.coordinate_workers(
            coordination_task=coordination_task,
            worker_tasks=worker_tasks
        )
        
        print("\n" + "=" * 70)
        print("📊 PARALLEL COORDINATION RESULT:")
        print(f"✅ Success: {result['success']}")
        print(f"💰 Total Cost: ${result.get('total_cost', 0):.4f}")
        print(f"⏱️ Total Time: {result.get('total_time', 0):.2f}s")
        print(f"👥 Workers: {len(result.get('worker_results', []))}")
        print(f"📁 Task Name: {result.get('task_name', 'N/A')}")
        
        # Show individual worker results
        if result.get('worker_results'):
            print(f"\n👥 WORKER RESULTS:")
            for worker_result in result['worker_results']:
                print(f"   🤖 {worker_result.worker_id}:")
                print(f"      Success: {worker_result.success}")
                print(f"      Cost: ${worker_result.cost:.4f}")
                print(f"      Iterations: {worker_result.iteration_count}")
                print(f"      Time: {worker_result.execution_time:.2f}s")
                if not worker_result.success:
                    print(f"      Error: {worker_result.error}")
        
        # Check what files were created
        print("\n📁 FILES CREATED:")
        created_files = []
        for file_path in Path(".").glob("**/*"):
            if (file_path.is_file() and 
                not file_path.name.startswith('.') and 
                file_path.suffix in ['.py', '.html', '.css', '.txt', '.md'] and
                'test_multi_agent' not in file_path.name):
                created_files.append(file_path)
                print(f"  📄 {file_path} ({file_path.stat().st_size} bytes)")
        
        # Check for parallel structure
        directories = [p for p in Path(".").glob("*") if p.is_dir() and not p.name.startswith('.')]
        if directories:
            print(f"\n📁 DIRECTORIES CREATED:")
            for dir_path in directories:
                if dir_path.name not in ['docs', '__pycache__']:
                    print(f"  📁 {dir_path}/")
                    # List files in each directory
                    for file_path in dir_path.glob("*"):
                        if file_path.is_file():
                            print(f"    📄 {file_path.name}")
        
        # Test any Python files
        python_files = [f for f in created_files if f.suffix == '.py' and 'app' in f.name.lower()]
        for py_file in python_files:
            print(f"\n🧪 TESTING {py_file.name}:")
            try:
                code = py_file.read_text()
                compile(code, str(py_file), 'exec')
                print(f"   ✅ Compiles successfully!")
                
                if 'flask' in code.lower():
                    print(f"   ✅ Uses Flask framework!")
                if '@app.route' in code:
                    print(f"   ✅ Has route decorators!")
                    
            except SyntaxError as e:
                print(f"   ❌ Syntax error: {e}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_multi_agent_parallel())
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)