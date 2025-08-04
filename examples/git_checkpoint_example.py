#!/usr/bin/env python3
"""
Example: Automatic Git Checkpoints Feature

This example demonstrates the automatic git checkpoint feature that creates
professional commit history after each task group or phase completion.
"""

import asyncio
import subprocess
from pathlib import Path
from equitrcoder.modes.single_agent_mode import run_single_agent_mode
from equitrcoder.modes.multi_agent_mode import run_multi_agent_parallel
from equitrcoder.utils.git_manager import GitManager

def show_git_log(title="Git Log"):
    """Helper function to display git log."""
    try:
        result = subprocess.run(
            ['git', 'log', '--oneline', '-10'], 
            capture_output=True, 
            text=True,
            check=True
        )
        print(f"\n📝 {title}:")
        print("-" * 40)
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("  No commits found")
        print("-" * 40)
    except subprocess.CalledProcessError:
        print(f"\n📝 {title}: Git not available or no commits")

async def basic_git_checkpoint_example():
    """
    Basic example showing automatic git commits after task group completion.
    """
    print("🚀 Starting Basic Git Checkpoint Example")
    print("=" * 50)
    
    # Show initial git state
    show_git_log("Initial Git State")
    
    result = await run_single_agent_mode(
        task_description="Create a simple Python calculator with basic operations (add, subtract, multiply, divide)",
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,  # Enable automatic git commits
        max_cost=3.0
    )
    
    if result["success"]:
        print("\n✅ Calculator creation completed!")
        print(f"💰 Cost: ${result.get('cost', 0):.4f}")
        
        # Show git log after completion
        show_git_log("Git Log After Task Completion")
        
        print("\n🎯 Expected Commit Pattern:")
        print("• feat(testing): Complete task group 'test_suite'")
        print("• feat(core): Complete task group 'calculator_logic'")
        print("• feat(documentation): Complete task group 'documentation'")
        
        print("\n📋 Each commit represents:")
        print("• A logical unit of work (task group)")
        print("• Professional conventional commit format")
        print("• Automatic creation after successful completion")
        print("• Traceable development history")
    else:
        print(f"\n❌ Task failed: {result.get('error')}")

async def multi_agent_git_checkpoint_example():
    """
    Example showing git commits after parallel phase completion.
    """
    print("\n🚀 Starting Multi-Agent Git Checkpoint Example")
    print("=" * 55)
    
    # Show git state before multi-agent task
    show_git_log("Git State Before Multi-Agent Task")
    
    result = await run_multi_agent_parallel(
        task_description="""
        Create a web-based todo application with:
        - SQLite database for storing todos
        - Flask REST API with CRUD operations
        - HTML/CSS/JavaScript frontend
        - Basic user authentication
        - Unit tests for API endpoints
        """,
        num_agents=3,
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,  # Enable phase-based git commits
        max_cost_per_agent=2.5
    )
    
    if result["success"]:
        print("\n✅ Todo application completed!")
        print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
        print(f"📊 Phases executed: {result.get('total_phases', 0)}")
        
        # Show git log after multi-agent completion
        show_git_log("Git Log After Multi-Agent Task")
        
        print("\n🎯 Expected Phase Commit Pattern:")
        print("• chore(orchestration): Complete Phase 3")
        print("  └── Completed: [frontend_ui, testing_suite, documentation]")
        print("• chore(orchestration): Complete Phase 2")
        print("  └── Completed: [authentication_system]")
        print("• chore(orchestration): Complete Phase 1")
        print("  └── Completed: [database_setup, backend_api]")
        
        print("\n📋 Phase commits show:")
        print("• Which task groups completed in parallel")
        print("• Professional orchestration history")
        print("• Easy recovery points for complex projects")
    else:
        print(f"\n❌ Multi-agent task failed: {result.get('error')}")

async def git_manager_direct_example():
    """
    Example showing direct GitManager usage for custom commits.
    """
    print("\n🛠️ Starting Direct GitManager Example")
    print("=" * 45)
    
    # Create GitManager instance
    git_manager = GitManager(repo_path=".")
    
    # Ensure repo is ready
    git_manager.ensure_repo_is_ready()
    
    # Example task group data (simulated)
    example_task_group = {
        "group_id": "example_feature",
        "specialization": "backend",
        "description": "Implement example feature with database integration",
        "status": "completed"
    }
    
    # Create a test file to commit
    test_file = Path("example_feature.py")
    test_file.write_text("""
# Example feature implementation
def example_function():
    '''Example function for demonstration.'''
    return "Hello from example feature!"

if __name__ == "__main__":
    print(example_function())
""".strip())
    
    print("📝 Created example file: example_feature.py")
    
    # Use GitManager to commit the task group completion
    success = git_manager.commit_task_group_completion(example_task_group)
    
    if success:
        print("✅ Task group commit created successfully!")
        
        # Show the commit
        show_git_log("Git Log After Direct GitManager Usage")
        
        print("\n🎯 Direct GitManager Benefits:")
        print("• Custom task group commits")
        print("• Conventional commit format")
        print("• Automatic file staging")
        print("• Professional commit messages")
    else:
        print("❌ Failed to create task group commit")
    
    # Clean up test file
    if test_file.exists():
        test_file.unlink()
        print("🧹 Cleaned up test file")

