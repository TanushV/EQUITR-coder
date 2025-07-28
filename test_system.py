#!/usr/bin/env python3
"""
Test script for EQUITR Coder system.
Tests both single-agent and multi-agent modes with specified models.
"""

import asyncio
import os
from pathlib import Path

# Set up environment for testing
os.environ.setdefault("MOONSHOT_API_KEY", os.getenv("MOONSHOT_API_KEY", ""))
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

async def test_single_agent():
    """Test single agent mode with moonshot/kimi-k2-0711-preview."""
    print("🤖 Testing Single Agent Mode")
    print("=" * 50)
    
    try:
        from equitrcoder.programmatic.interface import create_single_agent_coder, TaskConfiguration
        
        # Create single agent coder
        coder = create_single_agent_coder(
            repo_path="./test_single",
            model="moonshot/kimi-k2-0711-preview"
        )
        
        # Create test directory
        test_dir = Path("./test_single")
        test_dir.mkdir(exist_ok=True)
        os.chdir(test_dir)
        
        # Simple task configuration
        config = TaskConfiguration(
            description="Create a simple calculator",
            max_cost=2.0,
            max_iterations=999999
        )
        
        # Execute task
        print("📋 Executing task: Create a simple calculator")
        result = await coder.execute_task(
            "Create a simple calculator application with basic arithmetic operations (add, subtract, multiply, divide). Include proper error handling and a command-line interface.",
            config=config
        )
        
        # Print results
        print(f"✅ Success: {result.success}")
        print(f"💰 Cost: ${result.cost:.4f}")
        print(f"🔄 Iterations: {result.iterations}")
        if result.error:
            print(f"❌ Error: {result.error}")
        
        print("📄 Content preview:")
        print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
        
        return result.success
        
    except Exception as e:
        print(f"❌ Single agent test failed: {e}")
        return False
    finally:
        os.chdir("..")

async def test_multi_agent():
    """Test multi-agent mode with o3 supervisor and moonshot workers."""
    print("\n🤖🤖🤖 Testing Multi-Agent Mode")
    print("=" * 50)
    
    try:
        from equitrcoder.programmatic.interface import create_multi_agent_coder, MultiAgentTaskConfiguration
        
        # Create multi-agent coder
        coder = create_multi_agent_coder(
            repo_path="./test_multi",
            max_workers=2,
            supervisor_model="o3",
            worker_model="moonshot/kimi-k2-0711-preview"
        )
        
        # Create test directory
        test_dir = Path("./test_multi")
        test_dir.mkdir(exist_ok=True)
        os.chdir(test_dir)
        
        # Multi-agent task configuration
        config = MultiAgentTaskConfiguration(
            description="Create a todo management system",
            max_workers=2,
            max_cost=5.0,
            supervisor_model="o3",
            worker_model="moonshot/kimi-k2-0711-preview"
        )
        
        # Execute task
        print("📋 Executing task: Create a todo management system")
        result = await coder.execute_task(
            "Create a comprehensive todo management system with the following features: task creation, editing, deletion, marking as complete, priority levels, due dates, and a web interface. Include database storage and API endpoints.",
            config=config
        )
        
        # Print results
        print(f"✅ Success: {result.success}")
        print(f"💰 Cost: ${result.cost:.4f}")
        print(f"🔄 Iterations: {result.iterations}")
        if result.error:
            print(f"❌ Error: {result.error}")
        
        print("📄 Content preview:")
        print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
        
        return result.success
        
    except Exception as e:
        print(f"❌ Multi-agent test failed: {e}")
        return False
    finally:
        os.chdir("..")

async def test_document_workflow():
    """Test document creation workflow."""
    print("\n📄 Testing Document Workflow")
    print("=" * 50)
    
    try:
        from equitrcoder.core.document_workflow import DocumentWorkflowManager
        
        # Create test directory
        test_dir = Path("./test_docs")
        test_dir.mkdir(exist_ok=True)
        os.chdir(test_dir)
        
        # Create document manager
        doc_manager = DocumentWorkflowManager(model="moonshot/kimi-k2-0711-preview")
        
        # Test document creation
        result = await doc_manager.create_documents_programmatic(
            "Create a simple weather app with API integration",
            project_path=".",
            task_name="weather_app"
        )
        
        print(f"✅ Document creation success: {result.success}")
        if result.success:
            print(f"📄 Requirements: {result.requirements_path}")
            print(f"🏗️ Design: {result.design_path}")
            print(f"📋 Todos: {result.todos_path}")
            print(f"🎯 Task name: {result.task_name}")
        else:
            print(f"❌ Error: {result.error}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Document workflow test failed: {e}")
        return False
    finally:
        os.chdir("..")

async def main():
    """Run all tests."""
    print("🧪 EQUITR Coder System Tests")
    print("=" * 60)
    
    # Check API keys
    moonshot_key = os.getenv("MOONSHOT_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"🔑 MOONSHOT_API_KEY: {'✅ Set' if moonshot_key else '❌ Missing'}")
    print(f"🔑 OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")
    
    if not moonshot_key or not openai_key:
        print("⚠️ Missing API keys. Please set MOONSHOT_API_KEY and OPENAI_API_KEY environment variables.")
        return
    
    # Run tests
    results = []
    
    # Test document workflow first
    doc_result = await test_document_workflow()
    results.append(("Document Workflow", doc_result))
    
    # Test single agent
    single_result = await test_single_agent()
    results.append(("Single Agent", single_result))
    
    # Test multi-agent
    multi_result = await test_multi_agent()
    results.append(("Multi-Agent", multi_result))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())