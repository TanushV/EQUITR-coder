# Migration Guide: EQUITR_coder + src → equitrcoder

This guide helps you migrate from the old dual-package structure (`EQUITR_coder` and `src`) to the new unified `equitrcoder` package.

## 🔄 Overview of Changes

### Package Structure
```
Old Structure:
├── EQUITR-coder/EQUITR_coder/  # Main package
├── src/                        # Additional features
└── [scattered files]

New Structure:
├── equitrcoder/                # Unified package
│   ├── agents/                 # BaseAgent, WorkerAgent
│   ├── orchestrators/          # Single & Multi orchestrators
│   ├── tools/                  # Plugin system
│   ├── core/                   # Session, config, etc.
│   └── cli/                    # Unified CLI
```

### Key Architectural Changes

1. **Modular Agent System**: BaseAgent provides common functionality, WorkerAgent adds restrictions
2. **Unified Orchestrators**: SingleAgentOrchestrator for simple tasks, MultiAgentOrchestrator for complex coordination
3. **Enhanced Tool System**: Cleaner plugin architecture with proper Tool base class
4. **Improved CLI**: Single `equitrcoder` command with subcommands
5. **Better Session Management**: Enhanced persistence and cost tracking

## 📦 Import Changes

### Core Components

```python
# OLD: EQUITR_coder imports
from EQUITR_coder.core.orchestrator import AgentOrchestrator
from EQUITR_coder.core.session import SessionManagerV2
from EQUITR_coder.tools.base import Tool

# NEW: equitrcoder imports
from equitrcoder import create_single_orchestrator, create_multi_orchestrator
from equitrcoder.core.session import SessionManagerV2
from equitrcoder.tools.base import Tool
```

### Agent System

```python
# OLD: src imports
from src.agents.worker_agent import WorkerAgent
from src.orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator

# NEW: equitrcoder imports  
from equitrcoder import WorkerAgent, MultiAgentOrchestrator
from equitrcoder.agents import BaseAgent
```

### Tools

```python
# OLD: EQUITR_coder tools
from EQUITR_coder.tools.builtin.ask_supervisor import AskSupervisor
from EQUITR_coder.tools.discovery import discover_tools

# NEW: equitrcoder tools
from equitrcoder.tools.builtin.ask_supervisor import AskSupervisor
from equitrcoder.tools.discovery import discover_tools
```

## 🔧 Code Migration Examples

### Single Agent Usage

#### Before (EQUITR_coder)
```python
from EQUITR_coder.core.orchestrator import AgentOrchestrator
from EQUITR_coder.core.config import Config

config = Config()
orchestrator = AgentOrchestrator(config)
result = orchestrator.run_task("Fix the bug")
```

#### After (equitrcoder)
```python
from equitrcoder import create_single_orchestrator

# Simple approach
orchestrator = create_single_orchestrator(max_cost=1.0)
result = await orchestrator.execute_task("Fix the bug")

# Or with more control
from equitrcoder import BaseAgent, SingleAgentOrchestrator
agent = BaseAgent(max_cost=1.0, max_iterations=10)
orchestrator = SingleAgentOrchestrator(agent)
result = await orchestrator.execute_task("Fix the bug")
```

### Multi-Agent Usage

#### Before (src)
```python
from src.orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
from src.agents.worker_agent import WorkerAgent

orchestrator = MultiAgentOrchestrator()
worker = WorkerAgent("worker1", ["src/"], ["read_file", "edit_file"])
orchestrator.workers["worker1"] = worker
result = await orchestrator.execute_task("task1", "worker1", "Fix bug")
```

#### After (equitrcoder)
```python
from equitrcoder import create_multi_orchestrator, WorkerConfig

orchestrator = create_multi_orchestrator(
    max_concurrent_workers=3,
    global_cost_limit=5.0
)

config = WorkerConfig(
    worker_id="worker1",
    scope_paths=["src/"],
    allowed_tools=["read_file", "edit_file"],
    max_cost=1.0
)

worker = orchestrator.create_worker(config)
result = await orchestrator.execute_task("task1", "worker1", "Fix bug")
```

### Tool Development

#### Before (EQUITR_coder)
```python
from EQUITR_coder.tools.base import Tool

class MyTool(Tool):
    def __init__(self):
        super().__init__()
    
    def get_name(self):
        return "my_tool"
    
    def run(self, **kwargs):
        return {"result": "done"}
```

#### After (equitrcoder)
```python
from equitrcoder.tools.base import Tool, ToolResult

class MyTool(Tool):
    def get_name(self) -> str:
        return "my_tool"
    
    def get_description(self) -> str:
        return "My custom tool"
    
    async def run(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data="done")
```

## 🖥️ CLI Migration

### Command Changes

