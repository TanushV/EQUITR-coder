#!/usr/bin/env python3
"""
Simple test to verify LiteLLM connection works
"""

import sys
import os

sys.path.insert(0, "EQUITR-coder")

import litellm
import asyncio


async def test_litellm_connection():
    """Test basic LiteLLM connection"""
    try:
        # Test with a simple completion
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: litellm.completion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=10,
            ),
        )
        print("✅ LiteLLM connection successful")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ LiteLLM connection failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_litellm_connection())
