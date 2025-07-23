# EQUITR Coder Terminal Examples

Simulated terminal sessions showing real workflows with EQUITR Coder.

## Example 1: Installing EQUITR Coder

```bash
$ git clone https://github.com/equitr/EQUITR-coder.git
Cloning into 'EQUITR-coder'...
remote: Enumerating objects: 1500, done.
remote: Counting objects: 100% (1500/1500), done.
remote: Compressing objects: 100% (850/850), done.
remote: Total 1500 (delta 650), reused 1500 (delta 650), pack-reused 0
Receiving objects: 100% (1500/1500), 2.1 MiB | 1.5 MiB/s, done.
Resolving deltas: 100% (650/650), done.

$ cd EQUITR-coder

$ ./install.sh
🚀 EQUITR Coder Installation
=============================
Checking Python version...
✅ Python 3.11.5 found
⚠️  No virtual environment detected
Creating virtual environment...
✅ Virtual environment created and activated
Installing dependencies...
Requirement already satisfied: pip in ./equitr-env/lib/python3.11/site-packages (23.2.1)
Collecting typer>=0.9.0
  Downloading typer-0.9.0-py3-none-any.whl (45 kB)
[... dependency installation ...]
Installing EQUITR Coder...
Successfully installed EQUITR-coder-0.1.0
Creating configuration directory...
Creating default configuration...
✅ Default configuration created at ~/.equitr/config.yaml
Testing installation...
✅ EQUITR Coder installed successfully!
✅ Command 'equitrcoder' is available
Version check:
EQUITR Coder v0.1.0

🎉 Installation Complete!

Next Steps:
1. Set your API key:
   export OPENAI_API_KEY='your-api-key-here'

2. Start using EQUITR Coder:
   equitrcoder

3. For help:
   equitrcoder --help

Configuration file: ~/.equitr/config.yaml
Session directory: ~/.equitr/sessions

Happy coding! 🚀

$ export OPENAI_API_KEY="sk-proj-..."
$ equitrcoder --version
EQUITR Coder v0.1.0
```

## Example 2: Simple API Project