async def git_recovery_example():
    """
    Example showing how to use git checkpoints for recovery.
    """
    print("\n🔄 Starting Git Recovery Example")
    print("=" * 40)
    
    print("This example demonstrates how automatic git checkpoints")
    print("enable easy recovery from failed or incomplete tasks.")
    
    # Show current git state
    show_git_log("Current Git State")
    
    # Simulate a task that might fail partway through
    print("\n🎯 Scenario: Complex task that might fail partway")
    print("• Task groups: database_setup → backend_api → frontend_ui → testing")
    print("• If frontend_ui fails, we can recover from backend_api checkpoint")
    
    result = await run_single_agent_mode(
        task_description="Create a complex web application (this might fail to demonstrate recovery)",
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,
        max_cost=1.0,  # Low cost limit to potentially trigger failure
        max_iterations=5  # Low iteration limit
    )
    
    # Show git state regardless of success/failure
    show_git_log("Git State After Task Attempt")
    
    if result["success"]:
        print("\n✅ Task completed successfully!")
        print("🎯 All task groups completed with automatic checkpoints")
    else:
        print(f"\n⚠️ Task failed: {result.get('error')}")
        print("🎯 Recovery Options:")
        print("• Check git log to see which task groups completed")
        print("• Use 'git reset --hard <commit>' to return to last successful checkpoint")
        print("• Restart from the failed task group with higher limits")
        print("• Each commit represents a safe recovery point")
    
    print("\n📚 Recovery Commands:")
    print("• git log --oneline                    # See all checkpoints")
    print("• git show <commit-hash>               # See what was done in a checkpoint")
    print("• git reset --hard <commit-hash>       # Revert to a checkpoint")
    print("• git diff <commit1> <commit2>         # Compare checkpoints")

async def main():
    """
    Run all git checkpoint examples.
    """
    print("🎯 EQUITR Coder v2.0.0 - Automatic Git Checkpoints Examples")
    print("=" * 70)
    print("This demonstrates the automatic git checkpoint feature that creates")
    print("professional commit history for traceable AI-assisted development.")
    print("=" * 70)
    
    try:
        # Initialize git if needed
        git_manager = GitManager(".")
        git_manager.ensure_repo_is_ready()
        
        # Run basic example
        await basic_git_checkpoint_example()
        
        # Wait between examples
        await asyncio.sleep(2)
        
        # Run multi-agent example
        await multi_agent_git_checkpoint_example()
        
        # Wait between examples
        await asyncio.sleep(2)
        
        # Run direct GitManager example
        await git_manager_direct_example()
        
        # Wait between examples
        await asyncio.sleep(2)
        
        # Run recovery example
        await git_recovery_example()
        
        print("\n🎉 All git checkpoint examples completed!")
        
        print("\n📚 Key Git Checkpoint Benefits:")
        print("• ✅ Automatic commits after each logical completion")
        print("• 📝 Professional conventional commit messages")
        print("• 🔄 Easy recovery from any successful checkpoint")
        print("• 👥 Team-ready git history for code reviews")
        print("• 📊 Traceable development progress")
        print("• 🎯 No manual git management required")
        
        print("\n🛠️ Advanced Git Features:")
        print("• Automatic repository initialization")
        print("• Smart .gitignore creation")
        print("• Conventional commit format (feat, chore, etc.)")
        print("• Specialization-based commit categorization")
        print("• Phase-based commits for multi-agent tasks")
        
        print("\n🔍 Explore Your Git History:")
        print("• git log --oneline --graph           # Visual commit history")
        print("• git log --grep='feat('             # Find feature commits")
        print("• git log --grep='chore(orchestration)' # Find phase commits")
        print("• gitk or git log --all --graph      # GUI visualization")
        
    except Exception as e:
        print(f"\n💥 Git checkpoint examples failed with error: {e}")
        print("Make sure you have:")
        print("• Git installed and available in PATH")
        print("• Write permissions in the current directory")
        print("• EQUITR Coder v2.0.0 installed")
        print("• API keys configured in .env file")

if __name__ == "__main__":
    asyncio.run(main())