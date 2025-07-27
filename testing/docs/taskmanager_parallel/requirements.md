# requirements.md

## 1. Project Overview
Build a lightweight, web-based task management system that allows individuals or small teams to create, organize, track, and complete tasks. The system must be accessible from any modern browser, require no installation, and support real-time collaboration for up to 10 concurrent users per workspace.

## 2. Functional Requirements

### 2.1 Core Task Operations
- **Create Task**: Users can add a new task with title, description, due date, priority (Low, Medium, High), and assignee.
- **Edit Task**: Users can modify any field of an existing task.
- **Delete Task**: Users can remove a task with a confirmation prompt.
- **Mark Complete**: One-click toggle to mark/unmark a task as complete; completed tasks move to a separate “Done” section.

### 2.2 Organization & Views
- **Lists/Projects**: Users can group tasks into named lists (e.g., “Marketing Launch”, “Personal”).
- **Kanban Board**: Default view showing columns for To-Do, In-Progress, and Done; drag-and-drop to change status.
- **List View**: Compact table view with sortable columns (title, due date, priority, assignee).
- **Filter & Search**: Filter by assignee, priority, due date range, or keyword search in title/description.

### 2.3 Collaboration
- **Share Workspace**: Generate a shareable link or invite by email; invited users can view and edit tasks.
- **Real-time Updates**: Changes made by any user appear instantly for all others in the same workspace.
- **Comments**: Users can add threaded comments to any task.

### 2.4 Notifications
- **Due-date Reminders**: Email or in-app notification 24 h before a task is due.
- **Assignment Notification**: When a user is assigned or unassigned from a task.

### 2.5 User Management
- **Sign-up/Login**: Email + password or Google OAuth.
- **Guest Mode**: Allow limited use without account (tasks stored in local storage, no collaboration).
- **Profile**: Change display name and avatar.

## 3. Technical Requirements

### 3.1 Architecture
- **Frontend**: Single-page application built with React 18 + TypeScript.
- **Backend**: Node.js 20 + Express REST API.
- **Database**: PostgreSQL 15 with tables: users, workspaces, lists, tasks, comments.
- **Real-time**: WebSockets via Socket.IO for live updates.
- **Hosting**: Deploy on Vercel (frontend) and Railway (backend + DB).

### 3.2 API Endpoints (v1)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST   | /api/auth/register | Create account |
| POST   | /api/auth/login | Obtain JWT |
| GET    | /api/workspaces | List user workspaces |
| POST   | /api/workspaces | Create workspace |
| GET    | /api/workspaces/:id/tasks | Get all tasks |
| POST   | /api/tasks | Create task |
| PATCH  | /api/tasks/:id | Update task |
| DELETE | /api/tasks/:id | Delete task |
| POST   | /api/tasks/:id/comments | Add comment |

### 3.3 Non-Functional
- **Performance**: Page load < 2 s on 3G; drag-and-drop updates < 100 ms.
- **Security**: HTTPS only, JWT with 24 h expiry, hashed passwords (bcrypt 12 rounds), CORS whitelist.
- **Accessibility**: WCAG 2.1 AA compliance, keyboard navigation, screen-reader labels.
- **Browser Support**: Chrome 110+, Firefox 102+, Safari 15+, Edge 110+.

### 3.4 DevOps
- **CI/CD**: GitHub Actions → run tests → deploy to staging on push to `develop`, to production on `main`.
- **Testing**: 80 % unit test coverage (Jest + React Testing Library), Cypress e2e for critical flows.
- **Monitoring**: Sentry for error tracking, UptimeRobot for uptime alerts.

## 4. Success Criteria

| # | Criterion | Measurement |
|---|-----------|-------------|
| 1 | Core CRUD | User can create, read, update, delete a task in < 5 s end-to-end. |
| 2 | Real-time Sync | Two users on different machines see each other’s changes within 1 s. |
| 3 | Zero P1 Bugs | No critical production bugs for 7 consecutive days after launch. |
| 4 | Performance | Lighthouse score ≥ 90 on Performance, Accessibility, Best Practices, SEO. |
| 5 | Adoption | 100 registered users and 50 active workspaces within 30 days of launch. |
| 6 | Feedback | ≥ 4.0/5 average rating in post-sign-up survey (min 30 responses). |