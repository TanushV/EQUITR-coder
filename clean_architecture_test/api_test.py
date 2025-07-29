#!/usr/bin/env python3
"""
Test API connectivity for both models
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.providers.litellm import LiteLLMProvider, Message


async def test_moonshot_api():
    """Test moonshot API connectivity."""
    print("🧪 TESTING MOONSHOT API")
    print("=" * 40)
    
    try:
        from equitrcoder.utils.env_loader import auto_load_environment
        auto_load_environment()
        
        provider = LiteLLMProvider(model="moonshot/kimi-k2-0711-preview")
        
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say hello and tell me the current model you are.")
        ]
        
        print("Calling moonshot API...")
        response = await provider.chat(messages=messages)
        
        print(f"✅ Response: {response.content[:100]}...")
        print(f"✅ Cost: ${response.cost}")
        
        return True
        
    except Exception as e:
        print(f"❌ Moonshot API failed: {e}")
        return False


async def test_openai_api():
    """Test OpenAI API connectivity."""
    print("\n🧪 TESTING OPENAI API (O3)")
    print("=" * 40)
    
    try:
        from equitrcoder.utils.env_loader import auto_load_environment
        auto_load_environment()
        
        provider = LiteLLMProvider(model="o3")
        
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say hello and tell me the current model you are.")
        ]
        
        print("Calling OpenAI API...")
        response = await provider.chat(messages=messages)
        
        print(f"✅ Response: {response.content[:100]}...")
        print(f"✅ Cost: ${response.cost}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API failed: {e}")
        return False


async def main():
    """Test both APIs."""
    print("🧪 API CONNECTIVITY TESTS")
    print("=" * 50)
    
    moonshot_success = await test_moonshot_api()
    openai_success = await test_openai_api()
    
    print("\n" + "=" * 50)
    print("📊 API TEST RESULTS:")
    print(f"Moonshot: {'✅ WORKING' if moonshot_success else '❌ FAILED'}")
    print(f"OpenAI: {'✅ WORKING' if openai_success else '❌ FAILED'}")
    
    overall_success = moonshot_success and openai_success
    print(f"\nOverall: {'✅ ALL APIS WORKING' if overall_success else '❌ SOME APIS FAILED'}")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)