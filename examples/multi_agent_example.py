#!/usr/bin/env python3
"""
Multi-Agent Orchestration Example

This example demonstrates how to use EQUITR Coder's strong/weak agent paradigm
for complex software development tasks.
"""

import asyncio
import sys
import os

# Add the EQUITR-coder directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "EQUITR-coder"))

from EQUITR_coder.core.config import config_manager
from EQUITR_coder.core.orchestrator import AgentOrchestrator


async def demonstrate_multi_agent():
    """Demonstrate multi-agent orchestration with practical examples."""

    print("🚀 Multi-Agent Orchestration Demo")
    print("=" * 50)

    # Load configuration
    config = config_manager.load_config("default")

    # Enable multi-agent mode
    config.orchestrator.use_multi_agent = True
    config.llm.model = "gpt-4o-mini"  # Use same model for demo

    # Create orchestrator
    orchestrator = AgentOrchestrator(config, ".")

    try:
        # Example 1: System Architecture Design
        print("\n📋 Example 1: System Architecture Design")
        print("-" * 40)

        task1 = """
        Design a scalable notification system for a web application that needs to send:
        - Email notifications
        - SMS alerts  
        - Push notifications
        - In-app notifications
        
        Requirements:
        - Handle 1M+ notifications per day
        - Support multiple notification channels
        - Include retry mechanisms
        - Provide delivery tracking
        - Queue management for high volume
        """

        print("Task: Scalable notification system design")
        print("This will use supervisor for architecture + worker for implementation")

        # In a real scenario, this would run the orchestrator
        # result = await orchestrator.run(task1)
        # print(f"Cost: ${result.get('cost', 0):.4f}")

        # Example 2: Performance Optimization
        print("\n📋 Example 2: Performance Optimization")
        print("-" * 40)

        task2 = """
        Optimize a Python web scraper that's taking too long to process 10,000 URLs.
        Current issues:
        - Sequential processing is slow
        - Memory usage grows with large datasets
        - No error handling for failed requests
        - No rate limiting
        
        Provide both the optimization strategy and the improved implementation.
        """

        print("Task: Web scraper performance optimization")
        print("Supervisor will analyze bottlenecks, worker will implement fixes")

        # Example 3: Database Design
        print("\n📋 Example 3: Database Schema Design")
        print("-" * 40)

        task3 = """
        Design a database schema for a social media platform with:
        - Users and profiles
        - Posts and content
        - Comments and reactions
        - Follow relationships
        - Direct messages
        - Content moderation
        
        Consider scalability, data consistency, and query performance.
        """

        print("Task: Social media database design")
        print("Complex schema requiring supervisor's architectural insight")

        # Show available tools in multi-agent mode
        from EQUITR_coder.tools import registry

        tools = registry.get_all()

        print(f"\n🔧 Available tools in multi-agent mode: {len(tools)}")
        supervisor_tools = [
            name for name in tools.keys() if "supervisor" in name.lower()
        ]
        if supervisor_tools:
            print(f"   ✅ Supervisor consultation: {supervisor_tools}")

        print("\n💡 Usage Examples:")
        print('   EQUITR-coder chat --multi-agent "Design a caching strategy..."')
        print('   EQUITR-coder chat -M "Optimize this database query..."')
        print("   EQUITR-coder interactive --multi-agent")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await orchestrator.close()


async def run_simple_demo():
    """Run a simple demonstration without actual API calls."""

    print("\n🎯 Simple Multi-Agent Demo")
    print("=" * 30)

    # Simulate the flow
    scenarios = [
        {
            "task": "Create a REST API for user management",
            "supervisor_role": "Architecture design and security patterns",
            "worker_role": "Implementation and testing",
        },
        {
            "task": "Optimize database queries for a reporting system",
            "supervisor_role": "Query analysis and indexing strategy",
            "worker_role": "Query optimization and implementation",
        },
        {
            "task": "Design a microservices architecture for e-commerce",
            "supervisor_role": "System design and service boundaries",
            "worker_role": "Service implementation and integration",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['task']}")
        print(f"   👑 Supervisor: {scenario['supervisor_role']}")
        print(f"   🛠️ Worker: {scenario['worker_role']}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_simple_demo())

    print("\n" + "=" * 60)
    print("To run actual multi-agent orchestration:")
    print('EQUITR-coder chat --multi-agent "Your complex task here"')
    print("=" * 60)
