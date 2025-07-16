# EQUITR-coder Multi-Agent System

A sophisticated multi-agent workflow system with optional strong/weak model architecture for enhanced code development and project management.

## Features

### Model Selection Architecture
- **Single Model Mode**: Use one model (strong or weak) for all tasks
- **Multi-Model Mode**: Use strong model as supervisor + weak models as workers
- **Persistent Configuration**: Settings persist between sessions
- **Flexible Model Choices**: Support for GPT-4, GPT-3.5-turbo, Claude-3-opus, Claude-3-haiku

### Multi-Agent Workflow
- **Worker Agents**: Specialized agents with restricted file access and tool permissions
- **Supervisor System**: Strong model provides guidance to weak model workers
- **Task Orchestration**: Automatic task distribution and execution
- **Audit Phase**: Comprehensive project validation after task completion

### Configuration Management
- **CLI Interface**: Complete command-line control
- **Code API**: Programmatic configuration access
- **Persistent Storage**: Settings saved between sessions
- **Flexible Scope**: Per-project configuration

## Quick Start

### Installation
```bash
pip install equitrcoder-multi-agent
```

### Basic Usage

#### 1. Configure Model Mode
```bash
# Use single strong model
opencode model mode single
opencode model models strong

# Use multi-model with supervisor
opencode model mode multi
opencode model models strong --secondary weak
```

#### 2. Run Multi-Agent Workflow
```bash
# Run workflow in current project
opencode workflow

# Run with specific project root
opencode workflow --project-root /path/to/project
```

#### 3. Run Audit
```bash
# Run comprehensive audit
opencode audit

# Check system status
opencode status
```

### Programmatic Usage

```python
from src.api.model_api import ModelSelector
from src.orchestrator.multi_agent_orchestrator import run_multi_agent_workflow
import asyncio

# Configure models
selector = ModelSelector()
selector.configure_multi_model("strong", "weak")

# Run workflow
async def run_workflow():
    result = await run_multi_agent_workflow("./my-project")
    print(f"Completed {result['tasks_completed']} tasks")

asyncio.run(run_workflow())
```

## Architecture

### Components

#### 1. Configuration System (`src/config/`)
- `model_config.py`: Model selection and persistence
- `persistence/config_store.py`: Generic configuration storage

#### 2. CLI Interface (`src/cli/`)
- `main_cli.py`: Primary CLI entry point
- `model_cli.py`: Model-specific commands

#### 3. API Layer (`src/api/`)
- `model_api.py`: Programmatic model configuration

#### 4. Worker Agents (`src/agents/`)
- `worker_agent.py`: Restricted worker agents with file access control

#### 5. Orchestrator (`src/orchestrator/`)
- `multi_agent_orchestrator.py`: Task distribution and execution

#### 6. Audit System (`src/audit/`)
- `audit_phase.py`: Comprehensive project validation

#### 7. Feedback System (`src/feedback/`)
- `new_tasks.py`: Generate new tasks from audit results

#### 8. Tools (`src/tools/`)
- `ask_supervisor.py`: Supervisor consultation for workers

### Workflow

1. **Configuration**: Set model mode and selection
2. **Task Definition**: Define workers and tasks in PROJECT_CHECKLIST.json
3. **Execution**: Run multi-agent workflow
4. **Audit**: Validate results and generate new tasks if needed
5. **Iteration**: Continue until all tasks complete successfully

## Configuration Files

### Model Configuration
Stored in `~/.opencode/model_config.json`:
```json
{
  "mode": "multi",
  "primary_model": "strong",
  "secondary_model": "weak",
  "models": ["strong", "weak"]
}
```

### Project Checklist
Stored in `PROJECT_CHECKLIST.json`:
```json
{
  "workers_spec": [
    {
      "id": "frontend-worker",
      "scope_paths": ["src/frontend/"],
      "description": "Handles frontend components",
      "allowed_tools": ["read_file", "edit_file", "run_cmd", "git_commit", "ask_supervisor"]
    }
  ],
  "tasks": [
    {
      "id": 1,
      "title": "Implement login component",
      "assigned_to": "frontend-worker",
      "status": "todo"
    }
  ]
}
```

## CLI Commands

### Model Commands
```bash
# Set model mode
opencode model mode single|multi

# Configure models
opencode model models <primary> [--secondary <model>]

# Show current configuration
opencode model show

# List available models
opencode model list

# Reset to defaults
opencode model reset
```

### System Commands
```bash
# Run multi-agent workflow
opencode workflow [--project-root <path>]

# Run audit
opencode audit [--project-root <path>]

# Show system status
opencode status
```

## Advanced Usage

### Custom Worker Definition
```python
from src.core.project_checklist import WorkerSpec, Task, get_checklist_manager

manager = get_checklist_manager()

# Define custom worker
worker = WorkerSpec(
    id="custom-worker",
    scope_paths=["src/custom/"],
    description="Custom specialized worker",
    allowed_tools=["read_file", "edit_file", "run_cmd"]
)
manager.add_worker_spec(worker)

# Add task
task = Task(
    id=1,
    title="Implement custom feature",
    assigned_to="custom-worker",
    status="todo"
)
manager.add_task(task)
```

### Audit Customization
```python
from src.audit.audit_phase import AuditPhase

auditor = AuditPhase("./my-project")
results = auditor.run_audit()

if not results["audit_passed"]:
    print("Issues found:")
    for task in results.get("new_tasks", []):
        print(f"- {task['title']}")
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Project Structure
```
src/
├── agents/          # Worker agent implementations
├── api/             # Programmatic API
├── audit/           # Audit system
├── cli/             # Command-line interface
├── config/          # Configuration management
├── feedback/        # Task generation from audit
├── orchestrator/    # Multi-agent orchestration
├── persistence/     # Data persistence
├── tools/           # Shared tools and utilities
tests/               # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.