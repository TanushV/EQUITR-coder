#!/usr/bin/env python3
"""
Example: Multi-Agent Mode with Parallel Phases and Automatic Git Checkpoints

This example demonstrates how the new Task Group System works with multiple agents
executing task groups in parallel phases based on dependencies, with automatic
git commits after each successful phase completion.
"""

import asyncio
from equitrcoder.modes.multi_agent_mode import run_multi_agent_parallel, run_multi_agent_sequential

async def parallel_phases_example():
    """
    Example showing parallel phase execution with automatic git commits.
    """
    print("🚀 Starting Multi-Agent Parallel Phases Example")
    print("=" * 55)
    
    result = await run_multi_agent_parallel(
        task_description="""
        Build a complete web application with:
        - PostgreSQL database with user and product tables
        - Flask REST API with JWT authentication
        - React frontend with modern UI components
        - Redis caching layer
        - Comprehensive test suite
        - API documentation with Swagger
        """,
        num_agents=4,
        agent_model="moonshot/kimi-k2-0711-preview",
        orchestrator_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        auto_commit=True,  # Enable automatic git commits after each phase
        max_cost_per_agent=3.0,
        max_iterations_per_agent=25
    )
    
    if result["success"]:
        print("\n✅ Multi-agent web application completed!")
        print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
        print(f"📊 Total phases: {result.get('total_phases', 0)}")
        print("\n📋 Expected Phase Execution Flow:")
        print("Phase 1: [database_setup] (1 agent)")
        print("  └── database specialist sets up PostgreSQL schema")
        print("Phase 2: [backend_api, caching_layer] (2 agents in parallel)")
        print("  ├── backend specialist builds Flask API")
        print("  └── backend specialist sets up Redis caching")
        print("Phase 3: [frontend_ui, testing_suite, documentation] (3 agents in parallel)")
        print("  ├── frontend specialist builds React components")
        print("  ├── testing specialist creates comprehensive tests")
        print("  └── documentation specialist creates API docs")
        print("\n🤖 Each phase completion triggered an automatic git commit!")
        print("🔍 Check 'git log --oneline' to see phase-based commits:")
        print("   chore(orchestration): Complete Phase 3")
        print("   chore(orchestration): Complete Phase 2") 
        print("   chore(orchestration): Complete Phase 1")
    else:
        print(f"\n❌ Multi-agent task failed: {result.get('error')}")
        print(f"Failed at stage: {result.get('stage', 'unknown')}")

async def specialized_agents_example():
    """
    Example showing how agents are specialized by task group type.
    """
    print("\n🎭 Starting Specialized Agents Example")
    print("=" * 50)
    
    result = await run_multi_agent_parallel(
        task_description="""
        Create a microservices architecture with:
        - User service with MongoDB
        - Product service with PostgreSQL  
        - API Gateway with rate limiting
        - Frontend dashboard with charts
        - Docker containerization
        - Kubernetes deployment configs
        - Monitoring with Prometheus
        - Unit and integration tests
        """,
        num_agents=6,  # More agents for complex architecture
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,
        max_cost_per_agent=2.5
    )
    
    if result["success"]:
        print("\n✅ Microservices architecture completed!")
        print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
        print("\n🎭 Agent Specialization by Task Group:")
        print("• database_agent_user_service (database specialist)")
        print("• database_agent_product_service (database specialist)")
        print("• backend_agent_api_gateway (backend specialist)")
        print("• frontend_agent_dashboard (frontend specialist)")
        print("• infrastructure_agent_docker (infrastructure specialist)")
        print("• infrastructure_agent_kubernetes (infrastructure specialist)")
        print("• monitoring_agent_prometheus (monitoring specialist)")
        print("• testing_agent_test_suite (testing specialist)")
        print("\n📊 Parallel Phase Benefits:")
        print("• Independent groups executed simultaneously")
        print("• Specialized agents focused on their expertise")
        print("• Automatic coordination through dependencies")
        print("• Professional git history with phase commits")
    else:
        print(f"\n❌ Specialized agents task failed: {result.get('error')}")

