# EQUITR Coder - Complete Usage Guide

**Welcome to EQUITR Coder!** This is an AI-powered coding assistant that uses a revolutionary **Task Group System** with **Automatic Git Checkpoints** to help you build software projects using multiple AI agents working together.

## 🚀 What is EQUITR Coder?

EQUITR Coder is like having a team of AI programmers that can:
- Write code for you using **dependency-aware task management**
- Fix bugs in your projects with **automatic git checkpoints**
- Build complete applications from scratch with **intelligent planning**
- Work on multiple parts of a project simultaneously with **phase-based execution**
- Create documentation and tests with **specialized agents**
- Follow best practices and coding standards with **built-in auditing**

Think of it as your AI development team that never gets tired, automatically tracks progress, and creates professional git history.

## 🏗️ The Revolutionary Task Group System

EQUITR Coder uses a **state-of-the-art dependency-aware task management system** that breaks down complex projects into logical groups:

### 📋 How It Works

1. **Intelligent Planning**: AI analyzes your request and creates task groups with dependencies
2. **Specialized Execution**: Each group has a specialization (backend, frontend, database, testing, etc.)
3. **Dependency Resolution**: Groups execute only when their dependencies are complete
4. **Automatic Checkpoints**: Git commits after each successful group completion

### 🎯 Example Task Breakdown

When you ask for "Build a web server", the AI creates:

```json
{
  "task_groups": [
    {
      "group_id": "database_setup",
      "specialization": "database", 
      "dependencies": [],
      "todos": ["Design schema", "Setup connections"]
    },
    {
      "group_id": "backend_api",
      "specialization": "backend",
      "dependencies": ["database_setup"],
      "todos": ["Create endpoints", "Add authentication"]
    },
    {
      "group_id": "frontend_ui", 
      "specialization": "frontend",
      "dependencies": ["backend_api"],
      "todos": ["Build components", "Connect to API"]
    }
  ]
}
```

## 📋 Quick Start (5 Minutes)

### Step 1: Setup API Keys

EQUITR Coder needs AI models to work. Create a `.env` file in your project directory:

```bash
# Option 1: Use Moonshot (Recommended - cheaper)
MOONSHOT_API_KEY=your_moonshot_api_key_here

# Option 2: Use OpenAI 
OPENAI_API_KEY=your_openai_api_key_here

# Option 3: Use both (best flexibility)
MOONSHOT_API_KEY=your_moonshot_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Where to get API keys:**
- **Moonshot**: Sign up at [moonshot.cn](https://moonshot.cn) (Chinese service, very affordable)
- **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com) (English service, more expensive)

### Step 2: Install and Test

```bash
# Install the package
pip install -e .

# Test that it works
python -c "from equitrcoder.modes.single_agent_mode import run_single_agent_mode; print('✅ EQUITR Coder is ready!')"
```

### Step 3: Your First AI Coding Task with Task Groups

Create a file called `test_task_groups.py`:

```python
import asyncio
from equitrcoder.modes.single_agent_mode import run_single_agent_mode

async def main():
    # Ask AI to create a web application with dependency-aware planning
    result = await run_single_agent_mode(
        task_description="Create a Python web application with Flask, user authentication, and a simple dashboard",
        agent_model="moonshot/kimi-k2-0711-preview",
        orchestrator_model="moonshot/kimi-k2-0711-preview", 
        audit_model="o3",
        auto_commit=True  # Automatic git commits after each task group
    )
    
    if result["success"]:
        print("✅ AI successfully created your web application!")
        print(f"💰 Cost: ${result.get('cost', 0):.4f}")
        print(f"📋 Task groups completed with automatic git commits")
        print("🔍 Check your git log to see the step-by-step progress!")
    else:
        print("❌ Something went wrong:", result.get("error"))

