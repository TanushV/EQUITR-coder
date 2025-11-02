# CHANGELOG

## v2.4.0 (2025-11-02) - External Extension System & Pip-Friendly Customization

### 🚀 Major Features

#### External Extension System
- **Extension Path Resolution**: Hierarchical discovery system for tools, profiles, modes, and MCP servers with environment variable and project-local overrides
- **User Extension Workspace**: Automatic setup of `~/.EQUITR-coder/extensions/` directory for pip-installed customizations
- **Scaffolding CLI**: New commands `init-extension`, `create-tool`, `create-agent`, `create-mode` for rapid extension development
- **TUI Scaffolding**: Interactive `/scaffold` commands in the advanced TUI for extension creation
- **Mode Loader**: Pluggable mode discovery supporting built-in, external, and module-spec modes

### 🛠️ Core System Changes

#### Extension Discovery Architecture
- **Path Resolution**: `equitrcoder/utils/paths.py` provides centralized path management with precedence: environment overrides → project `.equitr/` → user home → packaged defaults
- **Enhanced Tool Discovery**: `equitrcoder/tools/discovery.py` now scans extension directories for Python modules and packages
- **Profile Manager Updates**: `equitrcoder/core/profile_manager.py` merges profiles from multiple sources with proper precedence
- **Mode Registry**: New `equitrcoder/modes/loader.py` enables dynamic mode loading from external sources
- **Configuration Schema**: Extended `default.yaml` and unified config to include extension search paths

#### CLI & TUI Enhancements
- **New CLI Commands**: `equitrcoder init-extension`, `create-tool`, `create-agent`, `create-mode` with template generation
- **TUI Scaffold Commands**: `/scaffold init|tool|agent|mode` in advanced TUI with live feedback
- **Extension Templates**: Ready-to-edit Python classes and YAML configurations with proper imports and structure

### 📋 API Changes

#### New Module Exports
```python
from equitrcoder import (
    # New extension utilities
    get_equitr_home,
    get_extension_search_paths,
    get_user_extensions_root,
    scaffold_tool,
    scaffold_profile,
    scaffold_mode,
    ScaffoldError,

    # Enhanced mode system
    mode_loader,
    get_available_modes,
    get_mode_callable,
)
```

#### New CLI Commands
```bash
# Initialize extension workspace
equitrcoder init-extension [--root PATH]

# Create extension templates
equitrcoder create-tool my_tool [--description "Tool description"]
equitrcoder create-agent qa_specialist [--description "Agent profile"]
equitrcoder create-mode custom_mode [--description "Execution mode"]
```

#### TUI Commands
```bash
# In advanced TUI
/scaffold init
/scaffold tool smoke_tester --force
/scaffold agent qa_specialist "Responsible for regression testing"
/scaffold mode focus_mode "Runs targeted verification"
```

### 🎯 Usage Examples

#### Setting Up Extensions
```bash
# Initialize user extension workspace
equitrcoder init-extension

# Create a custom tool
equitrcoder create-tool smoke_tester --description "Runs smoke tests"
# Edit ~/.EQUITR-coder/extensions/tools/smoke_tester.py

# Create a custom agent profile
equitrcoder create-agent qa_specialist --description "Quality assurance specialist"
# Edit ~/.EQUITR-coder/extensions/profiles/qa-specialist.yaml

# Create a custom mode
equitrcoder create-mode focus_mode --description "Targeted verification mode"
# Edit ~/.EQUITR-coder/extensions/modes/focus_mode_mode.py
```

#### Environment Configuration
```bash
# Override extension locations
export EQUITR_EXTENSIONS_DIR="/opt/equitr/extensions"
export EQUITR_TOOLS_PATH="/project/tools"
export EQUITR_PROFILES_PATH="/shared/profiles"
```

#### Project-Local Extensions
```bash
# Create .equitr/ in project root
mkdir .equitr
equitrcoder init-extension --root .equitr

# Add to .gitignore
echo ".equitr/" >> .gitignore
```

### 📚 Documentation Updates
- **CONFIGURATION_GUIDE.md**: Added extension search paths section with environment variables
- **ADDING_CUSTOM_TOOLS.md**: Updated with quick start guide and extension workflow
- **CREATING_MODES.md**: Added extension creation guide and scaffolding instructions
- **TUI_GUIDE.md**: Documented new `/scaffold` commands
- **README.md**: Added extension examples and CLI reference

### 🔧 Technical Improvements
- **Pip-Friendly**: All customizations work with pip installations without modifying site-packages
- **Hierarchical Discovery**: Multiple search paths with clear precedence rules
- **Template Generation**: Consistent scaffolding with proper imports and error handling
- **Dynamic Loading**: Runtime discovery of extensions without restarts
- **Path Resolution**: Cross-platform path handling with environment variable expansion

