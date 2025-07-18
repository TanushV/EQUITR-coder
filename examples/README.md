# EQUITR Coder Examples

This directory contains example workflows and usage patterns for EQUITR Coder.

## Example Workflows

### 1. Web API Development
```bash
equitrcoder --repo ./my-api-project
```

**Sample Conversation:**
```
What would you like to build?
> I want to create a REST API for a blog platform

🤖 EQUITR Coder: What features should the blog platform have?
> User authentication, create/edit/delete posts, comments, and categories

🤖 EQUITR Coder: What technology stack would you prefer?
> Python with FastAPI, PostgreSQL database, and JWT authentication

🤖 EQUITR Coder: Do you need any specific deployment considerations?
> Docker containers and environment-based configuration

✅ Planning conversation complete!
```

**Generated Documentation:**
- Requirements: User stories, API endpoints, authentication requirements
- Design: Database schema, API architecture, security considerations
- Todos: Step-by-step implementation tasks

### 2. Frontend Application
```bash
equitrcoder --repo ./my-frontend-app
```

**Sample Conversation:**
```
What would you like to build?
> A React dashboard for data visualization

🤖 EQUITR Coder: What kind of data will you be visualizing?
> Sales metrics, user analytics, and performance KPIs

🤖 EQUITR Coder: Any specific charting libraries or UI frameworks?
> Chart.js for graphs and Material-UI for components

🤖 EQUITR Coder: How will the data be fetched?
> REST API calls to our backend service

✅ Planning conversation complete!
```

### 3. Multi-Agent Complex Project
```bash
equitrcoder --multi-agent --repo ./complex-project
```

**Sample Conversation:**
```
What would you like to build?
> A microservices architecture with API gateway, auth service, and data processing

🤖 EQUITR Coder: How many microservices do you envision?
> Around 4-5 services: auth, user management, data processing, notification, and API gateway

🤖 EQUITR Coder: What's your preferred container orchestration?
> Kubernetes with Helm charts for deployment

🤖 EQUITR Coder: Any specific messaging or database requirements?
> RabbitMQ for async communication, PostgreSQL for main data, Redis for caching

✅ Planning conversation complete!
```

**Multi-Agent Execution:**
- Supervisor coordinates the overall architecture
- Worker agents handle individual services
- Parallel implementation of independent components

## CLI Options Examples

### Basic Usage
```bash
# Start with default settings
equitrcoder

# Specify model and budget
equitrcoder --model gpt-4o --budget 25.0

# Use specific configuration profile
equitrcoder --profile production

# Multi-agent mode
equitrcoder --multi-agent
```

### Repository-Specific
```bash
# Work in specific directory
equitrcoder --repo /path/to/project

# Resume previous session
equitrcoder --session my-session-id
```

## Interactive Commands

Within any session:

```bash
# View session information
/status

# Clear conversation history
/clear

# Toggle multi-agent mode
/multi-agent

# Exit session
/quit
```

## Documentation Examples

### Generated Requirements Document
```markdown
# Task Management API Requirements

## 1. PROJECT OVERVIEW
- RESTful API for task management
- User authentication and authorization
- CRUD operations for tasks and projects

## 2. FUNCTIONAL REQUIREMENTS
### User Management
- User registration and login
- JWT-based authentication
- Role-based access control

### Task Management
- Create, read, update, delete tasks
- Task categorization and tagging
- Due dates and priority levels
```

### Generated Design Document
```markdown
# System Architecture

## 1. TECHNOLOGY STACK
- FastAPI framework
- PostgreSQL with SQLAlchemy ORM
- JWT for authentication
- Docker for containerization

## 2. DATABASE SCHEMA
### Users Table
- id (UUID, primary key)
- email (string, unique)
- password_hash (string)
- created_at (timestamp)

### Tasks Table
- id (UUID, primary key)
- title (string)
- description (text)
- user_id (UUID, foreign key)
- due_date (timestamp)
```

### Generated Todo List
```markdown
# Implementation Tasks

## 1. SETUP TASKS (High Priority)
1. Initialize FastAPI project structure
2. Set up PostgreSQL database connection
3. Configure JWT authentication middleware
4. Create database migration system

## 2. CORE IMPLEMENTATION (High Priority)
5. Implement user registration endpoint
6. Implement user login endpoint
7. Create task CRUD endpoints
8. Add input validation with Pydantic

## 3. TESTING (Medium Priority)
9. Write unit tests for authentication
10. Write integration tests for API endpoints
11. Set up test database
```

## Best Practices

### 1. Prepare Your Requirements
Before starting, think about:
- Core functionality needed
- Technology preferences
- Deployment requirements
- Performance considerations

### 2. Be Specific in Conversations
- Mention specific technologies when you have preferences
- Describe user workflows and use cases
- Clarify any constraints or requirements

### 3. Review Documentation Carefully
- Check that requirements match your vision
- Verify design decisions align with your needs
- Ensure todos are actionable and complete

### 4. Use Multi-Agent for Complex Projects
Enable multi-agent mode when:
- Building multiple interconnected components
- Handling complex system architectures
- Need parallel development of independent modules

## Common Patterns

### API Development Pattern
1. Plan → Authentication + Core endpoints + Database design
2. Generate → Requirements with API specs + Design with schemas + Todos with priorities
3. Implement → Step-by-step following the todo list

### Frontend Development Pattern
1. Plan → UI/UX requirements + Component structure + Data flow
2. Generate → Requirements with user stories + Design with component hierarchy + Todos with implementation order
3. Implement → Following the component-based todo structure

### Full-Stack Pattern
1. Plan → Both frontend and backend requirements + Integration points
2. Generate → Comprehensive requirements + System design + Coordinated todos
3. Implement → Often benefits from multi-agent mode for parallel development

## Configuration Examples

### Development Configuration
```yaml
# ~/.equitr/config.yaml
llm:
  model: "gpt-4o-mini"  # Cost-effective for development
  budget: 10.0
  temperature: 0.3

orchestrator:
  use_multi_agent: false
  max_iterations: 15
```

### Production Configuration
```yaml
# ~/.equitr/config.yaml
llm:
  model: "gpt-4o"  # Higher quality for production
  budget: 50.0
  temperature: 0.1

orchestrator:
  use_multi_agent: true
  max_iterations: 25
```

## Troubleshooting

### Common Issues
1. **Documentation not generated**: Check API key and model availability
2. **Multi-agent mode not working**: Verify configuration and model compatibility
3. **Session not persisting**: Check session directory permissions
4. **Budget exceeded**: Adjust budget in configuration or use smaller model

### Getting Help
- Use `/help` command in interactive mode
- Check configuration with `/status`
- Review generated documentation in `docs/` directory
- Consult the main README for detailed setup instructions