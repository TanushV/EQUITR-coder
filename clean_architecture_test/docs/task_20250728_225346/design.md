# design.md

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 index.html (SPA)                      │   │
│  │  ┌─────────────┐        ┌──────────────────────┐    │   │
│  │  │   Form      │        │   Task List          │    │   │
│  │  │  (Add)      │        │  (Delete buttons)    │    │   │
│  │  └─────────────┘        └──────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │ AJAX (fetch)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  app.py                              │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │   │
│  │  │   Routes    │  │  Storage     │  │  Error    │ │   │
│  │  │  - GET /    │  │  Manager     │  │  Handler  │ │   │
│  │  │  - GET /api │  │  (tasks.json)│  │           │ │   │
│  │  │  - POST /api│  │              │  │           │ │   │
│  │  │  - DELETE   │  │              │  │           │ │   │
│  │  └─────────────┘  └──────────────┘  └───────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 2. Components

### 2.1 Backend Components

#### 2.1.1 Flask Application (`app.py`)
- **Purpose**: Core web server handling HTTP requests
- **Responsibilities**:
  - Serve static HTML template
  - Handle REST API endpoints
  - Manage JSON file I/O operations
  - Implement error handling middleware

#### 2.1.2 Storage Manager
- **Purpose**: Abstract JSON file operations
- **Interface**:
  ```python
  class TaskStore:
      def read_tasks() -> List[Dict[str, Any]]
      def write_tasks(tasks: List[Dict[str, Any]]) -> None
      def get_next_id() -> int
  ```

#### 2.1.3 Validation Layer
- **Purpose**: Validate incoming request data
- **Functions**:
  - `validate_task_text(text: str) -> Tuple[bool, str]`
  - `validate_json_payload(request) -> Tuple[bool, Dict[str, Any]]`

### 2.2 Frontend Components

#### 2.2.1 HTML Structure (`templates/index.html`)
- **Sections**:
  - Task input form with validation messages
  - Task list container with loading state
  - Error display area

#### 2.2.2 JavaScript Modules (`static/js/app.js`)
- **Modules**:
  - `TaskAPI`: Handles all fetch operations
  - `TaskRenderer`: Manages DOM updates
  - `FormValidator`: Client-side validation
  - `EventManager`: Binds user interactions

#### 2.2.3 CSS Framework (`static/css/style.css`)
- **Components**:
  - Base styles (reset, typography)
  - Layout utilities (container, spacing)
  - Component styles (form, buttons, task items)
  - Responsive breakpoints

## 3. Data Flow

### 3.1 Add Task Flow
```
User → Form Submit → JS Validation → POST /api/tasks → 
Server Validation → Generate ID → Write JSON → Return Task → 
Update DOM → Clear Form
```

### 3.2 View Tasks Flow
```
Page Load → GET /api/tasks → Parse JSON → 
Sort by ID (desc) → Render Task List → Bind Delete Handlers
```

### 3.3 Delete Task Flow
```
Delete Click → Confirm → DELETE /api/tasks/{id} → 
Update JSON → 204 Response → Remove DOM Element
```

### 3.4 Error Handling Flow
```
Error Occurs → Catch in JS → Display Inline Message → 
Log to Console → Reset UI State
```

## 4. Implementation Plan

### Phase 1: Project Setup (Day 1)
1. Create project directory structure
2. Set up virtual environment
3. Install Flask dependency
4. Create basic `app.py` with hello world route

### Phase 2: Backend Development (Day 2)
1. Implement storage manager with atomic writes
2. Create API endpoints:
   - `GET /api/tasks`
   - `POST /api/tasks`
   - `DELETE /api/tasks/<id>`
3. Add comprehensive error handling
4. Write unit tests for storage operations

### Phase 3: Frontend Development (Day 3)
1. Create responsive HTML template
2. Implement CSS styling
3. Build JavaScript modules:
   - API client
   - DOM manipulation
   - Event handling
4. Add client-side validation

### Phase 4: Integration & Testing (Day 4)
1. Connect frontend to backend
2. Test all user flows
3. Handle edge cases:
   - Empty submissions
   - Network failures
   - Concurrent modifications
4. Cross-browser testing

### Phase 5: Polish & Documentation (Day 5)
1. Add loading states
2. Implement accessibility features
3. Create README with setup instructions
4. Performance optimization

## 5. File Structure

```
todo-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── tasks.json            # Persistent storage (auto-generated)
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
│
├── templates/
│   └── index.html       # Single-page application
│
├── static/
│   ├── css/
│   │   └── style.css    # All styling rules
│   ├── js/
│   │   └── app.js       # Frontend JavaScript
│   └── images/          # Icons or logos (if needed)
│
├── tests/
│   ├── test_app.py      # Backend unit tests
│   └── test_storage.py  # Storage layer tests
│
└── docs/
    ├── api.md          # API documentation
    └── deployment.md   # Deployment guide
```

### 5.1 Key File Details

#### `app.py` Structure
```python
# Core imports
from flask import Flask, render_template, request, jsonify
import json
import os
from typing import List, Dict, Any

# Configuration
class Config:
    TASKS_FILE = 'tasks.json'
    MAX_TASK_LENGTH = 200

# Storage Manager
class TaskStore:
    # Implementation details...

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # Implementation...

@app.route('/api/tasks', methods=['POST'])
def create_task():
    # Implementation...

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    # Implementation...

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400
```

#### `index.html` Key Sections
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Todo App</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <main class="container">
        <h1>My Tasks</h1>
        
        <!-- Task Input Form -->
        <form id="task-form" class="task-form">
            <label for="task-input" class="sr-only">New task</label>
            <input type="text" 
                   id="task-input" 
                   placeholder="Add a new task..."
                   maxlength="200"
                   required>
            <button type="submit" class="btn btn-primary">Add</button>
        </form>
        
        <!-- Error Display -->
        <div id="error-message" class="error-message hidden"></div>
        
        <!-- Task List -->
        <ul id="task-list" class="task-list">
            <!-- Tasks will be populated here -->
        </ul>
        
        <!-- Loading State -->
        <div id="loading" class="loading hidden">Loading tasks...</div>
    </main>
    
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

#### `style.css` Architecture
```css
/* CSS Custom Properties */
:root {
    --primary-color: #007bff;
    --danger-color: #dc3545;
    --spacing-unit: 8px;
    --max-width: 600px;
}

/* Base Styles */
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }

/* Layout */
.container { max-width: var(--max-width); margin: 0 auto; }

/* Components */
.task-form { display: flex; gap: var(--spacing-unit); }
.task-item { display: flex; justify-content: space-between; }
.btn { padding: calc(var(--spacing-unit) * 1.5); border: none; }

/* Responsive */
@media (max-width: 480px) {
    .container { padding: var(--spacing-unit); }
}
```

#### `app.js` Module Structure
```javascript
// API Client
const TaskAPI = {
    async getTasks() { /* fetch implementation */ },
    async createTask(text) { /* POST implementation */ },
    async deleteTask(id) { /* DELETE implementation */ }
};

// DOM Manager
const TaskRenderer = {
    renderTask(task) { /* create DOM elements */ },
    removeTask(id) { /* remove from DOM */ },
    showError(message) { /* display error */ }
};

// Event Handlers
document.addEventListener('DOMContentLoaded', () => {
    // Initialize app
    loadTasks();
    bindFormSubmit();
});
```