#!/usr/bin/env python3
"""
Comprehensive Mode Test Execution Script for EquitrCoder

This script runs comprehensive tests across all agent configurations:
- Single agent mode
- Multi-agent sequential mode  
- Multi-agent parallel mode

All tests use the moonshot/kimi-k2-0711-preview model and are executed
in isolated environments to prevent interference.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from testing.comprehensive_mode_testing import (
    ComprehensiveModeTestController,
    ComprehensiveTestConfig
)


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive mode tests for EquitrCoder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_comprehensive_mode_tests.py                    # Run all tests
  python run_comprehensive_mode_tests.py --single-only     # Run only single agent tests
  python run_comprehensive_mode_tests.py --multi-only      # Run only multi-agent tests
  python run_comprehensive_mode_tests.py --parallel-only   # Run only parallel tests
  python run_comprehensive_mode_tests.py --model gpt-4     # Use different model
        """
    )
    
    # Test selection arguments
    parser.add_argument(
        '--single-only',
        action='store_true',
        help='Run only single agent tests'
    )
    
    parser.add_argument(
        '--multi-only',
        action='store_true', 
        help='Run only multi-agent tests (both sequential and parallel)'
    )
    
    parser.add_argument(
        '--sequential-only',
        action='store_true',
        help='Run only multi-agent sequential tests'
    )
    
    parser.add_argument(
        '--parallel-only',
        action='store_true',
        help='Run only multi-agent parallel tests'
    )
    
    # Configuration arguments
    parser.add_argument(
        '--model',
        default='moonshot/kimi-k2-0711-preview',
        help='Model to use for all tests (default: moonshot/kimi-k2-0711-preview)'
    )
    
    parser.add_argument(
        '--max-cost',
        type=float,
        default=15.0,
        help='Maximum cost limit per test (default: 15.0)'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=25,
        help='Maximum iterations per test (default: 25)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Timeout in seconds per test (default: 600)'
    )
    
    parser.add_argument(
        '--task',
        default='Create a simple calculator application with basic arithmetic operations (add, subtract, multiply, divide), a command-line interface, input validation, error handling for division by zero, and comprehensive unit tests',
        help='Test task description'
    )
    
    parser.add_argument(
        '--agents',
        type=int,
        default=3,
        help='Number of parallel agents for parallel mode (default: 3)'
    )
    
    # Output arguments
    parser.add_argument(
        '--output-dir',
        default='testing/comprehensive_mode_tests',
        help='Output directory for test results (default: testing/comprehensive_mode_tests)'
    )
    
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do not clean up test environments after completion'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-auto-fix',
        action='store_true',
        help='Disable automatic fix attempts'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("=" * 80)
    print("🧪 EQUITRCODER COMPREHENSIVE MODE TESTING FRAMEWORK")
    print("=" * 80)
    print(f"📋 Test Task: {args.task}")
    print(f"🤖 Model: {args.model}")
    print(f"💰 Max Cost per Test: ${args.max_cost}")
    print(f"🔄 Max Iterations: {args.max_iterations}")
    print(f"⏱️  Timeout: {args.timeout}s")
    print(f"👥 Parallel Agents: {args.agents}")
    print(f"📁 Output Directory: {args.output_dir}")
    print("=" * 80)
    
    # Validate environment
    if not validate_environment():
        print("❌ Environment validation failed. Please check your setup.")
        return 1
    
    # Create test configuration
    test_config = ComprehensiveTestConfig(
        model=args.model,
        max_cost_per_test=args.max_cost,
        max_iterations_per_test=args.max_iterations,
        timeout_seconds=args.timeout,
        test_task=args.task,
        parallel_agents_count=args.agents,
        max_workers=args.agents,
        base_test_dir=args.output_dir,
        enable_auto_fix=not args.no_auto_fix,
        preserve_artifacts=not args.no_cleanup,
        verbose_output=args.verbose
    )
    
    # Initialize test controller
    controller = ComprehensiveModeTestController(config=test_config)
    
    try:
        # Determine which tests to run
        if args.single_only:
            print("🤖 Running SINGLE AGENT tests only...")
            results = await controller.run_single_agent_tests()
            print_single_agent_summary(results)
            
        elif args.sequential_only:
            print("👥 Running MULTI-AGENT SEQUENTIAL tests only...")
            results = await controller.run_multi_agent_sequential_tests()
            print_multi_agent_summary(results, "Sequential")
            
        elif args.parallel_only:
            print("⚡ Running MULTI-AGENT PARALLEL tests only...")
            results = await controller.run_multi_agent_parallel_tests()
            print_multi_agent_summary(results, "Parallel")
            
        elif args.multi_only:
            print("👥⚡ Running MULTI-AGENT tests (sequential and parallel)...")
            seq_results = await controller.run_multi_agent_sequential_tests()
            par_results = await controller.run_multi_agent_parallel_tests()
            print_multi_agent_summary(seq_results, "Sequential")
            print_multi_agent_summary(par_results, "Parallel")
            
        else:
            print("🚀 Running ALL COMPREHENSIVE MODE tests...")
            results = await controller.run_comprehensive_tests()
            print_comprehensive_summary(results)
        
        # Cleanup if requested
        if not args.no_cleanup:
            print("\n🧹 Cleaning up test environments...")
            cleaned = controller.environment_manager.cleanup_all_environments(preserve_artifacts=True)
            print(f"   Cleaned up {cleaned} environments")
        
        print("\n✅ Testing completed successfully!")
        print(f"📁 Results saved to: {controller.get_test_run_directory()}")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def validate_environment() -> bool:
    """Validate that the environment is set up correctly for testing."""
    print("🔍 Validating environment...")
    
    # Check if we're in the right directory
    if not Path("equitrcoder").exists():
        print("❌ Not in EquitrCoder project root directory")
        return False
    
    # Check for required modules
    try:
        import equitrcoder
        print("✅ EquitrCoder module found")
    except ImportError:
        print("❌ EquitrCoder module not found. Please install the package.")
        return False
    
    # Load environment variables first
    try:
        from equitrcoder.utils.env_loader import auto_load_environment
        auto_load_environment()
    except Exception as e:
        print(f"⚠️ Could not load environment variables: {e}")
    
    # Check for API keys (at least one should be available)
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'MOONSHOT_API_KEY': os.getenv('MOONSHOT_API_KEY'),
        'AZURE_API_KEY': os.getenv('AZURE_API_KEY'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY')
    }
    
    available_keys = [key for key, value in api_keys.items() if value]
    if not available_keys:
        print("⚠️ No API keys found in environment variables")
        print("   Please set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, MOONSHOT_API_KEY, AZURE_API_KEY, OPENROUTER_API_KEY")
        return False
    else:
        print(f"✅ Found API keys: {', '.join(available_keys)}")
    
    # Check write permissions for test directory
    test_dir = Path("testing")
    test_dir.mkdir(exist_ok=True)
    if not os.access(test_dir, os.W_OK):
        print(f"❌ No write permission for test directory: {test_dir}")
        return False
    
    print("✅ Environment validation passed")
    return True


