#!/usr/bin/env python3
"""
Comprehensive example of using EQUITR Coder programmatically.

This example demonstrates:
- Single and multi-agent task execution
- Configuration management
- Callback usage
- Error handling
- Git integration
- Session management
"""

import asyncio
import os
from pathlib import Path

from equitrcoder import (
    EquitrCoder,
    MultiAgentTaskConfiguration,
    TaskConfiguration,
    WorkerConfiguration,
    create_multi_agent_coder,
    create_single_agent_coder,
)


async def single_agent_example():
    """Example of single agent usage."""
    print("🔹 Single Agent Example")
    print("=" * 50)

    # Create single agent coder
    coder = create_single_agent_coder(repo_path=".", git_enabled=True)

    # Configure task
    config = TaskConfiguration(
        description="Simple file analysis",
        max_cost=1.0,
        max_iterations=10,
        auto_commit=True,
        commit_message="Add analysis from single agent",
    )

    try:
        # Execute task
        result = await coder.execute_task(
            "Analyze the project structure and create a summary in README_ANALYSIS.md",
            config=config,
        )

        if result.success:
            print(f"✅ Task completed successfully!")
            print(f"   Cost: ${result.cost:.4f}")
            print(f"   Time: {result.execution_time:.2f}s")
            print(f"   Iterations: {result.iterations}")
            if result.git_committed:
                print(f"   Committed: {result.commit_hash}")
        else:
            print(f"❌ Task failed: {result.error}")

    finally:
        await coder.cleanup()


async def multi_agent_example():
    """Example of multi-agent usage."""
    print("\n🔹 Multi-Agent Example")
    print("=" * 50)

    # Create multi-agent coder
    coder = create_multi_agent_coder(
        repo_path=".",
        max_workers=3,
        supervisor_model="gpt-4",
        worker_model="gpt-3.5-turbo",
        git_enabled=True,
    )

    # Configure task
    config = MultiAgentTaskConfiguration(
        description="Complex development task",
        max_workers=3,
        max_cost=5.0,
        auto_commit=True,
        commit_message="Multi-agent development work",
    )

    try:
        # Execute complex task
        result = await coder.execute_task(
            "Create a comprehensive test suite for the entire project, including unit tests, integration tests, and documentation tests",
            config=config,
        )

        if result.success:
            print(f"✅ Multi-agent task completed!")
            print(f"   Cost: ${result.cost:.4f}")
            print(f"   Time: {result.execution_time:.2f}s")
            print(f"   Workers used: {result.iterations}")
            if result.git_committed:
                print(f"   Committed: {result.commit_hash}")
        else:
            print(f"❌ Multi-agent task failed: {result.error}")

    finally:
        await coder.cleanup()


async def callback_example():
    """Example with callbacks for monitoring."""
    print("\n🔹 Callback Monitoring Example")
    print("=" * 50)

    def on_task_start(description, mode):
        print(f"🚀 Starting {mode} task: {description[:50]}...")

    def on_task_complete(result):
        if result.success:
            print(f"✅ Task completed in {result.execution_time:.2f}s")
        else:
            print(f"❌ Task failed: {result.error}")

    def on_tool_call(tool_data):
        tool_name = tool_data.get("tool_name", "unknown")
        success = tool_data.get("success", True)
        status = "✓" if success else "✗"
        print(f"🔧 {status} Tool: {tool_name}")

    def on_message(message_data):
        role = message_data["role"].upper()
        content = (
            message_data["content"][:100] + "..."
            if len(message_data["content"]) > 100
            else message_data["content"]
        )
        print(f"💬 [{role}]: {content}")

    # Create coder with callbacks
    coder = EquitrCoder(mode="single")
    coder.on_task_start = on_task_start
    coder.on_task_complete = on_task_complete
    coder.on_tool_call = on_tool_call
    coder.on_message = on_message

    try:
        config = TaskConfiguration(
            description="Monitored task", max_cost=0.5, max_iterations=5
        )

        result = await coder.execute_task(
            "Add type hints to any Python files that are missing them", config=config
        )

        print(f"Final result: {'Success' if result.success else 'Failed'}")

    finally:
        await coder.cleanup()


