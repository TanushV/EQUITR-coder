#!/usr/bin/env python3
"""
Example demonstrating the enhanced audit system with required reasoning.

This shows how the audit system now requires explicit reasons for both
pass and fail decisions, focusing specifically on whether completed todos
were actually implemented properly.
"""

import asyncio
from equitrcoder.tools.builtin.audit import audit_manager
from equitrcoder.tools.builtin.todo import todo_manager


async def demonstrate_audit_reasoning():
    """Demonstrate the audit system with reasoning requirements."""
    
    print("🔍 AUDIT SYSTEM WITH REASONING DEMONSTRATION")
    print("=" * 60)
    
    # Clear existing todos for clean demo
    existing_todos = todo_manager.list_todos()
    for todo in existing_todos:
        todo_manager.delete_todo(todo.id)
    
    # Create some sample todos to simulate a completed task
    print("\n📋 Creating sample todos...")
    
    todo1 = todo_manager.create_todo(
        title="Create authentication system",
        description="Implement user login and registration",
        priority="high",
        tags=["backend", "security"]
    )
    
    todo2 = todo_manager.create_todo(
        title="Setup database schema",
        description="Create users table and migrations",
        priority="medium",
        tags=["database"]
    )
    
    todo3 = todo_manager.create_todo(
        title="Add API endpoints",
        description="Create REST endpoints for user management",
        priority="medium",
        tags=["api"]
    )
    
    print(f"✅ Created todos: {todo1.id}, {todo2.id}, {todo3.id}")
    
    # Mark some todos as completed to simulate work being done
    print("\n🔄 Marking todos as completed...")
    todo_manager.update_todo(todo1.id, status="completed")
    todo_manager.update_todo(todo2.id, status="completed")
    # Leave todo3 as pending
    
    print("✅ Marked 2 todos as completed, 1 still pending")
    
    # Show the audit context that would be generated
    print("\n🔍 AUDIT CONTEXT GENERATION")
    print("-" * 40)
    
    audit_context = audit_manager.get_audit_context()
    if audit_context:
        print("Generated audit context:")
        print(audit_context[:500] + "..." if len(audit_context) > 500 else audit_context)
    
    # Demonstrate different audit scenarios
    print("\n📊 AUDIT SCENARIOS WITH REASONING")
    print("-" * 40)
    
    # Scenario 1: Audit passes with proper reasoning
    print("\n✅ SCENARIO 1: Audit passes")
    audit_passed_reason = """All completed todos have corresponding implementations:
- 'Create authentication system' → auth.py file exists with login/register functions
- 'Setup database schema' → migrations/001_users.sql exists with proper schema
Both implementations match requirements and design specifications."""
    
    result1 = audit_manager.record_audit_result(
        passed=True,
        audit_result="AUDIT PASSED - All implementations verified",
        reason=audit_passed_reason
    )
    print(f"Should continue audit cycle: {result1}")
    
    # Reset for next scenario
    audit_manager.audit_failure_count = 0
    
    # Scenario 2: Audit fails with specific reasoning
    print("\n❌ SCENARIO 2: Audit fails")
    audit_failed_reason = """Todo 'Create authentication system' marked complete but auth.py file missing.
Todo 'Setup database schema' complete but no database migrations found."""
    
    audit_failed_result = """AUDIT FAILED - Missing implementations for completed todos
REASON FOR FAILING: Todo 'Create authentication system' marked complete but auth.py file missing
SPECIFIC ISSUES FOUND:
1. auth.py file does not exist despite todo being marked complete
2. No database migration files found in migrations/ directory
3. API endpoints not implemented despite being marked as done"""
    
    result2 = audit_manager.record_audit_result(
        passed=False,
        audit_result=audit_failed_result,
        reason=audit_failed_reason
    )
    print(f"Should continue audit cycle: {result2}")
    
    # Show the todos created from audit failure
    print("\n📋 Todos created from audit failure:")
    audit_todos = [t for t in todo_manager.list_todos() if 'audit-fix' in t.tags]
    for todo in audit_todos:
        print(f"  - {todo.title}")
        print(f"    Priority: {todo.priority}")
        print(f"    Description: {todo.description[:100]}...")
    
    # Scenario 3: Multiple failures leading to escalation
    print("\n🚨 SCENARIO 3: Multiple failures → Escalation")
    
    # Second failure
    result3 = audit_manager.record_audit_result(
        passed=False,
        audit_result="AUDIT FAILED - Still missing auth.py file",
        reason="Authentication system still not implemented despite previous audit failure"
    )
    print(f"After 2nd failure, should continue: {result3}")
    
    # Show escalation todo
    escalation_todos = [t for t in todo_manager.list_todos() if 'urgent' in t.tags and 'manual-review' in t.tags]
    if escalation_todos:
        print("\n🚨 ESCALATION TODO CREATED:")
        escalation_todo = escalation_todos[0]
        print(f"  Title: {escalation_todo.title}")
        print(f"  Priority: {escalation_todo.priority}")
        print(f"  Assignee: {escalation_todo.assignee}")
        print(f"  Description: {escalation_todo.description[:200]}...")
    
    # Show the enhanced audit context format
    print("\n📋 ENHANCED AUDIT CONTEXT FORMAT")
    print("-" * 40)
    print("""
The audit context now includes:

🎯 REQUIRED RESPONSE FORMAT:
You MUST provide a clear reason for your audit decision in both cases:

- If audit passes: Respond EXACTLY with 'AUDIT PASSED' followed by:
  * REASON FOR PASSING: Explain specifically why all completed todos were properly implemented
  * Example: "AUDIT PASSED - All 5 completed todos have corresponding implementations: 
    authentication system files exist and function correctly, database schema matches design, 
    API endpoints are implemented as specified."

- If audit fails: Respond EXACTLY with 'AUDIT FAILED' followed by:
  * REASON FOR FAILING: Explain specifically which completed todos were not properly implemented
  * SPECIFIC ISSUES FOUND: List each concrete problem
  * Example: "AUDIT FAILED - Todo 'Create login endpoint' marked complete but no login.py file exists, 
    Todo 'Setup database' complete but no database schema found."

CRITICAL: Your reasoning must focus ONLY on whether completed todos were actually implemented, 
not on future work or pending todos.
    """)
    
    print("\n✅ AUDIT REASONING DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demonstrate_audit_reasoning())