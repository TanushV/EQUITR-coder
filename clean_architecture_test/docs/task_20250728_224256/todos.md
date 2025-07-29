## Backend & API Development
- [ ] Initialize Flask project structure with `app.py`, `requirements.txt`, and `static/` directory
- [ ] Implement `GET /` route to serve `index.html` from static folder
- [ ] Create `GET /api/tasks` endpoint to read and return all tasks from JSON file
- [ ] Build `POST /api/tasks` endpoint with validation for non-empty descriptions
- [ ] Implement `PUT /api/tasks/<id>` endpoint to toggle task completion status
- [ ] Create `DELETE /api/tasks/<id>` endpoint to remove tasks
- [ ] Add atomic file operations for JSON storage using tempfile and os.replace
- [ ] Add error handling middleware for 400/404/500 responses with JSON messages

## Frontend & Styling
- [ ] Create `index.html` with task form, task list container, and proper meta tags
- [ ] Build responsive CSS layout with mobile-first design and flexbox
- [ ] Style completed tasks with strikethrough and lighter color
- [ ] Implement JavaScript fetch calls for all CRUD operations
- [ ] Add dynamic DOM updates for adding, toggling, and deleting tasks
- [ ] Add form validation and error message display
- [ ] Ensure responsive design works at 320px minimum width
- [ ] Add loading states and focus management for better UX