#!/usr/bin/env python3
"""
Simple test to validate tool registration and multi-agent setup
"""

import sys
import os

# Add the EQUITR-coder directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "EQUITR-coder"))

from EQUITR_coder.tools import registry, discovery
from EQUITR_coder.core.config import Config


def test_tool_discovery():
    """Test basic tool discovery"""
    print("🔍 Testing tool discovery...")

    # Discover tools
    discovery.discover_builtin_tools()
    discovery.discover_custom_tools()

    # List available tools
    tools = registry.get_all()
    print(f"✅ Found {len(tools)} tools:")
    for name, tool in tools.items():
        print(f"  - {name}: {tool.description[:50]}...")

    return tools


def test_config():
    """Test config creation"""
    print("\n⚙️ Testing config creation...")

    config_dict = {
        "llm": {
            "provider": "litellm",
            "model": "gpt-4o-mini",
            "api_base": "http://localhost:4000",
            "temperature": 0.1,
            "max_tokens": 4000,
            "budget": 5.0,
        },
        "orchestrator": {"max_iterations": 10, "use_multi_agent": True},
        "tools": {"enabled": ["filesystem", "shell", "git", "search", "todos"]},
        "repository": {"index_on_start": False},
        "session": {"persist": True},
    }

    try:
        config = Config(**config_dict)
        print("✅ Config created successfully")
        print(f"  - Multi-agent enabled: {config.orchestrator.use_multi_agent}")
        return config
    except Exception as e:
        print(f"❌ Config error: {e}")
        return None


if __name__ == "__main__":
    tools = test_tool_discovery()
    config = test_config()

    if config and tools:
        print("\n🎉 Basic setup validated!")
    else:
        print("\n⚠️ Issues found in setup")
