# Todos for Agent 2

## Assigned Categories
Agent 2 is responsible for the following categories:

## Category 2: Task Management & Collaboration API
- [ ] Build task CRUD endpoints:
- [ ] `GET /api/tasks` with query parameters for filtering/sorting
- [ ] `POST /api/tasks` for task creation
- [ ] `PUT /api/tasks/:id` for task updates
- [ ] `DELETE /api/tasks/:id` for task deletion
- [ ] Implement task filtering by status, priority, assignee, tags, and due date
- [ ] Add sorting functionality by creation date, due date, priority, or title
- [ ] Create comment system endpoints:
- [ ] `POST /api/tasks/:id/comments` for adding comments
- [ ] `GET /api/tasks/:id/comments` for retrieving comments
- [ ] Build task sharing endpoint (`POST /api/tasks/:id/share`) with email integration
- [ ] Implement task assignment functionality with user lookup
- [ ] Add full-text search endpoint with PostgreSQL full-text search
- [ ] Create notification service for email alerts using SendGrid
- [ ] Set up Redis job queue for asynchronous email processing
- [ ] Implement proper authorization checks for all endpoints

## Instructions
- You are Agent 2 of 3
- Complete ALL todos in your assigned categories above
- Each category is a complete, self-contained set of related tasks
- You cannot finish until ALL your todos are marked as completed
- Use communication tools to coordinate with other agents
- Read the requirements.md and design.md files for context
- Work systematically through each category