```bash
$ mkdir my-todo-api
$ cd my-todo-api
$ equitrcoder

🚀 EQUITR Coder - Interactive Mode

Workflow:
1. Chat with the AI to discuss your requirements
2. AI generates mandatory documentation (todo, requirements, design)
3. Review and approve documentation
4. AI executes tasks using documentation as context

Commands:
  /quit - Exit the session
  /clear - Clear conversation history
  /status - Show session status
  /multi-agent - Toggle multi-agent mode
  /help - Show this help

─────────────────────────────── Configuration ───────────────────────────────
Model: gpt-4o-mini
Profile: default
Repository: /Users/dev/my-todo-api
Budget: $25.0
Multi-agent: Disabled
──────────────────────────────────────────────────────────────────────────────

What would you like to build?
> I want to create a simple REST API for managing todo items

🎯 Starting Planning Conversation
The AI will ask questions to understand your requirements...

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Great! I'd like to understand your requirements better. What programming      │
│ language and framework would you prefer for this REST API?                    │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> Python with FastAPI

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Excellent choice! What database would you like to use for storing the todo    │
│ items?                                                                         │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> SQLite for simplicity

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Perfect! What fields should each todo item have? For example: title,          │
│ description, completed status, due date, priority, etc.                       │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> Title, description, completed status, and created_at timestamp

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Do you need any authentication for the API, or should it be open access?      │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> No authentication needed, keep it simple

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ READY_TO_DOCUMENT                                                             │
╰────────────────────────────────────────────────────────────────────────────────╯

✅ Planning conversation complete!

📋 Generating Documentation...

📋 Generated Documentation

╭─────────────────────────── 📄 Requirements Document ───────────────────────────╮
│ # Todo API Requirements                                                        │
│                                                                                │
│ ## 1. PROJECT OVERVIEW                                                        │
│ - Simple REST API for managing todo items                                     │
│ - Built with Python and FastAPI                                               │
│ - SQLite database for data persistence                                        │
│ - No authentication required                                                  │
│                                                                                │
│ ## 2. FUNCTIONAL REQUIREMENTS                                                 │
│ ### Todo Item Structure                                                        │
│ - title (string): Task title                                                  │
│ - description (string): Detailed description                                  │
│ - completed (boolean): Completion status                                      │
│ - created_at (timestamp): Creation date and time                              │
│                                                                                │
│ ### API Endpoints                                                              │
│ - GET /todos - List all todos                                                 │
│ - POST /todos - Create new todo                                               │
│ - GET /todos/{id} - Get specific todo                                         │
│ - PUT /todos/{id} - Update todo                                               │
│ - DELETE /todos/{id} - Delete todo                                            │
│                                                                                │
│ ## 3. NON-FUNCTIONAL REQUIREMENTS                                             │
│ - Simple and lightweight                                                      │
│ - JSON API responses                                                           │
│ - Proper HTTP status codes                                                     │
│ - Input validation                                                             │
│ - Auto-generated API documentation                                             │
╰────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── 🏗️ Design Document ───────────────────────────────╮
│ # Todo API Design                                                              │
│                                                                                │
│ ## 1. TECHNOLOGY STACK                                                        │
│ - Framework: FastAPI                                                           │
│ - Database: SQLite with SQLAlchemy ORM                                        │
│ - Language: Python 3.8+                                                       │
│ - Validation: Pydantic models                                                  │
│                                                                                │
│ ## 2. PROJECT STRUCTURE                                                       │
│ ```                                                                            │
│ my-todo-api/                                                                   │
│ ├── app/                                                                       │
│ │   ├── __init__.py                                                           │
│ │   ├── main.py          # FastAPI application                                │
│ │   ├── models.py        # SQLAlchemy models                                  │
│ │   ├── schemas.py       # Pydantic schemas                                   │
│ │   └── database.py      # Database configuration                             │
│ ├── requirements.txt     # Python dependencies                                │
│ └── README.md           # Project documentation                                │
│ ```                                                                            │
│                                                                                │
│ ## 3. DATABASE SCHEMA                                                         │
│ ### Todo Table                                                                 │
│ - id (INTEGER, PRIMARY KEY, AUTOINCREMENT)                                    │
│ - title (VARCHAR(200), NOT NULL)                                              │
│ - description (TEXT)                                                           │
│ - completed (BOOLEAN, DEFAULT FALSE)                                          │
│ - created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)                           │
│                                                                                │
│ ## 4. API DESIGN                                                              │
│ ### Endpoints                                                                  │
│ - GET /todos -> List[TodoResponse]                                             │
│ - POST /todos -> TodoResponse                                                  │
│ - GET /todos/{id} -> TodoResponse                                              │
│ - PUT /todos/{id} -> TodoResponse                                              │
│ - DELETE /todos/{id} -> {"message": "Todo deleted"}                           │
╰────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────────── ✅ Todo List ───────────────────────────────────╮
│ # Todo API Implementation Tasks                                                │
│                                                                                │
│ ## 1. SETUP TASKS (High Priority)                                             │
│ 1. Create project structure and directories                                    │
│ 2. Set up virtual environment and dependencies                                 │
│ 3. Initialize FastAPI application                                              │
│ 4. Configure SQLite database connection                                        │
│                                                                                │
│ ## 2. CORE IMPLEMENTATION (High Priority)                                     │
│ 5. Create SQLAlchemy Todo model                                               │
│ 6. Create Pydantic schemas for request/response                               │
│ 7. Implement database initialization                                           │
│ 8. Create GET /todos endpoint                                                  │
│ 9. Create POST /todos endpoint                                                 │
│ 10. Create GET /todos/{id} endpoint                                            │
│ 11. Create PUT /todos/{id} endpoint                                            │
│ 12. Create DELETE /todos/{id} endpoint                                         │
│                                                                                │
│ ## 3. VALIDATION & ERROR HANDLING (Medium Priority)                           │
│ 13. Add input validation for all endpoints                                     │
│ 14. Implement proper error handling                                            │
│ 15. Add HTTP status codes for different scenarios                              │
│                                                                                │
│ ## 4. DOCUMENTATION & TESTING (Medium Priority)                               │
│ 16. Set up automatic API documentation                                         │
│ 17. Create README with setup instructions                                      │
│ 18. Add basic tests for endpoints                                              │
│                                                                                │
│ ## 5. DEPLOYMENT (Low Priority)                                               │
│ 19. Create requirements.txt                                                    │
│ 20. Add Docker configuration (optional)                                        │
╰────────────────────────────────────────────────────────────────────────────────╯

Review documentation: [approve/revise/quit] (approve): approve
✅ Documentation approved!

🚀 Starting Implementation with MANDATORY Documentation Context

╭─────────────────────────────── 🤖 Implementation Complete ───────────────────────╮
│ I've successfully implemented the Todo API based on the approved              │
│ documentation! Here's what was created:                                       │
│                                                                                │
│ 📁 Project Structure:                                                         │
│ - app/main.py: FastAPI application with all endpoints                         │
│ - app/models.py: SQLAlchemy Todo model                                        │
│ - app/schemas.py: Pydantic request/response schemas                           │
│ - app/database.py: Database configuration and connection                      │
│ - requirements.txt: All necessary dependencies                                │
│ - README.md: Setup and usage instructions                                     │
│                                                                                │
│ 🔗 API Endpoints Implemented:                                                 │
│ - GET /todos - List all todos                                                 │
│ - POST /todos - Create new todo                                               │
│ - GET /todos/{id} - Get specific todo                                         │
│ - PUT /todos/{id} - Update todo                                               │
│ - DELETE /todos/{id} - Delete todo                                            │
│                                                                                │
│ ✅ Features Included:                                                         │
│ - SQLite database with SQLAlchemy ORM                                         │
│ - Automatic API documentation at /docs                                        │
│ - Input validation with Pydantic                                              │
│ - Proper HTTP status codes                                                     │
│ - Error handling for not found cases                                          │
│                                                                                │
│ 🚀 To start the server:                                                       │
│ 1. pip install -r requirements.txt                                            │
│ 2. uvicorn app.main:app --reload                                              │
│ 3. Visit http://localhost:8000/docs for API documentation                     │
╰────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────── 📊 Usage Stats ───────────────────────────────╮
│ Total tokens: 3,842                                                           │
│ Cost: $0.0156                                                                 │
╰────────────────────────────────────────────────────────────────────────────────╯

Start another project?: [y/N] n

👋 Goodbye!

$ ls -la
total 16
drwxr-xr-x  4 dev  staff  128 Dec 18 10:30 .
drwxr-xr-x  3 dev  staff   96 Dec 18 10:25 ..
drwxr-xr-x  5 dev  staff  160 Dec 18 10:30 app
drwxr-xr-x  5 dev  staff  160 Dec 18 10:30 docs
-rw-r--r--  1 dev  staff  245 Dec 18 10:30 requirements.txt
-rw-r--r--  1 dev  staff 1534 Dec 18 10:30 README.md

$ ls docs/
design.md        requirements.md  todos.md

$ cat requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0

$ uvicorn app.main:app --reload
INFO:     Will watch for changes in these directories: ['/Users/dev/my-todo-api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

# Server is now running at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

## Example 3: Multi-Agent Complex Project

```bash
$ mkdir ecommerce-platform
$ cd ecommerce-platform
$ equitrcoder --multi-agent --budget 50.0

