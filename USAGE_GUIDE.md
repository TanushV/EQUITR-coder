# EQUITR Coder - Complete Usage Guide

**Welcome to EQUITR Coder!** This is an AI-powered coding assistant that can help you build software projects using multiple AI agents working together.

## 🚀 What is EQUITR Coder?

EQUITR Coder is like having a team of AI programmers that can:
- Write code for you
- Fix bugs in your projects
- Build complete applications from scratch
- Work on multiple parts of a project simultaneously
- Create documentation and tests
- Follow best practices and coding standards

Think of it as your AI development team that never gets tired and works exactly how you want them to.

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
python -c "from equitrcoder import CleanOrchestrator; print('✅ EQUITR Coder is ready!')"
```

### Step 3: Your First AI Coding Task

Create a file called `test_ai_coder.py`:

```python
import asyncio
from equitrcoder import run_task_single_agent

async def main():
    # Ask AI to create a simple calculator
    result = await run_task_single_agent(
        "Create a Python calculator that can add, subtract, multiply and divide two numbers. Save it as calculator.py"
    )
    
    if result["success"]:
        print("✅ AI successfully created your calculator!")
        print(f"💰 Cost: ${result['cost'):.4f}")
        print(f"🔄 Iterations: {result['iterations']}")
    else:
        print("❌ Something went wrong:", result.get("error"))

# Run it
asyncio.run(main())
```

Run it:
```bash
python test_ai_coder.py
```

**What happens:**
1. AI creates planning documents (requirements, design, todos)
2. AI writes the calculator code
3. AI tests the code to make sure it works
4. AI performs an audit to verify quality
5. You get a working `calculator.py` file!

## 🎯 Three Ways to Use EQUITR Coder

### 1. 🤖 Simple Method (Direct Functions)

**Best for:** Quick tasks, learning, simple automation

```python
import asyncio
from equitrcoder import run_task_single_agent, run_task_multi_agent

# Single AI agent for simple tasks
async def single_agent_example():
    result = await run_task_single_agent(
        "Create a to-do list app with HTML, CSS and JavaScript"
    )
    return result

