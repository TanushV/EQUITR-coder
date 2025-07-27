# design.md

## 1. System Architecture

### 1.1 High-Level Overview
```
┌─────────────────────────────┐
│        Vercel CDN           │
│   (React SPA + Assets)      │
└────────────┬────────────────┘
             │ HTTPS
┌────────────┴────────────────┐
│     Railway Edge Proxy      │
│        (HTTPS Term.)        │
└────────────┬────────────────┘
             │
┌────────────┴────────────────┐
│      Express API Layer      │
│   (REST + Socket.IO)        │
├────────────┬────────────────┤
│   Service Layer (Domain)    │
├────────────┬────────────────┤
│   Data Access Layer (DAL)   │
├────────────┬────────────────┤
│    PostgreSQL 15 Cluster    │
│  (Primary + Read Replica)   │
└─────────────────────────────┘
```

### 1.2 Deployment Topology
- **Frontend**: Vercel Edge Network (global CDN, automatic HTTPS, preview deployments)
- **Backend**: Railway container with auto-scaling (1 → 3 instances based on CPU > 70 %)
- **Database**: Railway PostgreSQL with daily backups at 02:00 UTC, 7-day retention
- **Static Assets**: Served via Vercel's global CDN with immutable caching headers

## 2. Components

### 2.1 Frontend Components (React + TypeScript)

#### 2.1.1 Core UI Components
```
src/components/
├── atoms/
│   ├── Button/
│   ├── Input/
│   ├── Checkbox/
│   ├── Avatar/
│   └── Badge/
├── molecules/
│   ├── TaskCard/
│   ├── CommentThread/
│   ├── FilterBar/
│   └── UserPicker/
├── organisms/
│   ├── KanbanBoard/
│   ├── TaskList/
│   ├── WorkspaceSidebar/
│   └── NotificationCenter/
└── templates/
    ├── WorkspaceLayout/
    └── AuthLayout/
```

#### 2.1.2 State Management
- **Global State**: Zustand stores
  - `useAuthStore` - user session, tokens
  - `useWorkspaceStore` - current workspace, members
  - `useTaskStore` - tasks, filters, sorting
  - `useSocketStore` - WebSocket connection, events
- **Local State**: React hooks for component-specific state
- **Optimistic Updates**: Immediate UI updates with rollback on error

#### 2.1.3 Real-time Layer
- Socket.IO client with automatic reconnection
- Event namespacing: `workspace:{id}` for scoping
- Presence indicators via `user:online` events

### 2.2 Backend Components (Node.js + Express)

#### 2.2.1 API Layer
```
src/api/
├── middleware/
│   ├── auth.middleware.ts
│   ├── validation.middleware.ts
│   ├── rate-limit.middleware.ts
│   └── cors.middleware.ts
├── routes/
│   ├── auth.routes.ts
│   ├── workspace.routes.ts
│   ├── task.routes.ts
│   └── comment.routes.ts
├── controllers/
│   ├── auth.controller.ts
│   ├── workspace.controller.ts
│   ├── task.controller.ts
│   └── comment.controller.ts
└── validators/
    ├── auth.validator.ts
    ├── task.validator.ts
    └── workspace.validator.ts
```

#### 2.2.2 Service Layer
```
src/services/
├── auth.service.ts
├── workspace.service.ts
├── task.service.ts
├── notification.service.ts
└── realtime.service.ts
```

#### 2.2.3 Data Layer
```
src/database/
├── models/
│   ├── User.model.ts
│   ├── Workspace.model.ts
│   ├── Task.model.ts
│   └── Comment.model.ts
├── repositories/
│   ├── user.repository.ts
│   ├── workspace.repository.ts
│   └── task.repository.ts
├── migrations/
│   └── *.sql
└── seeds/
    └── development.seed.ts
```

### 2.3 Infrastructure Components

#### 2.3.1 CI/CD Pipeline
```
.github/
├── workflows/
│   ├── ci.yml
│   ├── deploy-staging.yml
│   └── deploy-production.yml
```

#### 2.3.2 Monitoring
- **Error Tracking**: Sentry DSN configuration
- **Performance**: New Relic APM integration
- **Uptime**: UptimeRobot webhook endpoints

## 3. Data Flow

### 3.1 Task Creation Flow
```
User → React Form → Zustand Store → Socket.IO Emit → Express API
     ↓
PostgreSQL ← DAL ← Service Layer ← Validation ← Controller
     ↓
Socket.IO Broadcast → All Connected Clients → UI Update
```

### 3.2 Real-time Update Flow
```
Client A → Socket.IO Event → Express Server → Redis Pub/Sub
     ↓
All Clients in Workspace ← Socket.IO Broadcast ← Redis Subscriber
```

