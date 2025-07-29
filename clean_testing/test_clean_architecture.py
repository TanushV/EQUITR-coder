#!/usr/bin/env python3
"""
Test the new clean architecture - CleanOrchestrator + CleanAgent
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.modes.single_agent_mode import run_single_agent_mode
from equitrcoder.modes.multi_agent_mode import run_multi_agent_sequential, run_multi_agent_parallel


async def test_clean_single_agent():
    """Test the clean single agent mode."""
    print("🧪 TESTING CLEAN SINGLE AGENT MODE")
    print("=" * 50)
    
    # Set up callbacks for monitoring
    def on_message(msg):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if role == 'tool' and msg.get('tool_name') in ['create_file', 'update_todo']:
            print(f"🔧 {msg.get('tool_name')}: {content[:100]}{'...' if len(content) > 100 else ''}")
        elif role == 'assistant':
            print(f"💬 AGENT: {content[:80]}{'...' if len(content) > 80 else ''}")
    
    def on_iteration(iteration, status):
        print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")
    
    def on_audit(audit_info):
        status = audit_info.get('status')
        if status == 'starting':
            print(f"🔍 Starting audit with {audit_info.get('model', 'unknown')}...")
        elif status == 'completed':
            passed = audit_info.get('passed', False)
            print(f"{'✅ AUDIT PASSED' if passed else '❌ AUDIT FAILED'}")
    
    callbacks = {
        'on_message': on_message,
        'on_iteration': on_iteration,
        'on_audit': on_audit
    }
    
    # Simple task
    task = """Create a simple temperature converter program:
1. Convert between Celsius and Fahrenheit
2. Have functions for both conversions
3. Include a main function that demonstrates both conversions
4. Save as 'temp_converter.py'"""
    
    print(f"🎯 Task: {task}")
    print("-" * 50)
    
    # Run single agent mode
    result = await run_single_agent_mode(
        task_description=task,
        agent_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        max_iterations=20,
        callbacks=callbacks
    )
    
    print("-" * 50)
    print("📊 SINGLE AGENT RESULT:")
    print(f"Success: {result['success']}")
    print(f"Cost: ${result.get('cost', 0):.4f}")
    print(f"Iterations: {result.get('iterations', 0)}")
    
    # Check if file was created
    temp_file = Path("temp_converter.py")
    if temp_file.exists():
        print(f"✅ temp_converter.py created ({temp_file.stat().st_size} bytes)")
        code = temp_file.read_text()
        
        # Test compilation
        try:
            compile(code, str(temp_file), 'exec')
            print("✅ Code compiles successfully")
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
    else:
        print("❌ temp_converter.py not created")
    
    return result['success']


async def test_clean_multi_agent_sequential():
    """Test the clean multi-agent sequential mode."""
    print("\n🧪 TESTING CLEAN MULTI-AGENT SEQUENTIAL MODE")
    print("=" * 50)
    
    # Set up callbacks
    def on_message(msg):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if role == 'tool' and msg.get('tool_name') in ['create_file', 'update_todo']:
            print(f"🔧 {msg.get('tool_name')}: {content[:80]}...")
    
    def on_audit(audit_info):
        if audit_info.get('status') == 'completed':
            passed = audit_info.get('passed', False)
            print(f"🔍 Audit: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    callbacks = {
        'on_message': on_message,
        'on_audit': on_audit
    }
    
    # Task that can be split between agents
    task = """Create a simple web application with:
1. HTML frontend with a form
2. Python backend with Flask
3. JSON data storage
4. Basic styling with CSS"""
    
    print(f"🎯 Task: {task}")
    print("-" * 50)
    
    # Run with 2 agents sequentially
    result = await run_multi_agent_sequential(
        task_description=task,
        num_agents=2,
        agent_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        max_iterations_per_agent=15,
        callbacks=callbacks
    )
    
    print("-" * 50)
    print("📊 MULTI-AGENT SEQUENTIAL RESULT:")
    print(f"Success: {result['success']}")
    print(f"Total Cost: ${result.get('total_cost', 0):.4f}")
    print(f"Total Iterations: {result.get('total_iterations', 0)}")
    print(f"Agents: {result.get('num_agents', 0)}")
    
    # Check what files were created
    created_files = []
    for file_path in Path(".").glob("**/*"):
        if (file_path.is_file() and 
            not file_path.name.startswith('.') and 
            file_path.suffix in ['.py', '.html', '.css', '.json'] and
            'test_clean' not in file_path.name):
            created_files.append(file_path)
    
    print(f"📁 Files created: {len(created_files)}")
    for f in created_files:
        print(f"  📄 {f}")
    
    return result['success']


async def main():
    """Run all clean architecture tests."""
    print("🧪 CLEAN ARCHITECTURE TESTING")
    print("=" * 60)
    
    try:
        # Test 1: Single Agent
        single_success = await test_clean_single_agent()
        
        # Test 2: Multi-Agent Sequential  
        multi_success = await test_clean_multi_agent_sequential()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 CLEAN ARCHITECTURE TEST SUMMARY:")
        print(f"Single Agent: {'✅ PASSED' if single_success else '❌ FAILED'}")
        print(f"Multi-Agent Sequential: {'✅ PASSED' if multi_success else '❌ FAILED'}")
        
        overall_success = single_success and multi_success
        print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)