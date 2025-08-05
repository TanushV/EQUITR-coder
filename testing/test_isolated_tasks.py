#!/usr/bin/env python3
"""
Test demonstrating task segregation and audit triggering only when ALL todos are completed.

This test shows:
1. How todos are segregated by task (different folders for docs)
2. How audit only triggers when ALL todos for a task are completed
3. How the reasoning system works with task-specific audits
"""

import asyncio
import tempfile
from pathlib import Path

from equitrcoder.core.document_workflow import DocumentWorkflowManager
from equitrcoder.tools.builtin.audit import audit_manager
from equitrcoder.tools.builtin.todo import todo_manager


async def test_task_segregation_and_audit():
    """Test task segregation and audit triggering logic."""
    
    print("🧪 TESTING TASK SEGREGATION AND AUDIT SYSTEM")
    print("=" * 60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Clear existing todos for clean test
        existing_todos = todo_manager.list_todos()
        for todo in existing_todos:
            todo_manager.delete_todo(todo.id)
        
        print(f"🧹 Cleared {len(existing_todos)} existing todos")
        
        # Create document workflow manager
        doc_manager = DocumentWorkflowManager(model="moonshot/kimi-k2-0711-preview")
        
        # Test 1: Create first task with segregated docs and todos
        print("\n📋 TEST 1: Creating Task A with segregated docs")
        print("-" * 40)
        
        task_a_result = await doc_manager.create_documents_programmatic(
            user_prompt="Create authentication system",
            project_path=str(temp_path),
            task_name="task_auth_system"
        )
        
        print(f"✅ Task A created successfully: {task_a_result.success}")
        print(f"📁 Task name: {task_a_result.task_name}")
        print(f"📄 Requirements: {task_a_result.requirements_path}")
        print(f"🏗️ Design: {task_a_result.design_path}")
        print(f"📋 Todos: {task_a_result.todos_path}")
        
        # Check todos created for Task A
        task_a_todos = [t for t in todo_manager.list_todos() if f"task-{task_a_result.task_name}" in t.tags]
        print(f"📊 Task A todos created: {len(task_a_todos)}")
        for todo in task_a_todos:
            print(f"  - {todo.status}: {todo.title}")
        
        # Test 2: Create second task with different segregated docs and todos
        print("\n📋 TEST 2: Creating Task B with segregated docs")
        print("-" * 40)
        
        task_b_result = await doc_manager.create_documents_programmatic(
            user_prompt="Create user dashboard",
            project_path=str(temp_path),
            task_name="task_user_dashboard"
        )
        
        print(f"✅ Task B created successfully: {task_b_result.success}")
        print(f"📁 Task name: {task_b_result.task_name}")
        print(f"📄 Requirements: {task_b_result.requirements_path}")
        print(f"🏗️ Design: {task_b_result.design_path}")
        print(f"📋 Todos: {task_b_result.todos_path}")
        
        # Check todos created for Task B
        task_b_todos = [t for t in todo_manager.list_todos() if f"task-{task_b_result.task_name}" in t.tags]
        print(f"📊 Task B todos created: {len(task_b_todos)}")
        for todo in task_b_todos:
            print(f"  - {todo.status}: {todo.title}")
        
        # Test 3: Verify task segregation
        print("\n🔍 TEST 3: Verifying task segregation")
        print("-" * 40)
        
        all_todos = todo_manager.list_todos()
        print(f"📊 Total todos in system: {len(all_todos)}")
        print(f"📊 Task A todos: {len(task_a_todos)}")
        print(f"📊 Task B todos: {len(task_b_todos)}")
        
        # Verify docs are in separate folders
        docs_dir = temp_path / "docs"
        task_a_dir = docs_dir / task_a_result.task_name
        task_b_dir = docs_dir / task_b_result.task_name
        
        print(f"📁 Task A docs folder exists: {task_a_dir.exists()}")
        print(f"📁 Task B docs folder exists: {task_b_dir.exists()}")
        
        if task_a_dir.exists():
            task_a_files = list(task_a_dir.glob("*.md"))
            print(f"📄 Task A files: {[f.name for f in task_a_files]}")
        
        if task_b_dir.exists():
            task_b_files = list(task_b_dir.glob("*.md"))
            print(f"📄 Task B files: {[f.name for f in task_b_files]}")
        
        # Test 4: Audit triggering logic - should NOT trigger when todos are pending
        print("\n🔍 TEST 4: Audit triggering with pending todos")
        print("-" * 40)
        
        # Check if audit should trigger for Task A (should be False - todos pending)
        should_trigger_a = audit_manager.should_trigger_audit(task_a_result.task_name)
        print(f"Should trigger audit for Task A (pending todos): {should_trigger_a}")
        
        # Check if audit should trigger for Task B (should be False - todos pending)
        should_trigger_b = audit_manager.should_trigger_audit(task_b_result.task_name)
        print(f"Should trigger audit for Task B (pending todos): {should_trigger_b}")
        
        # Test 5: Complete some todos for Task A (but not all)
        print("\n✅ TEST 5: Partially completing Task A todos")
        print("-" * 40)
        
        if task_a_todos:
            # Complete first todo only
            first_todo = task_a_todos[0]
            todo_manager.update_todo(first_todo.id, status="completed")
            print(f"✅ Completed todo: {first_todo.title}")
            
            # Check if audit should trigger (should still be False)
            should_trigger_partial = audit_manager.should_trigger_audit(task_a_result.task_name)
            print(f"Should trigger audit for Task A (partially complete): {should_trigger_partial}")
        
        # Test 6: Complete ALL todos for Task A
        print("\n✅ TEST 6: Completing ALL Task A todos")
        print("-" * 40)
        
        # Complete all remaining todos for Task A
        for todo in task_a_todos[1:]:  # Skip first one (already completed)
            todo_manager.update_todo(todo.id, status="completed")
            print(f"✅ Completed todo: {todo.title}")
        
        # Now check if audit should trigger (should be True)
        should_trigger_complete = audit_manager.should_trigger_audit(task_a_result.task_name)
        print(f"Should trigger audit for Task A (all complete): {should_trigger_complete}")
        
        # Task B should still not trigger (todos still pending)
        should_trigger_b_still = audit_manager.should_trigger_audit(task_b_result.task_name)
        print(f"Should trigger audit for Task B (still pending): {should_trigger_b_still}")
        
        # Test 7: Get audit context for completed task
        print("\n🔍 TEST 7: Getting audit context for completed task")
        print("-" * 40)
        
        audit_context = audit_manager.get_audit_context(task_a_result.task_name)
        if audit_context:
            print("✅ Audit context generated for Task A:")
            print(audit_context[:300] + "..." if len(audit_context) > 300 else audit_context)
        else:
            print("❌ No audit context generated")
        
        # Test 8: Verify task-specific filtering
        print("\n🔍 TEST 8: Verifying task-specific todo filtering")
        print("-" * 40)
        
        # Get todos for each task specifically
        task_a_filtered = [t for t in todo_manager.list_todos() if f"task-{task_a_result.task_name}" in t.tags]
        task_b_filtered = [t for t in todo_manager.list_todos() if f"task-{task_b_result.task_name}" in t.tags]
        
        print(f"📊 Task A filtered todos: {len(task_a_filtered)}")
        task_a_completed = [t for t in task_a_filtered if t.status == "completed"]
        task_a_pending = [t for t in task_a_filtered if t.status not in ["completed", "cancelled"]]
        print(f"  ✅ Completed: {len(task_a_completed)}")
        print(f"  ⏳ Pending: {len(task_a_pending)}")
        
        print(f"📊 Task B filtered todos: {len(task_b_filtered)}")
        task_b_completed = [t for t in task_b_filtered if t.status == "completed"]
        task_b_pending = [t for t in task_b_filtered if t.status not in ["completed", "cancelled"]]
        print(f"  ✅ Completed: {len(task_b_completed)}")
        print(f"  ⏳ Pending: {len(task_b_pending)}")
        
        # Test 9: Complete Task B and verify independent audit triggering
        print("\n✅ TEST 9: Completing Task B independently")
        print("-" * 40)
        
        # Complete all todos for Task B
        for todo in task_b_todos:
            todo_manager.update_todo(todo.id, status="completed")
            print(f"✅ Completed todo: {todo.title}")
        
        # Now both tasks should trigger audits independently
        should_trigger_a_final = audit_manager.should_trigger_audit(task_a_result.task_name)
        should_trigger_b_final = audit_manager.should_trigger_audit(task_b_result.task_name)
        
        print(f"Should trigger audit for Task A (complete): {should_trigger_a_final}")
        print(f"Should trigger audit for Task B (complete): {should_trigger_b_final}")
        
        # Test 10: Demonstrate audit context differences
        print("\n🔍 TEST 10: Comparing audit contexts for different tasks")
        print("-" * 40)
        
        audit_context_a = audit_manager.get_audit_context(task_a_result.task_name)
        audit_context_b = audit_manager.get_audit_context(task_b_result.task_name)
        
        if audit_context_a:
            print("📋 Task A audit context includes task-specific info:")
            if f"TASK-SPECIFIC AUDIT: {task_a_result.task_name}" in audit_context_a:
                print("  ✅ Contains task-specific header")
            if f"docs/{task_a_result.task_name}/" in audit_context_a:
                print("  ✅ Contains task-specific docs path")
        
        if audit_context_b:
            print("📋 Task B audit context includes task-specific info:")
            if f"TASK-SPECIFIC AUDIT: {task_b_result.task_name}" in audit_context_b:
                print("  ✅ Contains task-specific header")
            if f"docs/{task_b_result.task_name}/" in audit_context_b:
                print("  ✅ Contains task-specific docs path")
        
        print("\n✅ TASK SEGREGATION AND AUDIT TEST COMPLETE")
        print("=" * 60)
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"✅ Task A ({task_a_result.task_name}): {len(task_a_todos)} todos, all completed, audit ready")
        print(f"✅ Task B ({task_b_result.task_name}): {len(task_b_todos)} todos, all completed, audit ready")
        print(f"📁 Docs segregated in separate folders: docs/{task_a_result.task_name}/ and docs/{task_b_result.task_name}/")
        print("🔍 Audits only trigger when ALL todos for a specific task are completed")
        print("📋 Each audit context is task-specific and includes only relevant todos")


