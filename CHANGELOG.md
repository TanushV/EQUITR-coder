# CHANGELOG

## v2.0.0 (2025-02-08) - Revolutionary Task Group System & Automatic Git Checkpoints

### 🚀 Major Features

#### Task Group System
- **Dependency-Aware Architecture**: Projects automatically decomposed into logical task groups with intelligent dependency management
- **Specialized Execution**: Each task group has specializations (backend, frontend, database, testing, documentation)
- **Structured JSON Planning**: CleanOrchestrator generates sophisticated JSON plans instead of simple markdown todos
- **Session-Local Tracking**: All todos stored in `.EQUITR_todos_<task_name>.json` files to prevent todo compounding
- **Phase-Based Execution**: Multi-agent mode executes task groups in parallel phases based on dependencies

#### Automatic Git Checkpoints
- **Task Group Commits**: Automatic git commit after each successful task group completion
- **Phase Commits**: Multi-agent mode commits after each parallel phase completion
- **Conventional Commit Format**: Professional commit messages using `feat(specialization):` format
- **Configurable Control**: `auto_commit` flag in TaskConfiguration and MultiAgentTaskConfiguration
- **Repository Initialization**: Automatic git repo setup with `.gitignore` creation

### 🛠️ Core System Changes

#### Enhanced Todo Management
- **New Data Structures**: `TaskGroup`, `TodoItem`, `TodoList` with full dependency tracking
- **Rebuilt TodoManager**: Handles task groups, dependencies, and automatic completion detection
- **New Tools**: `list_task_groups`, `list_todos_in_group`, `update_todo_status`
- **Dependency Resolution**: `get_next_runnable_groups()` finds groups whose dependencies are met

#### Execution Mode Updates
- **Single-Agent Mode**: Sequential execution respecting task group dependencies
- **Multi-Agent Mode**: Parallel phases where agents work on independent groups simultaneously
- **Agent Specialization**: Agents assigned based on task group specialization
- **Communication Integration**: Existing agent communication tools work seamlessly

#### Git Integration
- **Enhanced GitManager**: New methods for task group and phase commits
- **Descriptive Commit Messages**: Automatic generation based on specialization and description
- **Error Handling**: Graceful fallback if git operations fail
- **Professional Workflow**: Creates traceable development history

### 📋 API Changes

#### New Configuration Options
```python
@dataclass
class TaskConfiguration:
    auto_commit: bool = True  # NEW: Enable automatic git commits

@dataclass  
class MultiAgentTaskConfiguration:
    auto_commit: bool = True  # NEW: Enable automatic git commits
```

#### New Execution Parameters
```python
# Single-agent mode now supports auto_commit
await run_single_agent_mode(
    task_description="Build a web server",
    auto_commit=True  # NEW parameter
)

# Multi-agent mode supports auto_commit
await run_multi_agent_parallel(
    task_description="Build a web server", 
    auto_commit=True  # NEW parameter
)
```

#### New Tools Available to Agents
```python
# List all task groups and dependencies
await agent.call_tool("list_task_groups")

# Get todos for specific group
await agent.call_tool("list_todos_in_group", group_id="backend_api")

# Mark todos complete (auto-completes groups)
await agent.call_tool("update_todo_status", todo_id="todo_123", status="completed")
```

### 🎯 Example Workflows

#### Task Group Execution Flow
1. **Planning**: CleanOrchestrator creates structured JSON plan with dependencies
2. **Sequential/Parallel Execution**: Agents execute groups based on dependency resolution
3. **Automatic Commits**: Git commit after each successful group/phase completion
4. **Professional History**: Git log shows step-by-step AI progress

#### Example Git History
```bash
feat(testing): Complete task group 'test_suite'
feat(frontend): Complete task group 'ui_components'  
feat(backend): Complete task group 'api_implementation'
feat(database): Complete task group 'schema_setup'
chore(orchestration): Complete Phase 2
```

### 📚 Documentation Updates
- **README.md**: Comprehensive Task Group System documentation
- **USAGE_GUIDE.md**: Complete rewrite with task group examples
- **Architecture Diagrams**: Updated to show dependency-aware workflow
- **Code Examples**: All examples updated for new system

### 🔧 Technical Improvements
- **Dependency Resolution Algorithm**: Efficient detection of runnable task groups
- **Session Isolation**: Each task maintains separate context and tracking
- **Error Recovery**: Better handling of failed task groups
- **Performance**: Optimized for complex multi-group projects

### 🚨 Breaking Changes
- **Todo System**: Complete replacement of simple todo system with task groups
- **Execution Flow**: Both single and multi-agent modes now use dependency-aware execution
- **File Structure**: Todo files now use JSON format instead of markdown
- **Tool Names**: Todo-related tools renamed for task group compatibility

### 🔄 Migration Guide
- **Existing Projects**: Will automatically use new task group system
- **API Calls**: Add `auto_commit=True/False` to configurations as needed
- **Custom Tools**: Update any tools that interact with todo system

---

## v1.0.3 (2025-10-15)
- Completed remaining tasks from audit:
  - Enhanced TUI appearance with CSS themes and colors
  - Added live pricing updates in TUI
  - Removed CLI references from documentation and dereferenced in setup.py 

## v1.0.2 (2025-10-15)
- Added dynamic model selection in TUI based on env keys
- Model updates: Workers to gpt-4.1, Supervisors to o3

## v1.0.1 (2025-10-14)
- Minor bug fixes

## v1.0.0 (2025-10-13)
- Initial release with multi-agent system, TUI, programmatic API, git integration