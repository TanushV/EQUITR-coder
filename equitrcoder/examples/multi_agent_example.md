# Multi-Agent Mode Example

This example demonstrates how to use EQUITR Coder's multi-agent mode for complex projects.

## When to Use Multi-Agent Mode

Multi-agent mode is ideal for:
- **Complex System Architecture**: Multiple interconnected components
- **Microservices**: Independent services that need coordination
- **Parallel Development**: Components that can be built simultaneously
- **Large Projects**: Projects with many independent modules

## Example: E-commerce Platform

Let's build a complete e-commerce platform with multi-agent coordination.

### 1. Start Multi-Agent Mode
```bash
equitrcoder --multi-agent --repo ./ecommerce-platform
```

### 2. Initial Planning Conversation
```
What would you like to build?
> I want to create a complete e-commerce platform with microservices architecture

🤖 EQUITR Coder: What microservices do you envision for the platform?
> User management, product catalog, shopping cart, payment processing, order management, and inventory tracking

🤖 EQUITR Coder: What technology stack would you prefer?
> Python with FastAPI for backend services, React for frontend, PostgreSQL for databases, Redis for caching, and Docker for containerization

🤖 EQUITR Coder: How should the services communicate?
> REST APIs between services and message queues (RabbitMQ) for async operations

🤖 EQUITR Coder: What about authentication and authorization?
> JWT tokens with OAuth2, centralized auth service, and role-based access control

🤖 EQUITR Coder: Any specific deployment requirements?
> Kubernetes deployment with Helm charts, environment-based configuration, and monitoring setup

✅ Planning conversation complete!
```

### 3. Generated Documentation

#### Requirements Document
```markdown
# E-commerce Platform Requirements

## 1. PROJECT OVERVIEW
- Microservices-based e-commerce platform
- Scalable architecture with independent services
- Modern web frontend with React

## 2. MICROSERVICES ARCHITECTURE
### User Management Service
- User registration and authentication
- Profile management
- Role-based access control

### Product Catalog Service
- Product CRUD operations
- Category management
- Search and filtering capabilities

### Shopping Cart Service
- Cart management per user
- Add/remove items
- Persistent cart storage

### Payment Processing Service
- Multiple payment methods
- Transaction processing
- Payment history

### Order Management Service
- Order creation and tracking
- Order status updates
- Order history

### Inventory Service
- Stock management
- Inventory tracking
- Low stock alerts

## 3. NON-FUNCTIONAL REQUIREMENTS
- High availability (99.9% uptime)
- Scalability to handle 10,000+ concurrent users
- Response time under 200ms for most operations
- Secure payment processing (PCI compliance)
```

#### Design Document
```markdown
# E-commerce Platform Design

## 1. SYSTEM ARCHITECTURE
### Microservices Architecture
- API Gateway (Kong/Nginx)
- Service Discovery (Consul/Eureka)
- Message Broker (RabbitMQ)
- Cache Layer (Redis)
- Database per Service (PostgreSQL)

### Communication Patterns
- Synchronous: REST APIs for user-facing operations
- Asynchronous: Message queues for background tasks
- Event-driven: Domain events for cross-service communication

## 2. SERVICE SPECIFICATIONS
### User Management Service
- **Database**: PostgreSQL
- **Endpoints**: /auth, /users, /profiles
- **Dependencies**: None (core service)

### Product Catalog Service
- **Database**: PostgreSQL with search index
- **Endpoints**: /products, /categories, /search
- **Dependencies**: None

### Shopping Cart Service
- **Database**: Redis for session storage
- **Endpoints**: /cart, /cart/items
- **Dependencies**: User Management, Product Catalog

### Payment Processing Service
- **Database**: PostgreSQL for transaction logs
- **Endpoints**: /payments, /transactions
- **Dependencies**: User Management, Order Management

### Order Management Service
- **Database**: PostgreSQL
- **Endpoints**: /orders, /order-status
- **Dependencies**: User Management, Product Catalog, Payment

### Inventory Service
- **Database**: PostgreSQL
- **Endpoints**: /inventory, /stock
- **Dependencies**: Product Catalog

## 3. DEPLOYMENT ARCHITECTURE
- Kubernetes cluster with namespaces per environment
- Helm charts for service deployment
- CI/CD pipeline with GitOps
- Monitoring with Prometheus and Grafana
```

#### Todo List
```markdown
# E-commerce Platform Implementation Tasks

## 1. INFRASTRUCTURE SETUP (High Priority)
1. Set up Kubernetes cluster configuration
2. Create Docker images for each service
3. Configure API Gateway (Kong)
4. Set up RabbitMQ message broker
5. Configure Redis cluster for caching
6. Set up PostgreSQL databases per service

## 2. CORE SERVICES (High Priority)
### User Management Service
7. Implement user registration endpoint
8. Implement JWT authentication
9. Create user profile management
10. Add role-based access control

### Product Catalog Service
11. Create product CRUD endpoints
12. Implement category management
13. Add search functionality with indexing
14. Create product image handling

### Shopping Cart Service
15. Implement cart session management
16. Create add/remove item endpoints
17. Add cart persistence with Redis
18. Implement cart expiration logic

## 3. BUSINESS LOGIC (Medium Priority)
### Payment Processing Service
19. Integrate payment gateway (Stripe/PayPal)
20. Implement transaction processing
21. Add payment method management
22. Create payment history endpoints

### Order Management Service
23. Implement order creation workflow
24. Add order status tracking
25. Create order history endpoints
26. Implement order cancellation logic

### Inventory Service
27. Create stock management endpoints
28. Implement inventory tracking
29. Add low stock alerts
30. Create inventory reports

## 4. FRONTEND (Medium Priority)
31. Create React application structure
32. Implement user authentication UI
33. Build product catalog interface
34. Create shopping cart component
35. Implement checkout process
36. Add order management dashboard

## 5. INTEGRATION & TESTING (Medium Priority)
37. Set up service-to-service communication
38. Implement event-driven messaging
39. Create integration tests
40. Set up end-to-end testing
41. Performance testing and optimization

## 6. DEPLOYMENT & MONITORING (Low Priority)
42. Create Helm charts for all services
43. Set up CI/CD pipelines
44. Configure monitoring and logging
45. Set up alerts and notifications
46. Create deployment documentation
```

