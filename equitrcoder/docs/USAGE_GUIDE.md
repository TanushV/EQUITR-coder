# EQUITR Coder Usage Guide

This guide covers all three modes of EQUITR Coder: Programmatic, CLI, and TUI modes. All modes use the **exact same underlying logic** and provide identical functionality.

## Core Architecture

All modes follow this unified workflow:

1. **Document Creation Phase**: Creates requirements.md, design.md, and todos.json in `docs/task_name/` folder
2. **Agent Execution Phase**: Agents receive enhanced context including:
   - Full repository map with function extraction
   - Requirements and design content
   - Current task group todos
   - Agent profile information
   - All conversation history and tool results
3. **Context Management**: Automatic compression when >75% context used, preserving core information
4. **Git Integration**: Automatic commits after task group completion (if enabled)

---

## 1. Programmatic Mode

**Best for**: Integration into other applications, automated workflows, batch processing

### Basic Usage

```python
import asyncio
from equitrcoder.programmatic.interface import (
    EquitrCoder, 
    TaskConfiguration, 
    MultiAgentTaskConfiguration
)

async def main():
    # Initialize the coder
    coder = EquitrCoder(repo_path=".", git_enabled=True)
    
    # Single agent task
    config = TaskConfiguration(
        description="Create a calculator app with basic math operations",
        max_cost=2.0,
        max_iterations=20,
        model="moonshot/kimi-k2-0711-preview",
        auto_commit=True
    )
    
    result = await coder.execute_task("Build a calculator", config)
    
    if result.success:
        print(f"✅ Task completed! Cost: ${result.cost:.4f}")
        print(f"📋 Iterations: {result.iterations}")
        print(f"🔗 Commit: {result.commit_hash}")
    else:
        print(f"❌ Task failed: {result.error}")

# Run the example
asyncio.run(main())
```

### Multi-Agent Configuration

```python
# Multi-agent task with specialized team
multi_config = MultiAgentTaskConfiguration(
    description="Build a full-stack web application",
    num_agents=3,
    max_cost=10.0,
    max_iterations=50,
    supervisor_model="gpt-4o-mini",
    worker_model="moonshot/kimi-k2-0711-preview",
    auto_commit=True,
    team=["backend_dev", "frontend_dev", "qa_engineer"]  # Use specialized profiles
)

result = await coder.execute_task("Create a todo app with React frontend and Node.js backend", multi_config)
```

### Advanced Features

```python
# Access detailed execution data
if result.success:
    print("📊 Execution Details:")
    print(f"   Conversation History: {len(result.conversation_history)} messages")
    print(f"   Tool Calls: {len(result.tool_call_history)} calls")
    print(f"   LLM Responses: {len(result.llm_responses)} responses")
    print(f"   Execution Time: {result.execution_time:.2f}s")
```

---

## 2. CLI Mode

**Best for**: Command-line workflows, CI/CD integration, scripting

### Installation & Setup

```bash
# Install EQUITR Coder
pip install equitrcoder

# Set up API keys
export MOONSHOT_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"  # Optional
```

### Single Agent Mode

```bash
# Basic single agent task
equitrcoder single "Create a Python calculator" --model moonshot/kimi-k2-0711-preview

# With cost and iteration limits
equitrcoder single "Build a web scraper" \
    --model moonshot/kimi-k2-0711-preview \
    --max-cost 5.0 \
    --max-iterations 30

# Resume a session
equitrcoder single "Continue the calculator" \
    --model moonshot/kimi-k2-0711-preview \
    --session-id my_session
```

### Multi-Agent Mode

```bash
# Multi-agent with specialized team
equitrcoder multi "Build a todo app with React and Node.js" \
    --supervisor-model gpt-4o-mini \
    --worker-model moonshot/kimi-k2-0711-preview \
    --team backend_dev,frontend_dev,qa_engineer \
    --workers 3 \
    --max-cost 15.0

# Simple multi-agent without specialized profiles
equitrcoder multi "Create a game in Python" \
    --supervisor-model moonshot/kimi-k2-0711-preview \
    --worker-model moonshot/kimi-k2-0711-preview \
    --workers 2
```

