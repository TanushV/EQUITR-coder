#!/usr/bin/env python3
"""
Multi-Agent Coordination Examples

This file demonstrates advanced usage patterns for equitrcoder's multi-agent functionality.
These examples show how to create and coordinate multiple WorkerAgents for complex tasks
with security restrictions and parallel execution.
"""

import asyncio
import os


# Import the main equitrcoder components
from equitrcoder.orchestrators.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
    WorkerConfig,
)


async def basic_multi_agent_example():
    """
    Example 1: Basic multi-agent coordination

    This shows how to create multiple workers and coordinate them for parallel tasks.
    """
    print("=== Example 1: Basic Multi-Agent Coordination ===")

    # Create multi-agent orchestrator
    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=2, global_cost_limit=3.0
    )

    # Create worker configurations with different scopes
    frontend_config = WorkerConfig(
        worker_id="frontend_dev",
        scope_paths=["equitrcoder/ui/", "equitrcoder/examples/"],
        allowed_tools=["read_file", "edit_file", "search_files"],
        max_cost=1.5,
        max_iterations=10,
    )

    backend_config = WorkerConfig(
        worker_id="backend_dev",
        scope_paths=["equitrcoder/core/", "equitrcoder/api/"],
        allowed_tools=["read_file", "edit_file", "run_cmd"],
        max_cost=1.5,
        max_iterations=10,
    )

    # Register workers
    orchestrator.create_worker(frontend_config)
    orchestrator.create_worker(backend_config)

    print(f"Created workers: {[w.worker_id for w in orchestrator.workers.values()]}")

    # Define parallel tasks
    tasks = [
        {
            "task_id": "ui_analysis",
            "worker_id": "frontend_dev",
            "task_description": "Analyze the UI components and suggest improvements",
            "context": {"priority": "high", "focus": "usability"},
        },
        {
            "task_id": "core_analysis",
            "worker_id": "backend_dev",
            "task_description": "Review the core modules for optimization opportunities",
            "context": {"priority": "medium", "focus": "performance"},
        },
    ]

    # Execute tasks in parallel
    print("Executing parallel tasks...")
    results = await orchestrator.execute_parallel_tasks(tasks)

    # Display results
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.worker_id}: {result.task_id}")
        print(f"   Time: {result.execution_time:.2f}s")
        print(f"   Cost: ${result.cost:.4f}")
        if not result.success:
            print(f"   Error: {result.error}")

    # Get orchestrator statistics
    stats = orchestrator.get_statistics()
    print("\n📊 Orchestrator Statistics:")
    print(f"   Total cost: ${stats['total_cost']:.4f}")
    print(f"   Active workers: {stats['active_workers']}")
    print(f"   Completed tasks: {stats['completed_tasks']}")

    return results


async def security_isolation_example():
    """
    Example 2: Security and isolation demonstration

    This shows how workers are isolated from each other and restricted to their scopes.
    """
    print("\n=== Example 2: Security and Isolation ===")

    orchestrator = MultiAgentOrchestrator()

    # Create workers with different security constraints
    secure_worker_config = WorkerConfig(
        worker_id="secure_worker",
        scope_paths=["equitrcoder/config/"],  # Only config files
        allowed_tools=["read_file"],  # Read-only access
        max_cost=0.5,
        max_iterations=5,
    )

    general_worker_config = WorkerConfig(
        worker_id="general_worker",
        scope_paths=["equitrcoder/examples/", "equitrcoder/docs/"],
        allowed_tools=["read_file", "edit_file", "search_files"],
        max_cost=1.0,
        max_iterations=10,
    )

    # Create workers
    secure_worker = orchestrator.create_worker(secure_worker_config)
    general_worker = orchestrator.create_worker(general_worker_config)

    # Test security restrictions
    print("Security checks for secure_worker:")
    print(
        f"  Can access config/default.yaml: {secure_worker.can_access_file('equitrcoder/config/default.yaml')}"
    )
    print(
        f"  Can access core/orchestrator.py: {secure_worker.can_access_file('equitrcoder/core/orchestrator.py')}"
    )
    print(f"  Can use read_file: {secure_worker.can_use_tool('read_file')}")
    print(f"  Can use edit_file: {secure_worker.can_use_tool('edit_file')}")

    print("\nSecurity checks for general_worker:")
    print(
        f"  Can access examples/README.md: {general_worker.can_access_file('equitrcoder/examples/README.md')}"
    )
    print(
        f"  Can access config/default.yaml: {general_worker.can_access_file('equitrcoder/config/default.yaml')}"
    )
    print(f"  Can use read_file: {general_worker.can_use_tool('read_file')}")
    print(f"  Can use edit_file: {general_worker.can_use_tool('edit_file')}")

    # Get detailed scope statistics
    secure_stats = secure_worker.get_scope_stats()
    general_stats = general_worker.get_scope_stats()

    print("\n📋 Secure Worker Scope:")
    print(f"   Allowed paths: {secure_stats['scope_paths']}")
    print(f"   Allowed tools: {secure_stats['allowed_tools']}")

    print("\n📋 General Worker Scope:")
    print(f"   Allowed paths: {general_stats['scope_paths']}")
    print(f"   Allowed tools: {general_stats['allowed_tools']}")

    return secure_worker, general_worker


