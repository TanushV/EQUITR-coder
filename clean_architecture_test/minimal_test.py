#!/usr/bin/env python3
"""
Minimal test of clean architecture components
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.core.clean_orchestrator import CleanOrchestrator


async def test_orchestrator_only():
    """Test just the orchestrator to verify doc creation works."""
    print("🧪 TESTING ORCHESTRATOR ONLY")
    print("=" * 50)
    
    try:
        orchestrator = CleanOrchestrator(model="moonshot/kimi-k2-0711-preview")
        
        # Simple task
        task = "Create a simple hello world program that prints 'Hello, World!' and save it as hello.py"
        
        print(f"Task: {task}")
        print("Creating documentation...")
        
        # Test doc creation
        result = await orchestrator.create_docs(
            task_description=task,
            project_path=".",
            num_agents=1
        )
        
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"✅ Task name: {result['task_name']}")
            print(f"✅ Requirements: {result['requirements_path']}")
            print(f"✅ Design: {result['design_path']}")
            print(f"✅ Todos: {result['todos_path']}")
            
            # Check if files exist
            for path_key in ['requirements_path', 'design_path', 'todos_path']:
                path = Path(result[path_key])
                if path.exists():
                    print(f"✅ {path.name} exists ({path.stat().st_size} bytes)")
                    
                    # Show first few lines
                    content = path.read_text()
                    first_lines = '\n'.join(content.split('\n')[:3])
                    print(f"   Preview: {first_lines}...")
                else:
                    print(f"❌ {path.name} missing")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_single_agent_basic():
    """Test single agent with minimal setup."""
    print("\n🧪 TESTING SINGLE AGENT BASIC")
    print("=" * 50)
    
    try:
        from equitrcoder.core.clean_agent import CleanAgent
        from equitrcoder.tools.discovery import discover_tools
        
        # Get minimal tools
        all_tools = discover_tools()
        essential_tools = [t for t in all_tools if t.get_name() in ['create_file', 'list_todos', 'update_todo']]
        
        print(f"Using {len(essential_tools)} essential tools")
        
        # Create agent
        agent = CleanAgent(
            agent_id="test_agent",
            model="moonshot/kimi-k2-0711-preview",
            tools=essential_tools,
            audit_model="o3",
            max_iterations=5  # Very limited iterations
        )
        
        # Set up monitoring
        iterations = []
        
        def on_iteration(iteration, status):
            iterations.append(iteration)
            print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")
        
        def on_audit(audit_info):
            if audit_info.get('status') == 'completed':
                passed = audit_info.get('passed', False)
                print(f"🔍 Audit: {'✅ PASSED' if passed else '❌ FAILED'}")
        
        agent.set_callbacks(on_iteration=on_iteration, on_audit=on_audit)
        
        # Very simple task
        task = "Use create_file to create hello.py with print('Hello, World!'). Then use update_todo to mark this task as completed."
        
        print(f"Task: {task}")
        print("Running agent...")
        
        result = await agent.run(task)
        
        print(f"Success: {result['success']}")
        print(f"Cost: ${result.get('cost', 0):.4f}")
        print(f"Iterations: {result.get('iterations', 0)}")
        print(f"Audit passed: {result.get('audit_result', {}).get('audit_passed', False)}")
        
        # Check if file was created
        hello_file = Path("hello.py")
        if hello_file.exists():
            print(f"✅ hello.py created: {hello_file.read_text().strip()}")
        else:
            print("❌ hello.py not created")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run minimal tests."""
    print("🧪 MINIMAL CLEAN ARCHITECTURE TESTS")
    print("=" * 60)
    
    # Test 1: Orchestrator only
    orchestrator_success = await test_orchestrator_only()
    
    # Test 2: Basic agent
    agent_success = await test_single_agent_basic()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MINIMAL TEST RESULTS:")
    print(f"Orchestrator: {'✅ PASSED' if orchestrator_success else '❌ FAILED'}")
    print(f"Agent: {'✅ PASSED' if agent_success else '❌ FAILED'}")
    
    overall_success = orchestrator_success and agent_success
    print(f"\nOverall: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)