def print_single_agent_summary(results):
    """Print summary for single agent test results."""
    print("\n" + "=" * 60)
    print("🤖 SINGLE AGENT TEST SUMMARY")
    print("=" * 60)
    print(f"Overall Success: {'✅ PASSED' if results.overall_success else '❌ FAILED'}")
    print(f"Total Time: {results.total_execution_time:.2f}s")
    print(f"Total Cost: ${results.total_cost:.4f}")
    print("\nIndividual Tests:")
    print(f"  📄 Document Creation: {'✅' if results.document_creation.success else '❌'} ({results.document_creation.execution_time:.1f}s)")
    print(f"  ✅ Todo Completion: {'✅' if results.todo_completion.success else '❌'} ({results.todo_completion.execution_time:.1f}s)")
    print(f"  🤖 Agent Execution: {'✅' if results.agent_execution.success else '❌'} ({results.agent_execution.execution_time:.1f}s)")
    print(f"  🔍 Audit Functionality: {'✅' if results.audit_functionality.success else '❌'} ({results.audit_functionality.execution_time:.1f}s)")


def print_multi_agent_summary(results, mode: str):
    """Print summary for multi-agent test results."""
    print(f"\n" + "=" * 60)
    print(f"👥 MULTI-AGENT {mode.upper()} TEST SUMMARY")
    print("=" * 60)
    print(f"Overall Success: {'✅ PASSED' if results.overall_success else '❌ FAILED'}")
    print(f"Total Time: {results.total_execution_time:.2f}s")
    print(f"Total Cost: ${results.total_cost:.4f}")
    print("\nIndividual Tests:")
    print(f"  📄 Document Creation: {'✅' if results.document_creation.success else '❌'} ({results.document_creation.execution_time:.1f}s)")
    print(f"  ✅ Todo Completion: {'✅' if results.todo_completion.success else '❌'} ({results.todo_completion.execution_time:.1f}s)")
    print(f"  🤝 Agent Coordination: {'✅' if results.agent_coordination.success else '❌'} ({results.agent_coordination.execution_time:.1f}s)")
    print(f"  🔍 Audit Functionality: {'✅' if results.audit_functionality.success else '❌'} ({results.audit_functionality.execution_time:.1f}s)")
    if hasattr(results, 'parallel_execution') and results.parallel_execution:
        print(f"  ⚡ Parallel Execution: {'✅' if results.parallel_execution.success else '❌'} ({results.parallel_execution.execution_time:.1f}s)")


