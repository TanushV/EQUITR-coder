# requirements.md

## 1. Project Overview
A minimal, single-page task-management web application that allows users to add, view, and delete tasks.  
The application consists of:
- A static HTML page served by Flask that contains a form to add new tasks and a list to display existing tasks.
- A Python Flask backend exposing REST-style endpoints for task operations.
- A local JSON file (`tasks.json`) used as the persistent data store.
- Basic CSS styling to ensure the interface is clean and usable.

## 2. Functional Requirements

| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-1 | Add a new task | 1. User enters task text in the form and clicks “Add”.<br>2. Task appears at the top of the task list without page reload (AJAX).<br>3. Empty or whitespace-only submissions are rejected with an inline error message. |
| FR-2 | View all tasks | 1. On page load, all existing tasks are fetched and displayed in chronological order (newest first).<br>2. Each task shows its text and a “Delete” button. |
| FR-3 | Delete a task | 1. Clicking “Delete” removes the task from the list and the JSON file without page reload.<br>2. The UI updates immediately to reflect the deletion. |
| FR-4 | Data persistence | 1. Tasks survive server restarts.<br>2. If `tasks.json` is missing or corrupted, the app starts with an empty list and recreates the file on the first write. |

## 3. Technical Requirements

### 3.1 Backend (Flask)
- **Framework**: Flask 2.x (Python 3.8+)
- **Routes**:
  - `GET /` → serves `index.html`
  - `GET /api/tasks` → returns JSON array of tasks  
    Example: `[{"id": 1, "text": "Buy milk"}, {"id": 2, "text": "Walk dog"}]`
  - `POST /api/tasks` → accepts JSON `{"text": "string"}`; returns the created task object with generated `id`
  - `DELETE /api/tasks/<int:id>` → deletes task with given `id`; returns `204 No Content` on success or `404 Not Found`
- **Storage**:
  - File: `tasks.json` in project root.
  - Format: list of objects with keys `id` (int, unique) and `text` (string).
  - Atomic writes: use temporary file + rename to avoid corruption.
- **Error Handling**:
  - Invalid JSON → `400 Bad Request`
  - Missing `text` field → `422 Unprocessable Entity`
  - File I/O errors → `500 Internal Server Error` with short JSON message `{ "error": "..." }`

### 3.2 Frontend
- **File**: `templates/index.html`
- **Behavior**:
  - Uses vanilla JavaScript `fetch()` for AJAX calls.
  - On page load: `GET /api/tasks` and render list.
  - On form submit: `POST /api/tasks`, then prepend new task to DOM.
  - On delete click: `DELETE /api/tasks/<id>`, then remove element from DOM.
- **Validation**:
  - Trim whitespace before sending.
  - Disable submit button while request in flight.
- **Accessibility**:
  - Form has `label` for input.
  - Buttons have `aria-label` attributes.

### 3.3 Styling
- **File**: `static/css/style.css`
- **Guidelines**:
  - Max width 600 px, centered.
  - Sans-serif font, 16 px base size.
  - Consistent 8 px spacing scale.
  - Primary color `#007bff`, danger color `#dc3545`.
  - Responsive: usable on 320 px wide screens.

### 3.4 Project Structure
```
todo-app/
├── app.py
├── tasks.json          (auto-created)
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── css/
        └── style.css
```

### 3.5 Dependencies
```
Flask==2.3.3
```

## 4. Success Criteria

| Checkpoint | Verification Method |
|---|---|
| 1. Local server starts | Run `python app.py`; visit `http://localhost:5000/`; page loads without errors. |
| 2. Add task | Submit form; new task appears instantly; `tasks.json` contains the new task. |
| 3. View tasks | Refresh browser; previously added tasks are still displayed in order. |
| 4. Delete task | Click “Delete”; task disappears; `tasks.json` no longer contains the task. |
| 5. Edge cases | Submit empty text → inline error shown; delete non-existent id → 404 returned. |
| 6. Styling | Page looks clean on Chrome, Firefox, and a mobile device (iPhone SE or Android). |
| 7. No console errors | Browser dev tools show zero JavaScript errors or warnings.