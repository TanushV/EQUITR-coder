# Creating New Modes Guide

This guide explains how to create custom execution modes for EQUITR Coder. All modes must follow the unified architecture to ensure consistency and feature parity.

## Core Architecture Requirements

Every mode MUST implement these components:

1. **Document Creation**: Use `CleanOrchestrator` to create requirements.md, design.md, and todos.json
2. **Agent Execution**: Use `CleanAgent` with enhanced context
3. **Context Management**: Automatic context compression and core context preservation
4. **Git Integration**: Optional auto-commit functionality
5. **Cost Tracking**: Global cost monitoring across all agents

---

## 1. Basic Mode Structure

### File Organization

```
equitrcoder/modes/
├── __init__.py
├── single_agent_mode.py      # Reference implementation
├── multi_agent_mode.py       # Reference implementation
└── your_custom_mode.py       # Your new mode
```

### Required Imports

```python
# equitrcoder/modes/your_custom_mode.py

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from ..core.clean_agent import CleanAgent
from ..core.clean_orchestrator import CleanOrchestrator
from ..tools.discovery import discover_tools
from ..tools.builtin.todo import set_global_todo_file, get_todo_manager
from ..utils.git_manager import GitManager
```

---

## 2. Mode Class Template

```python
class YourCustomMode:
    """Custom execution mode with your specific logic."""
    
    def __init__(
        self, 
        agent_model: str, 
        orchestrator_model: str, 
        audit_model: str,
        max_cost: Optional[float] = None,
        max_iterations: Optional[int] = None,
        auto_commit: bool = True,
        # Add your custom parameters here
        custom_param: str = "default_value"
    ):
        self.agent_model = agent_model
        self.orchestrator_model = orchestrator_model
        self.audit_model = audit_model
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        self.auto_commit = auto_commit
        self.custom_param = custom_param
        self.global_cost = 0.0  # Track total cost
        
        print(f"🎭 Your Custom Mode: Auto-commit is {'ON' if self.auto_commit else 'OFF'}")
        print(f"   Agent Model: {agent_model}, Audit Model: {audit_model}")
    
    async def run(
        self, 
        task_description: str, 
        project_path: str = ".", 
        callbacks: Optional[Dict[str, Callable]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Main execution method - MUST follow this pattern."""
        try:
            # STEP 1: Document Creation (MANDATORY)
            orchestrator = CleanOrchestrator(model=self.orchestrator_model)
            docs_result = await orchestrator.create_docs(
                task_description=task_description, 
                project_path=project_path,
                **kwargs  # Pass any additional parameters
            )
            
            if not docs_result["success"]:
                return {
                    "success": False, 
                    "error": f"Documentation failed: {docs_result['error']}", 
                    "stage": "planning"
                }
            
            # STEP 2: Git Manager Setup (MANDATORY)
            git_manager = GitManager(repo_path=project_path)
            if self.auto_commit:
                git_manager.ensure_repo_is_ready()
            
            # STEP 3: Todo System Setup (MANDATORY)
            print("🚀 Starting execution of the plan...")
            set_global_todo_file(docs_result['todos_path'])
            
            # STEP 4: Change to Project Directory (MANDATORY)
            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            try:
                # STEP 5: Your Custom Execution Logic
                execution_result = await self._execute_custom_logic(
                    docs_result, callbacks, **kwargs
                )
                
                # STEP 6: Return Standardized Result
                return {
                    "success": execution_result.get("success", False),
                    "docs_result": docs_result,
                    "cost": self.global_cost,
                    **execution_result  # Include your custom results
                }
                
            finally:
                # STEP 7: Restore Directory (MANDATORY)
                os.chdir(original_cwd)
                
        except Exception as e:
            return {"success": False, "error": str(e), "mode": "your_custom_mode"}
    
    async def _execute_custom_logic(
        self, 
        docs_result: Dict[str, Any], 
        callbacks: Optional[Dict[str, Callable]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Implement your custom execution logic here."""
        
        # Example: Create agents with enhanced context
        tools = discover_tools()
        
        # Create agent with enhanced context (MANDATORY pattern)
        agent = CleanAgent(
            agent_id="custom_agent",
            model=self.agent_model,
            tools=tools,
            context=docs_result,  # CleanAgent will enhance this automatically
            max_cost=self.max_cost,
            max_iterations=self.max_iterations,
            audit_model=self.audit_model
        )
        
        if callbacks:
            agent.set_callbacks(**callbacks)
        
        # Your custom task description
        task_desc = f"""Your custom instructions here.
        
        Use the enhanced context which includes:
        - Repository map with functions
        - Requirements and design content  
        - Current todos to complete
        - Agent profile information
        
        Complete the todos according to your custom logic.
        """
        
        # Execute the agent
        start_time = datetime.now()
        result = await agent.run(task_desc)
        end_time = datetime.now()
        
        # Track cost globally
        agent_cost = result.get("cost", 0.0)
        self.global_cost += agent_cost
        
        # Optional: Auto-commit if enabled
        if self.auto_commit and result.get("success"):
            git_manager = GitManager(repo_path=".")
            # Implement your commit logic here
        
        return {
            "success": result.get("success", False),
            "agent_result": result,
            "execution_time": (end_time - start_time).total_seconds(),
            "cost": agent_cost
        }

# STEP 8: Create Convenience Function (MANDATORY)
async def run_your_custom_mode(**kwargs) -> Dict[str, Any]:
    """Convenience function for your custom mode."""
    # Extract runtime parameters
    task_desc = kwargs.pop("task_description", "")
    project_path = kwargs.pop("project_path", ".")
    callbacks = kwargs.pop("callbacks", None)
    
    # Set defaults for your mode
    config = {
        "agent_model": "moonshot/kimi-k2-0711-preview",
        "orchestrator_model": "moonshot/kimi-k2-0711-preview", 
        "audit_model": "moonshot/kimi-k2-0711-preview",
        "max_cost": None,
        "max_iterations": None,
        "auto_commit": True,
        **kwargs  # Override with provided parameters
    }
    
    mode = YourCustomMode(**config)
    return await mode.run(
        task_description=task_desc, 
        project_path=project_path,
        callbacks=callbacks
    )
```

