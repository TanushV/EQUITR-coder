#!/usr/bin/env python3
"""
Test TRUE single agent mode (same model for orchestrator and agent).
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


async def test_true_single_agent_mode():
    """Test TRUE single agent mode where orchestrator IS the agent."""
    
    print("🧪 TESTING TRUE SINGLE AGENT MODE")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print("In this mode, orchestrator = agent = same model")
    print()
    
    try:
        print("📝 Setting up agent and orchestrator...")
        
        # Discover all available tools
        tools = discover_tools()
        print(f"🔧 Discovered {len(tools)} tools")
        
        # Create a base agent with tools
        agent = BaseAgent(
            agent_id="single_agent_true",
            tools=tools
        )
        print(f"🤖 Created agent: {agent.agent_id}")
        
        # Create orchestrator with SAME model for both (true single agent mode)
        model_name = "moonshot/kimi-k2-0711-preview"
        orchestrator = SingleAgentOrchestrator(
            agent=agent,
            model=model_name,
            supervisor_model=model_name,  # SAME model = true single agent
            max_iterations=None  # Unlimited
        )
        print(f"🎭 Created TRUE single agent orchestrator:")
        print(f"   Model: {model_name} (used for everything)")
        
        # Set up verbose callbacks
        def on_message(msg):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            tool_name = msg.get('tool_name', '')
            success = msg.get('success', None)
            
            if role == 'tool':
                status = "✅" if success else "❌"
                if tool_name in ['create_file', 'edit_file', 'update_todo', 'list_todos']:
                    print(f"🔧 TOOL {status} {tool_name}: {content[:200]}{'...' if len(content) > 200 else ''}")
                else:
                    print(f"🔧 TOOL {status} {tool_name}: {content[:80]}{'...' if len(content) > 80 else ''}")
            else:
                print(f"💬 {role.upper()}: {content[:120]}{'...' if len(content) > 120 else ''}")
        
        def on_iteration(iteration, status):
            print(f"\n🔁 === ITERATION {iteration} ===")
            cost = status.get('current_cost', 0)
            print(f"Cost: ${cost:.4f}, Can continue: {status.get('limits_status', {}).get('can_continue', True)}")
        
        def on_completion(result):
            print(f"\n🎯 COMPLETED: Success={result.get('success', False)}")
        
        orchestrator.set_callbacks(
            on_message=on_message,
            on_iteration=on_iteration,
            on_completion=on_completion
        )
        
        print("✅ Setup complete!\n")
        
        # Simple task - create a basic utility script
        test_task = """Create a simple Python utility script called 'utils.py' that:
1. Has a function to check if a number is even
2. Has a function to reverse a string
3. Has a main() function that tests both functions
4. Keep it simple and clean

Make sure it actually works."""
        
        print(f"🎯 TASK: {test_task}")
        print("=" * 70)
        
        # Execute the task
        result = await orchestrator.execute_task(
            task_description=test_task,
            context={"test_mode": True, "single_agent_mode": True}
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
        created_files = []
        for file_path in Path(".").glob("**/*"):
            if file_path.is_file() and not file_path.name.startswith('.') and file_path.suffix in ['.py', '.md', '.txt']:
                if file_path.name not in ['test_single_agent_true_mode.py', 'test_single_agent_fixed.py']:
                    created_files.append(file_path)
                    print(f"  📄 {file_path} ({file_path.stat().st_size} bytes)")
        
        # Test the utils.py if created
        utils_path = Path("utils.py")
        if utils_path.exists():
            print(f"\n🧪 TESTING UTILS.PY:")
            code = utils_path.read_text()
            print(f"📝 Code preview:")
            print("-" * 40)
            print(code[:600])
            if len(code) > 600:
                print("... (truncated)")
            print("-" * 40)
            
            # Syntax check
            try:
                compile(code, str(utils_path), 'exec')
                print("✅ Code compiles successfully!")
                
                # Check for expected functions
                if 'def ' in code:
                    print("✅ Contains function definitions!")
                if 'even' in code.lower():
                    print("✅ Has even number check!")
                if 'reverse' in code.lower():
                    print("✅ Has string reverse!")
                if 'main(' in code:
                    print("✅ Has main function!")
                    
            except SyntaxError as e:
                print(f"❌ Syntax error: {e}")
        else:
            print("❌ utils.py was not created!")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_true_single_agent_mode())
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)