### Utility Commands

```bash
# List available models
equitrcoder models
equitrcoder models --provider moonshot

# List available tools
equitrcoder tools --list

# Discover new tools
equitrcoder tools --discover
```

---

## 3. TUI Mode (Terminal User Interface)

**Best for**: Interactive development, learning, experimentation

### Launch TUI

```bash
# Start interactive TUI
equitrcoder tui

# Or specify mode (currently only single agent supported in TUI)
equitrcoder tui --mode single
```

### TUI Commands

Once in TUI mode, use these commands:

```
equitrcoder> /help          # Show help menu
equitrcoder> /model         # Select AI model
equitrcoder> /session       # Manage sessions
equitrcoder> /quit          # Exit TUI

# Execute tasks directly
equitrcoder> Create a Python calculator with GUI
equitrcoder> Build a web scraper for news articles
equitrcoder> Add unit tests to the existing code
```

### Model Selection in TUI

```
Available models:
  1. moonshot/kimi-k2-0711-preview
  2. openai/gpt-4
  3. openai/gpt-3.5-turbo
  4. anthropic/claude-3-sonnet
  5. anthropic/claude-3-haiku
  0. Enter custom model

Select supervisor model (number): 1
Select worker model (number): 1
```

---

## Common Features Across All Modes

### 1. **Enhanced Context System**
All modes provide agents with:
- **Repository Map**: Complete file structure with function extraction
- **Requirements Content**: What needs to be built
- **Design Content**: How to build it
- **Current Todos**: Specific tasks to complete
- **Agent Profile**: Specialization and available tools

### 2. **Context Compression**
- Automatically triggers when >75% of model's context is used
- Preserves core context (repo map, requirements, design, todos)
- Only compresses conversation history and tool results
- Shows compression statistics

### 3. **Git Integration**
- Automatic repository initialization
- Commits after each task group completion
- Commit messages include task group information
- Can be disabled with `auto_commit=False`

### 4. **Cost Tracking**
- Real-time cost monitoring
- Per-agent cost tracking in multi-agent mode
- Global cost limits and warnings
- Detailed cost reporting

### 5. **Tool System**
- Automatic tool discovery
- Profile-based tool filtering
- Built-in tools for file operations, git, communication
- Extensible tool architecture

---

## Model Recommendations

### Cost-Effective (Recommended)
- **moonshot/kimi-k2-0711-preview**: Best balance of cost and performance
- **moonshot/kimi-k1-32k**: Good for smaller tasks

### High-Performance (Expensive)
- **o3**: Most capable, highest cost
- **gpt-4o-mini**: Good supervisor model
- **anthropic/claude-3-sonnet**: Excellent for complex reasoning

### Usage Guidelines
- **Single Agent**: Use moonshot models for cost efficiency
- **Multi-Agent Supervisor**: Use gpt-4o-mini or o3 for coordination
- **Multi-Agent Workers**: Use moonshot models to keep costs down

---

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```bash
   export MOONSHOT_API_KEY="your_key_here"
   # Or create .env file in project root
   ```

2. **Model Not Available**
   ```bash
   equitrcoder models  # List available models
   ```

3. **High Costs**
   - Use moonshot models instead of OpenAI
   - Set lower `max_cost` limits
   - Use fewer agents in multi-agent mode

4. **Context Limit Reached**
   - System automatically compresses context
   - Reduce `max_iterations` if needed
   - Use models with larger context windows

### Getting Help

```bash
equitrcoder --help           # General help
equitrcoder single --help    # Single agent help
equitrcoder multi --help     # Multi-agent help
equitrcoder tools --list     # Available tools
```

---

## Next Steps

- See [CREATING_MODES.md](./CREATING_MODES.md) for creating custom modes
- See [CREATING_PROFILES.md](./CREATING_PROFILES.md) for creating agent profiles
- Check [examples/](../examples/) for more usage examples