# Run it
asyncio.run(main())
```

Run it:
```bash
python test_task_groups.py
```

**What happens:**
1. **Planning Phase**: AI creates requirements.md, design.md, and structured JSON task plan
2. **Sequential Execution**: AI executes task groups one by one based on dependencies
3. **Automatic Commits**: Git commit after each successful task group completion
4. **Professional History**: Your git log shows the AI's step-by-step progress

Check your git log:
```bash
git log --oneline
# feat(database): Complete task group 'database_setup'
# feat(backend): Complete task group 'api_implementation' 
# feat(frontend): Complete task group 'ui_components'
# feat(testing): Complete task group 'test_suite'
```

## 🎯 Three Ways to Use EQUITR Coder

### 1. 🤖 Simple Method (Direct Functions)

**Best for:** Quick tasks, learning, simple automation

```python
import asyncio
from equitrcoder.modes.single_agent_mode import run_single_agent_mode
from equitrcoder.modes.multi_agent_mode import run_multi_agent_parallel

# Single AI agent with dependency-aware execution
async def single_agent_example():
    result = await run_single_agent_mode(
        task_description="Create a to-do list app with HTML, CSS and JavaScript",
        auto_commit=True  # Automatic git commits
    )
    return result

# Multiple AI agents with parallel phase execution
async def multi_agent_example():
    result = await run_multi_agent_parallel(
        task_description="Build a complete web application with Flask backend, HTML frontend, and SQLite database",
        num_agents=3,  # 3 AI agents working in parallel phases
        auto_commit=True  # Automatic git commits after each phase
    )
    return result

# Run examples
asyncio.run(single_agent_example())
asyncio.run(multi_agent_example())
```

### 2. 🏗️ Professional Method (Programmatic Interface)

**Best for:** Production applications, complex workflows, integration with other systems

```python
import asyncio
from equitrcoder.programmatic.interface import EquitrCoder, TaskConfiguration, MultiAgentTaskConfiguration

async def professional_example():
    # Create a professional AI coder instance with git integration
    coder = EquitrCoder(
        repo_path="./my_project", # Where to work
        git_enabled=True         # Automatically commit changes
    )
    
    # Configure the task with automatic commits
    config = TaskConfiguration(
        description="Build a REST API with FastAPI",
        max_cost=5.0,           # Maximum $5 to spend
        max_iterations=30,      # Maximum 30 AI iterations
        model="moonshot/kimi-k2-0711-preview",  # Which AI model to use
        auto_commit=True,       # Automatically commit after each task group
    )
    
    # Execute the task with dependency-aware planning
    result = await coder.execute_task(
        "Create a FastAPI application with user authentication, CRUD operations, and SQLite database",
        config=config
    )
    
    print(f"Success: {result.success}")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Git committed: {result.git_committed}")
    print(f"Commit hash: {result.commit_hash}")
    
    return result

# Multi-agent professional example with parallel phases
async def multi_agent_professional():
    coder = EquitrCoder(git_enabled=True)
    
    config = MultiAgentTaskConfiguration(
        description="Build a complete e-commerce website",
        num_agents=4,          # 4 AI agents working in parallel phases
        max_cost=20.0,         # Maximum $20 total
        supervisor_model="moonshot/kimi-k2-0711-preview",  # Smart supervisor
        worker_model="moonshot/kimi-k2-0711-preview",      # Worker agents
        auto_commit=True       # Automatic git commits after each phase
    )
    
    result = await coder.execute_task(
        "Create a complete e-commerce website with product catalog, shopping cart, user accounts, and payment integration",
        config=config
    )
    
    return result

# Run examples
asyncio.run(professional_example())
asyncio.run(multi_agent_professional())
```

### 3. 🖥️ Interactive Method (TUI - Text User Interface)

**Best for:** Hands-on development, experimenting, real-time interaction

```python
import asyncio
from equitrcoder.ui.tui import SimpleTUI
from equitrcoder.core.config import config_manager

async def interactive_example():
    # Load configuration
    config = config_manager.load_config()
    
    # Start the interactive TUI with task group visualization
    tui = SimpleTUI(config)
    
    # This opens an interactive interface where you can:
    # - See task groups and their dependencies in real-time
    # - Watch agents execute groups sequentially or in parallel
    # - View automatic git commits as they happen
    # - Monitor costs and iterations per task group
    # - See live code changes with syntax highlighting
    
    await tui.run()  # This starts the interactive session

