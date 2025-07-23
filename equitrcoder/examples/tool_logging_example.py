#!/usr/bin/env python3
"""
Example demonstrating tool call logging and multi-agent with separate models.

This example shows:
1. How to enable tool call logging in programmatic mode
2. How to use separate models for supervisor and workers in multi-agent mode
3. How to access and analyze tool call statistics
"""

import asyncio
from pathlib import Path

# Add the EQUITR-coder package to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "EQUITR-coder"))

from equitrcoder.api import EquitrAPI, SyncEquitrAPI


async def async_example():
    """Async example with tool logging and multi-agent models."""
    print("🚀 Async Example: Multi-agent with Tool Logging")
    
    async with EquitrAPI(
        repo_path="./example_project",
        multi_agent=True,
        supervisor_model="anthropic/claude-3.5-sonnet",  # Powerful model for supervisor
        worker_model="anthropic/claude-3-haiku",         # Fast model for workers
        log_tool_calls=True,
        tool_log_file="example_tool_calls.log",
    ) as api:
        
        # Create a simple project
        response = await api.chat(
            "Create a simple Python calculator with basic operations (add, subtract, multiply, divide). "
            "Include proper error handling and a main function."
        )
        
        print("📋 Response:")
        print(response[:200] + "..." if len(response) > 200 else response)
        
        # Get tool call statistics
        stats = api.get_tool_call_stats()
        if stats:
            print(f"\n📊 Tool Call Statistics:")
            print(f"  Total calls: {stats.get('total_calls', 0)}")
            print(f"  Successful calls: {stats.get('successful_calls', 0)}")
            print(f"  Failed calls: {stats.get('failed_calls', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
            print(f"  Average duration: {stats.get('average_duration_ms', 0):.1f}ms")
            
            # Show tool usage breakdown
            tool_usage = stats.get('tool_usage', {})
            if tool_usage:
                print(f"\n🔧 Tool Usage Breakdown:")
                for tool_name, usage in tool_usage.items():
                    print(f"  {tool_name}: {usage['count']} calls, "
                          f"{usage['success_count']}/{usage['count']} successful")
        
        # Get recent tool call logs
        logs = api.get_tool_call_logs(limit=5)
        if logs:
            print(f"\n📝 Recent Tool Calls:")
            for log in logs[-3:]:  # Show last 3
                print(f"  {log['timestamp'][:19]} - {log['tool_name']}: "
                      f"{'✅' if log['success'] else '❌'} "
                      f"({log['duration_ms']:.1f}ms)")
        
        # Export logs for analysis
        api.export_tool_logs("detailed_tool_logs.json", format="json")
        print(f"\n💾 Exported detailed logs to detailed_tool_logs.json")


def sync_example():
    """Synchronous example with tool logging."""
    print("\n🚀 Sync Example: Single Agent with Tool Logging")
    
    with SyncEquitrAPI(
        repo_path="./example_project",
        multi_agent=False,
        model="anthropic/claude-3-haiku",
        log_tool_calls=True,
        tool_log_file="sync_tool_calls.log",
    ) as api:
        
        # Test a simple task
        response = api.chat("List the files in the current directory and show their sizes.")
        
        print("📋 Response:")
        print(response[:200] + "..." if len(response) > 200 else response)
        
        # Show statistics
        stats = api.get_tool_call_stats()
        if stats:
            print(f"\n📊 Tool Call Statistics:")
            print(f"  Total calls: {stats.get('total_calls', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0):.1%}")


def multi_model_comparison():
    """Compare different model configurations."""
    print("\n🚀 Multi-Model Comparison Example")
    
    configurations = [
        {
            "name": "Single Agent (Claude 3.5 Sonnet)",
            "config": {
                "multi_agent": False,
                "model": "anthropic/claude-3.5-sonnet",
                "log_tool_calls": True,
            }
        },
        {
            "name": "Multi-Agent (Sonnet + Haiku)",
            "config": {
                "multi_agent": True,
                "supervisor_model": "anthropic/claude-3.5-sonnet",
                "worker_model": "anthropic/claude-3-haiku",
                "log_tool_calls": True,
            }
        },
    ]
    
    task = "Create a simple README.md file for a Python project with installation and usage instructions."
    
    for config_info in configurations:
        print(f"\n--- {config_info['name']} ---")
        
        try:
            with SyncEquitrAPI(
                repo_path=f"./test_{config_info['name'].lower().replace(' ', '_')}",
                **config_info['config']
            ) as api:
                
                import time
                start_time = time.time()
                response = api.chat(task)
                end_time = time.time()
                
                stats = api.get_tool_call_stats()
                
                print(f"⏱️  Total time: {end_time - start_time:.1f}s")
                if stats:
                    print(f"🔧 Tool calls: {stats.get('total_calls', 0)}")
                    print(f"✅ Success rate: {stats.get('success_rate', 0):.1%}")
                
                # Show first 100 chars of response
                print(f"📝 Response preview: {response[:100]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🎯 EQUITR-Coder Tool Logging and Multi-Agent Examples\n")
    
    # Run async example
    asyncio.run(async_example())
    
    # Run sync example  
    sync_example()
    
    # Run comparison
    multi_model_comparison()
    
    print("\n✅ All examples completed!")
    print("📁 Check the generated log files:")
    print("  - example_tool_calls.log")
    print("  - sync_tool_calls.log") 
    print("  - detailed_tool_logs.json") 