async def complex_workflow_example():
    """
    Example 3: Complex workflow with dependencies

    This demonstrates a more sophisticated workflow where tasks depend on each other.
    """
    print("\n=== Example 3: Complex Workflow with Dependencies ===")

    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=3, global_cost_limit=5.0
    )

    # Create specialized workers
    analyzer_config = WorkerConfig(
        worker_id="analyzer",
        scope_paths=["equitrcoder/"],
        allowed_tools=["read_file", "search_files"],
        max_cost=2.0,
        max_iterations=15,
    )

    documenter_config = WorkerConfig(
        worker_id="documenter",
        scope_paths=["equitrcoder/docs/", "equitrcoder/examples/"],
        allowed_tools=["read_file", "edit_file"],
        max_cost=1.5,
        max_iterations=10,
    )

    tester_config = WorkerConfig(
        worker_id="tester",
        scope_paths=["equitrcoder/", "test_basic_functionality.py"],
        allowed_tools=["read_file", "run_cmd"],
        max_cost=1.5,
        max_iterations=10,
    )

    # Create workers
    orchestrator.create_worker(analyzer_config)
    orchestrator.create_worker(documenter_config)
    orchestrator.create_worker(tester_config)

    # Phase 1: Analysis (sequential)
    print("Phase 1: Analysis...")
    analysis_tasks = [
        {
            "task_id": "code_analysis",
            "worker_id": "analyzer",
            "task_description": "Analyze the codebase structure and identify key components",
            "context": {"phase": 1, "type": "analysis"},
        }
    ]

    analysis_results = await orchestrator.execute_parallel_tasks(analysis_tasks)

    if not analysis_results[0].success:
        print("❌ Analysis phase failed, stopping workflow")
        return None

    print("✅ Analysis phase completed")

    # Phase 2: Documentation and Testing (parallel)
    print("\nPhase 2: Documentation and Testing...")
    phase2_tasks = [
        {
            "task_id": "update_docs",
            "worker_id": "documenter",
            "task_description": "Update documentation based on the analysis results",
            "context": {"phase": 2, "depends_on": "code_analysis"},
        },
        {
            "task_id": "run_tests",
            "worker_id": "tester",
            "task_description": "Run existing tests to verify system health",
            "context": {"phase": 2, "type": "validation"},
        },
    ]

    phase2_results = await orchestrator.execute_parallel_tasks(phase2_tasks)

    # Check results
    all_successful = all(result.success for result in phase2_results)
    if all_successful:
        print("✅ All phases completed successfully!")
    else:
        print("⚠️  Some tasks in phase 2 failed")

    # Final statistics
    final_stats = orchestrator.get_statistics()
    print("\n📊 Final Workflow Statistics:")
    print(f"   Total tasks: {final_stats['completed_tasks']}")
    print(f"   Total cost: ${final_stats['total_cost']:.4f}")
    print(
        f"   Success rate: {(sum(1 for r in analysis_results + phase2_results if r.success) / len(analysis_results + phase2_results)) * 100:.1f}%"
    )

    return analysis_results + phase2_results


