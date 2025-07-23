# equitrcoder Examples

This directory contains practical examples demonstrating how to use equitrcoder's modular architecture for various AI coding tasks.

## 📁 Example Files

### Core Examples
- **`basic_single_agent.py`** - Simple single-agent usage patterns
- **`multi_agent_coordination.py`** - Complex multi-agent workflows
- **`custom_tools.py`** - Creating and using custom tools
- **`security_patterns.py`** - Safe multi-agent configurations
- **`session_management.py`** - Persistent session handling

### Documentation
- **`quickstart.md`** - Quick start guide with basic examples
- **`multi_agent_example.md`** - Detailed multi-agent coordination examples
- **`TERMINAL_EXAMPLES.md`** - CLI usage examples
- **`tool_logging_example.py`** - Tool usage logging and monitoring

## 🚀 Quick Examples

### 1. Basic Single Agent

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator

async def basic_example():
    # Create agent with limits
    agent = BaseAgent(max_cost=1.0, max_iterations=10)
    
    # Create orchestrator
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Execute task
    result = await orchestrator.execute_task("Analyze project structure")
    
    print(f"Success: {result['success']}")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Session: {result['session_id']}")

if __name__ == "__main__":
    asyncio.run(basic_example())
```

### 2. Multi-Agent with Security

```python
import asyncio
from equitrcoder import MultiAgentOrchestrator, WorkerConfig

async def multi_agent_example():
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator(
        max_concurrent_workers=2,
        global_cost_limit=3.0
    )
    
    # Create restricted workers
    frontend_config = WorkerConfig(
        worker_id="frontend",
        scope_paths=["src/frontend/"],
        allowed_tools=["read_file", "edit_file"],
        max_cost=1.5
    )
    
    backend_config = WorkerConfig(
        worker_id="backend",
        scope_paths=["src/backend/"],
        allowed_tools=["read_file", "edit_file", "run_cmd"],
        max_cost=1.5
    )
    
    # Register workers
    orchestrator.create_worker(frontend_config)
    orchestrator.create_worker(backend_config)
    
    # Execute parallel tasks
    tasks = [
        {
            "task_id": "ui_task",
            "worker_id": "frontend",
            "task_description": "Update UI components"
        },
        {
            "task_id": "api_task", 
            "worker_id": "backend",
            "task_description": "Fix API endpoints"
        }
    ]
    
    results = await orchestrator.execute_parallel_tasks(tasks)
    
    for result in results:
        print(f"{result.worker_id}: {result.success} (${result.cost:.4f})")

if __name__ == "__main__":
    asyncio.run(multi_agent_example())
```

### 3. Custom Tool Creation

```python
from equitrcoder.tools.base import Tool, ToolResult
from pydantic import BaseModel, Field

class CodeAnalysisArgs(BaseModel):
    file_path: str = Field(..., description="Path to the code file")
    analysis_type: str = Field(default="complexity", description="Type of analysis")

class CodeAnalysisTool(Tool):
    def get_name(self) -> str:
        return "analyze_code"
    
    def get_description(self) -> str:
        return "Analyze code complexity and quality metrics"
    
    def get_args_schema(self):
        return CodeAnalysisArgs
    
    async def run(self, file_path: str, analysis_type: str = "complexity") -> ToolResult:
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Simple analysis example
            lines = len(code.split('\n'))
            functions = code.count('def ')
            classes = code.count('class ')
            
            analysis = {
                "file": file_path,
                "type": analysis_type,
                "metrics": {
                    "lines": lines,
                    "functions": functions,
                    "classes": classes,
                    "complexity_score": (functions + classes) / max(lines, 1) * 100
                }
            }
            
            return ToolResult(success=True, data=analysis)
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

# Usage
async def custom_tool_example():
    from equitrcoder import BaseAgent, SingleAgentOrchestrator
    
    agent = BaseAgent()
    agent.add_tool(CodeAnalysisTool())
    
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Tool is now available to the agent
    result = await agent.call_tool("analyze_code", file_path="src/main.py")
    print(result)
```

### 4. Security and Restrictions

```python
import asyncio
from equitrcoder import WorkerAgent

async def security_example():
    # Create restricted worker
    worker = WorkerAgent(
        worker_id="secure_worker",
        scope_paths=["src/", "tests/"],  # Only these paths
        allowed_tools=["read_file", "edit_file"],  # Only these tools
        project_root="/safe/project/",
        max_cost=0.5,
        max_iterations=10
    )
    
    # Test restrictions
    print("Security checks:")
    print(f"Can access src/main.py: {worker.can_access_file('src/main.py')}")
    print(f"Can access ../secrets.txt: {worker.can_access_file('../secrets.txt')}")
    print(f"Can use read_file: {worker.can_use_tool('read_file')}")
    print(f"Can use run_cmd: {worker.can_use_tool('run_cmd')}")
    
    # Get scope statistics
    stats = worker.get_scope_stats()
    print(f"Allowed files: {stats['file_system_stats']['allowed_files']}")
    print(f"Allowed tools: {stats['allowed_tools']}")

