# Programmatic Usage Guide

This guide covers how to use EQUITR Coder programmatically in your Python applications using the clean OOP interface.

## Overview

The `EquitrCoder` class provides a high-level, object-oriented interface for executing AI coding tasks. It follows standard Python design patterns and includes:

- **Clean OOP Design**: Standard Python classes and methods
- **Type Safety**: Full type hints and dataclasses
- **Configuration Management**: Structured configuration objects
- **Error Handling**: Comprehensive exception handling
- **Resource Management**: Automatic cleanup and resource management
- **Git Integration**: Built-in version control operations
- **Session Management**: Persistent conversation history

## Quick Start

### Single Agent Usage

```python
import asyncio
from equitrcoder import EquitrCoder, TaskConfiguration

async def main():
    # Create a single-agent coder
    coder = EquitrCoder(mode="single")
    
    # Configure the task
    config = TaskConfiguration(
        description="Fix authentication bug",
        max_cost=2.0,
        max_iterations=15,
        auto_commit=True
    )
    
    # Execute the task
    result = await coder.execute_task(
        "Fix the authentication bug in the login module",
        config=config
    )
    
    # Check results
    if result.success:
        print(f"✅ Task completed in {result.execution_time:.2f}s")
        print(f"💰 Cost: ${result.cost:.4f}")
        print(f"🔄 Iterations: {result.iterations}")
        if result.git_committed:
            print(f"📝 Committed as: {result.commit_hash}")
    else:
        print(f"❌ Task failed: {result.error}")
    
    await coder.cleanup()

asyncio.run(main())
```

### Multi-Agent Usage

```python
import asyncio
from equitrcoder import EquitrCoder, MultiAgentTaskConfiguration

async def main():
    # Create a multi-agent coder
    coder = EquitrCoder(mode="multi")
    
    # Configure the task
    config = MultiAgentTaskConfiguration(
        description="Build web application",
        max_workers=3,
        max_cost=10.0,
        supervisor_model="gpt-4",
        worker_model="gpt-3.5-turbo",
        auto_commit=True
    )
    
    # Execute complex task
    result = await coder.execute_task(
        "Build a complete user authentication system with database, API, and frontend",
        config=config
    )
    
    print(f"Multi-agent result: {result.success}")
    print(f"Workers used: {result.iterations}")
    print(f"Total cost: ${result.cost:.4f}")
    
    await coder.cleanup()

asyncio.run(main())
```

## Factory Functions

For convenience, use the factory functions:

### Single Agent Factory

```python
from equitrcoder import create_single_agent_coder

# Simple usage
coder = create_single_agent_coder()

# With configuration
coder = create_single_agent_coder(
    repo_path="./my_project",
    git_enabled=True
)
```

### Multi-Agent Factory

```python
from equitrcoder import create_multi_agent_coder

# Simple usage
coder = create_multi_agent_coder()

# With configuration
coder = create_multi_agent_coder(
    repo_path="./my_project",
    max_workers=5,
    supervisor_model="gpt-4",
    worker_model="gpt-3.5-turbo"
)
```

## Configuration Classes

### TaskConfiguration

```python
from equitrcoder import TaskConfiguration

config = TaskConfiguration(
    description="Task description",
    max_cost=2.0,                    # Maximum cost in USD
    max_iterations=20,               # Maximum iterations
    session_id="my_session",         # Optional session ID
    model="gpt-4",                   # Optional model override
    auto_commit=True,                # Auto-commit changes
    commit_message="Custom message"  # Custom commit message
)
```

### MultiAgentTaskConfiguration

```python
from equitrcoder import MultiAgentTaskConfiguration

config = MultiAgentTaskConfiguration(
    description="Complex task description",
    max_workers=3,                       # Maximum concurrent workers
    max_cost=10.0,                       # Total cost limit
    supervisor_model="gpt-4",            # Supervisor model
    worker_model="gpt-3.5-turbo",       # Worker model
    auto_commit=True,                    # Auto-commit changes
    commit_message="Multi-agent work"    # Custom commit message
)
```

### WorkerConfiguration

