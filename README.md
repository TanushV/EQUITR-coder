# equitrcoder

**Modular AI coding assistant supporting single and multi-agent workflows**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

equitrcoder provides a clean, modular architecture for AI-powered coding assistance that scales from simple single-agent tasks to complex multi-agent coordination. Built from the ground up to be secure, cost-conscious, and highly extensible.

## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install -e .

# Or for development
pip install -e .[dev]
```

### Basic Usage

#### Single Agent (Simple Tasks)

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator

async def main():
    # Create a base agent with cost and iteration limits
    agent = BaseAgent(max_cost=1.0, max_iterations=10)
    
    # Create orchestrator
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Execute a task
    result = await orchestrator.execute_task("Analyze the project structure")
    
    if result["success"]:
        print(f"✅ Task completed!")
        print(f"💰 Cost: ${result['cost']:.4f}")
        print(f"🔄 Iterations: {result['iterations']}")
        print(f"📝 Session: {result['session_id']}")
    else:
        print(f"❌ Task failed: {result['error']}")

asyncio.run(main())
```

#### Multi-Agent (Complex Coordination)

```python
import asyncio
from equitrcoder import MultiAgentOrchestrator, WorkerConfig

async def main():
    # Create multi-agent orchestrator
    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=3,
        global_cost_limit=5.0
    )
    
    # Create specialized workers with restricted access
    frontend_config = WorkerConfig(
        worker_id="frontend_dev",
        scope_paths=["src/frontend/", "public/"],
        allowed_tools=["read_file", "edit_file", "run_cmd"],
        max_cost=2.0
    )
    
    backend_config = WorkerConfig(
        worker_id="backend_dev", 
        scope_paths=["src/backend/", "api/"],
        allowed_tools=["read_file", "edit_file", "run_cmd", "git_commit"],
        max_cost=2.0
    )
    
    # Register workers
    frontend_worker = orchestrator.create_worker(frontend_config)
    backend_worker = orchestrator.create_worker(backend_config)
    
    # Execute parallel tasks
    tasks = [
        {
            "task_id": "ui_update",
            "worker_id": "frontend_dev",
            "task_description": "Update the user interface components",
            "context": {"priority": "high"}
        },
        {
            "task_id": "api_fix",
            "worker_id": "backend_dev", 
            "task_description": "Fix the authentication API endpoint",
            "context": {"priority": "critical"}
        }
    ]
    
    # Execute tasks in parallel
    results = await orchestrator.execute_parallel_tasks(tasks)
    
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.worker_id}: {result.task_id}")
        print(f"   Time: {result.execution_time:.2f}s, Cost: ${result.cost:.4f}")

asyncio.run(main())
```

### Command Line Interface

```bash
# Single agent mode
equitrcoder single "Add error handling to the login function"

# Multi-agent mode with 3 workers
equitrcoder multi "Implement user authentication system" --workers 3 --max-cost 5.0

# Interactive TUI (if installed with [tui])
equitrcoder tui --mode single

# Start API server (if installed with [api])
equitrcoder api --host 0.0.0.0 --port 8000

# List available tools
equitrcoder tools --list

# Discover new tools
equitrcoder tools --discover
```

## 🏗️ Architecture

equitrcoder uses a layered, modular architecture:

```
┌─────────────────────────────────────────┐
│            CLI & API Layer              │
├─────────────────────────────────────────┤
│          Orchestration Layer            │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │ SingleAgent     │ │ MultiAgent      ││
│  │ Orchestrator    │ │ Orchestrator    ││
│  └─────────────────┘ └─────────────────┘│
├─────────────────────────────────────────┤
│             Agent Layer                 │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │   BaseAgent     │ │  WorkerAgent    ││
│  │  (Core Logic)   │ │ (Restricted)    ││
│  └─────────────────┘ └─────────────────┘│
├─────────────────────────────────────────┤
│    Tools & Utils Layer                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ File │ │ Git  │ │Shell │ │ Ask  │   │
│  │Tools │ │Tools │ │Tools │ │Super │   │
│  └──────┘ └──────┘ └──────┘ └──────┘   │
└─────────────────────────────────────────┘
```

### Core Components

#### Agents
- **BaseAgent**: Core functionality (messaging, tools, cost tracking, session management)
- **WorkerAgent**: Adds restricted file system access and tool whitelisting for security

#### Orchestrators
- **SingleAgentOrchestrator**: Simple wrapper for single-agent tasks with session management
- **MultiAgentOrchestrator**: Advanced coordination with parallel execution and supervisor oversight

#### Security Features
- **RestrictedFileSystem**: Path-based access control with traversal protection
- **Tool Whitelisting**: Fine-grained permission control per worker
- **Cost Limits**: Per-agent and global cost tracking and limits
- **Session Isolation**: Separate contexts for different workflows

## 🔧 Tool System

equitrcoder has an extensible plugin architecture for tools:

### Built-in Tools

