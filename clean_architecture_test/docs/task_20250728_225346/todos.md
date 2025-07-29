## Backend Development
- [ ] Create `app.py` with Flask app initialization and configuration
- [ ] Implement `TaskStore` class for atomic JSON file operations (read/write)
- [ ] Add `GET /api/tasks` endpoint to return all tasks as JSON
- [ ] Add `POST /api/tasks` endpoint with validation for new task creation
- [ ] Add `DELETE /api/tasks/<int:id>` endpoint for task deletion
- [ ] Implement error handling middleware for 400/404/500 responses
- [ ] Create `requirements.txt` with Flask==2.3.3
- [ ] Test all endpoints with curl/Postman

## Frontend Development
- [ ] Create `templates/index.html` with semantic HTML structure
- [ ] Build responsive CSS in `static/css/style.css` following design specs
- [ ] Implement JavaScript `TaskAPI` module for fetch operations
- [ ] Create `TaskRenderer` module for DOM manipulation and updates
- [ ] Add form validation and error message display
- [ ] Implement delete confirmation and immediate UI updates
- [ ] Add loading states and accessibility attributes
- [ ] Test responsive design on mobile and desktop