```python
from equitrcoder import WorkerConfiguration

worker_config = WorkerConfiguration(
    worker_id="frontend_dev",
    scope_paths=["src/frontend/", "public/"],
    allowed_tools=["read_file", "edit_file", "run_cmd"],
    max_cost=2.0,
    max_iterations=15,
    description="Frontend development worker"
)
```

## Advanced Usage

### Custom Workers and Parallel Tasks

```python
from equitrcoder import EquitrCoder, WorkerConfiguration

async def parallel_development():
    coder = EquitrCoder(mode="multi")
    
    # Create specialized workers
    frontend_config = WorkerConfiguration(
        worker_id="frontend_dev",
        scope_paths=["src/frontend/"],
        allowed_tools=["read_file", "edit_file", "run_cmd"]
    )
    
    backend_config = WorkerConfiguration(
        worker_id="backend_dev",
        scope_paths=["src/backend/"],
        allowed_tools=["read_file", "edit_file", "run_cmd", "git_commit"]
    )
    
    # Execute parallel tasks
    tasks = [
        {
            "task_id": "ui_update",
            "worker_id": "frontend_dev",
            "task_description": "Update the user interface",
            "context": {"priority": "high"}
        },
        {
            "task_id": "api_fix", 
            "worker_id": "backend_dev",
            "task_description": "Fix the API endpoints",
            "context": {"priority": "critical"}
        }
    ]
    
    results = await coder.execute_parallel_tasks(tasks)
    
    for result in results:
        print(f"{result.worker_id}: {result.success}")
    
    await coder.cleanup()
```

### Session Management

```python
from equitrcoder import EquitrCoder, TaskConfiguration

async def session_example():
    coder = EquitrCoder()
    
    # Continue previous session
    config = TaskConfiguration(
        description="Continue authentication work",
        session_id="auth_project"
    )
    
    result = await coder.execute_task(
        "Add password validation to the auth system",
        config=config
    )
    
    # Get session history
    session = coder.get_session_history("auth_project")
    if session:
        print(f"Session cost: ${session.cost:.4f}")
        print(f"Messages: {len(session.messages)}")
    
    # List all sessions
    sessions = coder.list_sessions()
    for session_info in sessions:
        print(f"Session: {session_info['session_id']}")
```

### Callbacks and Monitoring

```python
from equitrcoder import EquitrCoder

def on_task_start(description, mode):
    print(f"🚀 Starting {mode} task: {description}")

def on_task_complete(result):
    if result.success:
        print(f"✅ Completed in {result.execution_time:.2f}s")
    else:
        print(f"❌ Failed: {result.error}")

def on_tool_call(tool_data):
    tool_name = tool_data.get('tool_name', 'unknown')
    print(f"🔧 Using tool: {tool_name}")

def on_message(message_data):
    role = message_data['role'].upper()
    content = message_data['content'][:50] + "..."
    print(f"💬 [{role}]: {content}")

async def monitored_execution():
    coder = EquitrCoder()
    
    # Set callbacks
    coder.on_task_start = on_task_start
    coder.on_task_complete = on_task_complete
    coder.on_tool_call = on_tool_call
    coder.on_message = on_message
    
    result = await coder.execute_task("Implement caching system")
    await coder.cleanup()
```

### Git Integration

```python
from equitrcoder import EquitrCoder

async def git_example():
    coder = EquitrCoder(git_enabled=True)
    
    # Check git status
    status = coder.get_git_status()
    print(f"Modified files: {status.get('modified', [])}")
    
    # Get recent commits
    commits = coder.get_recent_commits(5)
    for commit in commits:
        print(f"{commit['hash']}: {commit['message']}")
    
    # Execute task with auto-commit
    config = TaskConfiguration(
        description="Add unit tests",
        auto_commit=True,
        commit_message="Add comprehensive unit tests"
    )
    
    result = await coder.execute_task(
        "Add unit tests for all authentication functions",
        config=config
    )
    
    if result.git_committed:
        print(f"Changes committed: {result.commit_hash}")
    
    await coder.cleanup()
```

## Error Handling

