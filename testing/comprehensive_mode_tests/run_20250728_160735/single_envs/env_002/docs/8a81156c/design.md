# design.md

## 1. System Architecture

The TODO completion system is designed as a modular, state-driven pipeline that processes TODO items from discovery through completion tracking. The architecture follows a producer-consumer pattern with persistent state management.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   TODO Source   │────▶│  TODO Processor  │────▶│  State Manager  │
│   Discovery     │     │   Engine         │     │   & Logger      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                ▼                          ▼
                       ┌──────────────────┐     ┌─────────────────┐
                       │  Update Service  │     │  Audit Trail    │
                       │  (update_todo)   │     │  (completion.log│
                       └──────────────────┘     └─────────────────┘
```

## 2. Components

### 2.1 TODO Discovery Service
**Purpose**: Identify and catalog all TODO items in the project
**Implementation**:
- **File**: `src/discovery/todo_finder.py`
- **Class**: `TODODiscoveryService`
- **Methods**:
  - `scan_project(root_path: str) -> List[TODOItem]`
  - `parse_todo_line(line: str, file_path: str, line_num: int) -> TODOItem`
  - `extract_metadata(todo_text: str) -> Dict[str, Any]`

### 2.2 TODO Item Model
**Purpose**: Standardized representation of TODO items
**Implementation**:
- **File**: `src/models/todo.py`
- **Class**: `TODOItem`
- **Attributes**:
  - `id: str` (UUID4)
  - `description: str`
  - `file_path: str`
  - `line_number: int`
  - `priority: int` (1-5, default 3)
  - `tags: List[str]`
  - `created_date: datetime`
  - `status: TODOStatus` (enum: PENDING, IN_PROGRESS, COMPLETED, BLOCKED)

### 2.3 Processing Engine
**Purpose**: Orchestrate the sequential processing of TODOs
**Implementation**:
- **File**: `src/processor/engine.py`
- **Class**: `TODOProcessor`
- **Methods**:
  - `load_todos() -> List[TODOItem]`
  - `sort_todos(todos: List[TODOItem]) -> List[TODOItem]`
  - `process_todo(todo: TODOItem) -> ProcessingResult`
  - `handle_error(todo: TODOItem, error: Exception)`

### 2.4 Update Service Adapter
**Purpose**: Interface with the update_todo tool/API
**Implementation**:
- **File**: `src/services/update_adapter.py`
- **Class**: `UpdateServiceAdapter`
- **Methods**:
  - `mark_completed(todo_id: str) -> bool`
  - `verify_completion(todo_id: str) -> bool`
  - `health_check() -> bool`

### 2.5 Audit Logger
**Purpose**: Maintain persistent audit trail
**Implementation**:
- **File**: `src/logging/audit_logger.py`
- **Class**: `AuditLogger`
- **Methods**:
  - `log_start(todo: TODOItem)`
  - `log_completion(todo: TODOItem, success: bool)`
  - `log_error(todo: TODOItem, error: str)`

### 2.6 Configuration Manager
**Purpose**: Manage system configuration
**Implementation**:
- **File**: `config/system.yaml`
- **Schema**:
  ```yaml
  project_root: "/path/to/project"
  todo_sources:
    - type: "markdown"
      path: "TODO.md"
    - type: "inline_comments"
      extensions: [".py", ".js", ".ts", ".md"]
      patterns: ["TODO:", "FIXME:", "HACK:"]
  update_service:
    type: "cli"  # or "api"
    endpoint: "http://localhost:8080/api/todos"
    auth_token: "${UPDATE_TOKEN}"
  processing_order: "priority"  # or "file_order", "creation_date"
  ```

## 3. Data Flow

### 3.1 Discovery Phase
1. **Input**: Project root directory
2. **Process**:
   - Recursively scan all files
   - Match against configured TODO patterns
   - Extract TODO metadata
   - Assign unique IDs
3. **Output**: List of TODOItem objects

### 3.2 Processing Phase
1. **Input**: Sorted list of pending TODOs
2. **Process**:
   - Filter out completed TODOs
   - Sort according to configured order
   - Process each TODO sequentially
3. **Output**: Processing results for each TODO

### 3.3 Update Phase
1. **Input**: Completed TODO ID
2. **Process**:
   - Call update_todo service
   - Verify update success
   - Update local state
3. **Output**: Success/failure status

### 3.4 Audit Phase
1. **Input**: Processing events
2. **Process**:
   - Write structured logs
   - Maintain completion log
   - Generate summary report
3. **Output**: audit.log file

## 4. Implementation Plan

### Phase 1: Foundation (Day 1)
- [ ] Create project structure
- [ ] Implement TODOItem model
- [ ] Set up configuration management
- [ ] Create basic logging infrastructure

### Phase 2: Discovery (Day 2)
- [ ] Implement TODO discovery for inline comments
- [ ] Implement TODO discovery for markdown files
- [ ] Add metadata extraction
- [ ] Create unit tests for discovery

### Phase 3: Processing Engine (Day 3)
- [ ] Implement sorting strategies
- [ ] Create processing orchestrator
- [ ] Add error handling
- [ ] Implement state persistence

### Phase 4: Update Integration (Day 4)
- [ ] Implement CLI adapter
- [ ] Implement API adapter
- [ ] Add retry logic
- [ ] Create health check endpoint

### Phase 5: Audit & Verification (Day 5)
- [ ] Implement audit logging
- [ ] Create verification script
- [ ] Add progress reporting
- [ ] Performance optimization

### Phase 6: Testing & Deployment (Day 6)
- [ ] Integration tests
- [ ] End-to-end testing
- [ ] Create Docker image
- [ ] Write deployment scripts

## 5. File Structure

```
todo-completion-system/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── todo_finder.py
│   │   └── patterns.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── todo.py
│   │   └── status.py
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── sorters.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── update_adapter.py
│   │   └── health_checker.py
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── audit_logger.py
│   │   └── formatters.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       └── validators.py
├── config/
│   ├── system.yaml
│   └── logging.yaml
├── scripts/
│   ├── verify_todos.sh
│   ├── deploy.sh
│   └── health_check.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── logs/
│   └── .gitkeep
├── Dockerfile
├── requirements.txt
├── setup.py
└── README.md
```

### Key Files Description

- **main.py**: Entry point with CLI interface
- **todo_finder.py**: Core discovery logic
- **engine.py**: Main processing orchestrator
- **update_adapter.py**: Abstraction layer for update_todo service
- **audit_logger.py**: Structured logging for audit trail
- **verify_todos.sh**: Post-execution verification script
- **system.yaml**: Central configuration file