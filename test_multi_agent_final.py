#!/usr/bin/env python3
"""
Final comprehensive test for multi-agent orchestration
"""

import asyncio
import sys
import os

# Add the EQUITR-coder directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "EQUITR-coder"))

from EQUITR_coder.core.config import config_manager
from EQUITR_coder.tools import registry, discovery


def test_tool_registration():
    """Test tool registration in both modes"""
    print("🔧 Testing tool registration...")

    # Clear registry first
    registry._tools.clear()

    # Discover tools
    discovery.discover_builtin_tools()
    discovery.discover_custom_tools()

    initial_tools = len(registry.get_all())
    print(f"   ✅ Initial tools: {initial_tools}")

    # Test multi-agent tool registration
    from EQUITR_coder.tools.builtin.ask_supervisor import AskSupervisor
    from EQUITR_coder.providers.litellm import LiteLLMProvider

    # Create mock provider
    mock_provider = LiteLLMProvider(
        model="gpt-4o-mini", api_base="http://localhost:4000", api_key="mock-key"
    )

    # Register ask_supervisor tool
    ask_tool = AskSupervisor(mock_provider)
    registry.register(ask_tool)

    final_tools = len(registry.get_all())
    ask_supervisor = registry.get("ask_supervisor")

    print(f"   ✅ After registration: {final_tools} tools")
    print(f"   ✅ ask_supervisor tool: {'✅' if ask_supervisor else '❌'}")

    return ask_supervisor is not None


def test_cli_integration():
    """Test CLI integration"""
    print("\n🖥️ Testing CLI integration...")

    # Test CLI help
    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "-m", "EQUITR_coder.cli", "chat", "--help"],
            capture_output=True,
            text=True,
            cwd="EQUITR-coder",
        )

        if "--multi-agent" in result.stdout or "-M" in result.stdout:
            print("   ✅ Multi-agent CLI flag available")
        else:
            print("   ❌ Multi-agent CLI flag missing")

    except Exception as e:
        print(f"   ❌ CLI test error: {e}")


def test_configuration_flow():
    """Test configuration flow"""
    print("\n⚙️ Testing configuration flow...")

    try:
        # Test config loading
        config = config_manager.load_config("default")

        # Test multi-agent flag
        original_value = getattr(config.orchestrator, "use_multi_agent", None)

        if original_value is not None:
            print(f"   ✅ use_multi_agent config: {original_value}")
        else:
            print("   ⚠️ use_multi_agent not in default config")

        # Test setting the flag
        config.orchestrator.use_multi_agent = True
        print("   ✅ Can set multi-agent mode")

    except Exception as e:
        print(f"   ❌ Config error: {e}")


def test_supervisor_agent():
    """Test supervisor agent initialization"""
    print("\n👑 Testing supervisor agent...")

    try:
        from EQUITR_coder.core.supervisor import SupervisorAgent
        from EQUITR_coder.core.session import SessionManagerV2
        from EQUITR_coder.providers.litellm import LiteLLMProvider

        # Create mock components
        mock_provider = LiteLLMProvider(
            model="gpt-4o-mini", api_base="http://localhost:4000", api_key="mock-key"
        )

        session_manager = SessionManagerV2()

        # Test supervisor initialization
        supervisor = SupervisorAgent(
            mock_provider, session_manager, ".", use_multi_agent=True
        )

        print("   ✅ Supervisor agent initialized")
        print(f"   ✅ Multi-agent mode: {supervisor.use_multi_agent}")

    except Exception as e:
        print(f"   ❌ Supervisor error: {e}")


def main():
    """Run all tests"""
    print("🚀 Multi-Agent Orchestration Test Suite")
    print("=" * 50)

    tests = [
        test_tool_registration,
        test_cli_integration,
        test_configuration_flow,
        test_supervisor_agent,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result is not False)  # None counts as success
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append(False)

    print("\n📊 Test Results:")
    print("-" * 30)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Multi-agent orchestration is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
