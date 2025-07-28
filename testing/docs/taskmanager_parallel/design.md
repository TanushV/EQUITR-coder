# design.md

## 1. System Architecture

### High-Level Overview
```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                        │
│                        (Nginx)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    Application Layer                          │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │   React Frontend    │    │   Node.js Backend   │         │
│  │   (TypeScript)      │◄──►│   (Express.js)      │         │
│  │   Port: 3000        │    │   Port: 5000        │         │
│  └─────────────────────┘    └──────────┬──────────┘         │
└─────────────────────────────────────────┼───────────────────┘
                                          │
┌─────────────────────────────────────────┴───────────────────┐
│                      Data Layer                               │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │   PostgreSQL        │    │   Redis Cache       │         │
│  │   Port: 5432        │    │   Port: 6379        │         │
│  └─────────────────────┘    └─────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   External Services                           │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │   SendGrid SMTP     │    │   Docker Registry   │         │
│  │   Port: 587         │    │   (GitHub Packages) │         │
│  └─────────────────────┘    └─────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Frontend**: React 18.2.0 + TypeScript 5.0 + Vite 4.4
- **Backend**: Node.js 18.17 + Express.js 4.18 + TypeScript 5.0
- **Database**: PostgreSQL 15.4 + pg-boss 9.0 (job queue)
- **Cache**: Redis 7.2 (session store + query cache)
- **Email**: SendGrid API v3
- **Container**: Docker + Docker Compose
- **Reverse Proxy**: Nginx 1.25

## 2. Components

### 2.1 Frontend Components

#### Core Components
```
src/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Modal/
│   │   └── LoadingSpinner/
│   ├── auth/
│   │   ├── LoginForm/
│   │   ├── RegisterForm/
│   │   └── ProtectedRoute/
│   ├── tasks/
│   │   ├── TaskList/
│   │   ├── TaskCard/
│   │   ├── TaskForm/
│   │   ├── TaskFilters/
│   │   └── TaskComments/
│   ├── dashboard/
│   │   ├── DashboardStats/
│   │   ├── QuickAddTask/
│   │   └── RecentActivity/
│   └── layout/
│       ├── Header/
│       ├── Sidebar/
│       └── Layout/
```

#### State Management
- **Global State**: Zustand stores
  - `useAuthStore` - Authentication state
  - `useTaskStore` - Task data and filters
  - `useNotificationStore` - Toast notifications
- **Local State**: React hooks for component-specific state
- **Server State**: React Query for API data caching

### 2.2 Backend Components

#### API Layer
```
src/
├── controllers/
│   ├── auth.controller.ts
│   ├── task.controller.ts
│   ├── comment.controller.ts
│   └── user.controller.ts
├── services/
│   ├── auth.service.ts
│   ├── task.service.ts
│   ├── email.service.ts
│   └── notification.service.ts
├── middleware/
│   ├── auth.middleware.ts
│   ├── validation.middleware.ts
│   ├── rateLimit.middleware.ts
│   └── errorHandler.middleware.ts
├── models/
│   ├── user.model.ts
│   ├── task.model.ts
│   └── comment.model.ts
├── routes/
│   ├── auth.routes.ts
│   ├── task.routes.ts
│   └── comment.routes.ts
├── utils/
│   ├── database.ts
│   ├── jwt.ts
│   └── validators.ts
└── jobs/
    ├── emailQueue.ts
    └── notificationQueue.ts
```

#### Database Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status task_status NOT NULL DEFAULT 'todo',
    priority task_priority NOT NULL DEFAULT 'medium',
    due_date TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    assignee_id UUID REFERENCES users(id),
    creator_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comments table
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_tasks_creator ON tasks(creator_id);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_comments_task ON comments(task_id);
CREATE INDEX idx_tasks_search ON tasks USING gin(to_tsvector('english', title || ' ' || description));
```

### 2.3 Infrastructure Components

#### Docker Configuration
```
docker-compose.yml
├── frontend/Dockerfile
├── backend/Dockerfile
├── nginx/Dockerfile
└── .dockerignore
```

#### CI/CD Pipeline
```
.github/
└── workflows/
    ├── ci.yml
    ├── cd-staging.yml
    └── cd-production.yml
```

## 3. Data Flow

### 3.1 Authentication Flow
```
1. User submits login form
   ↓
2. Frontend sends POST /api/auth/login
   ↓
3. Backend validates credentials
   ↓
4. Backend generates JWT token (24h expiry)
   ↓
5. Token stored in Redis with user session
   ↓
6. Token returned to frontend
   ↓
7. Frontend stores token in httpOnly cookie
   ↓
8. Subsequent requests include token
```

### 3.2 Task Creation Flow
```
1. User fills task form
   ↓
2. Frontend validates input
   ↓
3. POST /api/tasks with JWT token
   ↓
4. Backend validates JWT and input
   ↓
5. Task saved to PostgreSQL
   ↓
6. If assignee specified:
   - Email job queued to Redis
   - Notification service processes job
   - SendGrid sends email
   ↓
7. Task returned to frontend
   ↓
8. React Query cache updated
```

### 3.3 Search and Filter Flow
```
1. User applies filters/sort
   ↓
2. Frontend builds query parameters
   ↓
3. GET /api/tasks?status=todo&priority=high&sort=dueDate
   ↓
4. Backend checks Redis cache
   ↓
5. If cache miss:
   - Query PostgreSQL with optimized indexes
   - Cache results in Redis (5 min TTL)
   ↓
6. Paginated results returned
   ↓
7. Frontend displays results
```

### 3.4 Real-time Updates
```
1. User adds comment to task
   ↓
2. POST /api/tasks/:id/comments
   ↓
3. Comment saved to database
   ↓
4. WebSocket event emitted
   ↓
5. Connected clients receive update
   ↓
6. UI updates without refresh
```

## 4. Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Set up development environment
  - Docker containers for PostgreSQL, Redis
  - Backend API scaffolding
  - Frontend React setup with TypeScript
- [ ] Database schema creation
- [ ] Basic authentication endpoints
- [ ] User registration/login UI

### Phase 2: Core Features (Week 3-4)
- [ ] CRUD operations for tasks
- [ ] Task list with filtering/sorting
- [ ] Task creation/editing forms
- [ ] Basic dashboard layout

### Phase 3: Collaboration (Week 5-6)
- [ ] User management endpoints
- [ ] Task assignment functionality
- [ ] Comment system
- [ ] Email integration with SendGrid

### Phase 4: Polish & Performance (Week 7-8)
- [ ] Search implementation with full-text search
- [ ] Redis caching layer
- [ ] Rate limiting and security hardening
- [ ] Performance optimization

### Phase 5: Deployment (Week 9)
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Staging environment deployment
- [ ] Production deployment

### Testing Strategy
```
Unit Tests: Jest (backend), React Testing Library (frontend)
Integration Tests: Supertest for API endpoints
E2E Tests: Cypress for critical user flows
Load Tests: k6 for performance validation
```

## 5. File Structure

```
task-management-system/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.ts
│   │   │   ├── tasks.ts
│   │   │   └── comments.ts
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/
│   ├── src/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── utils/
│   │   ├── jobs/
│   │   └── server.ts
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   └── jest.config.js
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
├── database/
│   ├── migrations/
│   └── seeds/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```

### Environment Configuration
```
# .env.example
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=taskmanager
POSTGRES_USER=taskuser
POSTGRES_PASSWORD=securepassword

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=24h

# SendGrid
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@taskmanager.com

# Frontend
VITE_API_URL=http://localhost:5000/api
```