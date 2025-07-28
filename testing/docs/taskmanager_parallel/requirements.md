# requirements.md

## 1. Project Overview
Build a lightweight, web-based task management system that allows individuals or small teams to create, track, and complete tasks. The system should be simple enough for personal use yet flexible enough for small collaborative projects.

## 2. Functional Requirements

### 2.1 Core Task Management
- **Create Task**: Users can create a new task with title, description, due date, priority (Low/Medium/High), and status (To Do/In Progress/Done)
- **Edit Task**: Users can modify any field of an existing task
- **Delete Task**: Users can permanently remove a task
- **View Tasks**: Users can see all tasks in a list view with filtering and sorting options

### 2.2 User Management
- **User Registration**: New users can sign up with email and password
- **User Login**: Existing users can log in with credentials
- **User Profile**: Users can view and update their profile information
- **Session Management**: System maintains user sessions for 24 hours

### 2.3 Collaboration Features
- **Share Task**: Users can share individual tasks with other users via email
- **Assign Task**: Task creators can assign tasks to other registered users
- **Comments**: Users can add comments to tasks for discussion
- **Notifications**: Users receive email notifications for task assignments and comments

### 2.4 Organization Features
- **Tags**: Users can add multiple tags to tasks for categorization
- **Search**: Full-text search across task titles, descriptions, and comments
- **Filter**: Filter tasks by status, priority, assignee, tags, and due date
- **Sort**: Sort tasks by creation date, due date, priority, or title

### 2.5 Dashboard
- **Overview**: Display summary statistics (total tasks, completed today, overdue)
- **Quick Add**: One-click task creation from dashboard
- **Recent Activity**: Show 5 most recent updates across all tasks

## 3. Technical Requirements

### 3.1 Architecture
- **Frontend**: React.js with TypeScript
- **Backend**: Node.js with Express.js
- **Database**: PostgreSQL for persistent storage
- **Authentication**: JWT tokens for session management
- **Email Service**: SendGrid for email notifications

### 3.2 API Design
- RESTful API with following endpoints:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/tasks` (with query parameters for filtering/sorting)
  - `POST /api/tasks`
  - `PUT /api/tasks/:id`
  - `DELETE /api/tasks/:id`
  - `POST /api/tasks/:id/comments`
  - `POST /api/tasks/:id/share`

### 3.3 Data Models
```typescript
// User
{
  id: UUID,
  email: string,
  name: string,
  createdAt: Date,
  updatedAt: Date
}

// Task
{
  id: UUID,
  title: string,
  description: string,
  status: 'todo' | 'inprogress' | 'done',
  priority: 'low' | 'medium' | 'high',
  dueDate: Date,
  tags: string[],
  assigneeId: UUID | null,
  creatorId: UUID,
  createdAt: Date,
  updatedAt: Date
}

// Comment
{
  id: UUID,
  taskId: UUID,
  userId: UUID,
  content: string,
  createdAt: Date
}
```

### 3.4 Security
- Passwords hashed using bcrypt
- HTTPS only in production
- Rate limiting: 100 requests per minute per IP
- Input validation on all endpoints
- SQL injection prevention through parameterized queries

### 3.5 Performance
- Page load time < 2 seconds
- API response time < 500ms for 95% of requests
- Support 100 concurrent users
- Database queries optimized with proper indexing

### 3.6 Deployment
- Docker containers for easy deployment
- CI/CD pipeline using GitHub Actions
- Environment-based configuration
- Health check endpoint at `/health`

## 4. Success Criteria

### 4.1 Functional Testing
- [ ] User can register, login, and logout successfully
- [ ] User can create, edit, and delete tasks
- [ ] User can filter and sort tasks effectively
- [ ] Email notifications are sent for task assignments
- [ ] Search returns relevant results quickly
- [ ] Comments are properly associated with tasks

### 4.2 Performance Testing
- [ ] Load test passes with 100 concurrent users
- [ ] All API endpoints respond within 500ms
- [ ] Database handles 1000 tasks per user without degradation

### 4.3 Security Testing
- [ ] All endpoints require authentication except register/login
- [ ] Users can only access their own tasks
- [ ] SQL injection attempts are blocked
- [ ] Passwords are never returned in API responses

### 4.4 User Acceptance
- [ ] 5 beta users can complete basic task management workflow without assistance
- [ ] Users report the interface as "intuitive" in feedback survey
- [ ] Zero critical bugs reported in first week of use

### 4.5 Documentation
- [ ] API documentation is complete and accurate
- [ ] User guide with screenshots is provided
- [ ] README includes setup instructions for local development