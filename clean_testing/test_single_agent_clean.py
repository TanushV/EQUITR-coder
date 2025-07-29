#!/usr/bin/env python3
"""
Clean test for single agent orchestrator in isolated environment.
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


async def test_single_agent_clean():
    """Test single agent orchestrator with a simple task in clean environment."""
    
    print("🧪 CLEAN SINGLE AGENT TEST")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    print()
    
    try:
        print("📝 Setting up agent and orchestrator...")
        
        # Discover all available tools
        tools = discover_tools()
        print(f"🔧 Discovered {len(tools)} tools")
        
        # Create a base agent with tools
        agent = BaseAgent(
            agent_id="test_agent",
            tools=tools
        )
        print(f"🤖 Created agent: {agent.agent_id}")
        
        # Create orchestrator with specific model
        orchestrator = SingleAgentOrchestrator(
            agent=agent,
            model="moonshot/kimi-k2-0711-preview",
            max_iterations=None  # Unlimited
        )
        print(f"🎭 Created orchestrator with model: moonshot/kimi-k2-0711-preview")
        
        # Set up verbose callbacks to monitor everything
        def on_message(msg):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            tool_name = msg.get('tool_name', '')
            success = msg.get('success', None)
            
            if role == 'tool':
                status = "✅" if success else "❌"
                print(f"🔧 TOOL {status} {tool_name}: {content[:150]}{'...' if len(content) > 150 else ''}")
            else:
                print(f"💬 {role.upper()}: {content[:200]}{'...' if len(content) > 200 else ''}")
        
        def on_iteration(iteration, status):
            print(f"\n🔁 === ITERATION {iteration} === Status: {status}")
        
        def on_completion(result):
            print(f"\n✅ TASK COMPLETED: Success={result.get('success', False)}")
        
        orchestrator.set_callbacks(
            on_message=on_message,
            on_iteration=on_iteration,
            on_completion=on_completion
        )
        
        print("✅ Setup complete!\n")
        
        # Simple calculator task
        test_task = """Create a simple Python calculator program called 'calculator.py' that:
1. Can add, subtract, multiply, and divide two numbers
2. Has a main() function that asks for user input
3. Includes proper error handling for division by zero
4. Has a simple menu system
5. Can run from command line

Make it work properly and test it."""
        
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
            if file_path.is_file() and not file_path.name.startswith('.'):
                print(f"  📄 {file_path}")
        
        # Check if calculator.py was created and test it
        calc_path = Path("calculator.py")
        if calc_path.exists():
            print(f"\n🧪 TESTING CALCULATOR:")
            print(f"📄 Calculator file size: {calc_path.stat().st_size} bytes")
            
            # Read and show the code
            code = calc_path.read_text()
            print(f"📝 Calculator code preview:")
            print("-" * 40)
            print(code[:500])
            if len(code) > 500:
                print("... (truncated)")
            print("-" * 40)
            
            # Try to run syntax check
            try:
                compile(code, str(calc_path), 'exec')
                print("✅ Calculator code compiles successfully!")
            except SyntaxError as e:
                print(f"❌ Calculator has syntax error: {e}")
        else:
            print("❌ Calculator.py was not created!")
        
        # Check docs folder
        docs_path = Path("docs")
        if docs_path.exists():
            print(f"\n📚 DOCS FOLDER CONTENTS:")
            for doc_file in docs_path.rglob("*"):
                if doc_file.is_file():
                    print(f"  📄 {doc_file}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_single_agent_clean())
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)