🚀 EQUITR Coder - Interactive Mode

─────────────────────────────── Configuration ───────────────────────────────
Model: gpt-4o-mini
Profile: default
Repository: /Users/dev/ecommerce-platform
Budget: $50.0
Multi-agent: Enabled
──────────────────────────────────────────────────────────────────────────────

What would you like to build?
> I want to create a microservices e-commerce platform with user management, product catalog, shopping cart, and order processing

🎯 Starting Planning Conversation
The AI will ask questions to understand your requirements...

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Excellent! A microservices e-commerce platform is a great use case for       │
│ multi-agent mode. What technology stack would you prefer for the backend     │
│ services?                                                                     │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> Python with FastAPI for services, PostgreSQL for databases, Redis for caching, and Docker for containerization

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Great choice! How should the services communicate with each other?            │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> REST APIs for synchronous communication and RabbitMQ for asynchronous messaging

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ Perfect! What about the frontend? Would you like a web interface?            │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> Yes, a React frontend with a modern dashboard for managing products and orders

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ How should authentication and authorization work across the microservices?    │
╰────────────────────────────────────────────────────────────────────────────────╯

Your response
> JWT tokens with a centralized auth service and role-based access control

╭─────────────────────────────── 🤖 EQUITR Coder ───────────────────────────────╮
│ READY_TO_DOCUMENT                                                             │
╰────────────────────────────────────────────────────────────────────────────────╯

✅ Planning conversation complete!

📋 Generating Documentation...

[... Documentation generation process ...]

Review documentation: [approve/revise/quit] (approve): approve
✅ Documentation approved!

🚀 Starting Implementation with MANDATORY Documentation Context

🤖 Using multi-agent mode with MANDATORY documentation context

📋 Created 6 tasks for multi-agent execution:
1. Infrastructure and API Gateway Setup
2. User Management Service Implementation
3. Product Catalog Service Implementation
4. Shopping Cart Service Implementation
5. Order Processing Service Implementation
6. React Frontend Application

🔄 Spawning worker agents for parallel execution...

