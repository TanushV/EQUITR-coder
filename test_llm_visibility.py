#!/usr/bin/env python3
"""
Test script to demonstrate the new LLM response visibility feature
in the programmatic interface.
"""

import asyncio
import json
from equitrcoder.programmatic.interface import EquitrCoder, TaskConfiguration

async def test_llm_visibility():
    """Test the new LLM response visibility features."""
    
    print("🧪 Testing LLM Response Visibility Feature")
    print("=" * 50)
    
    # Create a simple task
    coder = EquitrCoder(repo_path=".", git_enabled=False)
    
    config = TaskConfiguration(
        description="Create a simple hello.py file that prints 'Hello, World!'",
        max_cost=1.0,
        max_iterations=5,
        auto_commit=False
    )
    
    # Execute the task
    print("🚀 Executing task...")
    result = await coder.execute_task(
        task_description="Create a simple hello.py file that prints 'Hello, World!'",
        config=config
    )
    
    print(f"\n✅ Task completed: {result.success}")
    print(f"💰 Cost: ${result.cost:.4f}")
    print(f"🔄 Iterations: {result.iterations}")
    
    # Demonstrate the new LLM response visibility
    if result.llm_responses:
        print(f"\n🤖 LLM Responses ({len(result.llm_responses)} total):")
        print("-" * 30)
        
        for i, response in enumerate(result.llm_responses, 1):
            print(f"\nResponse {i} (Iteration {response['iteration']}):")
            print(f"  Model: {response['model']}")
            print(f"  Content: {response['content'][:100]}..." if len(response['content']) > 100 else f"  Content: {response['content']}")
            print(f"  Tool Calls: {len(response['tool_calls'])}")
            print(f"  Cost: ${response['cost']:.4f}")
    
    if result.tool_call_history:
        print(f"\n🔧 Tool Calls ({len(result.tool_call_history)} total):")
        print("-" * 30)
        
        for i, tool_call in enumerate(result.tool_call_history, 1):
            print(f"\nTool Call {i} (Iteration {tool_call['iteration']}):")
            print(f"  Tool: {tool_call['tool_name']}")
            print(f"  Success: {tool_call['success']}")
            if tool_call['tool_args']:
                print(f"  Args: {json.dumps(tool_call['tool_args'], indent=2)[:200]}...")
    
    if result.conversation_history:
        print(f"\n💬 Conversation History ({len(result.conversation_history)} messages):")
        print("-" * 30)
        
        for i, msg in enumerate(result.conversation_history[-3:], 1):  # Show last 3 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            print(f"\n{role.upper()}: {content[:150]}..." if len(content) > 150 else f"\n{role.upper()}: {content}")
    
    print("\n" + "=" * 50)
    print("🎉 LLM Visibility Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_llm_visibility())