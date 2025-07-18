# EQUITR Coder

An advanced AI coding assistant with interactive documentation-driven development.

## Overview

EQUITR Coder is designed around a **Documentation-First Interactive Workflow**:

1. **Interactive Planning**: Have a conversation with the AI to discuss your project requirements
2. **Mandatory Documentation**: AI generates comprehensive documentation (requirements, design, todos)
3. **Context-Aware Implementation**: AI uses the generated documentation as context for all subsequent tasks
4. **Multi-Agent Support**: Complex projects can leverage multiple AI agents working in parallel

## Installation

```bash
# Clone the repository
git clone https://github.com/equitr/EQUITR-coder.git
cd EQUITR-coder

# Install dependencies
pip install -r requirements.txt

# Install the CLI
pip install -e .
```

## Usage

EQUITR Coder has **only one command**: `equitrcoder`

```bash
# Start interactive session
equitrcoder

# With specific options
equitrcoder --model gpt-4o --multi-agent --budget 10.0

# In a specific repository
equitrcoder --repo /path/to/your/project
```

## Interactive Workflow

### 1. Planning Conversation
When you start `equitrcoder`, you'll have a conversation with the AI to understand your project:

```
What would you like to build?
> I want to create a web API for managing tasks

🤖 EQUITR Coder: What kind of authentication do you want to use?
> JWT tokens with user registration and login

🤖 EQUITR Coder: What database would you prefer?
> PostgreSQL with SQLAlchemy

🤖 EQUITR Coder: Any specific framework preferences?
> FastAPI with Pydantic models

✅ Planning conversation complete!
```

### 2. Documentation Generation
After the conversation, EQUITR generates three mandatory documents:

- **📄 Requirements Document**: Detailed functional and non-functional requirements
- **🏗️ Design Document**: System architecture, component specifications, and implementation strategy
- **✅ Todo List**: Prioritized, actionable tasks with dependencies

### 3. Documentation Review
You review and approve the generated documentation:

```
📋 Generated Documentation

Requirements Document:
# Task Management API Requirements
## 1. PROJECT OVERVIEW
- RESTful API for task management
- JWT authentication system
- PostgreSQL database backend
...

Design Document:
# System Architecture
## 1. TECHNOLOGY STACK
- FastAPI framework
- PostgreSQL with SQLAlchemy ORM
- JWT for authentication
...

Todo List:
# Implementation Tasks
## 1. SETUP TASKS
1. Initialize FastAPI project structure
2. Set up PostgreSQL database
3. Configure JWT authentication
...

Review documentation: [approve/revise/quit] (approve): 
```

### 4. Context-Aware Implementation
Once approved, the AI uses the documentation as context for all implementation tasks:

```
🚀 Starting Implementation

🤖 Implementation Complete
Based on the requirements and design documents, I've implemented:
- FastAPI project structure with proper routing
- PostgreSQL database models using SQLAlchemy
- JWT authentication system with user registration
- Task CRUD operations with proper validation
- API documentation with OpenAPI/Swagger
...
```

## Multi-Agent Mode

For complex projects, enable multi-agent mode:

```bash
equitrcoder --multi-agent
```

In multi-agent mode:
- **Supervisor Agent**: Handles planning, task decomposition, and coordination
- **Worker Agents**: Execute specific tasks in parallel
- **Message Pool**: Enables inter-agent communication and synchronization

## Configuration

Configuration files are stored in `~/.equitr/config.yaml`:

```yaml
llm:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 4000
  budget: 50.0

orchestrator:
  use_multi_agent: false
  max_iterations: 20

session:
  session_dir: "~/.equitr/sessions"
  max_context: 32000

repository:
  ignore_patterns:
    - "*.log"
    - "node_modules/"
    - "__pycache__/"
```

## Features

### Core Features
- **Interactive Planning**: Conversational requirement gathering
- **Mandatory Documentation**: Automatic generation of requirements, design, and todo documents
- **Context-Aware Execution**: All tasks use generated documentation as context
- **Session Management**: Persistent conversation history
- **Git Integration**: Automatic commits for planning and implementation milestones

### Advanced Features
- **Multi-Agent Orchestration**: Parallel execution of complex tasks
- **Tool Ecosystem**: Extensible tool system for file operations, git commands, etc.
- **Budget Management**: Cost tracking and limits
- **Model Flexibility**: Support for various LLM providers (OpenAI, Anthropic, etc.)

## Commands

Within the interactive session:

- `/quit` - Exit the session
- `/clear` - Clear conversation history
- `/status` - Show session status
- `/multi-agent` - Toggle multi-agent mode
- `/help` - Show help information

## Project Structure

```
EQUITR-coder/
├── EQUITR_coder/
│   ├── core/
│   │   ├── orchestrator.py      # Main orchestration logic
│   │   ├── documentation.py     # Documentation generation
│   │   ├── supervisor.py        # Multi-agent coordination
│   │   └── config.py           # Configuration management
│   ├── providers/
│   │   ├── openrouter.py       # OpenRouter provider
│   │   └── litellm.py          # LiteLLM provider
│   ├── tools/
│   │   └── builtin/            # Built-in tools
│   └── interactive_cli.py      # Main CLI interface
├── docs/                       # Generated documentation
├── examples/                   # Usage examples
└── requirements.txt
```

## Documentation Files

Every project generates these files in the `docs/` directory:

- `requirements.md` - Comprehensive requirements document
- `design.md` - System architecture and design specifications
- `todos.md` - Prioritized implementation tasks

These files are used as context for all subsequent AI interactions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `equitrcoder`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/equitr/EQUITR-coder/issues
- Documentation: https://github.com/equitr/EQUITR-coder/wiki