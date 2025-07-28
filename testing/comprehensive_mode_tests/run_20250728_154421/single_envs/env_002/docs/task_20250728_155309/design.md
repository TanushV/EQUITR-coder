# design.md

## 1. System Architecture

```
┌─────────────────────────────────────────────┐
│              Todo Processor                 │
│              (Single Process)               │
├─────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐        │
│  │   Parser    │  │   Executor   │        │
│  │  (FR-1,2)   │  │   (FR-3)     │        │
│  └──────┬──────┘  └──────┬───────┘        │
│         │                │                 │
│  ┌──────┴────────────────┴───────┐        │
│  │        File Manager            │        │
│  │      (Read/Write)              │        │
│  └────────────────────────────────┘        │
└─────────────────────────────────────────────┘
```

## 2. Components

### 2.1 Parser Module
- **Purpose**: Reads and parses `todos.md`
- **Responsibilities**:
  - Validate file existence
  - Read UTF-8 content
  - Identify open todos (`- [ ]`)
  - Track line numbers for updates
- **Output**: List of `(line_number, todo_text)` tuples

### 2.2 Executor Module
- **Purpose**: Processes each identified todo
- **Responsibilities**:
  - Execute todo-specific logic
  - Update todo status to `- [x]`
  - Log completion to stdout
- **Interface**: `execute_todo(todo_text: str) -> bool`

### 2.3 File Manager
- **Purpose**: Handles file I/O operations
- **Responsibilities**:
  - Atomic read/write operations
  - Preserve file permissions
  - Handle backup creation (optional)
- **Methods**:
  - `read_file(path: str) -> List[str]`
  - `write_file(path: str, lines: List[str]) -> None`

### 2.4 Main Controller
- **Purpose**: Orchestrates the entire process
- **Flow**:
  1. Initialize components
  2. Parse todos
  3. Validate count (≥3 or warn)
  4. Execute first 3
  5. Update file
  6. Report results

## 3. Data Flow

```
1. File Read
   todos.md ────────┐
                    ▼
   ┌─────────────────────────────────┐
   │         Raw Lines               │
   │   ["- [ ] Task 1", ...]         │
   └─────────────────────────────────┘
                    │
                    ▼
2. Parse & Filter
   ┌─────────────────────────────────┐
   │      Open Todos                 │
   │ [(3, "Task 1"), (5, "Task 2")]  │
   └─────────────────────────────────┘
                    │
                    ▼
3. Execute Tasks
   ┌─────────────────────────────────┐
   │    Completed Tasks              │
   │ [True, True, True]              │
   └─────────────────────────────────┘
                    │
                    ▼
4. Update Lines
   ┌─────────────────────────────────┐
   │    Modified Lines               │
   │ ["- [x] Task 1", ...]           │
   └─────────────────────────────────┘
                    │
                    ▼
5. File Write
   todos.md ◄───────┘
```

## 4. Implementation Plan

### Phase 1: Setup (Day 1)
1. Create project structure
2. Initialize Python virtual environment
3. Create `requirements.txt` with dependencies
4. Set up basic logging configuration

### Phase 2: Core Development (Day 2-3)
1. Implement File Manager
   - `read_file()` with UTF-8 support
   - `write_file()` with atomic write
   - Error handling for missing files
2. Implement Parser
   - Regex pattern for `- [ ]` detection
   - Line number tracking
   - Edge case handling (malformed todos)
3. Implement Executor
   - Todo-to-action mapping
   - Logging implementation
   - Error handling for failed executions

### Phase 3: Integration & Testing (Day 4)
1. Create Main Controller
2. Implement argument parsing (optional)
3. Add comprehensive unit tests
4. Create sample `todos.md` for testing

### Phase 4: Deployment (Day 5)
1. Create executable script
2. Add usage documentation
3. Package for distribution
4. Final validation against requirements

## 5. File Structure

```
todo-processor/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── parser.py            # Todo parsing logic
│   ├── executor.py          # Todo execution logic
│   ├── file_manager.py      # File I/O operations
│   └── logger.py            # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_executor.py
│   ├── test_file_manager.py
│   └── fixtures/
│       ├── sample_todos.md
│       └── edge_cases.md
├── scripts/
│   └── run.sh              # Convenience script
├── todos.md                # Target file
├── requirements.txt
├── setup.py               # Package setup
└── README.md
```

### Key Files Description

**src/main.py**
```python
def main():
    # 1. Initialize components
    # 2. Parse todos
    # 3. Execute first 3
    # 4. Update file
    # 5. Report results
```

**src/parser.py**
```python
class TodoParser:
    OPEN_PATTERN = re.compile(r'^- \[ \] (.+)$')
    
    def parse(self, lines: List[str]) -> List[Tuple[int, str]]:
        # Returns [(line_num, todo_text), ...]
```

**src/executor.py**
```python
class TodoExecutor:
    def execute(self, todo_text: str) -> bool:
        # Maps todo text to specific action
        # Returns success status
```

**src/file_manager.py**
```python
class FileManager:
    def read_file(self, path: str) -> List[str]:
        # Returns list of lines
    
    def write_file(self, path: str, lines: List[str]) -> None:
        # Atomic write with backup
```