# Run interactive mode
asyncio.run(interactive_example())
```

## 📚 Common Use Cases with Task Groups

### 🔨 Building Applications

```python
# Web Applications (Sequential Dependencies)
await run_single_agent_mode(
    "Create a Flask web app with user login, dashboard, and SQLite database",
    auto_commit=True
)
# → database_setup → backend_api → frontend_ui → testing

# Desktop Applications  
await run_single_agent_mode(
    "Build a GUI calculator using tkinter with memory functions",
    auto_commit=True
)
# → core_logic → gui_components → testing → documentation

# APIs and Services (Parallel Phases)
await run_multi_agent_parallel(
    "Build a RESTful API with authentication, rate limiting, and documentation",
    num_agents=3,
    auto_commit=True
)
# → Phase 1: [database_setup] → Phase 2: [api_core, auth_system] → Phase 3: [documentation, testing]
```

### 🐛 Fixing and Improving Code

```python
# Bug Fixes with Automatic Commits
await run_single_agent_mode(
    "Fix the authentication bug in app.py where users can't log in",
    auto_commit=True
)
# → Creates: feat(bugfix): Complete task group 'authentication_fix'

# Code Refactoring with Dependency Tracking
await run_single_agent_mode(
    "Refactor the messy functions in utils.py to be more readable and efficient",
    auto_commit=True
)
# → analysis → refactoring → testing → documentation

# Adding Features with Proper Planning
await run_single_agent_mode(
    "Add password reset functionality to the existing user system",
    auto_commit=True
)
# → database_changes → backend_logic → frontend_ui → email_integration → testing
```

### 📖 Documentation and Testing

```python
# Comprehensive Documentation with Task Groups
await run_single_agent_mode(
    "Create comprehensive documentation for all functions in the codebase",
    auto_commit=True
)
# → code_analysis → api_docs → user_guides → examples → review

# Testing with Dependencies
await run_single_agent_mode(
    "Write unit tests for all functions in calculator.py using pytest",
    auto_commit=True
)
# → test_planning → unit_tests → integration_tests → test_documentation
```

## ⚙️ Advanced Configuration

### Task Group Control

```python
# View task groups before execution
from equitrcoder.tools.builtin.todo import todo_manager

# After orchestrator creates the plan
groups = todo_manager.todo_list.task_groups
for group in groups:
    print(f"Group: {group.group_id} ({group.specialization})")
    print(f"Dependencies: {group.dependencies}")
    print(f"Todos: {len(group.todos)}")
```

### Git Commit Customization

```python
# Automatic commits are enabled by default
config = TaskConfiguration(
    auto_commit=True,  # Enable automatic commits
)

# Disable automatic commits
config = TaskConfiguration(
    auto_commit=False,  # Manual git control
)
```

### Model Selection for Different Phases

```python
# Cheap and fast (recommended for most task groups)
agent_model = "moonshot/kimi-k2-0711-preview"  # ~$0.001 per 1K tokens

# More powerful orchestrator for complex planning
orchestrator_model = "moonshot/kimi-k2-0711-preview"

# Very powerful auditor for quality control
audit_model = "o3"  # Most expensive, use for final quality checks
```

### Multi-Agent Phase Strategies

```python
# Sequential Groups: One group at a time (more coordinated)
await run_single_agent_mode(
    "Build a web app",
    auto_commit=True
)

# Parallel Phases: Multiple groups simultaneously (faster)
await run_multi_agent_parallel(
    "Build a web app", 
    num_agents=3,
    auto_commit=True
)
```

### Monitoring Task Group Progress

```python
def on_task_group_start(group_info):
    print(f"🚀 Starting: {group_info['group_id']} ({group_info['specialization']})")

def on_task_group_complete(group_info):
    print(f"✅ Completed: {group_info['group_id']}")
    print(f"📝 Git commit created automatically")

def on_phase_complete(phase_num, groups):
    print(f"🎯 Phase {phase_num} completed with {len(groups)} groups")

# Use callbacks for real-time monitoring
result = await run_single_agent_mode(
    "Create a calculator",
    callbacks={
        'on_task_group_start': on_task_group_start,
        'on_task_group_complete': on_task_group_complete,
        'on_phase_complete': on_phase_complete
    },
    auto_commit=True
)
```

## 🎯 Best Practices with Task Groups

### 1. **Let AI Plan Dependencies**
```python
# Good: Let AI figure out the dependencies
"Create a web application with user authentication, dashboard, and database"

