#!/usr/bin/env python3
"""
Quick test of EQUITR Coder with a small task to verify implementation.
Tests in isolated testing folder.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    
    # Create single-agent coder in testing directory
    coder = EquitrCoder(mode='single', repo_path='.')
    
    # Very simple task
    task = "Create a simple hello.py file that prints 'Hello, World!' and add a comment explaining what it does"
    
    # Test task configuration with low cost and iterations
    config = TaskConfiguration(
        description=task,
        model='moonshot/kimi-k2-0711-preview',
        max_cost=0.08,  # Low cost limit
        max_iterations=3  # Few iterations
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
            # Show first few lines of each document
            content = doc_path.read_text()[:200] + "..." if len(doc_path.read_text()) > 200 else doc_path.read_text()
            print(f"   Preview: {content.strip()}")
        else:
            print(f"❌ Missing: {doc}")
            return False
    
    # Check if the actual file was created
    hello_file = Path("hello.py")
    if hello_file.exists():
        content = hello_file.read_text()
        print(f"\n📝 Created hello.py:")
        print(f"Content:\n{content}")
        if "Hello, World!" in content:
            print("✅ File contains expected content")
        else:
            print("⚠️ File doesn't contain expected content")
    else:
        print("⚠️ hello.py file not created")
    
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
        for todo in completed_todos[-5:]:  # Show last 5
            print(f"  ✅ {todo.title}")
    
    if pending_todos:
        print("Pending todos:")
        for todo in pending_todos[:5]:  # Show first 5
            print(f"  ⏳ {todo.title}")
    
    # Check audit system
    from equitrcoder.tools.builtin.audit import audit_manager
    should_audit = audit_manager.should_trigger_audit()
    print(f"\n🔍 Audit System: {'✅ Always triggers' if should_audit else '❌ Not triggering'}")
    
    return result.success

if __name__ == "__main__":
    # Change to testing directory
    os.chdir(Path(__file__).parent)
    print(f"Working directory: {os.getcwd()}")
    
    success = asyncio.run(test_small_task())
    if success:
        print("\n🎉 Quick test PASSED!")
    else:
        print("\n❌ Quick test FAILED!")
    sys.exit(0 if success else 1)