def print_comprehensive_summary(results):
    """Print comprehensive test summary."""
    print("\n" + "=" * 80)
    print("🏆 COMPREHENSIVE MODE TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"🎯 Overall Success: {'✅ ALL TESTS PASSED' if results.overall_success else '❌ SOME TESTS FAILED'}")
    print(f"⏱️  Total Execution Time: {results.total_execution_time:.2f} seconds")
    print(f"💰 Total Cost: ${results.total_cost:.4f}")
    print(f"📊 Test Timestamp: {results.test_timestamp}")
    print(f"📈 Success Rate: {results.get_success_rate():.1%}")
    
    print(f"\n📈 PERFORMANCE COMPARISON:")
    perf = results.performance_comparison
    if perf:
        print("┌─────────────────────┬──────────────┬──────────────┬──────────────┐")
        print("│ Metric              │ Single Agent │ Multi-Seq    │ Multi-Par    │")
        print("├─────────────────────┼──────────────┼──────────────┼──────────────┤")
        print(f"│ Execution Time (s)  │ {perf['execution_time_comparison']['single_agent']:>12.2f} │ {perf['execution_time_comparison']['multi_agent_sequential']:>12.2f} │ {perf['execution_time_comparison']['multi_agent_parallel']:>12.2f} │")
        print(f"│ Cost ($)            │ {perf['cost_comparison']['single_agent']:>12.4f} │ {perf['cost_comparison']['multi_agent_sequential']:>12.4f} │ {perf['cost_comparison']['multi_agent_parallel']:>12.4f} │")
        print(f"│ Success             │ {'✅':>12} │ {'✅' if perf['success_rate_comparison']['multi_agent_sequential'] else '❌':>12} │ {'✅' if perf['success_rate_comparison']['multi_agent_parallel'] else '❌':>12} │")
        print("└─────────────────────┴──────────────┴──────────────┴──────────────┘")
        
        print(f"\n🏃 Fastest Mode: {perf.get('fastest_mode', 'Unknown').replace('_', ' ').title()}")
        print(f"💰 Cheapest Mode: {perf.get('cheapest_mode', 'Unknown').replace('_', ' ').title()}")
    
    failed_tests = results.get_failed_tests()
    if failed_tests:
        print(f"\n⚠️  FAILED TESTS ({len(failed_tests)} issues found):")
        for i, test in enumerate(failed_tests, 1):
            print(f"  {i}. {test.test_name} ({test.mode}): {test.error_message}")
    else:
        print("\n✅ NO FAILED TESTS")
    
    if results.failure_analysis:
        print(f"\n🔍 FAILURE ANALYSIS ({len(results.failure_analysis)} issues found):")
        for i, failure in enumerate(results.failure_analysis, 1):
            print(f"  {i}. {failure.error_category.value.replace('_', ' ').title()}: {failure.root_cause}")
    
    print(f"\n📁 Detailed results saved to test directory")
    print("=" * 80)


if __name__ == "__main__":
    # Run the main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)