Agent: infrastructure_worker
✓ Task 1: Infrastructure setup complete
  - Docker configurations created
  - PostgreSQL and Redis setup
  - API Gateway configured with Kong
  - RabbitMQ message broker setup

Agent: backend_worker_1
✓ Task 2: User Management Service complete
  - JWT authentication implemented
  - User registration and login endpoints
  - Role-based access control
  - PostgreSQL database schema

Agent: backend_worker_2
✓ Task 3: Product Catalog Service complete
  - Product CRUD operations
  - Category management
  - Search functionality
  - Image handling system

Agent: backend_worker_3
✓ Task 4: Shopping Cart Service complete
  - Redis-based cart persistence
  - Cart session management
  - Add/remove item endpoints
  - Cart calculation logic

Agent: backend_worker_4
✓ Task 5: Order Processing Service complete
  - Order creation workflow
  - Payment integration setup
  - Order status tracking
  - Inventory management

Agent: frontend_worker
✓ Task 6: React Frontend complete
  - Modern dashboard interface
  - Product management screens
  - Shopping cart functionality
  - Order management system

✅ Multi-agent execution completed!
📊 Summary: 6 tasks completed successfully

╭─────────────────────────────── 🤖 Implementation Complete ───────────────────────╮
│ Multi-agent e-commerce platform implementation completed!                     │
│                                                                                │
│ 🏗️ Microservices Created:                                                     │
│ - User Management Service (Port 8001)                                         │
│ - Product Catalog Service (Port 8002)                                         │
│ - Shopping Cart Service (Port 8003)                                           │
│ - Order Processing Service (Port 8004)                                        │
│ - API Gateway (Port 8000)                                                     │
│                                                                                │
│ 🌐 Frontend Application:                                                      │
│ - React dashboard (Port 3000)                                                 │
│ - Product management interface                                                 │
│ - Shopping cart functionality                                                  │
│ - Order management system                                                      │
│                                                                                │
│ 📦 Infrastructure:                                                            │
│ - Docker Compose configuration                                                 │
│ - PostgreSQL databases per service                                             │
│ - Redis cache cluster                                                          │
│ - RabbitMQ message broker                                                      │
│                                                                                │
│ 🚀 To start the platform:                                                     │
│ 1. docker-compose up -d                                                       │
│ 2. Visit http://localhost:3000 for the dashboard                              │
│ 3. API Gateway at http://localhost:8000                                       │
│                                                                                │
│ 📚 Generated Documentation:                                                   │
│ - Complete API documentation                                                   │
│ - Service architecture diagrams                                               │
│ - Deployment instructions                                                      │
│ - Testing guidelines                                                           │
╰────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────── 📊 Usage Stats ───────────────────────────────╮
│ Total tokens: 15,847                                                          │
│ Cost: $0.7234                                                                 │
│ Agents used: 6                                                                │
│ Tasks completed: 6                                                            │
│ Parallel execution time: 12m 34s                                              │
╰────────────────────────────────────────────────────────────────────────────────╯

Start another project?: [y/N] n

$ ls -la
total 32
drwxr-xr-x  8 dev  staff  256 Dec 18 11:15 .
drwxr-xr-x  3 dev  staff   96 Dec 18 10:45 ..
drwxr-xr-x  5 dev  staff  160 Dec 18 11:15 docs
drwxr-xr-x  4 dev  staff  128 Dec 18 11:15 frontend
drwxr-xr-x  3 dev  staff   96 Dec 18 11:15 infrastructure
drwxr-xr-x  6 dev  staff  192 Dec 18 11:15 services
-rw-r--r--  1 dev  staff 2134 Dec 18 11:15 docker-compose.yml
-rw-r--r--  1 dev  staff 3421 Dec 18 11:15 README.md

$ docker-compose up -d
Creating network "ecommerce-platform_default" with the default driver
Creating ecommerce-platform_postgres_1 ... done
Creating ecommerce-platform_redis_1    ... done
Creating ecommerce-platform_rabbitmq_1 ... done
Creating ecommerce-platform_user-service_1 ... done
Creating ecommerce-platform_product-service_1 ... done
Creating ecommerce-platform_cart-service_1 ... done
Creating ecommerce-platform_order-service_1 ... done
Creating ecommerce-platform_api-gateway_1 ... done
Creating ecommerce-platform_frontend_1 ... done

$ docker-compose ps
                   Name                                 Command               State           Ports
