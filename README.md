# equitrcoder

**Modular AI coding assistant supporting single and multi-agent workflows**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

equitrcoder provides a clean, modular architecture for AI-powered coding assistance that scales from simple single-agent tasks to complex multi-agent coordination.

## 🚀 Quick Start

### Installation

```bash
pip install equitrcoder
```

For additional features:
```bash
pip install equitrcoder[api]  # API server support
pip install equitrcoder[tui]  # Terminal UI
pip install equitrcoder[all]  # Everything
```

### Single Agent Usage

```python
import asyncio
from equitrcoder import create_single_orchestrator

async def main():
    # Create a single agent orchestrator
    orchestrator = create_single_orchestrator(max_cost=1.0)
    
    # Execute a task
    result = await orchestrator.execute_task("Fix the bug in main.py")
    
    if result["success"]:
        print(f"✅ Task completed! Cost: ${result['cost']:.4f}")
    else:
        print(f"❌ Task failed: {result['error']}")

asyncio.run(main())
```

### Multi-Agent Usage

```python
import asyncio
from equitrcoder import create_multi_orchestrator, WorkerConfig

async def main():
    # Create multi-agent orchestrator
    orchestrator = create_multi_orchestrator(
        max_concurrent_workers=3,
        global_cost_limit=5.0
    )
    
    # Create specialized workers
    frontend_worker = WorkerConfig(
        worker_id="frontend_dev",
        scope_paths=["src/frontend/", "public/"],
        allowed_tools=["read_file", "edit_file", "run_cmd"]
    )
    
    backend_worker = WorkerConfig(
        worker_id="backend_dev", 
        scope_paths=["src/backend/", "api/"],
        allowed_tools=["read_file", "edit_file", "run_cmd", "git_commit"]
    )
    
    # Register workers
    orchestrator.create_worker(frontend_worker)
    orchestrator.create_worker(backend_worker)
    
    # Execute coordinated tasks
    tasks = [
        {
            "task_id": "ui_update",
            "worker_id": "frontend_dev",
            "task_description": "Update the user interface components"
        },
        {
            "task_id": "api_fix",
            "worker_id": "backend_dev", 
            "task_description": "Fix the authentication API endpoint"
        }
    ]
    
    results = await orchestrator.execute_parallel_tasks(tasks)
    
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.worker_id}: {result.task_id}")

asyncio.run(main())
```

### Command Line Interface

```bash
# Single agent mode
equitrcoder single "Add error handling to the login function"

# Multi-agent mode  
equitrcoder multi "Implement user authentication system" --workers 3

# Interactive TUI
equitrcoder tui --mode single

# Start API server
equitrcoder api --host 0.0.0.0 --port 8000

# List available tools
equitrcoder tools --list
```

## 🏗️ Architecture

equitrcoder uses a modular architecture that separates concerns and enables flexible composition:

### Core Components

- **BaseAgent**: Common functionality for all agents (messaging, tools, cost tracking)
- **WorkerAgent**: Specialized agent with restricted file system access for security
- **SingleAgentOrchestrator**: Simple orchestration for single-agent tasks
- **MultiAgentOrchestrator**: Advanced orchestration with supervisor oversight

### Key Features

- **🔒 Security**: Restricted file system access for worker agents
- **💰 Cost Control**: Built-in cost tracking and limits
- **🔧 Tool System**: Extensible plugin architecture for tools
- **📊 Session Management**: Persistent sessions with conversation history
- **🎯 Task Coordination**: Intelligent multi-agent task distribution
- **📈 Monitoring**: Comprehensive callbacks and status tracking

## 📖 Documentation

### Agent Types

#### BaseAgent
The foundation class providing:
- Message pool management
- Tool registry and execution
- Cost tracking and limits
- Iteration counting
- Callback system for monitoring

#### WorkerAgent
Extends BaseAgent with:
- Restricted file system access
- Tool whitelisting
- Scope-based permissions
- Enhanced security for multi-agent scenarios

### Orchestrators

#### SingleAgentOrchestrator
- Wraps a BaseAgent for simple task execution
- Session management
- Cost and iteration limits
- Progress monitoring

#### MultiAgentOrchestrator
- Coordinates multiple WorkerAgents
- Parallel task execution with concurrency control
- Global cost and iteration limits
- Supervisor integration for complex coordination

### Tool System

Tools are the primary way agents interact with the environment:

```python
from equitrcoder.tools.base import Tool, ToolResult

class CustomTool(Tool):
    def get_name(self) -> str:
        return "my_custom_tool"
    
    def get_description(self) -> str:
        return "Does something useful"
    
    async def run(self, **kwargs) -> ToolResult:
        # Tool implementation
        return ToolResult(success=True, data="Result")

# Add to agent
agent.add_tool(CustomTool())
```

Built-in tools include:
- File operations (read, write, search)
- Git operations (status, commit, diff)
- Shell command execution
- Supervisor consultation (for multi-agent)

## 🔧 Configuration

### Environment Variables

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export EQUITRCODER_MODEL="gpt-4"
export EQUITRCODER_MAX_COST="10.0"
```

### Configuration Files

equitrcoder supports YAML configuration files:

```yaml
# ~/.equitrcoder/config.yaml
llm:
  model: "gpt-4"
  max_tokens: 4000
  temperature: 0.1

orchestrator:
  max_iterations: 50
  max_cost: 5.0
  use_multi_agent: false

session:
  session_dir: "~/.equitrcoder/sessions"
  max_context: 8000
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install equitrcoder[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=equitrcoder

# Type checking
mypy equitrcoder

# Code formatting
black equitrcoder
isort equitrcoder
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/equitr/equitrcoder.git
cd equitrcoder
pip install -e .[dev]
```

### Code Quality

We use:
- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing

## 📝 Migration Guide

### From EQUITR_coder

```python
# Old
from EQUITR_coder.core.orchestrator import AgentOrchestrator

# New  
from equitrcoder import create_single_orchestrator
orchestrator = create_single_orchestrator()
```

### From src Package

```python
# Old
from src.agents.worker_agent import WorkerAgent

# New
from equitrcoder import create_worker_agent
worker = create_worker_agent("worker1", ["src/"], ["read_file"])
```

Backward compatibility shims are provided but will be removed in v2.0.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of excellent libraries like LiteLLM, FastAPI, and Textual
- Inspired by multi-agent frameworks and modern AI development practices
- Thanks to all contributors and the open source community

---

**equitrcoder** - Making AI coding assistance modular, secure, and scalable. 