#!/usr/bin/env python3
"""Test the complete workflow end-to-end."""

import asyncio
import sys
import os

# Add parent directory to path so we can import equitrcoder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from equitrcoder.programmatic.interface import EquitrCoder, TaskConfiguration

async def test_complete_workflow():
    print('🧪 Testing complete workflow with document creation and task execution...')
    
    # Create single-agent coder
    coder = EquitrCoder(mode='single', repo_path='.')
    
    # Test task configuration
    config = TaskConfiguration(
        description='Create a simple hello world Python script',
        model='moonshot/kimi-k2-0711-preview',
        max_cost=0.10,
        max_iterations=5
    )
    
    # Execute task with mandatory document creation
    result = await coder.execute_task('Create a simple hello world Python script', config)
    
    print(f'Result: {result.success}')
    if result.error:
        print(f'Error: {result.error}')
    
    print(f'Cost: ${result.cost:.4f}')
    print(f'Iterations: {result.iterations}')
    
    # Check if todos were created and some completed
    from equitrcoder.tools.builtin.todo import TodoManager
    todo_manager = TodoManager()
    todos = todo_manager.list_todos()
    
    completed_todos = [t for t in todos if t.status == 'completed']
    pending_todos = [t for t in todos if t.status == 'pending']
    
    print(f'\\nTodos status:')
    print(f'  Total: {len(todos)}')
    print(f'  Completed: {len(completed_todos)}')
    print(f'  Pending: {len(pending_todos)}')
    
    if completed_todos:
        print('\\nCompleted todos:')
        for todo in completed_todos[:5]:  # Show first 5
            print(f'  ✅ {todo.title}')
    
    if pending_todos:
        print('\\nPending todos:')
        for todo in pending_todos[:5]:  # Show first 5
            print(f'  ⏳ {todo.title}')

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())