# Multiple AI agents for complex tasks  
async def multi_agent_example():
    result = await run_task_multi_agent(
        "Build a complete web application with Flask backend, HTML frontend, and SQLite database",
        num_agents=3  # 3 AI agents working together
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
from equitrcoder import EquitrCoder, TaskConfiguration, MultiAgentTaskConfiguration

async def professional_example():
    # Create a professional AI coder instance
    coder = EquitrCoder(
        mode="single",           # or "multi" for multiple agents
        repo_path="./my_project", # Where to work
        git_enabled=True         # Automatically commit changes
    )
    
    # Configure the task
    config = TaskConfiguration(
        description="Build a REST API with FastAPI",
        max_cost=5.0,           # Maximum $5 to spend
        max_iterations=30,      # Maximum 30 AI iterations
        model="moonshot/kimi-k2-0711-preview",  # Which AI model to use
        auto_commit=True,       # Automatically commit to git
        commit_message="AI: Built FastAPI REST API"
    )
    
    # Execute the task
    result = await coder.execute_task(
        "Create a FastAPI application with user authentication, CRUD operations, and SQLite database",
        config=config
    )
    
    print(f"Success: {result.success}")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Files changed: {result.content}")
    print(f"Git committed: {result.git_committed}")
    
    return result

# Multi-agent professional example
async def multi_agent_professional():
    coder = EquitrCoder(mode="multi")
    
    config = MultiAgentTaskConfiguration(
        description="Build a complete e-commerce website",
        max_workers=4,          # 4 AI agents working together
        max_cost=20.0,         # Maximum $20 total
        supervisor_model="moonshot/kimi-k2-0711-preview",  # Smart supervisor
        worker_model="moonshot/kimi-k2-0711-preview",      # Worker agents
        auto_commit=True
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
    
    # Start the interactive TUI
    tui = SimpleTUI(config)
    
    # This opens an interactive interface where you can:
    # - Select AI models
    # - Enter tasks interactively
    # - See real-time progress
    # - View live code changes
    # - Monitor costs and iterations
    
    await tui.run()  # This starts the interactive session

# Run interactive mode
asyncio.run(interactive_example())
```

## 📚 Common Use Cases

### 🔨 Building Applications

```python
# Web Applications
await run_task_single_agent(
    "Create a Flask web app with user login, dashboard, and SQLite database"
)

# Desktop Applications  
await run_task_single_agent(
    "Build a GUI calculator using tkinter with memory functions"
)

# Command Line Tools
await run_task_single_agent(
    "Create a CLI tool for managing to-do lists with add, remove, and list commands"
)

# APIs and Services
await run_task_multi_agent(
    "Build a RESTful API with authentication, rate limiting, and documentation",
    num_agents=2
)
```

### 🐛 Fixing and Improving Code

```python
# Bug Fixes
await run_task_single_agent(
    "Fix the authentication bug in app.py where users can't log in"
)

# Code Refactoring
await run_task_single_agent(
    "Refactor the messy functions in utils.py to be more readable and efficient"
)

# Adding Features
await run_task_single_agent(
    "Add password reset functionality to the existing user system"
)

# Performance Optimization
await run_task_single_agent(
    "Optimize the database queries in models.py to improve performance"
)
```

### 📖 Documentation and Testing

```python
# Generate Documentation
await run_task_single_agent(
    "Create comprehensive documentation for all functions in the codebase"
)

# Write Tests
await run_task_single_agent(
    "Write unit tests for all functions in calculator.py using pytest"
)

# Code Review
await run_task_single_agent(
    "Review the code in main.py and suggest improvements for security and performance"
)
```

## ⚙️ Advanced Configuration

### Model Selection

```python
# Cheap and fast (recommended for most tasks)
model = "moonshot/kimi-k2-0711-preview"  # ~$0.001 per 1K tokens

# More powerful but expensive
model = "openai/gpt-4"  # ~$0.03 per 1K tokens

# Very powerful for complex reasoning
model = "o3"  # Most expensive, use for complex tasks only
```

### Cost Management

```python
config = TaskConfiguration(
    description="Your task",
    max_cost=2.0,        # Stop if cost exceeds $2
    max_iterations=20,   # Stop after 20 AI iterations
)
```

### Multi-Agent Strategies

```python
# Sequential: Agents work one after another (more coordinated)
await run_multi_agent_sequential(
    "Build a web app",
    num_agents=3
)

# Parallel: Agents work simultaneously (faster but less coordinated)
await run_multi_agent_parallel(
    "Build a web app", 
    num_agents=3
)
```

### Monitoring and Callbacks

```python
def on_message(msg):
    print(f"AI says: {msg['content'][:100]}...")

def on_iteration(iteration, status):
    print(f"Iteration {iteration}: Cost=${status['cost']:.4f}")

def on_tool_call(tool_info):
    print(f"AI used tool: {tool_info['tool_name']}")

# Use callbacks for real-time monitoring
result = await run_single_agent_mode(
    "Create a calculator",
    callbacks={
        'on_message': on_message,
        'on_iteration': on_iteration, 
        'on_tool_call': on_tool_call
    }
)
```

## 🎯 Best Practices

### 1. **Start Small**
```python
# Good: Specific, achievable task
"Create a function that calculates fibonacci numbers"

# Bad: Too vague and complex
"Build me a social media platform like Facebook"
```

### 2. **Be Specific**
```python
# Good: Clear requirements
"Create a REST API with /users endpoint that supports GET, POST, PUT, DELETE operations using Flask and SQLite"

# Bad: Vague requirements  
"Make an API for users"
```

### 3. **Use Multi-Agent for Complex Tasks**
```python
# Single agent: Good for focused tasks
await run_task_single_agent("Fix the bug in login.py")

# Multi-agent: Good for complex projects
await run_task_multi_agent(
    "Build a complete blog system with admin panel, user comments, and email notifications",
    num_agents=4
)
```

### 4. **Monitor Costs**
```python
# Always set cost limits for production use
config = TaskConfiguration(
    max_cost=5.0,  # Never spend more than $5
    max_iterations=25  # Never run more than 25 iterations
)
```

### 5. **Use Git Integration**
```python
# Enable automatic git commits
config = TaskConfiguration(
    auto_commit=True,
    commit_message="AI: Added new feature"
)
```

## 🔧 Troubleshooting

### "No module named 'equitrcoder'"
```bash
# Install the package
pip install -e .
```

### "API key not found"  
```bash
# Check your .env file exists and has the right keys
cat .env

# Make sure the .env file is in the same directory as your Python script
```

### "Task failed" or "Agent got stuck"
```python
# Try with more iterations or higher cost limit
config = TaskConfiguration(
    max_cost=10.0,      # Increase cost limit
    max_iterations=50   # Increase iteration limit
)
```

### "Too expensive"
```python
# Use cheaper model
model = "moonshot/kimi-k2-0711-preview"  # Much cheaper than GPT-4

# Set strict cost limits
max_cost = 1.0  # Only spend $1 maximum
```

## 📊 Understanding Results

Every task returns detailed information:

```python
result = await run_task_single_agent("Create a calculator")

print(f"Success: {result['success']}")        # True/False
print(f"Cost: ${result['cost']:.4f}")        # How much was spent
print(f"Iterations: {result['iterations']}")  # How many AI iterations
print(f"Agent ID: {result['agent_id']}")     # Which agent did the work
print(f"Session ID: {result['session_id']}")  # Session identifier

# Audit information (quality check)
audit = result['audit_result']  
print(f"Audit passed: {audit['audit_passed']}")  # Did the work pass quality check?
print(f"Audit feedback: {audit['audit_content']}")  # Quality feedback
```

## 🎉 You're Ready to Go!

You now know how to:
- ✅ Set up EQUITR Coder with API keys
- ✅ Run simple single-agent tasks
- ✅ Use multiple agents for complex projects
- ✅ Use the professional programmatic interface
- ✅ Monitor costs and progress
- ✅ Troubleshoot common issues

**Start with simple tasks and work your way up to complex projects. The AI agents are powerful and will surprise you with what they can build!**

## 📖 More Examples

Check the `examples/` directory for more detailed examples:
- `examples/basic_single_agent.py` - Simple single agent usage
- `examples/multi_agent_coordination.py` - Complex multi-agent projects  
- `examples/programmatic_example.py` - Professional API usage
- `examples/tool_logging_example.py` - Advanced monitoring

**Happy coding with AI! 🤖✨**