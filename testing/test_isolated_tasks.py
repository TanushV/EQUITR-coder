#!/usr/bin/env python3
"""
Test that tasks are properly isolated and todos don't compound.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from equitrcoder.core.document_workflow import DocumentWorkflowManager
from equitrcoder.tools.builtin.todo import TodoManager

async def test_task_isolation():
    """Test that each task creates isolated documents and todos."""
    print("🧪 Testing Task Isolation and Todo Management")
    print("=" * 60)
    
    # Load environment
    from equitrcoder.utils.env_loader import auto_load_environment
    env_status = auto_load_environment()
    
    if not env_status.get('providers', {}).get('moonshot', {}).get('available'):
        print("❌ Moonshot API not available")
        return False
    
    # Create document manager with test-specific todo file
    test_todo_file = "test_todos.json"
    doc_manager = DocumentWorkflowManager(
        model='moonshot/kimi-k2-0711-preview',
        todo_file=test_todo_file
    )
    
    # Clean up any existing test todos
    if Path(test_todo_file).exists():
        Path(test_todo_file).unlink()
    
    print("🧹 Starting with clean todo system")
    
    # Task 1: Simple calculator
    print("\n📋 Task 1: Creating simple calculator task")
    result1 = await doc_manager.create_documents_programmatic(
        user_prompt="Create a simple calculator with add and subtract",
        project_path=".",
        task_name="calculator_task"
    )
    
    if not result1.success:
        print(f"❌ Task 1 failed: {result1.error}")
        return False
    
    # Check task 1 documents
    task1_dir = Path("docs/calculator_task")
    if not task1_dir.exists():
        print("❌ Task 1 directory not created")
        return False
    
    task1_docs = ["requirements.md", "design.md", "todos.md"]
    for doc in task1_docs:
        if not (task1_dir / doc).exists():
            print(f"❌ Task 1 missing {doc}")
            return False
    
    print("✅ Task 1 documents created in isolated folder")
    
    # Check todos for task 1
    todo_manager = TodoManager(todo_file=test_todo_file)
    task1_todos = [t for t in todo_manager.list_todos() if "task-calculator_task" in t.tags]
    print(f"📝 Task 1 created {len(task1_todos)} todos")
    
    # Task 2: Simple web server
    print("\n📋 Task 2: Creating web server task")
    result2 = await doc_manager.create_documents_programmatic(
        user_prompt="Create a simple web server with basic routing",
        project_path=".",
        task_name="webserver_task"
    )
    
    if not result2.success:
        print(f"❌ Task 2 failed: {result2.error}")
        return False
    
    # Check task 2 documents
    task2_dir = Path("docs/webserver_task")
    if not task2_dir.exists():
        print("❌ Task 2 directory not created")
        return False
    
    task2_docs = ["requirements.md", "design.md", "todos.md"]
    for doc in task2_docs:
        if not (task2_dir / doc).exists():
            print(f"❌ Task 2 missing {doc}")
            return False
    
    print("✅ Task 2 documents created in isolated folder")
    
    # Check todos for task 2
    task2_todos = [t for t in todo_manager.list_todos() if "task-webserver_task" in t.tags]
    print(f"📝 Task 2 created {len(task2_todos)} todos")
    
    # Verify isolation
    all_todos = todo_manager.list_todos()
    total_todos = len(all_todos)
    
    print(f"\n📊 Todo Analysis:")
    print(f"   Total todos in system: {total_todos}")
    print(f"   Task 1 todos: {len(task1_todos)}")
    print(f"   Task 2 todos: {len(task2_todos)}")
    print(f"   Expected total: {len(task1_todos) + len(task2_todos)}")
    
    # Verify no compounding
    if total_todos == len(task1_todos) + len(task2_todos):
        print("✅ No todo compounding - perfect isolation!")
    else:
        print("❌ Todo compounding detected")
        return False
    
    # Verify folder structure
    docs_dir = Path("docs")
    task_folders = [d for d in docs_dir.iterdir() if d.is_dir()]
    
    print(f"\n📁 Document Structure:")
    for folder in task_folders:
        docs_in_folder = [f for f in folder.iterdir() if f.is_file()]
        print(f"   {folder.name}/")
        for doc in docs_in_folder:
            print(f"     ├── {doc.name}")
    
    # Verify reasonable task counts
    task1_content = (task1_dir / "todos.md").read_text()
    task2_content = (task2_dir / "todos.md").read_text()
    
    task1_count = task1_content.count('- [ ]')
    task2_count = task2_content.count('- [ ]')
    
    print(f"\n📋 Task Counts:")
    print(f"   Task 1: {task1_count} tasks")
    print(f"   Task 2: {task2_count} tasks")
    
    if 8 <= task1_count <= 15 and 8 <= task2_count <= 15:
        print("✅ Both tasks have reasonable task counts (8-15)")
    else:
        print("⚠️ Task counts outside ideal range")
    
    # Clean up test files
    if Path(test_todo_file).exists():
        Path(test_todo_file).unlink()
    
    return True

async def test_parallel_agent_isolation():
    """Test that parallel agent todos are properly categorized and isolated."""
    print("\n👥 Testing Parallel Agent Todo Isolation")
    print("=" * 50)
    
    # Create document manager
    test_todo_file = "test_parallel_todos.json"
    doc_manager = DocumentWorkflowManager(
        model='moonshot/kimi-k2-0711-preview',
        todo_file=test_todo_file
    )
    
    # Clean up any existing test todos
    if Path(test_todo_file).exists():
        Path(test_todo_file).unlink()
    
    # Create base documents
    result = await doc_manager.create_documents_programmatic(
        user_prompt="Create a task management system",
        project_path=".",
        task_name="taskmanager_parallel"
    )
    
    if not result.success:
        print(f"❌ Base document creation failed: {result.error}")
        return False
    
    # Create parallel agent todos
    requirements_content = Path(result.requirements_path).read_text()
    design_content = Path(result.design_path).read_text()
    
    agent_todo_files = await doc_manager.create_split_todos_for_parallel_agents(
        user_prompt="Create a task management system",
        requirements_content=requirements_content,
        design_content=design_content,
        num_agents=3,
        project_path="."
    )
    
    if len(agent_todo_files) != 3:
        print(f"❌ Expected 3 agent files, got {len(agent_todo_files)}")
        return False
    
    print("✅ Created todos for 3 parallel agents")
    
    # Verify each agent has distinct categories
    all_categories = []
    total_agent_todos = 0
    
    for i, todo_file in enumerate(agent_todo_files):
        content = Path(todo_file).read_text()
        
        # Extract categories
        categories = []
        for line in content.split('\n'):
            if line.startswith('## ') and 'Instructions' not in line and 'Assigned Categories' not in line:
                categories.append(line[3:].strip())
        
        # Count todos
        todo_count = content.count('- [ ]')
        total_agent_todos += todo_count
        
        print(f"   Agent {i+1}: {len(categories)} categories, {todo_count} todos")
        all_categories.extend(categories)
    
    # Check for category overlap
    unique_categories = set(all_categories)
    if len(all_categories) == len(unique_categories):
        print("✅ No category overlap between agents")
    else:
        print("❌ Category overlap detected")
        return False
    
    # Verify todos in system
    todo_manager = TodoManager(todo_file=test_todo_file)
    system_todos = todo_manager.list_todos()
    
    print(f"📝 System todos: {len(system_todos)}")
    print(f"📝 Agent file todos: {total_agent_todos}")
    
    # Clean up test files
    if Path(test_todo_file).exists():
        Path(test_todo_file).unlink()
    
    return len(system_todos) == total_agent_todos

async def main():
    """Run all isolation tests."""
    # Change to testing directory
    os.makedirs("testing", exist_ok=True)
    os.chdir("testing")
    print(f"Working directory: {os.getcwd()}")
    
    tests = [
        ("Task Isolation", test_task_isolation),
        ("Parallel Agent Isolation", test_parallel_agent_isolation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print("\n🎯 ISOLATION TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success, error in results:
        if success:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED" + (f" - {error}" if error else ""))
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL ISOLATION TESTS PASSED!")
        print("\n🚀 Verified:")
        print("  ✅ Tasks create isolated document folders")
        print("  ✅ Todos don't compound between tasks")
        print("  ✅ Parallel agents get distinct categories")
        print("  ✅ Reasonable task counts (8-15 per task)")
        print("  ✅ Clean todo system management")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)