----------------------------------------------------------------------------------------------------------
ecommerce-platform_api-gateway_1        uvicorn app.main:app --hos ...   Up      0.0.0.0:8000->8000/tcp
ecommerce-platform_cart-service_1       uvicorn app.main:app --hos ...   Up      0.0.0.0:8003->8000/tcp
ecommerce-platform_frontend_1           npm start                        Up      0.0.0.0:3000->3000/tcp
ecommerce-platform_order-service_1      uvicorn app.main:app --hos ...   Up      0.0.0.0:8004->8000/tcp
ecommerce-platform_postgres_1           docker-entrypoint.sh postgres   Up      0.0.0.0:5432->5432/tcp
ecommerce-platform_product-service_1    uvicorn app.main:app --hos ...   Up      0.0.0.0:8002->8000/tcp
ecommerce-platform_rabbitmq_1           docker-entrypoint.sh rabbi ...   Up      0.0.0.0:5672->5672/tcp
ecommerce-platform_redis_1              docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
ecommerce-platform_user-service_1       uvicorn app.main:app --hos ...   Up      0.0.0.0:8001->8000/tcp

# All services are now running!
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# Service docs: http://localhost:8001/docs, 8002/docs, etc.
```

## Example 4: CLI Options and Commands

```bash
# Basic usage
$ equitrcoder
[Interactive session starts]

# Show help
$ equitrcoder --help
Usage: equitrcoder [OPTIONS]

 Start EQUITR Coder interactive session with mandatory documentation
 generation.

Options:
  --repo         -r      TEXT   Repository path to analyze [default: .]
  --profile      -p      TEXT   Configuration profile to use [default: default]
  --model        -m      TEXT   LLM model to use (overrides config) [default: None]
  --budget       -b      FLOAT  Budget limit in USD (overrides config) [default: None]
  --multi-agent  -M             Enable multi-agent mode
  --version      -v             Show version information
  --help                        Show this message and exit.

# Show version
$ equitrcoder --version
EQUITR Coder v0.1.0

# Use specific model
$ equitrcoder --model gpt-4o
[Session starts with GPT-4o]

# Enable multi-agent mode
$ equitrcoder --multi-agent
[Multi-agent session starts]

# Set budget limit
$ equitrcoder --budget 10.0
[Session starts with $10 budget]

# Work in specific directory
$ equitrcoder --repo /path/to/my/project
[Session starts in specified directory]

# Combine options
$ equitrcoder --multi-agent --model gpt-4o --budget 100.0 --repo ./my-complex-project
[Advanced session with all options]
```

## Example 5: Interactive Session Commands

```bash
$ equitrcoder

What would you like to build?
> /help

🚀 EQUITR Coder - Interactive Mode

Workflow:
1. Chat with the AI to discuss your requirements
2. AI generates mandatory documentation (todo, requirements, design)
3. Review and approve documentation
4. AI executes tasks using documentation as context

Commands:
  /quit - Exit the session
  /clear - Clear conversation history
  /status - Show session status
  /multi-agent - Toggle multi-agent mode
  /help - Show this help

What would you like to build?
> /status

╭─────────────────────────────── Session Status ───────────────────────────────╮
│ Messages: 2                                                                   │
│ Total cost: $0.0000                                                          │
│ Iterations: 0                                                                 │
│ Multi-agent: Disabled                                                         │
│ Model: gpt-4o-mini                                                           │
╰───────────────────────────────────────────────────────────────────────────────╯

What would you like to build?
> /multi-agent
✅ Multi-agent mode enabled

What would you like to build?
> /clear
✅ Conversation history cleared

What would you like to build?
> I want to build a simple calculator app

[... conversation continues ...]

What would you like to build?
> /quit
👋 Goodbye!

$
```

## Example 6: Configuration and Troubleshooting

```bash
# Check current configuration
$ cat ~/.equitr/config.yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.3
  max_tokens: 4000
  budget: 25.0

orchestrator:
  use_multi_agent: false
  max_iterations: 20

session:
  session_dir: "~/.equitr/sessions"
  max_context: 32000

# Check sessions
$ ls ~/.equitr/sessions/
session_20231218_103045.json
session_20231218_114521.json

# Test API key
$ equitrcoder --model gpt-4o-mini --budget 1.0
[If API key is invalid, you'll get an error]

# Debug with minimal budget
$ equitrcoder --budget 0.50
[Useful for testing without spending much]

# Reset configuration
$ rm -rf ~/.equitr/config.yaml
$ equitrcoder
[Will create default configuration]
```

These terminal examples show the complete workflow from installation through complex multi-agent projects, demonstrating how EQUITR Coder works in practice.