# equitrcoder Quickstart Guide

Get up and running with equitrcoder in minutes! This guide will walk you through installation, basic usage, and your first AI coding tasks.

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- An OpenAI API key OR Anthropic API key

### Install equitrcoder

```bash
# Clone and install
git clone <repository-url>
cd equitrcoder
pip install -e .

# For development with additional features
pip install -e .[dev]
```

### Set up API Keys

```bash
# Option 1: OpenAI
export OPENAI_API_KEY="sk-your-openai-key-here"

# Option 2: Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"

# Optional: Set default preferences
export EQUITRCODER_MODEL="gpt-4"
export EQUITRCODER_MAX_COST="2.0"
```

## 🎯 Your First Task

### Option 1: Command Line (Easiest)

```bash
# Single agent task
equitrcoder single "Analyze the structure of this project and suggest improvements"

# Multi-agent task with 2 workers
equitrcoder multi "Review the codebase for security issues" --workers 2 --max-cost 3.0
```

### Option 2: Python Code (More Control)

Create a file called `my_first_task.py`:

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator

async def main():
    # Create an agent with reasonable limits
    agent = BaseAgent(
        max_cost=1.0,        # Spend up to $1.00
        max_iterations=10    # Maximum 10 back-and-forth exchanges
    )
    
    # Create orchestrator
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Execute your first task
    result = await orchestrator.execute_task(
        "Look at the files in this directory and tell me what this project does"
    )
    
    # Check results
    if result["success"]:
        print("🎉 Task completed successfully!")
        print(f"💰 Cost: ${result['cost']:.4f}")
        print(f"🔄 Iterations: {result['iterations']}")
        print(f"📝 Session ID: {result['session_id']}")
    else:
        print(f"❌ Task failed: {result['error']}")

# Run it
if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_first_task.py
```

## 🔧 Basic Examples

### Example 1: Code Analysis

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator

async def analyze_code():
    agent = BaseAgent(max_cost=0.5, max_iterations=5)
    orchestrator = SingleAgentOrchestrator(agent)
    
    result = await orchestrator.execute_task(
        "Find all Python files in this project and identify potential bugs or improvements"
    )
    
    if result["success"]:
        print("✅ Analysis complete!")
        print(f"Cost: ${result['cost']:.4f}")
    else:
        print(f"❌ Analysis failed: {result['error']}")

asyncio.run(analyze_code())
```

### Example 2: Multi-Agent Workflow

```python
import asyncio
from equitrcoder import MultiAgentOrchestrator, WorkerConfig

async def multi_agent_workflow():
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=2,
        global_cost_limit=2.0
    )
    
    # Create specialized workers
    analyzer_config = WorkerConfig(
        worker_id="analyzer",
        scope_paths=["equitrcoder/"],
        allowed_tools=["read_file", "search_files"],
        max_cost=1.0
    )
    
    documenter_config = WorkerConfig(
        worker_id="documenter", 
        scope_paths=["equitrcoder/docs/", "README.md"],
        allowed_tools=["read_file", "edit_file"],
        max_cost=1.0
    )
    
    # Register workers
    analyzer = orchestrator.create_worker(analyzer_config)
    documenter = orchestrator.create_worker(documenter_config)
    
    # Define parallel tasks
    tasks = [
        {
            "task_id": "code_review",
            "worker_id": "analyzer",
            "task_description": "Review the core modules for code quality"
        },
        {
            "task_id": "update_docs",
            "worker_id": "documenter",
            "task_description": "Update documentation to reflect current features"
        }
    ]
    
    # Execute in parallel
    results = await orchestrator.execute_parallel_tasks(tasks)
    
    # Show results
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.worker_id}: {result.task_id} (${result.cost:.4f})")

asyncio.run(multi_agent_workflow())
```

### Example 3: With Progress Monitoring

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator

async def monitored_task():
    agent = BaseAgent(max_cost=1.0, max_iterations=8)
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Set up monitoring
    def on_iteration(iteration, status):
        cost = status.get('current_cost', 0)
        print(f"🔄 Iteration {iteration}: Cost ${cost:.4f}")
    
    def on_completion(results, final_status):
        final_cost = final_status.get('current_cost', 0)
        print(f"🏁 Completed! Final cost: ${final_cost:.4f}")
    
    orchestrator.set_callbacks(
        on_iteration=on_iteration,
        on_completion=on_completion
    )
    
    # Execute with monitoring
    result = await orchestrator.execute_task(
        "Create a simple Python script that demonstrates the main features of this project"
    )
    
    return result

asyncio.run(monitored_task())
```

## 🔒 Security Example

```python
import asyncio
from equitrcoder import WorkerAgent

async def secure_worker_example():
    # Create a restricted worker
    secure_worker = WorkerAgent(
        worker_id="secure_task",
        scope_paths=["equitrcoder/examples/"],  # Only examples directory
        allowed_tools=["read_file"],            # Read-only access
        max_cost=0.3,                          # Low cost limit
        max_iterations=5                       # Few iterations
    )
    
    # Test security restrictions
    print("🔒 Security Tests:")
    print(f"Can access examples/README.md: {secure_worker.can_access_file('equitrcoder/examples/README.md')}")
    print(f"Can access ../core/config.py: {secure_worker.can_access_file('../core/config.py')}")
    print(f"Can use read_file: {secure_worker.can_use_tool('read_file')}")
    print(f"Can use edit_file: {secure_worker.can_use_tool('edit_file')}")
    
    # Get scope statistics
    stats = secure_worker.get_scope_stats()
    print(f"\n📊 Worker Scope:")
    print(f"Allowed paths: {stats['scope_paths']}")
    print(f"Allowed tools: {stats['allowed_tools']}")

