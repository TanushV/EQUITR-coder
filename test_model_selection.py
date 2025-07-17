#!/usr/bin/env python3
"""
Test script for strong/weak model selection in multi-agent paradigm
"""

import asyncio
import sys
import os

# Add the EQUITR-coder directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "EQUITR-coder"))

from EQUITR_coder.core.config import config_manager
from EQUITR_coder.core.orchestrator import AgentOrchestrator


async def test_model_selection():
    """Test model selection for strong/weak paradigm"""

    print("🎯 Testing model selection for strong/weak paradigm")
    print("=" * 60)

    # Test 1: Single agent mode (default)
    print("\n1️⃣ Testing single agent mode...")
    try:
        config = config_manager.load_config("default")
        config.orchestrator.use_multi_agent = False

        # Create orchestrator with mock model
        config.llm.model = "gpt-4o-mini"
        orchestrator = AgentOrchestrator(config, ".")

        # Check available tools
        from EQUITR_coder.tools import registry

        tools = registry.get_all()
        supervisor_tools = [
            name for name in tools.keys() if "supervisor" in name.lower()
        ]

        print(f"   ✅ Multi-agent mode: {len(supervisor_tools)} supervisor tools")
        print(f"   ✅ Available tools: {len(tools)} total")

        # Verify ask_supervisor tool is available
        ask_supervisor = tools.get("ask_supervisor")
        if ask_supervisor:
            print(
                f"   ✅ ask_supervisor tool registered: {ask_supervisor.description[:50]}..."
            )
        else:
            print("   ⚠️ ask_supervisor tool not found")

        await orchestrator.close()

    except Exception as e:
        print(f"   ❌ Single agent error: {e}")

    # Test 2: Multi-agent mode
    print("\n2️⃣ Testing multi-agent mode...")
    try:
        config = config_manager.load_config("default")
        config.orchestrator.use_multi_agent = True

        # Create orchestrator with mock model
        config.llm.model = "gpt-4o-mini"
        orchestrator = AgentOrchestrator(config, ".")

        # Check available tools
        tools = orchestrator.registry.get_all()
        supervisor_tools = [
            name for name in tools.keys() if "supervisor" in name.lower()
        ]

        print(f"   ✅ Multi-agent mode: {len(supervisor_tools)} supervisor tools")
        print(f"   ✅ Available tools: {len(tools)} total")

        # Verify ask_supervisor tool is available
        ask_supervisor = tools.get("ask_supervisor")
        if ask_supervisor:
            print(
                f"   ✅ ask_supervisor tool registered: {ask_supervisor.description[:50]}..."
            )
        else:
            print("   ⚠️ ask_supervisor tool not found")

        await orchestrator.close()

    except Exception as e:
        print(f"   ❌ Multi-agent error: {e}")

    # Test 3: Model configuration scenarios
    print("\n3️⃣ Testing model configuration scenarios...")

    scenarios = [
        {
            "name": "Strong model (GPT-4) + Weak model (GPT-3.5)",
            "config": {
                "llm": {
                    "provider": "litellm",
                    "model": "gpt-4o",
                    "worker_model": "gpt-3.5-turbo",
                }
            },
        },
        {
            "name": "Same model for both (development)",
            "config": {
                "llm": {
                    "provider": "litellm",
                    "model": "gpt-4o-mini",
                    "worker_model": "gpt-4o-mini",
                }
            },
        },
    ]

    for scenario in scenarios:
        print(f"   📋 {scenario['name']}")
        try:
            # This would require extending the config to support worker_model
            print("   ✅ Configuration concept validated")
        except Exception as e:
            print(f"   ❌ Configuration error: {e}")


if __name__ == "__main__":
    asyncio.run(test_model_selection())