if __name__ == "__main__":
    asyncio.run(security_example())
```

### 5. Session Management

```python
import asyncio
from equitrcoder import BaseAgent, SingleAgentOrchestrator
from equitrcoder.core.session import SessionManagerV2

async def session_example():
    # Create session manager
    session_manager = SessionManagerV2()
    
    # Create agent and orchestrator
    agent = BaseAgent(max_cost=2.0)
    orchestrator = SingleAgentOrchestrator(agent, session_manager=session_manager)
    
    # First task with new session
    result1 = await orchestrator.execute_task(
        "Start working on authentication module",
        session_id="auth-project"
    )
    print(f"Task 1 - Session: {result1['session_id']}")
    
    # Continue in same session
    result2 = await orchestrator.execute_task(
        "Continue with the authentication work",
        session_id="auth-project"
    )
    print(f"Task 2 - Session: {result2['session_id']}")
    
    # Check session history
    session = session_manager.load_session("auth-project")
    if session:
        print(f"Session cost: ${session.cost:.4f}")
        print(f"Session iterations: {session.iteration_count}")
        print(f"Messages: {len(session.messages)}")

if __name__ == "__main__":
    asyncio.run(session_example())
```

## 🖥️ CLI Examples

```bash
# Single agent tasks
equitrcoder single "Fix the bug in authentication module"
equitrcoder single "Add error handling to user registration" --max-cost 1.0

# Multi-agent coordination
equitrcoder multi "Implement user management system" --workers 3 --max-cost 5.0

# Interactive mode (if TUI installed)
equitrcoder tui --mode single

# API server (if API installed)
equitrcoder api --host 0.0.0.0 --port 8080

# Tool management
equitrcoder tools --list
equitrcoder tools --discover
```

## 🔧 Advanced Patterns

### Callback Monitoring

```python
async def monitoring_example():
    from equitrcoder import BaseAgent, SingleAgentOrchestrator
    
    agent = BaseAgent()
    orchestrator = SingleAgentOrchestrator(agent)
    
    # Set up monitoring callbacks
    def on_message(message_data):
        print(f"[{message_data['role']}] {message_data['content'][:50]}...")
    
    def on_iteration(iteration, status):
        print(f"Iteration {iteration}: Cost ${status['current_cost']:.4f}")
    
    def on_completion(results, final_status):
        print(f"Completed! Final cost: ${final_status['current_cost']:.4f}")
    
    orchestrator.set_callbacks(
        on_message=on_message,
        on_iteration=on_iteration,
        on_completion=on_completion
    )
    
    # Execute with monitoring
    result = await orchestrator.execute_task("Analyze codebase structure")
```

### Error Handling and Limits

```python
async def limits_example():
    from equitrcoder import BaseAgent, SingleAgentOrchestrator
    
    # Agent with strict limits
    agent = BaseAgent(max_cost=0.1, max_iterations=3)
    orchestrator = SingleAgentOrchestrator(agent)
    
    try:
        result = await orchestrator.execute_task("Complex analysis task")
        
        if not result["success"]:
            print(f"Task failed: {result['error']}")
            
            # Check if limits were exceeded
            status = agent.get_status()
            limits = status["limits_status"]
            
            if limits["cost_exceeded"]:
                print("Cost limit exceeded!")
            if limits["iterations_exceeded"]:
                print("Iteration limit exceeded!")
                
    except Exception as e:
        print(f"Execution error: {e}")
```

## 📚 More Examples

For more detailed examples, check out:

- **`quickstart.md`** - Step-by-step beginner guide
- **`multi_agent_example.md`** - Complex coordination scenarios
- **`TERMINAL_EXAMPLES.md`** - CLI usage patterns
- **`tool_logging_example.py`** - Advanced tool monitoring

## 🤝 Contributing Examples

To add new examples:

1. Create a new `.py` file with clear, working code
2. Add comprehensive comments explaining each step
3. Include error handling and best practices
4. Add the example to this README
5. Test the example thoroughly

Examples should be:
- **Self-contained** - Can run independently
- **Well-documented** - Clear explanations
- **Realistic** - Practical use cases
- **Secure** - Demonstrate security best practices

---

**Happy coding with equitrcoder!** 🚀