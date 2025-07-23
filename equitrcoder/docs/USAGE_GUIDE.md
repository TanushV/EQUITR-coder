# equitrcoder Usage Guide

This guide covers how to use equitrcoder's modular architecture for both single-agent and multi-agent AI coding workflows.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Single Agent Usage](#single-agent-usage)
3. [Multi-Agent Coordination](#multi-agent-coordination)
4. [Security and Restrictions](#security-and-restrictions)
5. [Session Management](#session-management)
6. [Tool System](#tool-system)
7. [CLI Usage](#cli-usage)
8. [Configuration](#configuration)
9. [Best Practices](#best-practices)

## Quick Start

### Installation

```bash
# Install the package
pip install -e .

# For development with additional tools
pip install -e .[dev]
```

### Environment Setup

```bash
export OPENAI_API_KEY="your-openai-key"
# OR
export ANTHROPIC_API_KEY="your-anthropic-key"

# Optional configuration
export EQUITRCODER_MODEL="gpt-4"
export EQUITRCODER_MAX_COST="5.0"
```

### Basic Example

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator

async def main():
    # Create agent with limits
    agent = BaseAgent(max_cost=1.0, max_iterations=10)
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Execute task
    result = await orchestrator.execute_task("Analyze project structure")
    
    if result["success"]:
        print(f"✅ Success! Cost: ${result['cost']:.4f}")
    else:
        print(f"❌ Failed: {result['error']}")

asyncio.run(main())
```

## Single Agent Usage

### BaseAgent

The `BaseAgent` is the foundation class providing core functionality:

```python
from equitrcoder.agents.base_agent import BaseAgent

# Create agent with configuration
agent = BaseAgent(
    max_cost=2.0,           # Maximum cost limit
    max_iterations=20,      # Maximum iterations
    model="gpt-4",          # LLM model to use
    temperature=0.1         # Model temperature
)

# Check agent status
status = agent.get_status()
print(f"Current cost: ${status['current_cost']:.4f}")
print(f"Iterations: {status['current_iterations']}")
```

### SingleAgentOrchestrator

The orchestrator manages single-agent workflows:

```python
from equitrcoder.orchestrators.single_orchestrator import SingleAgentOrchestrator

# Create orchestrator
orchestrator = SingleAgentOrchestrator(agent)

# Execute task
result = await orchestrator.execute_task(
    task_description="Fix bug in authentication module",
    context={"priority": "high"}
)

# Check results
if result["success"]:
    print(f"Task completed in {result['iterations']} iterations")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Session: {result['session_id']}")
else:
    print(f"Task failed: {result['error']}")
```

### Monitoring and Callbacks

```python
# Set up monitoring callbacks
def on_message(message_data):
    print(f"[{message_data['role']}] {message_data['content'][:50]}...")

def on_iteration(iteration, status):
    print(f"Iteration {iteration}: ${status['current_cost']:.4f}")

def on_completion(results, final_status):
    print(f"Completed! Final cost: ${final_status['current_cost']:.4f}")

# Apply callbacks
orchestrator.set_callbacks(
    on_message=on_message,
    on_iteration=on_iteration,
    on_completion=on_completion
)

# Execute with monitoring
result = await orchestrator.execute_task("Analyze codebase")
```

## Multi-Agent Coordination

### Creating Workers

```python
from equitrcoder.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig

# Create orchestrator
orchestrator = MultiAgentOrchestrator(
    max_concurrent_workers=3,
    global_cost_limit=10.0
)

# Define worker configurations
frontend_config = WorkerConfig(
    worker_id="frontend_dev",
    scope_paths=["src/frontend/", "public/"],
    allowed_tools=["read_file", "edit_file", "run_cmd"],
    max_cost=3.0,
    max_iterations=15
)

backend_config = WorkerConfig(
    worker_id="backend_dev",
    scope_paths=["src/backend/", "api/"],
    allowed_tools=["read_file", "edit_file", "run_cmd", "git_commit"],
    max_cost=3.0,
    max_iterations=15
)

# Create workers
frontend_worker = orchestrator.create_worker(frontend_config)
backend_worker = orchestrator.create_worker(backend_config)
```

### Parallel Task Execution

```python
# Define parallel tasks
tasks = [
    {
        "task_id": "ui_improvements",
        "worker_id": "frontend_dev",
        "task_description": "Improve user interface components",
        "context": {"priority": "high", "deadline": "2024-01-15"}
    },
    {
        "task_id": "api_optimization",
        "worker_id": "backend_dev",
        "task_description": "Optimize API performance",
        "context": {"priority": "medium", "focus": "database"}
    }
]

# Execute tasks in parallel
results = await orchestrator.execute_parallel_tasks(tasks)

# Process results
for result in results:
    status = "✅" if result.success else "❌"
    print(f"{status} {result.worker_id}: {result.task_id}")
    print(f"   Time: {result.execution_time:.2f}s")
    print(f"   Cost: ${result.cost:.4f}")
    if not result.success:
        print(f"   Error: {result.error}")
```

### Orchestrator Statistics

```python
# Get comprehensive statistics
stats = orchestrator.get_statistics()
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Active workers: {stats['active_workers']}")
print(f"Completed tasks: {stats['completed_tasks']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

## Security and Restrictions

### WorkerAgent Security

The `WorkerAgent` extends `BaseAgent` with security restrictions:

```python
from equitrcoder.agents.worker_agent import WorkerAgent

# Create restricted worker
worker = WorkerAgent(
    worker_id="secure_worker",
    scope_paths=["src/", "tests/"],        # Restricted paths
    allowed_tools=["read_file", "edit_file"],  # Allowed tools only
    project_root="/safe/project/path",     # Root boundary
    max_cost=1.0,
    max_iterations=10
)

# Test security restrictions
print(f"Can access src/main.py: {worker.can_access_file('src/main.py')}")
print(f"Can access ../secrets: {worker.can_access_file('../secrets.txt')}")
print(f"Can use read_file: {worker.can_use_tool('read_file')}")
print(f"Can use shell: {worker.can_use_tool('shell')}")
```

### Scope Statistics

```python
# Get detailed scope information
stats = worker.get_scope_stats()
print("Scope Statistics:")
print(f"  Allowed paths: {stats['scope_paths']}")
print(f"  Allowed tools: {stats['allowed_tools']}")
print(f"  File system stats: {stats['file_system_stats']}")
```

### Path Traversal Protection

```python
# The RestrictedFileSystem prevents path traversal attacks
from equitrcoder.utils.restricted_fs import RestrictedFileSystem

fs = RestrictedFileSystem(
    allowed_paths=["src/", "docs/"],
    project_root="/project/root"
)

# These will be blocked
print(fs.is_allowed("../../../etc/passwd"))  # False
print(fs.is_allowed("src/../../../secrets")) # False

# These will be allowed
print(fs.is_allowed("src/main.py"))          # True
print(fs.is_allowed("docs/README.md"))       # True
```

## Session Management

### Creating Sessions

```python
from equitrcoder.core.session import SessionManagerV2

# Create session manager
session_manager = SessionManagerV2()

# Create or load session
session = session_manager.create_session("my-project")

# Use with orchestrator
orchestrator = SingleAgentOrchestrator(
    agent, 
    session_manager=session_manager
)
```

### Session Continuity

```python
# First task
result1 = await orchestrator.execute_task(
    "Start implementing user authentication",
    session_id="auth-feature"
)

# Continue in same session
result2 = await orchestrator.execute_task(
    "Add password validation to the auth system",
    session_id="auth-feature"  # Same session ID
)

# Check session history
session = session_manager.load_session("auth-feature")
if session:
    print(f"Total cost: ${session.cost:.4f}")
    print(f"Messages: {len(session.messages)}")
    print(f"Iterations: {session.iteration_count}")
```

### Session Metadata

```python
# Add metadata to session
session.metadata.update({
    "project": "user-management",
    "version": "1.0.0",
    "team": "backend-team"
})

# Save session
session_manager.save_session(session)
```

## Tool System

### Built-in Tools

equitrcoder includes several built-in tools:

```python
# File operations
await agent.call_tool("read_file", file_path="src/main.py")
await agent.call_tool("edit_file", file_path="src/main.py", content="new content")

# Git operations
await agent.call_tool("git_status")
await agent.call_tool("git_commit", message="Fix authentication bug")

# Shell commands
await agent.call_tool("run_cmd", cmd="pytest tests/")

# Search operations
await agent.call_tool("search_files", pattern="*.py", directory="src/")
```

### Custom Tools

Create custom tools by extending the `Tool` base class:

```python
from equitrcoder.tools.base import Tool, ToolResult
from pydantic import BaseModel, Field

class CodeAnalysisArgs(BaseModel):
    file_path: str = Field(..., description="Path to analyze")
    analysis_type: str = Field(default="complexity", description="Analysis type")

class CodeAnalysisTool(Tool):
    def get_name(self) -> str:
        return "analyze_code"
    
    def get_description(self) -> str:
        return "Analyze code complexity and quality"
    
    def get_args_schema(self):
        return CodeAnalysisArgs
    
    async def run(self, file_path: str, analysis_type: str = "complexity") -> ToolResult:
        # Your analysis logic here
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Simple metrics
            lines = len(code.split('\n'))
            functions = code.count('def ')
            classes = code.count('class ')
            
            result = {
                "file": file_path,
                "lines": lines,
                "functions": functions,
                "classes": classes,
                "complexity_score": (functions + classes) / max(lines, 1) * 100
            }
            
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

# Add to agent
agent.add_tool(CodeAnalysisTool())
```

### Tool Discovery

```python
from equitrcoder.tools.discovery import discover_tools

# Discover available tools
tools = discover_tools("equitrcoder.tools.builtin")
print(f"Found {len(tools)} tools")

for tool in tools:
    print(f"- {tool.get_name()}: {tool.get_description()}")
```

## CLI Usage

### Single Agent Mode

```bash
# Basic usage
equitrcoder single "Fix the authentication bug"

# With options
equitrcoder single "Optimize database queries" \
    --max-cost 2.0 \
    --max-iterations 15 \
    --model gpt-4

# With session
equitrcoder single "Continue working on feature X" \
    --session-id "feature-x-dev"
```

### Multi-Agent Mode

```bash
# Basic multi-agent
equitrcoder multi "Implement user management system" \
    --workers 3 \
    --max-cost 10.0

# Advanced configuration
equitrcoder multi "Build REST API" \
    --workers 2 \
    --max-cost 5.0 \
    --global-timeout 3600 \
    --enable-supervisor
```

### Interactive TUI

```bash
# Start interactive mode
equitrcoder tui --mode single

# Multi-agent interactive
equitrcoder tui --mode multi --workers 3
```

### API Server

```bash
# Start API server
equitrcoder api --host 0.0.0.0 --port 8000

# With configuration
equitrcoder api \
    --host 127.0.0.1 \
    --port 8080 \
    --workers 4 \
    --max-cost 20.0
```

### Tool Management

```bash
# List available tools
equitrcoder tools --list

# Discover new tools
equitrcoder tools --discover

# Test a tool
equitrcoder tools --test read_file --args '{"file_path": "README.md"}'
```

## Configuration

### Environment Variables

```bash
# Required: API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Default settings
export EQUITRCODER_MODEL="gpt-4"
export EQUITRCODER_MAX_COST="5.0"
export EQUITRCODER_MAX_ITERATIONS="25"
export EQUITRCODER_SESSION_DIR="~/.equitrcoder/sessions"
```

### Configuration Files

Create `~/.equitrcoder/config.yaml`:

```yaml
llm:
  model: "gpt-4"
  max_tokens: 4000
  temperature: 0.1
  timeout: 60

orchestrator:
  max_iterations: 50
  max_cost: 10.0
  use_multi_agent: false
  concurrent_workers: 3

session:
  session_dir: "~/.equitrcoder/sessions"
  max_context: 8000
  auto_save: true

tools:
  discovery_paths:
    - "equitrcoder.tools.builtin"
    - "equitrcoder.tools.custom"
  timeout: 30

security:
  restricted_paths:
    - "/etc"
    - "/var"
    - "~/.ssh"
  max_file_size: 10485760  # 10MB
```

### Project-Specific Configuration

Create `.equitrcoder.yaml` in your project root:

```yaml
project:
  name: "my-project"
  version: "1.0.0"
  
workers:
  frontend:
    scope_paths: ["src/frontend/", "public/"]
    allowed_tools: ["read_file", "edit_file", "run_cmd"]
    max_cost: 2.0
    
  backend:
    scope_paths: ["src/backend/", "api/"]
    allowed_tools: ["read_file", "edit_file", "run_cmd", "git_commit"]
    max_cost: 3.0

defaults:
  max_cost: 5.0
  max_iterations: 25
  model: "gpt-4"
```

## Best Practices

### Cost Management

```python
# Set appropriate limits
agent = BaseAgent(
    max_cost=1.0,      # Start small
    max_iterations=10  # Prevent runaway
)

# Monitor costs
status = agent.get_status()
if status['current_cost'] > 0.8 * agent.max_cost:
    print("⚠️  Approaching cost limit")
```

### Error Handling

```python
try:
    result = await orchestrator.execute_task("Complex task")
    
    if not result["success"]:
        # Check specific failure reasons
        if "cost" in result["error"].lower():
            print("Cost limit exceeded - increase budget")
        elif "iteration" in result["error"].lower():
            print("Iteration limit exceeded - increase limit or simplify task")
        else:
            print(f"Task failed: {result['error']}")
            
except Exception as e:
    print(f"Execution error: {e}")
```

### Security Best Practices

```python
# Always use restricted workers for untrusted tasks
worker = WorkerAgent(
    worker_id="untrusted_task",
    scope_paths=["safe/directory/"],  # Limit scope
    allowed_tools=["read_file"],      # Minimal tools
    max_cost=0.5,                     # Low limits
    max_iterations=5
)

# Validate file paths
if not worker.can_access_file(user_provided_path):
    raise SecurityError("Access denied to file")
```

### Session Management

```python
# Use descriptive session IDs
session_id = f"project-{project_name}-{feature}-{datetime.now().strftime('%Y%m%d')}"

# Clean up old sessions periodically
session_manager.cleanup_old_sessions(days=30)

# Backup important sessions
session_manager.export_session("critical-project", "backup.json")
```

### Multi-Agent Coordination

```python
# Design workers with clear responsibilities
workers = {
    "analyzer": ["read_file", "search_files"],      # Analysis only
    "implementer": ["read_file", "edit_file"],      # Implementation
    "tester": ["read_file", "run_cmd"],             # Testing
    "reviewer": ["read_file", "git_commit"]         # Review and commit
}

# Use phases for complex workflows
phases = [
    {"phase": "analysis", "workers": ["analyzer"]},
    {"phase": "implementation", "workers": ["implementer"]},
    {"phase": "testing", "workers": ["tester"]},
    {"phase": "review", "workers": ["reviewer"]}
]
```

### Performance Optimization

```python
# Use appropriate models for tasks
simple_agent = BaseAgent(model="gpt-3.5-turbo")    # For simple tasks
complex_agent = BaseAgent(model="gpt-4")           # For complex tasks

# Batch similar operations
tasks = [
    {"task_id": f"analyze_{file}", "description": f"Analyze {file}"}
    for file in python_files
]
results = await orchestrator.execute_parallel_tasks(tasks)
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   # or
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. **Cost Limit Exceeded**
   ```python
   # Increase limits or use cheaper model
   agent = BaseAgent(max_cost=5.0, model="gpt-3.5-turbo")
   ```

3. **Path Access Denied**
   ```python
   # Check worker scope
   print(worker.can_access_file("path/to/file"))
   ```

4. **Tool Not Found**
   ```python
   # Check available tools
   tools = agent.get_available_tools()
   print([tool.get_name() for tool in tools])
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
agent = BaseAgent(debug=True)
```

### Getting Help

- Check the examples in `equitrcoder/examples/`
- Review the configuration guide in `equitrcoder/docs/CONFIGURATION_GUIDE.md`
- Run the basic functionality test: `python test_basic_functionality.py`
- Use the CLI help: `equitrcoder --help`

---

For more advanced usage patterns, see the examples in the `equitrcoder/examples/` directory.