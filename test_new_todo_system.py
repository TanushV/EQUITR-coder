#!/usr/bin/env python3
"""
Test script to verify the new dependency-aware Task Group System works correctly.
"""

import asyncio
import json
from pathlib import Path
from equitrcoder.tools.builtin.todo import TodoManager, set_global_todo_file

async def test_new_todo_system():
    """Test the new dependency-aware todo system."""
    print("🧪 Testing the new dependency-aware Task Group System...")
    
    # Create a test todo file
    test_file = Path("test_todos.json")
    if test_file.exists():
        test_file.unlink()
    
    # Set up the todo manager
    set_global_todo_file(str(test_file))
    
    # Import the global manager
    from equitrcoder.tools.builtin.todo import todo_manager
    
    # Create test task groups with dependencies
    print("\n1. Creating task groups with dependencies...")
    
    # Group 1: No dependencies (can run first)
    group1 = todo_manager.create_task_group(
        group_id="setup",
        specialization="backend_dev",
        description="Set up project foundation",
        dependencies=[]
    )
    
    # Group 2: Depends on group1
    group2 = todo_manager.create_task_group(
        group_id="api_development",
        specialization="backend_dev", 
        description="Develop API endpoints",
        dependencies=["setup"]
    )
    
    # Group 3: Depends on group2
    group3 = todo_manager.create_task_group(
        group_id="frontend",
        specialization="frontend_dev",
        description="Build user interface",
        dependencies=["api_development"]
    )
    
    # Add todos to each group
    print("\n2. Adding todos to groups...")
    
    todo_manager.add_todo_to_group("setup", "Initialize project structure")
    todo_manager.add_todo_to_group("setup", "Set up database schema")
    
    todo_manager.add_todo_to_group("api_development", "Create user authentication API")
    todo_manager.add_todo_to_group("api_development", "Implement CRUD operations")
    
    todo_manager.add_todo_to_group("frontend", "Create login page")
    todo_manager.add_todo_to_group("frontend", "Build dashboard")
    
    # Test dependency resolution
    print("\n3. Testing dependency resolution...")
    
    # Initially, only setup should be runnable
    runnable = todo_manager.get_next_runnable_groups()
    print(f"Phase 1 runnable groups: {[g.group_id for g in runnable]}")
    assert len(runnable) == 1 and runnable[0].group_id == "setup"
    
    # Complete setup group by marking all its todos as completed
    print("\n4. Completing setup group...")
    setup_group = todo_manager.get_task_group("setup")
    for todo in setup_group.todos:
        todo_manager.update_todo_status(todo.id, "completed")
    
    # Now api_development should be runnable
    runnable = todo_manager.get_next_runnable_groups()
    print(f"Phase 2 runnable groups: {[g.group_id for g in runnable]}")
    assert len(runnable) == 1 and runnable[0].group_id == "api_development"
    
    # Complete api_development group
    print("\n5. Completing api_development group...")
    api_group = todo_manager.get_task_group("api_development")
    for todo in api_group.todos:
        todo_manager.update_todo_status(todo.id, "completed")
    
    # Now frontend should be runnable
    runnable = todo_manager.get_next_runnable_groups()
    print(f"Phase 3 runnable groups: {[g.group_id for g in runnable]}")
    assert len(runnable) == 1 and runnable[0].group_id == "frontend"
    
    # Complete frontend group
    print("\n6. Completing frontend group...")
    frontend_group = todo_manager.get_task_group("frontend")
    for todo in frontend_group.todos:
        todo_manager.update_todo_status(todo.id, "completed")
    
    # Now no groups should be runnable and all should be complete
    runnable = todo_manager.get_next_runnable_groups()
    print(f"Final runnable groups: {[g.group_id for g in runnable]}")
    assert len(runnable) == 0
    
    all_complete = todo_manager.are_all_tasks_complete()
    print(f"All tasks complete: {all_complete}")
    assert all_complete
    
    # Test the JSON structure
    print("\n7. Verifying JSON structure...")
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    print(f"Task groups in JSON: {len(data['task_groups'])}")
    print(f"JSON structure keys: {list(data.keys())}")
    
    # Clean up
    test_file.unlink()
    
    print("\n✅ All tests passed! The new dependency-aware Task Group System is working correctly.")
    print("\n🎉 Key improvements implemented:")
    print("   • Hierarchical task groups with dependencies")
    print("   • Phased execution based on dependency resolution")
    print("   • JSON-based structured planning")
    print("   • Automatic group completion detection")
    print("   • Profile-based agent specialization")

if __name__ == "__main__":
    asyncio.run(test_new_todo_system())