# The AI will automatically create:
# database_setup → backend_api → frontend_ui → testing
```

### 2. **Use Descriptive Task Descriptions**
```python
# Good: Specific requirements that help AI create better task groups
"Create a REST API with /users endpoint that supports GET, POST, PUT, DELETE operations using Flask and SQLite, with JWT authentication"

# Bad: Vague requirements that lead to poor task group planning
"Make an API for users"
```

### 3. **Trust the Automatic Git Commits**
```python
# Good: Enable auto-commits for professional git history
config = TaskConfiguration(auto_commit=True)

# Check your git log to see the AI's progress:
# git log --oneline
# feat(backend): Complete task group 'api_implementation'
# feat(database): Complete task group 'schema_setup'
# feat(frontend): Complete task group 'ui_components'
```

### 4. **Use Multi-Agent for Complex Projects**
```python
# Single agent: Good for sequential dependencies
await run_single_agent_mode("Fix the bug in login.py")

# Multi-agent: Good for projects with parallel work
await run_multi_agent_parallel(
    "Build a complete blog system with admin panel, user comments, and email notifications",
    num_agents=4,
    auto_commit=True
)
```

### 5. **Monitor Task Group Costs**
```python
# Set cost limits per task group execution
config = TaskConfiguration(
    max_cost=5.0,  # Never spend more than $5 total
    max_iterations=25  # Never run more than 25 iterations per group
)
```

## 🔧 Troubleshooting Task Groups

### "Task group failed"
```python
# Check which group failed and why
result = await run_single_agent_mode("Your task")
if not result["success"]:
    print(f"Failed at stage: {result.get('stage')}")
    print(f"Error: {result.get('error')}")
```

### "Dependencies not met"
```python
# The AI automatically handles dependencies, but if there's an issue:
# 1. Check the generated JSON plan in .EQUITR_todos_*.json
# 2. Look for circular dependencies
# 3. Simplify the task description
```

### "Git commits not working"
```bash
# Make sure git is initialized
git init

# Check git status
git status

# Verify auto_commit is enabled
config = TaskConfiguration(auto_commit=True)
```

### "Too many task groups created"
```python
# For simpler tasks, be more specific:
# Instead of: "Build a social media platform"
# Use: "Create a simple user profile page with HTML and CSS"
```

## 📊 Understanding Task Group Results

Every task returns detailed task group information:

```python
result = await run_single_agent_mode("Create a calculator", auto_commit=True)

print(f"Success: {result['success']}")        # True/False
print(f"Cost: ${result.get('cost', 0):.4f}")        # How much was spent
print(f"Task groups completed: {result.get('task_groups_completed', 0)}")  # How many groups finished
print(f"Git commits created: {result.get('git_commits', 0)}")  # Number of automatic commits

# Check git log for detailed history
import subprocess
git_log = subprocess.run(['git', 'log', '--oneline', '-10'], capture_output=True, text=True)
print("Recent commits:")
print(git_log.stdout)
```

## 🎉 You're Ready for Professional AI Development!

You now know how to:
- ✅ Use the revolutionary Task Group System for intelligent project planning
- ✅ Enable automatic git checkpoints for professional development workflow
- ✅ Run dependency-aware single-agent tasks
- ✅ Use parallel-phase multi-agent execution for complex projects
- ✅ Monitor task group progress and costs
- ✅ Troubleshoot task group issues

**The Task Group System with Automatic Git Checkpoints makes EQUITR Coder the most advanced AI coding assistant available. Start with simple tasks and work your way up to complex, multi-phase projects!**

## 📖 More Examples

Check the `examples/` directory for more detailed examples:
- `examples/task_group_single_agent.py` - Task group single agent usage
- `examples/task_group_multi_agent.py` - Parallel phase multi-agent projects  
- `examples/git_checkpoint_example.py` - Automatic git commit examples
- `examples/dependency_management.py` - Advanced dependency handling

**Happy coding with AI Task Groups! 🤖✨📋**