### 4. Multi-Agent Execution

With multi-agent mode enabled, EQUITR Coder will:

```
🤖 Using multi-agent mode for complex project

📋 Created 6 tasks for multi-agent execution:
1. Infrastructure and Gateway Setup
2. User Management Service Implementation
3. Product Catalog Service Implementation
4. Shopping Cart Service Implementation
5. Payment and Order Services Implementation
6. Frontend Application Development

🔄 Spawning worker agents for parallel execution...

Agent: infrastructure_worker
✓ Task 1: Infrastructure setup complete
  - Kubernetes configurations created
  - Docker images configured
  - API Gateway setup with Kong
  - RabbitMQ and Redis configured

Agent: backend_worker_1
✓ Task 2: User Management Service complete
  - JWT authentication implemented
  - User registration and profile endpoints
  - Role-based access control
  - PostgreSQL database schema

Agent: backend_worker_2
✓ Task 3: Product Catalog Service complete
  - Product CRUD operations
  - Category management
  - Search functionality with indexing
  - Image handling system

Agent: backend_worker_3
✓ Task 4: Shopping Cart Service complete
  - Redis-based cart persistence
  - Cart session management
  - Add/remove item endpoints
  - Cart expiration logic

Agent: backend_worker_4
✓ Task 5: Payment and Order Services complete
  - Payment gateway integration
  - Order creation workflow
  - Transaction processing
  - Order status tracking

Agent: frontend_worker
✓ Task 6: Frontend Application complete
  - React application with routing
  - Authentication UI components
  - Product catalog interface
  - Shopping cart and checkout
  - Order management dashboard

✅ Multi-agent execution completed!
📊 Summary: 6 tasks completed successfully
```

### 5. Generated Project Structure

```
ecommerce-platform/
├── docs/
│   ├── requirements.md
│   ├── design.md
│   └── todos.md
├── infrastructure/
│   ├── kubernetes/
│   │   ├── namespaces.yaml
│   │   ├── api-gateway.yaml
│   │   └── databases.yaml
│   ├── docker-compose.yml
│   └── helm-charts/
├── services/
│   ├── user-management/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── product-catalog/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── shopping-cart/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── payment-processing/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── order-management/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── inventory/
│       ├── app/
│       ├── Dockerfile
│       └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── tests/
│   ├── integration/
│   ├── e2e/
│   └── performance/
└── README.md
```

## Multi-Agent Coordination Features

### 1. Parallel Execution
- Multiple worker agents handle different services simultaneously
- Tasks are executed in parallel when dependencies allow
- Significant time savings for complex projects

### 2. Inter-Agent Communication
- Agents share information about interfaces and contracts
- Coordination messages ensure compatibility
- Shared context prevents conflicts

### 3. Dependency Management
- Supervisor tracks task dependencies
- Ensures prerequisite tasks complete before dependent tasks start
- Handles complex dependency graphs automatically

### 4. Error Handling and Recovery
- If one agent fails, others continue with independent tasks
- Failed tasks are retried or escalated to supervisor
- Comprehensive error reporting and recovery strategies

## Benefits of Multi-Agent Mode

### 1. **Speed**: Parallel execution reduces overall development time
### 2. **Quality**: Specialized agents focus on specific areas of expertise
### 3. **Coordination**: Supervisor ensures architectural consistency
### 4. **Scalability**: Can handle very large, complex projects
### 5. **Reliability**: Fault tolerance and error recovery

## Best Practices for Multi-Agent Mode

### 1. Use for Complex Projects
- Multiple independent components
- Microservices architectures
- Large-scale applications

### 2. Provide Clear Requirements
- Detailed planning conversations
- Specific technology preferences
- Clear architectural decisions

### 3. Review Generated Documentation
- Verify service boundaries
- Check integration points
- Ensure comprehensive coverage

### 4. Monitor Agent Communication
- Watch for coordination messages
- Verify dependency resolution
- Check for integration issues

## Configuration for Multi-Agent Mode

```yaml
# ~/.equitr/config.yaml
orchestrator:
  use_multi_agent: true
  max_iterations: 30
  worker_timeout: 600
  max_workers: 5

llm:
  model: "gpt-4o"  # More powerful model for complex coordination
  budget: 100.0    # Higher budget for multi-agent projects
  temperature: 0.2 # Lower temperature for consistent architecture
```

Multi-agent mode transforms EQUITR Coder into a powerful orchestrator capable of handling enterprise-scale projects with the coordination and efficiency of a complete development team.