```python
from equitrcoder import EquitrCoder, TaskConfiguration

async def robust_execution():
    coder = EquitrCoder()
    
    try:
        config = TaskConfiguration(
            description="Complex task",
            max_cost=1.0,  # Low cost limit
            max_iterations=5  # Low iteration limit
        )
        
        result = await coder.execute_task(
            "Build a complete web application",  # Ambitious task
            config=config
        )
        
        if not result.success:
            print(f"Task failed: {result.error}")
            print(f"Partial progress made: {result.iterations} iterations")
            print(f"Cost incurred: ${result.cost:.4f}")
        
    except Exception as e:
        print(f"Execution error: {e}")
    
    finally:
        await coder.cleanup()
```

## Best Practices

### 1. Resource Management

Always use proper cleanup:

```python
async def proper_cleanup():
    coder = EquitrCoder(mode="multi")
    try:
        # Your task execution
        result = await coder.execute_task("Build feature")
    finally:
        await coder.cleanup()  # Always cleanup

# Or use async context manager pattern
class EquitrCoderContext(EquitrCoder):
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

async def context_example():
    async with EquitrCoderContext() as coder:
        result = await coder.execute_task("Build feature")
        # Automatic cleanup on exit
```

### 2. Configuration Management

Use environment variables and configuration files:

```python
import os
from equitrcoder import EquitrCoder

# Environment-based configuration
coder = EquitrCoder(
    mode=os.getenv("EQUITR_MODE", "single"),
    repo_path=os.getenv("EQUITR_REPO_PATH", "."),
    git_enabled=os.getenv("EQUITR_GIT_ENABLED", "true").lower() == "true"
)
```

### 3. Cost and Iteration Limits

Set appropriate limits based on task complexity:

```python
# Simple tasks
simple_config = TaskConfiguration(
    description="Fix typo",
    max_cost=0.5,
    max_iterations=5
)

# Complex tasks
complex_config = MultiAgentTaskConfiguration(
    description="Build application",
    max_workers=5,
    max_cost=20.0
)
```

### 4. Error Recovery

Implement retry logic for transient failures:

```python
import asyncio
from equitrcoder import EquitrCoder, TaskConfiguration

async def retry_execution(task_description, max_retries=3):
    coder = EquitrCoder()
    
    for attempt in range(max_retries):
        try:
            config = TaskConfiguration(
                description=task_description,
                max_cost=2.0 * (attempt + 1)  # Increase cost limit on retry
            )
            
            result = await coder.execute_task(task_description, config)
            
            if result.success:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result.error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    await coder.cleanup()
    return None  # All retries failed
```

## Advanced Features

### Environment Validation

EQUITR Coder provides methods to validate your setup:

- `check_available_api_keys()`: Returns dict of available providers.
- `check_model_availability(model, test_call=False)`: Async method to check if a model is supported and working.

Example:

```python
coder = EquitrCoder()
keys = coder.check_available_api_keys()
if 'openai' not in keys:
    print("OpenAI key missing")

model_status = await coder.check_model_availability("claude-3-sonnet", test_call=True)
if model_status:
    print("Model is ready")
```

Use these before tasks to avoid runtime errors.

## Integration Examples

### Flask Web Application

```
```

## Researcher Mode (ML Only)

Use `ResearchTaskConfiguration` to run the researcher mode programmatically:

```python
import asyncio
from equitrcoder.programmatic.interface import EquitrCoder, ResearchTaskConfiguration

async def main():
    coder = EquitrCoder(repo_path=".", mode="research")

    config = ResearchTaskConfiguration(
        description="Evaluate ResNet on CIFAR-10 with data augmentation ablation",
        max_workers=3,
        max_cost=12.0,
        supervisor_model="moonshot/kimi-k2-0711-preview",
        worker_model="moonshot/kimi-k2-0711-preview",
        team=["ml_researcher", "data_engineer", "experiment_runner", "report_writer"],
        research_context={
            "datasets": [
                {"path": "./data/cifar10", "description": "Local CIFAR-10 dataset"}
            ],
            "experiments": [
                {"name": "baseline", "command": "python train.py --dataset cifar10 --epochs 1"},
                {"name": "aug", "command": "python train.py --dataset cifar10 --epochs 1 --augment"}
            ]
        }
    )

    result = await coder.execute_task(config.description, config)
    print("Success:", result.success)

asyncio.run(main())
```

Artifacts produced under `docs/task_<timestamp>/`:
- `requirements.md`, `design.md`, `todos.json`
- `research_plan.yaml`, `experiments.yaml`
- `research_report.md`