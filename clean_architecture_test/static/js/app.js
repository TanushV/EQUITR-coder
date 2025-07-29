// Task Management Application - Frontend JavaScript

/**
 * API Client for task operations
 */
const TaskAPI = {
    baseURL: window.location.origin,

    /**
     * Fetch all tasks from the server
     * @returns {Promise<Array>} Array of task objects
     */
    async getTasks() {
        try {
            const response = await fetch('/api/tasks');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching tasks:', error);
            throw error;
        }
    },

    /**
     * Create a new task
     * @param {string} text - The task text
     * @returns {Promise<Object>} The created task object
     */
    async createTask(text) {
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text.trim() })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating task:', error);
            throw error;
        }
    },

    /**
     * Delete a task by ID
     * @param {number} id - The task ID to delete
     * @returns {Promise<void>}
     */
    async deleteTask(id) {
        try {
            const response = await fetch(`/api/tasks/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            return;
        } catch (error) {
            console.error('Error deleting task:', error);
            throw error;
        }
    }
};

/**
 * DOM Manipulation and Rendering
 */
const TaskRenderer = {
    taskList: null,
    taskForm: null,
    taskInput: null,
    errorMessage: null,
    loadingIndicator: null,
    submitButton: null,

    /**
     * Initialize DOM element references
     */
    init() {
        this.taskList = document.getElementById('task-list');
        this.taskForm = document.getElementById('task-form');
        this.taskInput = document.getElementById('task-input');
        this.errorMessage = document.getElementById('error-message');
        this.loadingIndicator = document.getElementById('loading');
        this.submitButton = this.taskForm.querySelector('button[type="submit"]');
    },

    /**
     * Render a single task in the DOM
     * @param {Object} task - The task object with id and text
     */
    renderTask(task) {
        const li = document.createElement('li');
        li.className = 'task-item';
        li.dataset.taskId = task.id;
        
        li.innerHTML = `
            <span class="task-text" title="${this.escapeHtml(task.text)}">${this.escapeHtml(task.text)}</span>
            <button type="button" 
                    class="btn btn-danger delete-btn" 
                    aria-label="Delete task: ${this.escapeHtml(task.text)}"
                    data-task-id="${task.id}">
                Delete
            </button>
        `;

        // Add the new task at the beginning of the list (newest first)
        this.taskList.insertBefore(li, this.taskList.firstChild);

        // Bind delete handler
        const deleteBtn = li.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', () => this.handleDelete(task.id));
    },

    /**
     * Remove a task from the DOM
     * @param {number} taskId - The ID of the task to remove
     */
    removeTask(taskId) {
        const taskElement = this.taskList.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
            taskElement.remove();
        }
    },

    /**
     * Clear all tasks from the DOM
     */
    clearTasks() {
        this.taskList.innerHTML = '';
    },

    /**
     * Display an error message
     * @param {string} message - The error message to display
     */
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.remove('hidden');
        this.errorMessage.setAttribute('role', 'alert');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideError();
        }, 5000);
    },

    /**
     * Hide the error message
     */
    hideError() {
        this.errorMessage.classList.add('hidden');
        this.errorMessage.removeAttribute('role');
    },

    /**
     * Show loading state
     */
    showLoading() {
        this.loadingIndicator.classList.remove('hidden');
        this.taskList.classList.add('hidden');
    },

    /**
     * Hide loading state
     */
    hideLoading() {
        this.loadingIndicator.classList.add('hidden');
        this.taskList.classList.remove('hidden');
    },

    /**
     * Disable form during submission
     */
    disableForm() {
        this.taskInput.disabled = true;
        this.submitButton.disabled = true;
        this.submitButton.textContent = 'Adding...';
    },

    /**
     * Enable form after submission
     */
    enableForm() {
        this.taskInput.disabled = false;
        this.submitButton.disabled = false;
        this.submitButton.textContent = 'Add';
    },

    /**
     * Clear the task input field
     */
    clearInput() {
        this.taskInput.value = '';
        this.taskInput.focus();
    },

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - The text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Handle delete task with confirmation
     * @param {number} taskId - The ID of the task to delete
     */
    async handleDelete(taskId) {
        const taskElement = this.taskList.querySelector(`[data-task-id="${taskId}"]`);
        const taskText = taskElement.querySelector('.task-text').textContent;

        if (confirm(`Are you sure you want to delete: "${taskText}"?`)) {
            try {
                await TaskAPI.deleteTask(taskId);
                this.removeTask(taskId);
                
                // Announce to screen readers
                this.announceToScreenReader(`Task "${taskText}" deleted`);
            } catch (error) {
                this.showError('Failed to delete task. Please try again.');
            }
        }
    },

    /**
     * Announce changes to screen readers
     * @param {string} message - The message to announce
     */
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.style.position = 'absolute';
        announcement.style.left = '-10000px';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
};

/**
 * Form Validation
 */
const FormValidator = {
    /**
     * Validate task input
     * @param {string} text - The task text to validate
     * @returns {Object} Validation result with isValid and message
     */
    validateTaskText(text) {
        const trimmed = text.trim();
        
        if (!trimmed) {
            return {
                isValid: false,
                message: 'Task cannot be empty'
            };
        }
        
        if (trimmed.length > 200) {
            return {
                isValid: false,
                message: 'Task must be 200 characters or less'
            };
        }
        
        return {
            isValid: true,
            message: ''
        };
    }
};

/**
 * Application Controller
 */
const App = {
    /**
     * Initialize the application
     */
    async init() {
        TaskRenderer.init();
        this.bindEvents();
        await this.loadTasks();
    },

    /**
     * Bind event listeners
     */
    bindEvents() {
        TaskRenderer.taskForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Clear error when user starts typing
        TaskRenderer.taskInput.addEventListener('input', () => {
            TaskRenderer.hideError();
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                TaskRenderer.taskForm.dispatchEvent(new Event('submit'));
            }
        });
    },

    /**
     * Handle form submission
     * @param {Event} e - The submit event
     */
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const taskText = TaskRenderer.taskInput.value;
        const validation = FormValidator.validateTaskText(taskText);
        
        if (!validation.isValid) {
            TaskRenderer.showError(validation.message);
            return;
        }

        TaskRenderer.disableForm();
        TaskRenderer.hideError();

        try {
            const newTask = await TaskAPI.createTask(taskText);
            TaskRenderer.renderTask(newTask);
            TaskRenderer.clearInput();
            
            // Announce to screen readers
            TaskRenderer.announceToScreenReader(`Task "${newTask.text}" added`);
        } catch (error) {
            TaskRenderer.showError('Failed to add task. Please try again.');
        } finally {
            TaskRenderer.enableForm();
        }
    },

    /**
     * Load all tasks from the server
     */
    async loadTasks() {
        TaskRenderer.showLoading();
        
        try {
            const tasks = await TaskAPI.getTasks();
            TaskRenderer.clearTasks();
            
            if (tasks.length === 0) {
                TaskRenderer.taskList.innerHTML = '<li class="empty-state">No tasks yet. Add one above!</li>';
            } else {
                tasks.forEach(task => TaskRenderer.renderTask(task));
            }
        } catch (error) {
            TaskRenderer.showError('Failed to load tasks. Please refresh the page.');
            TaskRenderer.taskList.innerHTML = '<li class="error-state">Could not load tasks</li>';
        } finally {
            TaskRenderer.hideLoading();
        }
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// Handle visibility change - refresh tasks when tab becomes visible
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        App.loadTasks();
    }
});