---

## 3. Advanced Mode Examples

### Specialized Workflow Mode

```python
class SpecializedWorkflowMode:
    """Mode that follows a specific workflow pattern."""
    
    async def _execute_custom_logic(self, docs_result, callbacks, **kwargs):
        # Phase 1: Analysis
        analysis_result = await self._run_analysis_phase(docs_result)
        
        # Phase 2: Implementation  
        impl_result = await self._run_implementation_phase(docs_result, analysis_result)
        
        # Phase 3: Testing
        test_result = await self._run_testing_phase(docs_result, impl_result)
        
        return {
            "success": all([analysis_result["success"], impl_result["success"], test_result["success"]]),
            "phases": {
                "analysis": analysis_result,
                "implementation": impl_result, 
                "testing": test_result
            }
        }
    
    async def _run_analysis_phase(self, docs_result):
        """Custom analysis phase."""
        # Create specialized agent for analysis
        analysis_tools = [tool for tool in discover_tools() if tool.get_name() in ["read_file", "grep_search", "list_files"]]
        
        agent = CleanAgent(
            agent_id="analysis_agent",
            model=self.agent_model,
            tools=analysis_tools,
            context=docs_result,
            audit_model=self.audit_model
        )
        
        return await agent.run("Analyze the codebase and requirements...")
```

### Parallel Processing Mode

```python
class ParallelProcessingMode:
    """Mode that processes multiple tasks in parallel."""
    
    async def _execute_custom_logic(self, docs_result, callbacks, **kwargs):
        # Split todos into parallel groups
        todo_groups = self._split_todos_for_parallel_processing()
        
        # Create agents for each group
        agent_coroutines = []
        for i, group in enumerate(todo_groups):
            agent = CleanAgent(
                agent_id=f"parallel_agent_{i}",
                model=self.agent_model,
                tools=discover_tools(),
                context={**docs_result, "assigned_todos": group},
                audit_model=self.audit_model
            )
            agent_coroutines.append(agent.run(f"Complete todos: {[t['title'] for t in group]}"))
        
        # Execute all agents in parallel
        results = await asyncio.gather(*agent_coroutines)
        
        return {
            "success": all(r.get("success", False) for r in results),
            "parallel_results": results
        }
```

---

## 4. Integration Requirements

### Add to Mode Registry

```python
# equitrcoder/modes/__init__.py

from .single_agent_mode import run_single_agent_mode
from .multi_agent_mode import run_multi_agent_parallel, run_multi_agent_sequential  
from .your_custom_mode import run_your_custom_mode  # Add your mode

__all__ = [
    "run_single_agent_mode",
    "run_multi_agent_parallel", 
    "run_multi_agent_sequential",
    "run_your_custom_mode"  # Export your mode
]
```

### Add to Programmatic Interface