async def session_management_example():
    """Example of session management."""
    print("\n🔹 Session Management Example")
    print("=" * 50)

    coder = EquitrCoder()

    try:
        # Use a specific session
        session_id = "development_session"

        config = TaskConfiguration(
            description="Session-based task", session_id=session_id, max_cost=1.0
        )

        # Execute first task
        result1 = await coder.execute_task(
            "Create a simple utility function for string manipulation", config=config
        )

        # Execute second task in same session
        result2 = await coder.execute_task(
            "Add unit tests for the utility function you just created", config=config
        )

        # Check session history
        session = coder.get_session_history(session_id)
        if session:
            print(f"📊 Session '{session_id}':")
            print(f"   Total cost: ${session.cost:.4f}")
            print(f"   Messages: {len(session.messages)}")

        # List all sessions
        sessions = coder.list_sessions()
        print(f"📝 Total sessions: {len(sessions)}")
        for session_info in sessions[:3]:  # Show first 3
            print(f"   - {session_info['session_id']}: ${session_info['cost']:.4f}")

    finally:
        await coder.cleanup()


async def git_integration_example():
    """Example of git integration."""
    print("\n🔹 Git Integration Example")
    print("=" * 50)

    coder = EquitrCoder(git_enabled=True)

    try:
        # Check git status
        status = coder.get_git_status()
        print(f"📁 Git Status:")
        if "error" in status:
            print(f"   Error: {status['error'][0]}")
        else:
            print(f"   Modified: {len(status.get('modified', []))}")
            print(f"   Untracked: {len(status.get('untracked', []))}")

        # Get recent commits
        commits = coder.get_recent_commits(3)
        print(f"📜 Recent commits:")
        for commit in commits:
            print(f"   {commit['hash']}: {commit['message'][:50]}...")

        # Execute task with custom commit message
        config = TaskConfiguration(
            description="Git example task",
            max_cost=0.5,
            auto_commit=True,
            commit_message="Add documentation improvements from AI assistant",
        )

        result = await coder.execute_task(
            "Improve the README.md file with better formatting and examples",
            config=config,
        )

        if result.git_committed:
            print(f"✅ Changes committed: {result.commit_hash}")

    finally:
        await coder.cleanup()


async def error_handling_example():
    """Example of robust error handling."""
    print("\n🔹 Error Handling Example")
    print("=" * 50)

    async def safe_execute_task(task_description, max_retries=3):
        """Execute task with retry logic."""
        for attempt in range(max_retries):
            coder = EquitrCoder()
            try:
                config = TaskConfiguration(
                    description=task_description,
                    max_cost=0.5 * (attempt + 1),  # Increase cost limit on retry
                    max_iterations=5 * (attempt + 1),  # Increase iterations on retry
                )

                result = await coder.execute_task(task_description, config)

                if result.success:
                    print(f"✅ Task succeeded on attempt {attempt + 1}")
                    return result
                else:
                    print(f"⚠️ Attempt {attempt + 1} failed: {result.error}")
                    if attempt < max_retries - 1:
                        print(f"   Retrying with higher limits...")
                        await asyncio.sleep(1)  # Brief delay before retry

            except Exception as e:
                print(f"❌ Attempt {attempt + 1} error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

            finally:
                await coder.cleanup()

        print(f"❌ All {max_retries} attempts failed")
        return None

    # Try a challenging task
    result = await safe_execute_task(
        "Create a complex machine learning pipeline with data preprocessing, model training, and evaluation"
    )

    if result:
        print(f"Final success: ${result.cost:.4f} cost")
    else:
        print("Task ultimately failed after all retries")


async def main():
    """Run all examples."""
    print("🎯 EQUITR Coder Programmatic Interface Examples")
    print("=" * 60)

    # Set up environment (optional)
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️ Warning: No API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("   Examples will run but may fail without proper API access.")
        print()

    try:
        await single_agent_example()
        await multi_agent_example()
        await callback_example()
        await session_management_example()
        await git_integration_example()
        await error_handling_example()

        print("\n🎉 All examples completed!")

    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