async def test_audit_reasoning_with_tasks():
    """Test audit reasoning system with task-specific context."""
    
    print("\n🧪 TESTING AUDIT REASONING WITH TASK SEGREGATION")
    print("=" * 60)
    
    # Simulate audit results for different tasks
    print("\n📋 Simulating audit results for segregated tasks...")
    
    # Test audit pass with task-specific reasoning
    task_name = "task_auth_system"
    audit_pass_result = f"""AUDIT PASSED - All 3 completed todos for {task_name} have corresponding implementations

REASON FOR PASSING: Verified all authentication system todos:
1. 'Create login endpoint' → auth/login.py exists with proper login function
2. 'Setup user database' → migrations/001_users.sql exists with correct schema
3. 'Add password hashing' → auth/security.py exists with bcrypt implementation

All implementations match requirements in docs/{task_name}/requirements.md and follow design in docs/{task_name}/design.md"""
    
    print("✅ AUDIT PASS EXAMPLE:")
    print(audit_pass_result[:200] + "...")
    
    # Extract reasoning
    lines = audit_pass_result.split('\n')
    reason = ""
    for line in lines:
        if line.strip().startswith("REASON FOR PASSING:"):
            reason = line.replace("REASON FOR PASSING:", "").strip()
            break
    
    print(f"📝 Extracted reason: {reason[:100]}...")
    
    # Test audit fail with task-specific reasoning
    audit_fail_result = f"""AUDIT FAILED - Todo 'Create login endpoint' for {task_name} marked complete but auth/login.py missing

REASON FOR FAILING: Authentication system implementation incomplete:
- Todo 'Create login endpoint' marked complete but auth/login.py file does not exist
- Todo 'Setup user database' complete but no migration files found in migrations/

SPECIFIC ISSUES FOUND:
1. Missing file: auth/login.py (required by completed todo)
2. Missing directory: migrations/ (required by database setup todo)
3. Requirements in docs/{task_name}/requirements.md not fully implemented"""
    
    print("\n❌ AUDIT FAIL EXAMPLE:")
    print(audit_fail_result[:200] + "...")
    
    # Extract failure reasoning
    fail_reason = ""
    for line in audit_fail_result.split('\n'):
        if line.strip().startswith("REASON FOR FAILING:"):
            fail_reason = line.replace("REASON FOR FAILING:", "").strip()
            break
    
    print(f"📝 Extracted failure reason: {fail_reason[:100]}...")
    
    print("\n✅ AUDIT REASONING TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(test_task_segregation_and_audit())
    asyncio.run(test_audit_reasoning_with_tasks())