```python
# File operations (with security restrictions for WorkerAgent)
await worker.call_tool("read_file", file_path="src/main.py")
await worker.call_tool("edit_file", file_path="src/main.py", content="new content")

# Git operations
await worker.call_tool("git_commit", message="Fix authentication bug")

# Shell commands
await worker.call_tool("run_cmd", cmd="pytest tests/")

# Supervisor consultation (multi-agent only)
await worker.call_tool("ask_supervisor", 
                      question="Should I refactor this function?",
                      context_files=["src/auth.py"])
```

### Custom Tools

```python
from equitrcoder.tools.base import Tool, ToolResult
from pydantic import BaseModel, Field

class MyCustomArgs(BaseModel):
    input_text: str = Field(..., description="Text to process")

class MyCustomTool(Tool):
    def get_name(self) -> str:
        return "my_custom_tool"
    
    def get_description(self) -> str:
        return "Does something useful with text"
    
    def get_args_schema(self):
        return MyCustomArgs
    
    async def run(self, input_text: str) -> ToolResult:
        # Your tool logic here
        result = input_text.upper()
        return ToolResult(success=True, data=result)

# Add to agent
agent.add_tool(MyCustomTool())
```

## 📊 Session Management

equitrcoder provides persistent session management:

```python
from equitrcoder.core.session import SessionManagerV2

# Create session manager
session_manager = SessionManagerV2()

# Create or resume session
session = session_manager.create_session("my-project-session")

# Use with orchestrator
orchestrator = SingleAgentOrchestrator(agent, session_manager=session_manager)
result = await orchestrator.execute_task("Continue previous work", 
                                        session_id="my-project-session")
```

Sessions automatically track:
- Conversation history
- Cost accumulation
- Task completion status
- Iteration counts
- Metadata and context

## 🔒 Security & Restrictions

### WorkerAgent Security

```python
# Create a restricted worker
worker = WorkerAgent(
    worker_id="secure_worker",
    scope_paths=["src/", "tests/"],        # Can only access these paths
    allowed_tools=["read_file", "edit_file"], # Can only use these tools
    project_root="/safe/project/path",      # Root boundary
    max_cost=1.0,                          # Cost limit
    max_iterations=20                      # Iteration limit
)

# Security features:
print(worker.can_access_file("src/main.py"))     # True
print(worker.can_access_file("../secrets.txt"))  # False
print(worker.can_use_tool("read_file"))          # True  
print(worker.can_use_tool("shell"))              # False
```

### Multi-Agent Isolation

```python
# Workers are isolated from each other
orchestrator = MultiAgentOrchestrator()

worker1 = orchestrator.create_worker(WorkerConfig(
    worker_id="frontend",
    scope_paths=["frontend/"],
    allowed_tools=["read_file", "edit_file"]
))

worker2 = orchestrator.create_worker(WorkerConfig(
    worker_id="backend", 
    scope_paths=["backend/"],
    allowed_tools=["read_file", "edit_file", "run_cmd"]
))

# worker1 cannot access backend/ files
# worker2 cannot access frontend/ files
# Each has separate cost and iteration limits
```

## 📖 Examples

Check out the `equitrcoder/examples/` directory for:

- **Basic Usage**: Simple single-agent examples
- **Multi-Agent Workflows**: Complex coordination patterns
- **Custom Tools**: How to create and integrate custom tools
- **Security Patterns**: Safe multi-agent configurations
- **CLI Usage**: Command-line interface examples

## 🧪 Testing

```bash
# Run the basic functionality test
python test_basic_functionality.py

# Install development dependencies
pip install -e .[dev]

# Run full test suite (when available)
pytest

# Type checking
mypy equitrcoder

# Code formatting
black equitrcoder
isort equitrcoder
```

## 🔧 Configuration

### Environment Variables

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export EQUITRCODER_MODEL="gpt-4"
export EQUITRCODER_MAX_COST="5.0"
```

### Configuration Files

```yaml
# equitrcoder/config/default.yaml
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

tools:
  discovery_paths:
    - "equitrcoder.tools.builtin"
    - "equitrcoder.tools.custom"
```

## 🤝 Contributing

We welcome contributions! The codebase is designed to be modular and extensible:

### Development Setup

```bash
git clone <repository-url>
cd equitrcoder
pip install -e .[dev]
```

### Adding New Tools

1. Create your tool class inheriting from `Tool`
2. Implement required methods: `get_name()`, `get_description()`, `get_args_schema()`, `run()`
3. Add to `equitrcoder/tools/custom/`
4. Tools are auto-discovered on startup

### Adding New Agent Types

1. Inherit from `BaseAgent` 
2. Override methods as needed
3. Add any specialized functionality
4. Create corresponding orchestrator if needed

## 📝 Migration from Previous Versions

If migrating from the old `EQUITR_coder` or `src` packages, see `MIGRATION.md` for detailed instructions. Backward compatibility shims are provided but will be removed in v2.0.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built on excellent libraries like LiteLLM, Pydantic, and asyncio
- Inspired by modern multi-agent frameworks and secure coding practices
- Thanks to all contributors and the open source community

---

**equitrcoder** - Modular, secure, and scalable AI coding assistance 🚀 