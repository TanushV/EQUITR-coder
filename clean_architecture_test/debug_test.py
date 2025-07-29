#!/usr/bin/env python3
"""
Debug test to check if basic components work
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Testing imports...")
    from equitrcoder.core.clean_orchestrator import CleanOrchestrator
    from equitrcoder.core.clean_agent import CleanAgent
    from equitrcoder.tools.discovery import discover_tools
    print("✅ All imports successful")
    
    print("\nTesting environment loading...")
    from equitrcoder.utils.env_loader import auto_load_environment
    auto_load_environment()
    print("✅ Environment loaded")
    
    print("\nTesting tool discovery...")
    tools = discover_tools()
    print(f"✅ Found {len(tools)} tools: {[t.get_name() for t in tools[:5]]}...")
    
    print("\nTesting orchestrator creation...")
    orchestrator = CleanOrchestrator(model="moonshot/kimi-k2-0711-preview")
    print("✅ Orchestrator created")
    
    print("\nTesting agent creation...")
    agent = CleanAgent(
        agent_id="test_agent",
        model="moonshot/kimi-k2-0711-preview",
        tools=tools[:3],  # Just a few tools
        audit_model="o3"
    )
    print("✅ Agent created")
    
    print("\n🎉 All basic components working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)