```bash
# OLD: Multiple entry points
EQUITR-coder --task "Fix bug"
python -m src.cli.main_cli multi-agent

# NEW: Unified CLI
equitrcoder single "Fix bug"
equitrcoder multi "Coordinate tasks" --workers 3
equitrcoder tui --mode single
equitrcoder api --port 8000
```

### Configuration

#### Before
```yaml
# Multiple config files in different locations
EQUITR_coder/config/default.yaml
src/config/model_config.py
```

#### After
```yaml
# Single config location
~/.equitrcoder/config.yaml
llm:
  model: "gpt-4"
orchestrator:
  max_cost: 5.0
  use_multi_agent: false
```

## 🔒 Security Improvements

### Restricted File System

The new `WorkerAgent` has enhanced security with `RestrictedFileSystem`:

```python
# OLD: Basic path checking
worker = WorkerAgent("worker1", ["src/"], ["read_file"])
# Limited security controls

# NEW: Comprehensive restriction system
from equitrcoder.utils import RestrictedFileSystem

worker = WorkerAgent(
    worker_id="worker1",
    scope_paths=["src/", "tests/"],
    allowed_tools=["read_file", "edit_file"],
    project_root="."
)

# Built-in security features:
# - Path traversal protection
# - Tool whitelisting  
# - Scope validation
# - Access logging
```

## 📊 Session Management

### Enhanced Sessions

```python
# OLD: Basic session handling
from EQUITR_coder.core.session import SessionManagerV2
session_manager = SessionManagerV2()

# NEW: Rich session features
from equitrcoder.core.session import SessionManagerV2
session_manager = SessionManagerV2()

# Enhanced features:
# - Cost tracking per session
# - Task checklists
# - Automatic persistence
# - Session switching
# - Background saves
```

## 🧪 Testing Migration

### Test Structure

```python
# OLD: Scattered test approaches
import pytest
from EQUITR_coder.core.orchestrator import AgentOrchestrator

def test_orchestrator():
    orchestrator = AgentOrchestrator(config)
    # Test implementation

# NEW: Modular testing
import pytest
from equitrcoder import create_single_orchestrator, BaseAgent

@pytest.mark.asyncio
async def test_single_orchestrator():
    agent = BaseAgent(max_cost=0.1)
    orchestrator = create_single_orchestrator(agent=agent)
    
    result = await orchestrator.execute_task("test task")
    assert result["success"]

@pytest.mark.asyncio  
async def test_multi_orchestrator():
    from equitrcoder import create_multi_orchestrator, WorkerConfig
    
    orchestrator = create_multi_orchestrator()
    config = WorkerConfig("test_worker", ["."], ["read_file"])
    worker = orchestrator.create_worker(config)
    
    result = await orchestrator.execute_task("test", "test_worker", "task")
    assert result.success
```

## 🚀 Performance Improvements

### Async/Await Support

```python
# OLD: Mixed sync/async patterns
result = orchestrator.run_task("task")  # Sync
result = await orchestrator.async_run("task")  # Async

# NEW: Consistent async API
result = await orchestrator.execute_task("task")  # Always async
```

### Concurrent Execution

```python
# OLD: Sequential execution
for task in tasks:
    result = await orchestrator.execute_task(task)

# NEW: Parallel execution
results = await orchestrator.execute_parallel_tasks(tasks)
```

## 🛠️ Breaking Changes

### Required Updates

1. **All imports must be updated** - old packages won't work
2. **CLI commands changed** - update scripts and documentation
3. **Async/await required** - all orchestrator methods are now async
4. **Tool interface changed** - custom tools need ToolResult return type
5. **Config format changed** - YAML structure is different

### Deprecated Features

These features are deprecated and will be removed in v2.0:
- `EQUITR_coder` package imports (use backward compatibility shim)
- `src` package imports (use backward compatibility shim)
- Old CLI entry points
- Legacy tool return formats

## 📋 Migration Checklist

- [ ] Update all imports to use `equitrcoder`
- [ ] Convert synchronous calls to async/await
- [ ] Update CLI commands in scripts
- [ ] Migrate configuration files
- [ ] Update custom tools to use ToolResult
- [ ] Test single-agent workflows
- [ ] Test multi-agent coordination
- [ ] Update documentation and examples
- [ ] Train team on new architecture
- [ ] Plan removal of backward compatibility shims

## 🆘 Getting Help

If you encounter issues during migration:

1. **Check the examples** in the README and documentation
2. **Use backward compatibility** shims temporarily
3. **File an issue** on GitHub with migration questions
4. **Join our community** for real-time help

## 🎯 Benefits After Migration

- **Cleaner Architecture**: Modular, testable, maintainable code
- **Better Security**: Restricted file system and tool access
- **Enhanced Performance**: Async-first, concurrent execution
- **Improved Monitoring**: Rich callbacks and status tracking
- **Unified CLI**: Single command with consistent interface
- **Future-Proof**: Foundation for advanced features

---

**Need help?** Open an issue or reach out to the community. We're here to help make your migration smooth! 🚀 