# Task Management Web Application – Technical Design Document

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │   index.html    │  │   app.js (XHR)   │  │ styles.css │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/1.1 (JSON)
┌─────────────────────────────────────────────────────────────┐
│                  Flask Server (Python)                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │   app.py        │  │  REST Routes     │  │ Storage    │ │
│  │  (Flask App)    │◄─┤  /api/tasks/*    │◄─┤ tasks.json │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

- **Single-Process Model**: Flask’s built-in dev server serves both static assets and API endpoints.  
- **Stateless API**: Each request reads/writes the JSON file; no in-memory state.  
- **Concurrency**: File I/O protected by a simple file-lock to prevent race conditions under light load (sufficient for single-user usage).

---

## 2. Components

| Component | Responsibility | Technology |
|---|---|---|
| **Static File Server** | Serve `index.html`, `styles.css`, `app.js` | Flask `send_from_directory` |
| **Task API** | CRUD operations on tasks | Flask Blueprint `/api/tasks` |
| **Storage Layer** | Atomic read/write of `tasks.json` | Python `json`, `tempfile`, `os.replace` |
| **Frontend Logic** | DOM updates, fetch calls | Vanilla JS (ES6) |
| **Presentation Layer** | Layout, typography, responsiveness | CSS Flexbox, media queries |

---

## 3. Data Flow

### 3.1 Sequence – Add Task
```
User → [Submit Form] → JS (preventDefault) → fetch POST /api/tasks
     ← 201 Created ← Flask (write JSON) ← Storage Layer
JS → append <li> → DOM updated
```

### 3.2 Sequence – Toggle Complete
```
User → [Check Checkbox] → JS → fetch PUT /api/tasks/<id>
     ← 200 OK ← Flask (update JSON)
JS → toggle .completed class → strikethrough
```

### 3.3 Sequence – Delete Task
```
User → [Click Delete] → JS → fetch DELETE /api/tasks/<id>
     ← 204 No Content ← Flask (remove from JSON)
JS → remove <li> → DOM updated
```

### 3.4 Storage Format (`tasks.json`)
```json
[
  {
    "id": 1,
    "description": "Buy milk",
    "completed": false
  },
  {
    "id": 2,
    "description": "Walk dog",
    "completed": true
  }
]
```

- `id` monotonically increasing integer (max id + 1).  
- File created automatically on first write if missing.

---

## 4. Implementation Plan

### Phase 1 – Project Skeleton (Day 1)
1. `mkdir task-app && cd task-app`
2. `python -m venv venv && source venv/bin/activate`
3. `pip install flask==2.3.3`
4. `pip freeze > requirements.txt`
5. Create directory tree:
   ```
   task-app/
   ├── app.py
   ├── tasks.json (initially absent)
   ├── requirements.txt
   └── static/
       ├── index.html
       ├── css/
       │   └── styles.css
       └── js/
           └── app.js
   ```

### Phase 2 – Backend API (Day 1)
1. **app.py**
   - Initialize Flask app.
   - Implement `GET /` → `send_from_directory('static', 'index.html')`.
   - Implement `GET /api/tasks`:
     - Read `tasks.json` (return `[]` if absent).
     - Return JSON array.
   - Implement `POST /api/tasks`:
     - Validate JSON body (`description` non-empty string).
     - Generate next `id`.
     - Append to list, atomic write.
     - Return 201 + new task JSON.
   - Implement `PUT /api/tasks/<int:id>`:
     - Find task by id.
     - Update `completed` field.
     - Atomic write.
     - Return 200 + updated task.
   - Implement `DELETE /api/tasks/<int:id>`:
     - Remove task.
     - Atomic write.
     - Return 204.
   - Add error handlers for 400, 404, 500 returning JSON.

2. **Storage utilities**
   - `_read_tasks()` → list
   - `_write_tasks(tasks)` → atomic write using `tempfile.NamedTemporaryFile` + `os.replace`.

### Phase 3 – Frontend Markup (Day 2)
1. **static/index.html**
   - `<!doctype html>` with viewport meta.
   - `<form id="add-task-form">` with `<input required>` and `<button>Add</button>`.
   - `<ul id="task-list">` placeholder.
   - Link `styles.css` and `app.js`.

### Phase 4 – Styling (Day 2)
1. **static/css/styles.css**
   - Reset margins/paddings.
   - `.container { max-width: 600px; margin: auto; }`
   - `.task-item.completed { text-decoration: line-through; color: #888; }`
   - Responsive media query `@media (max-width: 600px) { … }`.

### Phase 5 – Client Logic (Day 3)
1. **static/js/app.js**
   - `DOMContentLoaded` → `fetch('/api/tasks')` → render list.
   - `add-task-form` submit handler:
     - `event.preventDefault()`.
     - `fetch POST` with JSON body.
     - On success, clear input and append `<li>`.
   - Delegate click/change events for checkbox and delete buttons.
   - Helper `renderTask(task)` → create `<li>` with data attributes.
   - Error handling: show `<span class="error">` messages.

### Phase 6 – Testing & Polish (Day 3)
1. Manual test checklist (see §4 Success Criteria).
2. Add favicon.ico (optional).
3. Add `README.md` with run instructions.

---

## 5. File Structure

```
task-app/
├── app.py                 # Flask application entry point
├── tasks.json             # Auto-generated persistent storage
├── requirements.txt       # Flask==2.3.3
├── README.md              # Quick-start guide
└── static/
    ├── index.html         # Single-page markup
    ├── css/
    │   └── styles.css     # Responsive styling
    └── js/
        └── app.js         # Client-side logic
```

### 5.1 Key Files Detail

#### app.py
```python
from flask import Flask, request, jsonify, send_from_directory
import json, os, tempfile

app = Flask(__name__)
TASKS_FILE = 'tasks.json'

def _read_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def _write_tasks(tasks):
    with tempfile.NamedTemporaryFile('w', delete=False, dir='.') as tmp:
        json.dump(tasks, tmp, indent=2)
        tmp.flush()
        os.replace(tmp.name, TASKS_FILE)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(_read_tasks())

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json(force=True, silent=False)
    if not data or not data.get('description') or not data['description'].strip():
        return jsonify({'error': 'description is required'}), 400
    tasks = _read_tasks()
    new_id = max([t['id'] for t in tasks], default=0) + 1
    task = {
        'id': new_id,
        'description': data['description'].strip(),
        'completed': False
    }
    tasks.append(task)
    _write_tasks(tasks)
    return jsonify(task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(force=True, silent=False)
    if data is None or 'completed' not in data:
        return jsonify({'error': 'completed boolean required'}), 400
    tasks = _read_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return jsonify({'error': 'task not found'}), 404
    task['completed'] = bool(data['completed'])
    _write_tasks(tasks)
    return jsonify(task)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    tasks = _read_tasks()
    tasks = [t for t in tasks if t['id'] != task_id]
    _write_tasks(tasks)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
```

#### static/index.html (excerpt)
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Task Manager</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>
  <div class="container">
    <h1>My Tasks</h1>
    <form id="add-task-form">
      <input id="task-input" type="text" placeholder="Add new task..." required>
      <button>Add</button>
    </form>
    <ul id="task-list"></ul>
  </div>
  <script src="js/app.js"></script>
</body>
</html>
```

#### static/css/styles.css (excerpt)
```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #f5f5f5; }
.container { max-width: 600px; margin: 40px auto; padding: 0 10px; }
h1 { margin-bottom: 20px; }
form { display: flex; gap: 8px; margin-bottom: 20px; }
input[type=text] { flex: 1; padding: 8px; font-size: 1rem; }
button { padding: 8px 12px; font-size: 1rem; cursor: pointer; }
#task-list { list-style: none; }
.task-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; }
.task-item.completed span { text-decoration: line-through; color: #888; }
.delete-btn { margin-left: auto; background: none; border: none; color: crimson; cursor: pointer; }
@media (max-width: 600px) {
  .container { margin: 20px 10px; }
}
```

#### static/js/app.js (excerpt)
```javascript
const form = document.getElementById('add-task-form');
const input = document.getElementById('task-input');
const list = document.getElementById('task-list');

async function fetchTasks() {
  const res = await fetch('/api/tasks');
  const tasks = await res.json();
  list.innerHTML = '';
  tasks.forEach(renderTask);
}

function renderTask(task) {
  const li = document.createElement('li');
  li.className = 'task-item';
  li.dataset.id = task.id;
  if (task.completed) li.classList.add('completed');

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.checked = task.completed;
  checkbox.addEventListener('change', toggleTask);

  const span = document.createElement('span');
  span.textContent = task.description;

  const del = document.createElement('button');
  del.textContent = '×';
  del.className = 'delete-btn';
  del.addEventListener('click', deleteTask);

  li.append(checkbox, span, del);
  list.appendChild(li);
}

async function addTask(e) {
  e.preventDefault();
  const description = input.value.trim();
  if (!description) return;
  const res = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description })
  });
  if (res.ok) {
    const task = await res.json();
    renderTask(task);
    input.value = '';
    input.focus();
  } else {
    alert('Error adding task');
  }
}

async function toggleTask(e) {
  const li = e.target.closest('.task-item');
  const id = li.dataset.id;
  const completed = e.target.checked;
  const res = await fetch(`/api/tasks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed })
  });
  if (res.ok) {
    li.classList.toggle('completed', completed);
  } else {
    e.target.checked = !completed;
    alert('Error updating task');
  }
}

async function deleteTask(e) {
  const li = e.target.closest('.task-item');
  const id = li.dataset.id;
  const res = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
  if (res.ok) {
    li.remove();
  } else {
    alert('Error deleting task');
  }
}

form.addEventListener('submit', addTask);
fetchTasks();
```

---

## 6. Future Enhancements (Out of Scope)
- User authentication & multi-user support.  
- SQLite instead of JSON for concurrent writes.  
- Drag-and-drop task reordering.  
- Due dates and filtering.