async def supervisor_consultation_example():
    """
    Example 4: Supervisor consultation and coordination

    This shows how workers can consult with a supervisor for guidance.
    """
    print("\n=== Example 4: Supervisor Consultation ===")

    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=2,
        global_cost_limit=3.0,
        enable_supervisor=True,  # Enable supervisor
    )

    # Create workers that can ask supervisor
    worker_config = WorkerConfig(
        worker_id="consulting_worker",
        scope_paths=["equitrcoder/"],
        allowed_tools=["read_file", "ask_supervisor"],  # Include ask_supervisor tool
        max_cost=2.0,
        max_iterations=15,
    )

    orchestrator.create_worker(worker_config)

    # Task that might need supervisor guidance
    tasks = [
        {
            "task_id": "complex_decision",
            "worker_id": "consulting_worker",
            "task_description": "Analyze the project and make recommendations, consulting supervisor when needed",
            "context": {"requires_guidance": True},
        }
    ]

    print("Executing task with supervisor consultation...")
    results = await orchestrator.execute_parallel_tasks(tasks)

    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} Task: {result.task_id}")
        print(f"   Cost: ${result.cost:.4f}")

        # Check if supervisor was consulted
        if hasattr(result, "supervisor_consultations"):
            print(f"   Supervisor consultations: {result.supervisor_consultations}")

    return results


async def error_recovery_example():
    """
    Example 5: Error handling and recovery in multi-agent scenarios

    This demonstrates how to handle failures gracefully in multi-agent workflows.
    """
    print("\n=== Example 5: Error Handling and Recovery ===")

    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=2, global_cost_limit=2.0
    )

    # Create workers with very strict limits to force failures
    limited_worker_config = WorkerConfig(
        worker_id="limited_worker",
        scope_paths=["equitrcoder/"],
        allowed_tools=["read_file"],
        max_cost=0.01,  # Very low limit
        max_iterations=1,  # Very low limit
    )

    normal_worker_config = WorkerConfig(
        worker_id="normal_worker",
        scope_paths=["equitrcoder/examples/"],
        allowed_tools=["read_file", "search_files"],
        max_cost=1.0,
        max_iterations=10,
    )

    # Create workers
    orchestrator.create_worker(limited_worker_config)
    orchestrator.create_worker(normal_worker_config)

    # Tasks designed to test failure handling
    tasks = [
        {
            "task_id": "likely_to_fail",
            "worker_id": "limited_worker",
            "task_description": "Perform comprehensive analysis of the entire codebase",  # Too complex for limits
            "context": {"expected": "failure"},
        },
        {
            "task_id": "should_succeed",
            "worker_id": "normal_worker",
            "task_description": "List the example files in the examples directory",
            "context": {"expected": "success"},
        },
    ]

    print("Executing tasks with expected failures...")
    results = await orchestrator.execute_parallel_tasks(tasks)

    # Analyze results
    successful_tasks = [r for r in results if r.success]
    failed_tasks = [r for r in results if not r.success]

    print("\n📊 Results Summary:")
    print(f"   Successful tasks: {len(successful_tasks)}")
    print(f"   Failed tasks: {len(failed_tasks)}")

    for result in results:
        status = "✅" if result.success else "❌"
        print(f"\n{status} {result.task_id} ({result.worker_id}):")
        print(f"   Cost: ${result.cost:.4f}")
        if not result.success:
            print(f"   Error: {result.error}")

            # Check if it was a limit violation
            if "cost" in result.error.lower() or "iteration" in result.error.lower():
                print("   Cause: Resource limit exceeded")

    # Recovery strategy example
    if failed_tasks:
        print("\n🔄 Recovery Strategy:")
        print("   - Retry failed tasks with higher limits")
        print("   - Break down complex tasks into smaller ones")
        print("   - Reassign tasks to different workers")

    return results


async def main():
    """
    Main function that runs all multi-agent examples
    """
    print("🚀 equitrcoder Multi-Agent Coordination Examples")
    print("=" * 60)

    # Check if we have API keys configured
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: No API keys found in environment variables.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run these examples.")
        print("   Examples will show the structure but may not execute successfully.")
        print()

    try:
        # Run all examples
        await basic_multi_agent_example()
        await security_isolation_example()
        await complex_workflow_example()
        await supervisor_consultation_example()
        await error_recovery_example()

        print("\n🎉 All multi-agent examples completed!")
        print("\nKey takeaways:")
        print("- Multi-agent coordination enables parallel processing")
        print("- Security isolation protects sensitive operations")
        print("- Complex workflows can be broken into phases")
        print("- Supervisor consultation provides guidance for complex decisions")
        print("- Error handling ensures graceful failure recovery")
        print("\nNext steps:")
        print("- Try creating your own worker configurations")
        print("- Experiment with different task distributions")
        print("- Check out custom_tools.py for tool development examples")

    except Exception as e:
        print(f"\n💥 Error running examples: {e}")
        print("This might be due to missing API keys or network issues.")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
