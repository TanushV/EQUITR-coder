#!/usr/bin/env python3
"""
Quick test of single agent mode only
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.modes.single_agent_mode import run_single_agent_mode


async def test_single_agent():
    """Quick test of single agent mode."""
    print("🧪 QUICK SINGLE AGENT TEST")
    print("=" * 50)
    
    # Simple monitoring
    def on_message(msg):
        role = msg.get('role', 'unknown')
        if role == 'tool':
            tool_name = msg.get('metadata', {}).get('tool_name', 'unknown')
            print(f"🔧 Tool: {tool_name}")
        elif role == 'assistant':
            content = msg.get('content', '')
            print(f"🤖 Agent: {content[:60]}...")
    
    def on_iteration(iteration, status):
        print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")
    
    def on_audit(audit_info):
        if audit_info.get('status') == 'completed':
            passed = audit_info.get('passed', False)
            print(f"🔍 Audit: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    callbacks = {
        'on_message': on_message,
        'on_iteration': on_iteration,
        'on_audit': on_audit
    }
    
    # Very simple task
    task = """Create a simple hello world program:
1. Print 'Hello, World!'
2. Add a comment explaining what it does
3. Save as 'hello.py'"""
    
    print(f"Task: {task}")
    print("-" * 50)
    
    try:
        result = await run_single_agent_mode(
            task_description=task,
            agent_model="moonshot/kimi-k2-0711-preview",
            audit_model="o3",
            max_iterations=10,
            callbacks=callbacks
        )
        
        print("-" * 50)
        print(f"Result: {result['success']}")
        print(f"Cost: ${result.get('cost', 0):.4f}")
        print(f"Iterations: {result.get('iterations', 0)}")
        
        # Check file
        hello_file = Path("hello.py")
        if hello_file.exists():
            print(f"✅ hello.py created")
            print(f"Content:\n{hello_file.read_text()}")
        else:
            print("❌ hello.py not created")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_single_agent())
    print(f"\nOverall: {'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)