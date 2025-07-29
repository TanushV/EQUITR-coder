#!/usr/bin/env python3
"""
Test the FIXED single agent orchestrator in clean environment.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.orchestrators.single_orchestrator import SingleAgentOrchestrator
from equitrcoder.agents.base_agent import BaseAgent
from equitrcoder.tools.discovery import discover_tools


async def test_single_agent_fixed():
    """Test the FIXED single agent orchestrator with a simple task."""
    
    print("🧪 TESTING FIXED SINGLE AGENT ORCHESTRATOR")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print()
    
    try:
        print("📝 Setting up agent and orchestrator...")
        
        # Discover all available tools
        tools = discover_tools()
        print(f"🔧 Discovered {len(tools)} tools")
        
        # Create a base agent with tools
        agent = BaseAgent(
            agent_id="test_agent_fixed",
            tools=tools
        )
        print(f"🤖 Created agent: {agent.agent_id}")
        
        # Create orchestrator with specific model (moonshot for worker, o3 for supervisor)
        orchestrator = SingleAgentOrchestrator(
            agent=agent,
            model="moonshot/kimi-k2-0711-preview",
            supervisor_model="o3",  # Use o3 for supervisor/audit
            max_iterations=None  # Unlimited
        )
        print(f"🎭 Created orchestrator with:")
        print(f"   Worker model: moonshot/kimi-k2-0711-preview")
        print(f"   Supervisor model: o3")
        
        # Set up verbose callbacks to monitor everything
        iteration_count = 0
        def on_message(msg):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            tool_name = msg.get('tool_name', '')
            success = msg.get('success', None)
            
            if role == 'tool':
                status = "✅" if success else "❌"
                # Show more detail for important tools
                if tool_name in ['create_file', 'edit_file', 'update_todo', 'list_todos']:
                    print(f"🔧 TOOL {status} {tool_name}: {content[:300]}{'...' if len(content) > 300 else ''}")
                else:
                    print(f"🔧 TOOL {status} {tool_name}: {content[:100]}{'...' if len(content) > 100 else ''}")
            else:
                print(f"💬 {role.upper()}: {content[:150]}{'...' if len(content) > 150 else ''}")
        
        def on_iteration(iteration, status):
            nonlocal iteration_count
            iteration_count = iteration
            print(f"\n🔁 === ITERATION {iteration} ===")
            print(f"Status: Cost=${status.get('current_cost', 0):.4f}, Tools={len(status.get('available_tools', []))}")
        
        def on_completion(result):
            print(f"\n🎯 TASK COMPLETED: Success={result.get('success', False)}")
        
        orchestrator.set_callbacks(
            on_message=on_message,
            on_iteration=on_iteration,
            on_completion=on_completion
        )
        
        print("✅ Setup complete!\n")
        
        # Simple web server task that should be doable
        test_task = """Create a simple Python web server using Flask that:
1. Has a single route '/' that returns 'Hello, World!'
2. Runs on port 5000
3. Has proper error handling
4. Save it as 'app.py'

Keep it simple and functional."""
        
        print(f"🎯 TASK: {test_task}")
        print("=" * 70)
        
        # Execute the task
        result = await orchestrator.execute_task(
            task_description=test_task,
            context={"test_mode": True, "clean_environment": True}
        )
        
        print("\n" + "=" * 70)
        print("📊 FINAL RESULT:")
        print(f"✅ Success: {result['success']}")
        print(f"💰 Cost: ${result['cost']:.4f}")
        print(f"🔄 Iterations: {result['iterations']}")
        print(f"📁 Task Name: {result.get('task_name', 'N/A')}")
        
        if not result['success']:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Check what files were created
        print("\n📁 FILES CREATED:")
        current_files = list(Path(".").glob("**/*"))
        for file_path in current_files:
            if file_path.is_file() and not file_path.name.startswith('.') and file_path.name != 'test_single_agent_fixed.py':
                print(f"  📄 {file_path} ({file_path.stat().st_size} bytes)")
        
        # Check if app.py was created and test it
        app_path = Path("app.py")
        if app_path.exists():
            print(f"\n🧪 TESTING WEB SERVER:")
            print(f"📄 App file size: {app_path.stat().st_size} bytes")
            
            # Read and show the code
            code = app_path.read_text()
            print(f"📝 App code preview:")
            print("-" * 40)
            print(code[:800])
            if len(code) > 800:
                print("... (truncated)")
            print("-" * 40)
            
            # Try to run syntax check
            try:
                compile(code, str(app_path), 'exec')
                print("✅ App code compiles successfully!")
                
                # Check if it imports Flask
                if 'flask' in code.lower() or 'Flask' in code:
                    print("✅ Uses Flask framework!")
                if 'app.run(' in code:
                    print("✅ Has app.run() call!")
                if '@app.route' in code:
                    print("✅ Has route decorators!")
                    
            except SyntaxError as e:
                print(f"❌ App has syntax error: {e}")
        else:
            print("❌ app.py was not created!")
        
        # Check docs folder
        docs_path = Path("docs")
        if docs_path.exists():
            print(f"\n📚 DOCS FOLDER CONTENTS:")
            for doc_file in docs_path.rglob("*"):
                if doc_file.is_file():
                    print(f"  📄 {doc_file}")
        
        # Check todo files
        todo_files = list(Path(".").glob(".EQUITR_todos_*.json"))
        if todo_files:
            print(f"\n📋 TODO FILES:")
            for todo_file in todo_files:
                print(f"  📄 {todo_file}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_single_agent_fixed())
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)