### 🚨 Compatibility Notes
- **Backward Compatible**: Existing in-repo customizations continue to work
- **Migration Path**: Existing custom tools/profiles can be moved to user extension directories
- **No Breaking Changes**: All existing APIs remain functional

---

## v2.3.0 (2025-10-26) - Production-Ready Architecture & Technical Debt Resolution

### 🏗️ Major Architecture Improvements
- **Unified Configuration Management**: Complete consolidation of all YAML configuration files with intelligent caching, schema validation, and hot-reloading capability
- **Dependency Injection System**: Full IoC container with singleton, transient, and scoped lifetimes, circular dependency detection, and interface-based resolution
- **Standardized Error Handling**: Contextual error handling with automatic categorization, recovery suggestions, escalation, and correlation tracking
- **Comprehensive Validation Engine**: Schema validation, input parameter validation, file permission validation, and API response validation with detailed guidance

### ⚡ Performance & Optimization
- **Intelligent File Caching**: Automatic cache invalidation based on file modification time, memory usage monitoring, and performance statistics
- **String Operation Optimization**: Memory-efficient string building, context optimization for large text operations, and template engine with caching
- **Performance Monitoring System**: Real-time profiling, bottleneck identification, regression detection, and automated performance optimization
- **Memory Management**: Automatic memory optimization, leak detection, and garbage collection monitoring

### 🛡️ Production Readiness
- **Interface Standardization**: Consistent interfaces across all similar functionality (ICache, IValidator, IMonitor, IConfigurable)
- **Thread Safety**: All core components are thread-safe with proper locking mechanisms
- **Comprehensive Testing**: 240+ unit and integration tests covering all new components
- **Security Enhancements**: File permission validation, input sanitization, and secure error handling

### 🧹 Technical Debt Resolution
- **Configuration Consolidation**: Eliminated hardcoded values throughout codebase (timeout=600, max_cost=5.0, etc.)
- **Error Handling Standardization**: Replaced all bare except clauses and silent failures with proper error handling
- **Code Quality Improvements**: Removed legacy code, resolved TODO/FIXME items, simplified complex nested logic
- **Naming Standardization**: Consistent naming conventions across all components

### 🔧 Developer Experience
- **Enhanced Documentation**: Updated README with architecture improvements and comprehensive component documentation
- **Improved Testing**: Comprehensive test suite with performance and security validation
- **Better Error Messages**: Contextual error messages with specific recovery suggestions
- **Development Tools**: Enhanced debugging and monitoring capabilities

### 📊 Metrics
- **Test Coverage**: 240+ tests with comprehensive coverage of all new components
- **Performance**: Significant improvements in string operations, file caching, and memory usage
- **Code Quality**: Eliminated technical debt across 50+ files with standardized patterns
- **Architecture**: Clean separation of concerns with dependency injection and interface standardization

Note: Detailed v2.2.0 release notes were merged here from RELEASE_NOTES_v2.2.0.md.

## v2.1.0 (2025-08-05) - Legacy Cleanup & Lint Compliance

### 💥 Breaking Changes
- **Single-Agent Foundation Only**: Removed `WorkerAgent` class and all public re-exports.  All execution paths (single and multi-agent) are now built on `BaseAgent` / `CleanAgent`.
- **Offline-Mode Stubs Removed**: DummyCoder and other non-LLM placeholder code deleted; the system again expects real model back-ends.
- **Deprecated Shim Package Removed**: `EQUITR_coder/` compatibility package deleted.

### 🚀 Enhancements
- **Project-wide Lint Pass**: Resolved every Ruff / Flake8 functional error in core code; tools use explicit imports, no wildcard re-exports.
- **Tools Package Hardened**: `equitrcoder/tools/builtin/__init__.py` now exports explicit modules via `__all__`.
- **GitManager Safety**: Defensive one-line statements expanded for clarity; early returns on non-repo paths.
- **Utils**: Replaced bare `except` in `litellm_utils.py`; moved imports to top of file.

### 🧹 Legacy Code Isolation
- Marked `examples/`, legacy `tests/` and auto-generated artefacts as non-core.  Primary runtime resides in:
  - `equitrcoder/core/*`
  - `equitrcoder/programmatic/*`
  - `equitrcoder/tools/*`
  - `testing/comprehensive_mode_testing/*`

### 🔧 Developer Experience
- Added `requirements-dev.txt` with Ruff, Flake8, pytest and docs dependencies.
- Environment setup now mentions creating a virtualenv `equitr-dev` for isolated installs.

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