asyncio.run(secure_worker_example())
```

## 📊 Session Management

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator
from equitrcoder.core.session import SessionManagerV2

async def session_example():
    # Create session manager
    session_manager = SessionManagerV2()
    
    # Create agent and orchestrator
    agent = BaseAgent(max_cost=1.5, max_iterations=12)
    orchestrator = SingleAgentOrchestrator(agent, session_manager=session_manager)
    
    # First task in a named session
    print("🎯 Starting first task...")
    result1 = await orchestrator.execute_task(
        "Analyze the project structure and create a summary",
        session_id="project-analysis"
    )
    
    if result1["success"]:
        print(f"✅ First task done! Session: {result1['session_id']}")
    
    # Continue in the same session
    print("\n🎯 Continuing in same session...")
    result2 = await orchestrator.execute_task(
        "Based on the previous analysis, suggest 3 specific improvements",
        session_id="project-analysis"  # Same session
    )
    
    if result2["success"]:
        print(f"✅ Second task done! Session: {result2['session_id']}")
    
    # Check session statistics
    session = session_manager.load_session("project-analysis")
    if session:
        print(f"\n📈 Session Statistics:")
        print(f"Total cost: ${session.cost:.4f}")
        print(f"Total iterations: {session.iteration_count}")
        print(f"Messages in conversation: {len(session.messages)}")

asyncio.run(session_example())
```

## 🛠️ CLI Commands Cheat Sheet

```bash
# Single Agent Commands
equitrcoder single "Your task here"
equitrcoder single "Fix bugs in auth.py" --max-cost 1.0 --model gpt-4
equitrcoder single "Continue previous work" --session-id "my-session"

# Multi-Agent Commands  
equitrcoder multi "Build a web API" --workers 3 --max-cost 5.0
equitrcoder multi "Security audit" --workers 2 --enable-supervisor

# Interactive Mode (if TUI available)
equitrcoder tui --mode single
equitrcoder tui --mode multi --workers 2

# Tool Management
equitrcoder tools --list                    # Show available tools
equitrcoder tools --discover               # Find new tools
equitrcoder tools --test read_file --args '{"file_path": "README.md"}'

# API Server (if API available)
equitrcoder api --port 8000                # Start API server
```

## ⚙️ Configuration

### Quick Configuration

Create `~/.equitrcoder/config.yaml`:

```yaml
llm:
  model: "gpt-4"
  max_tokens: 4000
  temperature: 0.1

orchestrator:
  max_iterations: 25
  max_cost: 5.0

session:
  session_dir: "~/.equitrcoder/sessions"
  auto_save: true

tools:
  discovery_paths:
    - "equitrcoder.tools.builtin"
    - "equitrcoder.tools.custom"
```

### Environment Variables

```bash
# Add to your ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="your-key-here"
export EQUITRCODER_MODEL="gpt-4"
export EQUITRCODER_MAX_COST="3.0"
export EQUITRCODER_MAX_ITERATIONS="20"
```

## 🚨 Common Issues & Solutions

### Issue: "No API key found"
```bash
# Solution: Set your API key
export OPENAI_API_KEY="sk-your-key-here"
# OR
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Issue: "Cost limit exceeded"
```python
# Solution: Increase the limit or use a cheaper model
agent = BaseAgent(max_cost=2.0, model="gpt-3.5-turbo")
```

### Issue: "Permission denied" for file access
```python
# Solution: Check if worker can access the file
print(worker.can_access_file("path/to/file"))
# Add path to worker's scope_paths if needed
```

### Issue: "Tool not found"
```python
# Solution: Check available tools
tools = agent.get_available_tools()
print([tool.get_name() for tool in tools])
```

## 🧪 Test Your Installation

Run the basic functionality test:

```bash
python test_basic_functionality.py
```

This will test:
- ✅ Agent creation
- ✅ Tool loading  
- ✅ Session management
- ✅ Basic orchestration
- ✅ Security restrictions

## 🎓 Next Steps

Now that you have equitrcoder working:

1. **Try the Examples**: Check out `equitrcoder/examples/` for more complex scenarios
2. **Read the Usage Guide**: `equitrcoder/docs/USAGE_GUIDE.md` has comprehensive documentation
3. **Create Custom Tools**: Learn to extend equitrcoder with your own tools
4. **Explore Multi-Agent**: Try coordinating multiple AI agents for complex tasks
5. **Configure for Your Workflow**: Customize settings in your config file

## 💡 Tips for Success

### Start Small
- Begin with simple tasks and low cost limits
- Gradually increase complexity as you learn the system

### Monitor Costs
- Always set `max_cost` limits
- Use cheaper models like `gpt-3.5-turbo` for experimentation

### Use Sessions
- Name your sessions descriptively
- Resume sessions to continue complex work

### Security First
- Use WorkerAgent with restricted scopes for untrusted tasks
- Always validate file paths and tool usage

### Experiment
- Try different combinations of workers and tasks
- Use the monitoring callbacks to understand what's happening

## 🆘 Getting Help

- **Examples**: `equitrcoder/examples/` directory
- **Documentation**: `equitrcoder/docs/` directory  
- **CLI Help**: `equitrcoder --help`
- **Test Suite**: `python test_basic_functionality.py`

## 🎉 Congratulations!

You're now ready to use equitrcoder for AI-powered coding assistance. The modular architecture lets you start simple with single agents and scale up to complex multi-agent workflows as your needs grow.

**Happy coding with AI! 🚀**