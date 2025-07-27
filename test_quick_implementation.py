#!/usr/bin/env python3
"""
Quick test of EQUITR Coder with a small task to verify implementation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from equitrcoder.programmatic.interface import EquitrCoder, TaskConfiguration

async def test_small_task():
    """Test with a very small, simple task."""
    print("🧪 Testing EQUITR Coder with Small Task")
    print("=" * 50)
    
    # Load environment
    from equitrcoder.utils.env_loader import auto_load_environment
    env_status = auto_load_environment()
    
    if not env_status.get('providers', {}).get('moonshot', {}).get('available'):
        print("❌ Moonshot API not available. Please check your .env file.")
        return False
    
    print("✅ Environment loaded successfully")
    
    # Create single-agent coder
    coder = EquitrCoder(mode='single', repo_path='.')
    
    # Very simple task
    task = "Create a simple hello.py file that prints 'Hello, World!'"
    
    # Test task configuration with low cost and iterations
    config = TaskConfiguration(
        description=task,
        model='moonshot/kimi-k2-0711-preview',
        max_cost=0.05,  # Very low cost limit
        max_iterations=2  # Only 2 iterations
    )
    
    print(f"🎯 Task: {task}")
    print(f"💰 Max Cost: ${config.max_cost}")
    print(f"🔄 Max Iterations: {config.max_iterations}")
    print("-" * 50)
    
    # Execute task
    result = await coder.execute_task(task, config)
    
    print("-" * 50)
    print(f"✅ Success: {result.success}")
    print(f"💰 Actual Cost: ${result.cost:.4f}")
    print(f"🔄 Iterations Used: {result.iterations}")
    
    if result.error:
        print(f"❌ Error: {result.error}")
        return False
    
    # Verify documents were created
    docs_dir = Path("docs")
    required_docs = ["requirements.md", "design.md", "todos.md"]
    
    print("\n📄 Checking Documents:")
    for doc in required_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            print(f"✅ {doc} - {doc_path.stat().st_size} bytes")
        else:
            print(f"❌ Missing: {doc}")
            return False
    
    # Check if the actual file was created
    hello_file = Path("hello.py")
    if hello_file.exists():
        content = hello_file.read_text()
        print(f"\n📝 Created hello.py:")
        print(f"Content: {content.strip()}")
        if "Hello, World!" in content:
            print("✅ File contains expected content")
        else:
            print("⚠️ File doesn't contain expected content")
    else:
        print("⚠️ hello.py file not created (may be expected if task was just planning)")
    
    # Check todos
    from equitrcoder.tools.builtin.todo import TodoManager
    todo_manager = TodoManager()
    todos = todo_manager.list_todos()
    
    print(f"\n📋 Todos in System: {len(todos)}")
    completed_todos = [t for t in todos if t.status == "completed"]
    pending_todos = [t for t in todos if t.status == "pending"]
    
    print(f"✅ Completed: {len(completed_todos)}")
    print(f"⏳ Pending: {len(pending_todos)}")
    
    if completed_todos:
        print("Recent completed todos:")
        for todo in completed_todos[-3:]:  # Show last 3
            print(f"  ✅ {todo.title}")
    
    if pending_todos:
        print("Pending todos:")
        for todo in pending_todos[:3]:  # Show first 3
            print(f"  ⏳ {todo.title}")
    
    return result.success

if __name__ == "__main__":
    success = asyncio.run(test_small_task())
    if success:
        print("\n🎉 Quick test PASSED!")
    else:
        print("\n❌ Quick test FAILED!")
    sys.exit(0 if success else 1)