#!/usr/bin/env python3
"""
Test script for multi-agent orchestration
"""

import asyncio
import sys
import os

# Add the EQUITR-coder directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "EQUITR-coder"))

from EQUITR_coder.core.config import config_manager
from EQUITR_coder.core.orchestrator import AgentOrchestrator


async def test_multi_agent():
    """Test multi-agent orchestration with ask_supervisor tool"""

    # Load test config
    import yaml

    with open("test_config.yaml", "r") as f:
        config_data = yaml.safe_load(f)

    # Create config from dict
    from EQUITR_coder.core.config import Config

    config = Config(**config_data)

    # Ensure multi-agent mode is enabled
    config.orchestrator.use_multi_agent = True
    # Create orchestrator
    orchestrator = AgentOrchestrator(config, ".")

    try:
        # Test a simple task that might benefit from supervisor consultation
        test_task = "Create a Python function to calculate fibonacci numbers, but I'm not sure about the best approach. Should I use recursion, iteration, or memoization?"

        print("🤖 Testing multi-agent orchestration...")
        print(f"Task: {test_task}")
        print("-" * 50)

        response = await orchestrator.run(test_task)

        print("Response:")
        print(response.get("content", "No content returned"))
        print(f"Cost: ${response.get('cost', 0):.4f}")
        print(f"Tokens: {response.get('usage', {}).get('total_tokens', 0)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(test_multi_agent())
