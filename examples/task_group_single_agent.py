#!/usr/bin/env python3
"""
Example: Single-Agent Mode with Task Groups and Automatic Git Checkpoints

This example demonstrates how the new Task Group System works with a single agent
that executes task groups sequentially based on dependencies, with automatic
git commits after each successful group completion.
"""

import asyncio
from equitrcoder.modes.single_agent_mode import run_single_agent_mode

async def basic_task_group_example():
    """
    Basic example showing task group execution with automatic git commits.
    """
    print("🚀 Starting Single-Agent Task Group Example")
    print("=" * 50)
    
    result = await run_single_agent_mode(
        task_description="Create a Python web application with Flask, user authentication, and a simple dashboard",
        agent_model="moonshot/kimi-k2-0711-preview",
        orchestrator_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        auto_commit=True,  # Enable automatic git commits
        max_cost=5.0,
        max_iterations=30
    )
    
    if result["success"]:
        print("\n✅ Task completed successfully!")
        print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
        print(f"🔄 Iterations: {result.get('iterations', 0)}")
        print("\n📋 Task Group Execution Flow:")
        print("1. Planning Phase: AI created structured JSON plan with dependencies")
        print("2. Sequential Execution: Groups executed based on dependencies")
        print("3. Automatic Commits: Git commit after each successful group")
        print("\n🔍 Check your git log to see the step-by-step progress:")
        print("   git log --oneline")
        print("\nExpected commit pattern:")
        print("   feat(testing): Complete task group 'test_suite'")
        print("   feat(frontend): Complete task group 'dashboard_ui'")
        print("   feat(backend): Complete task group 'authentication_system'")
        print("   feat(database): Complete task group 'database_setup'")
    else:
        print(f"\n❌ Task failed: {result.get('error')}")
        print(f"Failed at stage: {result.get('stage', 'unknown')}")

async def complex_dependency_example():
    """
    Example showing complex dependencies with multiple specializations.
    """
    print("\n🏗️ Starting Complex Dependency Example")
    print("=" * 50)
    
    result = await run_single_agent_mode(
        task_description="""
        Create a complete e-commerce system with:
        - SQLite database with product and user tables
        - Flask REST API with authentication and CRUD operations
        - HTML/CSS/JavaScript frontend with shopping cart
        - Unit tests for all components
        - API documentation
        """,
        agent_model="moonshot/kimi-k2-0711-preview",
        orchestrator_model="moonshot/kimi-k2-0711-preview", 
        audit_model="o3",
        auto_commit=True,
        max_cost=10.0,
        max_iterations=50
    )
    
    if result["success"]:
        print("\n✅ Complex e-commerce system completed!")
        print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
        print("\n📋 Expected Task Group Flow:")
        print("1. database_setup (database) - No dependencies")
        print("2. backend_api (backend) - Depends on database_setup")
        print("3. authentication_system (backend) - Depends on backend_api")
        print("4. frontend_ui (frontend) - Depends on authentication_system")
        print("5. shopping_cart (frontend) - Depends on frontend_ui")
        print("6. testing_suite (testing) - Depends on all above")
        print("7. documentation (documentation) - Depends on testing_suite")
        print("\n🤖 Each group completion triggered an automatic git commit!")
    else:
        print(f"\n❌ Complex task failed: {result.get('error')}")

async def monitoring_example():
    """
    Example showing how to monitor task group progress in real-time.
    """
    print("\n📊 Starting Monitoring Example")
    print("=" * 50)
    
    def on_task_group_start(group_info):
        print(f"🚀 Starting task group: {group_info.get('group_id')} ({group_info.get('specialization')})")
        print(f"   Dependencies: {group_info.get('dependencies', [])}")
    
    def on_task_group_complete(group_info):
        print(f"✅ Completed task group: {group_info.get('group_id')}")
        print(f"📝 Automatic git commit created")
    
    def on_iteration(iteration, status):
        print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")
    
    result = await run_single_agent_mode(
        task_description="Create a simple blog system with posts, comments, and user management",
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,
        callbacks={
            'on_task_group_start': on_task_group_start,
            'on_task_group_complete': on_task_group_complete,
            'on_iteration': on_iteration
        },
        max_cost=7.0
    )
    
    if result["success"]:
        print(f"\n✅ Blog system completed with monitoring!")
        print(f"💰 Final cost: ${result.get('cost', 0):.4f}")
    else:
        print(f"\n❌ Monitored task failed: {result.get('error')}")

async def main():
    """
    Run all task group examples.
    """
    print("🎯 EQUITR Coder v2.0.0 - Task Group System Examples")
    print("=" * 60)
    print("This demonstrates the revolutionary Task Group System with")
    print("dependency-aware execution and automatic git checkpoints.")
    print("=" * 60)
    
    try:
        # Run basic example
        await basic_task_group_example()
        
        # Wait a moment between examples
        await asyncio.sleep(2)
        
        # Run complex example
        await complex_dependency_example()
        
        # Wait a moment between examples
        await asyncio.sleep(2)
        
        # Run monitoring example
        await monitoring_example()
        
        print("\n🎉 All examples completed!")
        print("\n📚 Key Takeaways:")
        print("• Task groups are automatically created based on project complexity")
        print("• Dependencies ensure logical execution order")
        print("• Automatic git commits create professional development history")
        print("• Each specialization (backend, frontend, database, etc.) is handled appropriately")
        print("• Session-local tracking prevents todo compounding")
        
        print("\n🔍 Next Steps:")
        print("• Check 'git log --oneline' to see the automatic commit history")
        print("• Examine the .EQUITR_todos_*.json files to see the structured plans")
        print("• Try the multi-agent examples for parallel phase execution")
        
    except Exception as e:
        print(f"\n💥 Example failed with error: {e}")
        print("Make sure you have:")
        print("• API keys set in .env file")
        print("• EQUITR Coder v2.0.0 installed")
        print("• Git initialized in your project directory")

if __name__ == "__main__":
    asyncio.run(main())