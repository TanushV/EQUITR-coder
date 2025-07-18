# EQUITR Coder Quickstart Guide

Get started with EQUITR Coder in 5 minutes.

## Prerequisites

- Python 3.8+
- Git
- OpenAI API key (or other LLM provider)

## Installation

```bash
# Clone and install
git clone https://github.com/equitr/EQUITR-coder.git
cd EQUITR-coder
pip install -e .

# Set up API key
export OPENAI_API_KEY="your-api-key-here"
```

## Your First Project

### 1. Start EQUITR Coder
```bash
equitrcoder
```

### 2. Describe Your Project
```
What would you like to build?
> I want to create a simple todo list API with Python
```

### 3. Answer Planning Questions
The AI will ask clarifying questions:
```
🤖 EQUITR Coder: What framework would you prefer for the API?
> FastAPI

🤖 EQUITR Coder: What database would you like to use?
> SQLite for simplicity

🤖 EQUITR Coder: Do you need user authentication?
> No, just basic CRUD operations

✅ Planning conversation complete!
```

### 4. Review Generated Documentation
EQUITR will generate three documents:
- **Requirements**: What the API should do
- **Design**: How it will be built
- **Todos**: Step-by-step implementation tasks

Review and approve:
```
Review documentation: [approve/revise/quit] (approve): approve
```

### 5. Watch Implementation
The AI will implement your project following the generated documentation:
```
🚀 Starting Implementation

🤖 Implementation Complete
I've created a FastAPI todo list API with:
- SQLite database with SQLAlchemy
- CRUD endpoints for todos
- Pydantic models for validation
- API documentation with Swagger
- Docker configuration
...
```

## What Gets Generated

### Project Structure
```
your-project/
├── docs/
│   ├── requirements.md    # Generated requirements
│   ├── design.md         # System design
│   └── todos.md          # Implementation tasks
├── app/
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   └── database.py       # Database setup
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── README.md            # Project documentation
```

### Documentation Files
Each project gets comprehensive documentation:

**requirements.md**: Detailed functional and non-functional requirements
**design.md**: System architecture, database schema, API design
**todos.md**: Prioritized implementation tasks

## Advanced Usage

### Multi-Agent Mode
For complex projects:
```bash
equitrcoder --multi-agent
```

### Custom Configuration
```bash
equitrcoder --model gpt-4o --budget 20.0 --repo ./my-project
```

### Resume Session
```bash
equitrcoder --session my-session-id
```

## CLI Commands

Within the interactive session:
- `/quit` - Exit
- `/clear` - Clear conversation
- `/status` - Show session info
- `/multi-agent` - Toggle multi-agent mode
- `/help` - Show help

## Configuration

Create `~/.equitr/config.yaml`:
```yaml
llm:
  model: "gpt-4o"
  budget: 25.0
  temperature: 0.3

orchestrator:
  use_multi_agent: false
  max_iterations: 20
```

## Example Projects

### Simple API
```
What would you like to build?
> A REST API for managing books with CRUD operations

Generated:
- FastAPI with SQLAlchemy
- Book model with title, author, ISBN
- CRUD endpoints
- API documentation
```

### Frontend App
```
What would you like to build?
> A React dashboard for displaying user analytics

Generated:
- React app with TypeScript
- Chart.js for visualizations
- Material-UI components
- API integration setup
```

### Full-Stack App
```
What would you like to build?
> A complete blog platform with frontend and backend

Generated:
- FastAPI backend with PostgreSQL
- React frontend with authentication
- Docker compose setup
- Comprehensive documentation
```

## Tips for Success

### 1. Be Specific
Instead of: "I want a web app"
Say: "I want a FastAPI blog with PostgreSQL, JWT auth, and React frontend"

### 2. Mention Constraints
- Technology preferences
- Performance requirements
- Deployment needs
- Budget constraints

### 3. Use Multi-Agent for Complex Projects
Enable when building:
- Multiple microservices
- Complex system architectures
- Projects with many independent components

### 4. Review Documentation Carefully
The generated docs become the context for all implementation. Make sure they're accurate.

## Common Workflows

### API Development
1. Planning → Discuss endpoints, database, auth
2. Documentation → Requirements, design, todos
3. Implementation → Follow todo list step-by-step

### Frontend Development
1. Planning → UI requirements, components, data flow
2. Documentation → User stories, component design, tasks
3. Implementation → Component-by-component development

### Full-Stack Development
1. Planning → Both frontend and backend requirements
2. Documentation → System design with integration points
3. Implementation → Often uses multi-agent mode

## Next Steps

1. Try the basic workflow with a simple project
2. Explore multi-agent mode for complex projects
3. Customize configuration for your needs
4. Check out the examples directory for more patterns

## Getting Help

- Use `/help` in interactive mode
- Check `/status` for session information
- Review generated documentation in `docs/`
- Consult the main README for detailed information