```python
# equitrcoder/programmatic/interface.py

from ..modes.your_custom_mode import run_your_custom_mode

@dataclass
class YourCustomTaskConfiguration:
    """Configuration for your custom mode."""
    description: str
    custom_param: str = "default"
    max_cost: float = 5.0
    max_iterations: int = 30
    model: Optional[str] = None
    auto_commit: bool = True

class EquitrCoder:
    async def execute_task(self, task_description: str, config: Union[TaskConfiguration, MultiAgentTaskConfiguration, YourCustomTaskConfiguration]) -> ExecutionResult:
        # Add your mode handling
        elif isinstance(config, YourCustomTaskConfiguration):
            result_data = await run_your_custom_mode(
                task_description=task_description,
                agent_model=config.model or "moonshot/kimi-k2-0711-preview",
                orchestrator_model=config.model or "moonshot/kimi-k2-0711-preview",
                audit_model=config.model or "moonshot/kimi-k2-0711-preview",
                project_path=self.repo_path,
                max_cost=config.max_cost,
                max_iterations=config.max_iterations,
                auto_commit=config.auto_commit,
                custom_param=config.custom_param
            )
```

### Add to CLI Interface

```python
# equitrcoder/cli/unified_main.py

from ..modes.your_custom_mode import run_your_custom_mode

def create_parser():
    # Add subparser for your mode
    custom_parser = subparsers.add_parser("custom", help="Run your custom mode")
    custom_parser.add_argument("task", help="Task description")
    custom_parser.add_argument("--custom-param", help="Your custom parameter")
    # Add other arguments...

async def run_your_custom_cli(args):
    """CLI handler for your custom mode."""
    result = await run_your_custom_mode(
        task_description=args.task,
        agent_model=args.model or "moonshot/kimi-k2-0711-preview",
        orchestrator_model=args.model or "moonshot/kimi-k2-0711-preview", 
        audit_model=args.model or "moonshot/kimi-k2-0711-preview",
        custom_param=args.custom_param
    )
    
    if result["success"]:
        print("✅ Custom mode completed successfully!")
        return 0
    else:
        print(f"❌ Custom mode failed: {result.get('error')}")
        return 1

def main():
    # Add to command routing
    elif args.command == "custom":
        return asyncio.run(run_your_custom_cli(args))
```

---

## 5. Testing Your Mode

### Unit Tests

```python
# tests/test_your_custom_mode.py

import pytest
from equitrcoder.modes.your_custom_mode import run_your_custom_mode

@pytest.mark.asyncio
async def test_your_custom_mode():
    """Test your custom mode."""
    result = await run_your_custom_mode(
        task_description="Test task",
        agent_model="test_model",
        orchestrator_model="test_model",
        audit_model="test_model",
        project_path="test_project"
    )
    
    assert "success" in result
    assert "docs_result" in result
    assert "cost" in result
```

### Integration Tests

```python
# Test with real models (requires API keys)
@pytest.mark.integration
async def test_your_custom_mode_integration():
    result = await run_your_custom_mode(
        task_description="Create a simple Python function",
        agent_model="moonshot/kimi-k2-0711-preview",
        orchestrator_model="moonshot/kimi-k2-0711-preview",
        audit_model="moonshot/kimi-k2-0711-preview"
    )
    
    assert result["success"] == True
    assert result["cost"] > 0
```

---

## 6. Best Practices

### Do's ✅

1. **Always use CleanOrchestrator** for document creation
2. **Always use CleanAgent** with enhanced context
3. **Always implement git integration** with auto_commit option
4. **Always track costs globally** across all agents
5. **Always restore working directory** in finally block
6. **Always follow the standardized return format**
7. **Always provide convenience functions** for easy integration

### Don'ts ❌

1. **Don't bypass the document creation phase** - it's mandatory
2. **Don't create agents without enhanced context** - use docs_result
3. **Don't ignore cost tracking** - users need visibility
4. **Don't hardcode paths or models** - make them configurable
5. **Don't skip error handling** - modes should be robust
6. **Don't break the unified architecture** - maintain consistency

### Performance Tips

1. **Use async/await properly** for concurrent operations
2. **Implement context compression** if you have long conversations
3. **Monitor token usage** and implement limits
4. **Use appropriate models** for different tasks (cheap for workers, smart for supervisors)
5. **Implement proper cleanup** in finally blocks

---

## 7. Example: Complete Custom Mode

See [examples/custom_mode_example.py](../examples/custom_mode_example.py) for a complete working example of a custom mode implementation.

---

## Next Steps

1. **Study existing modes**: Look at `single_agent_mode.py` and `multi_agent_mode.py`
2. **Start simple**: Create a basic mode first, then add complexity
3. **Test thoroughly**: Use both unit and integration tests
4. **Document your mode**: Add usage examples and parameter descriptions
5. **Consider profiles**: Your mode might benefit from specialized agent profiles

For questions or help, check the existing mode implementations or create an issue in the repository.