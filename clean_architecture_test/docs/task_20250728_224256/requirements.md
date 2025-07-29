# Task Management Web Application – Requirements

## 1. Project Overview
Build a lightweight, single-page web application that lets users create, view, and manage a personal task list.  
The application will consist of:

- A static HTML page served by a Python Flask backend.  
- A REST-style API (Flask routes) that reads from and writes to a local JSON file.  
- Client-side JavaScript that calls the API and updates the DOM without full page reloads.  
- Minimal, clean CSS styling for desktop and mobile browsers.

The entire solution must be runnable with a single command (`python app.py`) and require no external databases or third-party services.

---

## 2. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | **Add Task** – User can enter a task description in a text field and click “Add” to create a new task. | Must |
| FR-2 | **View Tasks** – All existing tasks are displayed in a scrollable list immediately on page load and after any change. | Must |
| FR-3 | **Mark Complete** – Each task has a checkbox; checking it marks the task as complete and updates the UI. | Must |
| FR-4 | **Delete Task** – Each task has a delete button; clicking it removes the task from the list and storage. | Must |
| FR-5 | **Persistent Storage** – Tasks survive server restarts; data is stored in a single JSON file (`tasks.json`) on disk. | Must |
| FR-6 | **Validation** – Empty or whitespace-only descriptions cannot be submitted. | Should |
| FR-7 | **Responsive UI** – Layout adapts to screen widths ≥ 320 px. | Should |
| FR-8 | **No Full-Page Reloads** – All interactions (add, toggle, delete) update the list via AJAX/fetch. | Must |

---

## 3. Technical Requirements

### 3.1 Backend (Flask)
- **Framework**: Flask 2.x (Python ≥ 3.8).  
- **Routes**:
  - `GET /` – Serve `index.html`.  
  - `GET /api/tasks` – Return JSON array of all tasks.  
  - `POST /api/tasks` – Accept JSON `{ "description": "string" }`, return created task object with `id`, `description`, `completed`.  
  - `PUT /api/tasks/<id>` – Accept JSON `{ "completed": bool }`, return updated task.  
  - `DELETE /api/tasks/<id>` – Remove task, return `204 No Content`.  
- **Storage**:
  - File `tasks.json` in project root.  
  - Format: `[{"id": int, "description": str, "completed": bool}]`.  
  - Atomic read/write (lock file or temp file + rename).  
- **Error Handling**:
  - 400 for invalid JSON or missing fields.  
  - 404 for unknown task ID.  
  - All errors return JSON `{ "error": "message" }`.

### 3.2 Frontend
- **Files**:
  - `static/index.html` – Single-page markup.  
  - `static/css/styles.css` – Styling.  
  - `static/js/app.js` – Client logic.  
- **Behavior**:
  - On page load, fetch `/api/tasks` and render list.  
  - Add form submits via `fetch` POST; on success, append new task to DOM.  
  - Checkbox change triggers `PUT /api/tasks/<id>`.  
  - Delete button triggers `DELETE /api/tasks/<id>` and removes DOM element.  
- **UX**:
  - Disable submit button while request in flight.  
  - Show inline error messages for failed requests.  
  - Focus returns to input field after successful add.

### 3.3 Styling
- **Design**:
  - Light theme, sans-serif font, max-width 600 px centered container.  
  - Completed tasks shown with strikethrough and lighter color.  
  - Buttons and checkboxes sized for touch targets ≥ 44 × 44 px.  
- **Responsive**:
  - Flexbox layout; single column on mobile, two-column (sidebar + list) optional on desktop.  
  - No external CSS frameworks; pure CSS.

### 3.4 Deployment & Tooling
- **Entry Point**: `app.py` at project root.  
- **Dependencies**: `requirements.txt` listing only `Flask`.  
- **Directory Layout**:
  ```
  task-app/
  ├── app.py
  ├── tasks.json (auto-created if missing)
  ├── requirements.txt
  └── static/
      ├── index.html
      ├── css/
      │   └── styles.css
      └── js/
          └── app.js
  ```
- **CORS**: Not required (same origin).  
- **Logging**: Flask default logging to stdout.

---

## 4. Success Criteria

| Checkpoint | How to Verify |
|---|---|
| 1. Server starts | Run `python app.py`; browse to `http://localhost:5000/` → page loads without errors. |
| 2. Add task | Enter “Buy milk” and click Add → task appears instantly; `tasks.json` contains new entry. |
| 3. Mark complete | Check the checkbox → text strikethrough appears; refresh page → state persists. |
| 4. Delete task | Click delete → task disappears; `tasks.json` updated; no 404/500 errors in console. |
| 5. Validation | Submit empty form → UI shows error message; no entry added. |
| 6. Responsiveness | Resize browser to 320 px width → layout remains usable; no horizontal scroll. |
| 7. Persistence | Stop server, restart → previously added tasks still displayed. |
| 8. No reloads | Monitor Network tab → only API calls, no full page requests after initial load. |

All checkboxes above must pass for the project to be considered complete.