### 3.3 Authentication Flow
```
User Credentials → /api/auth/login → bcrypt.compare → JWT.sign
     ↓
Client Storage (httpOnly cookie) → Subsequent Requests → JWT.verify
```

### 3.4 Database Schema
```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255),
    display_name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workspaces
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    owner_id UUID REFERENCES users(id),
    invite_code VARCHAR(8) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workspace Members
CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

-- Lists
CREATE TABLE lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    name VARCHAR(100) NOT NULL,
    position INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID REFERENCES lists(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo',
    priority VARCHAR(10) DEFAULT 'medium',
    due_date TIMESTAMP,
    assignee_id UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comments
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id),
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    parent_id UUID REFERENCES comments(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tasks_list_id ON tasks(list_id);
CREATE INDEX idx_tasks_assignee_id ON tasks(assignee_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_comments_task_id ON comments(task_id);
```

## 4. Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. **Repository Setup**
   - Initialize monorepo with Turborepo
   - Configure TypeScript, ESLint, Prettier
   - Set up GitHub Actions for CI

2. **Database Setup**
   - Create PostgreSQL schema
   - Set up migration system (node-pg-migrate)
   - Seed development data

3. **Backend Skeleton**
   - Express server with health check
   - Middleware setup (CORS, helmet, compression)
   - Basic error handling

### Phase 2: Authentication (Week 2-3)
1. **Auth API**
   - Implement /register, /login, /logout
   - JWT token generation and validation
   - Google OAuth integration

2. **Frontend Auth**
   - Login/register forms
   - Auth context and protected routes
   - Token storage (httpOnly cookies)

### Phase 3: Core Task Operations (Week 3-4)
1. **Task API**
   - CRUD endpoints with validation
   - Pagination and filtering
   - Soft delete implementation

2. **Task UI**
   - Task creation modal
   - Task list view
   - Edit/delete functionality

### Phase 4: Real-time & Collaboration (Week 4-5)
1. **WebSocket Setup**
   - Socket.IO server integration
   - Room-based workspace isolation
   - Event broadcasting

2. **Collaboration Features**
   - Workspace sharing via invite code
   - Real-time task updates
   - Presence indicators

### Phase 5: Advanced Features (Week 5-6)
1. **Kanban Board**
   - Drag-and-drop implementation (react-beautiful-dnd)
   - Column persistence
   - Status transitions

2. **Notifications**
   - Email service (SendGrid)
   - Due date reminder cron job
   - In-app notification center

### Phase 6: Polish & Launch (Week 6-7)
1. **Performance Optimization**
   - Code splitting and lazy loading
   - Image optimization
   - Database query optimization

2. **Testing**
   - Unit tests (80% coverage)
   - E2E tests for critical flows
   - Performance testing

3. **Deployment**
   - Staging environment setup
   - Production deployment
   - Monitoring configuration

## 5. File Structure

```
task-management-system/
├── apps/
│   ├── web/                    # React frontend
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── stores/
│   │   │   ├── services/
│   │   │   ├── utils/
│   │   │   └── types/
│   │   ├── public/
│   │   ├── tests/
│   │   └── package.json
│   └── api/                    # Express backend
│       ├── src/
│       │   ├── api/
│       │   ├── services/
│       │   ├── database/
│       │   ├── utils/
│       │   └── types/
│       ├── tests/
│       └── package.json
├── packages/
│   ├── shared-types/          # Shared TypeScript types
│   ├── ui-components/         # Reusable React components
│   └── eslint-config/         # Shared ESLint config
├── infrastructure/
│   ├── docker/
│   ├── terraform/
│   └── kubernetes/
├── scripts/
│   ├── dev.sh
│   ├── build.sh
│   └── deploy.sh
├── .github/
│   └── workflows/
├── docs/
│   ├── api/
│   └── architecture/
├── turbo.json
├── package.json
└── README.md
```

### Environment Configuration
```
# .env.development
VITE_API_URL=http://localhost:3001
VITE_SOCKET_URL=http://localhost:3001
DATABASE_URL=postgresql://user:pass@localhost:5432/taskdb
JWT_SECRET=dev-secret-key
SENDGRID_API_KEY=sg-dev-key

# .env.production
VITE_API_URL=https://api.taskapp.com
VITE_SOCKET_URL=wss://api.taskapp.com
DATABASE_URL=${RAILWAY_DATABASE_URL}
JWT_SECRET=${JWT_SECRET}
SENDGRID_API_KEY=${SENDGRID_API_KEY}
```