async def sequential_vs_parallel_comparison():
    """
    Example comparing sequential vs parallel multi-agent execution.
    """
    print("\n⚖️ Starting Sequential vs Parallel Comparison")
    print("=" * 55)
    
    task_description = """
    Build a simple e-commerce API with:
    - SQLite database with products table
    - Flask API with CRUD operations
    - Basic authentication system
    - Unit tests for all endpoints
    """
    
    print("🔄 Running Sequential Multi-Agent Mode...")
    sequential_result = await run_multi_agent_sequential(
        task_description=task_description,
        num_agents=3,
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,
        max_cost_per_agent=2.0
    )
    
    print("⚡ Running Parallel Multi-Agent Mode...")
    parallel_result = await run_multi_agent_parallel(
        task_description=task_description,
        num_agents=3,
        agent_model="moonshot/kimi-k2-0711-preview", 
        auto_commit=True,
        max_cost_per_agent=2.0
    )
    
    print("\n📊 Comparison Results:")
    print(f"Sequential - Success: {sequential_result.get('success')}, Cost: ${sequential_result.get('cost', 0):.4f}")
    print(f"Parallel   - Success: {parallel_result.get('success')}, Cost: ${parallel_result.get('cost', 0):.4f}")
    
    print("\n🎯 Key Differences:")
    print("Sequential Mode:")
    print("  • Groups execute one at a time across all agents")
    print("  • More coordinated but potentially slower")
    print("  • Better for tasks requiring tight coordination")
    
    print("Parallel Mode:")
    print("  • Independent groups execute simultaneously")
    print("  • Faster execution for complex projects")
    print("  • Better for tasks with clear separation of concerns")

async def monitoring_multi_agent_example():
    """
    Example showing how to monitor multi-agent task group progress.
    """
    print("\n📊 Starting Multi-Agent Monitoring Example")
    print("=" * 55)
    
    def on_phase_start(phase_num, groups):
        print(f"\n🚀 Starting Phase {phase_num} with {len(groups)} task groups:")
        for group in groups:
            print(f"   • {group.get('group_id')} ({group.get('specialization')})")
    
    def on_phase_complete(phase_num, groups):
        print(f"\n✅ Phase {phase_num} completed!")
        print(f"📝 Automatic git commit created for phase")
        for group in groups:
            print(f"   ✓ {group.get('group_id')} finished")
    
    def on_agent_message(agent_id, message):
        print(f"🤖 {agent_id}: {message[:100]}...")
    
    result = await run_multi_agent_parallel(
        task_description="Create a blog platform with user management, post creation, and comment system",
        num_agents=3,
        agent_model="moonshot/kimi-k2-0711-preview",
        auto_commit=True,
        callbacks={
            'on_phase_start': on_phase_start,
            'on_phase_complete': on_phase_complete,
            'on_agent_message': on_agent_message
        },
        max_cost_per_agent=3.0
    )
    
    if result["success"]:
        print(f"\n✅ Monitored multi-agent task completed!")
        print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
        print(f"📊 Phases executed: {result.get('total_phases', 0)}")
    else:
        print(f"\n❌ Monitored task failed: {result.get('error')}")

async def main():
    """
    Run all multi-agent task group examples.
    """
    print("🎯 EQUITR Coder v2.0.0 - Multi-Agent Task Group Examples")
    print("=" * 65)
    print("This demonstrates parallel phase execution with specialized agents")
    print("and automatic git checkpoints after each phase completion.")
    print("=" * 65)
    
    try:
        # Run parallel phases example
        await parallel_phases_example()
        
        # Wait between examples
        await asyncio.sleep(2)
        
        # Run specialized agents example
        await specialized_agents_example()
        
        # Wait between examples
        await asyncio.sleep(2)
        
        # Run comparison example
        await sequential_vs_parallel_comparison()
        
        # Wait between examples
        await asyncio.sleep(2)
        
        # Run monitoring example
        await monitoring_multi_agent_example()
        
        print("\n🎉 All multi-agent examples completed!")
        print("\n📚 Key Multi-Agent Benefits:")
        print("• Parallel execution of independent task groups")
        print("• Specialized agents for different types of work")
        print("• Automatic phase-based git commits")
        print("• Scalable architecture for complex projects")
        print("• Built-in agent communication and coordination")
        
        print("\n🔍 Advanced Features:")
        print("• Agent specialization based on task group type")
        print("• Dependency-aware phase scheduling")
        print("• Professional git history with phase commits")
        print("• Real-time monitoring and callbacks")
        print("• Cost management per agent")
        
        print("\n🚀 Next Steps:")
        print("• Examine the git log to see phase-based commit history")
        print("• Check .EQUITR_todos_*.json for the structured plans")
        print("• Try the programmatic interface for production use")
        
    except Exception as e:
        print(f"\n💥 Multi-agent examples failed with error: {e}")
        print("Make sure you have:")
        print("• API keys set in .env file")
        print("• EQUITR Coder v2.0.0 installed")
        print("• Git initialized in your project directory")
        print("• Sufficient API quota for multiple agents")

if __name__ == "__main__":
    asyncio.run(main())