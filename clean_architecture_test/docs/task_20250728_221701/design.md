# Technical Design Document – Calculator Program (`calculator.py`)

## 1. System Architecture

```
┌─────────────────────────────────────────────┐
│              calculator.py                  │
│  ┌─────────────────────────────────────┐   │
│  │         Main Entry Point            │   │
│  │            main()                   │   │
│  └─────────────────┬───────────────────┘   │
│                    │                         │
│  ┌─────────────────┴───────────────────┐   │
│  │         User Interface Layer        │   │
│  │  - display_menu()                   │   │
│  │  - get_number(prompt)               │   │
│  │  - get_operation()                  │   │
│  └─────────────────┬───────────────────┘   │
│                    │                         │
│  ┌─────────────────┴───────────────────┐   │
│  │         Business Logic Layer        │   │
│  │  - add(a, b)                        │   │
│  │  - subtract(a, b)                   │   │
│  │  - multiply(a, b)                   │   │
│  │  - divide(a, b)                     │   │
│  └─────────────────┬───────────────────┘   │
│                    │                         │
│  ┌─────────────────┴───────────────────┐   │
│  │         Validation Layer            │   │
│  │  - validate_number(input_str)       │   │
│  │  - validate_operation(op_str)       │   │
│  └─────────────────┬───────────────────┘   │
│                    │                         │
│  ┌─────────────────┴───────────────────┐   │
│  │         Utility Layer               │   │
│  │  - format_result(value)             │   │
│  │  - is_exit_command(input_str)       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 2. Components

### 2.1 Core Components

| Component | Purpose | Interface |
|---|---|---|
| **Calculator Engine** | Performs mathematical operations | Four functions: `add()`, `subtract()`, `multiply()`, `divide()` |
| **Input Handler** | Manages user input with validation | `get_number()`, `get_operation()`, `validate_input()` |
| **UI Manager** | Handles user interaction and display | `display_menu()`, `display_result()`, `display_error()` |
| **Exit Controller** | Manages program termination | `should_exit()`, `handle_exit()` |

### 2.2 Data Types

| Type | Description | Example |
|---|---|---|
| **Number** | Float or integer input | `3.5`, `42`, `-7.25` |
| **Operation** | String representing operation | `"+"`, `"-"`, `"*"`, `"/"` |
| **Result** | Formatted string output | `"5.60"`, `"Error: Division by zero"` |

### 2.3 Error Types

| Error | Trigger | Handling |
|---|---|---|
| `ValueError` | Non-numeric input | Re-prompt user |
| `ZeroDivisionError` | Division by zero | Display error, re-prompt |
| `KeyboardInterrupt` | Ctrl+C | Graceful exit |

## 3. Data Flow

### 3.1 Happy Path Flow
```
User Input → Validation → Operation → Calculation → Format → Display
     ↓            ↓           ↓           ↓           ↓         ↓
"3.5" → float(3.5) → "+" → add(3.5,2.1) → 5.6 → "5.60" → Console
```

### 3.2 Error Flow
```
User Input → Validation → Error Detection → Error Display → Re-prompt
     ↓            ↓              ↓               ↓            ↓
"abc" → ValueError → catch → "Invalid input" → Retry
```

### 3.3 Exit Flow
```
User Input → Exit Detection → Confirmation → Program Termination
     ↓            ↓              ↓               ↓
"q" → is_exit_command → True → sys.exit(0)
```

## 4. Implementation Plan

### Phase 1: Core Structure (30 min)
1. Create `calculator.py` with file header
2. Implement basic function signatures
3. Add `main()` entry point
4. Set up module docstring

### Phase 2: Mathematical Operations (20 min)
1. Implement `add(a, b)` with docstring
2. Implement `subtract(a, b)` with docstring
3. Implement `multiply(a, b)` with docstring
4. Implement `divide(a, b)` with ZeroDivisionError handling

### Phase 3: Input Validation (25 min)
1. Create `get_number(prompt)` with ValueError handling
2. Create `get_operation()` with validation
3. Implement exit command detection
4. Add input sanitization (strip whitespace, lowercase)

### Phase 4: User Interface (20 min)
1. Create `display_menu()` function
2. Implement result formatting (`format_result()`)
3. Add error message display
4. Create main loop in `main()`

### Phase 5: Integration & Testing (15 min)
1. Test all operations with valid inputs
2. Test edge cases (division by zero, negative numbers)
3. Test exit commands at each prompt
4. Run pylint/flake8 for style compliance

### Phase 6: Polish & Documentation (10 min)
1. Add comprehensive docstrings
2. Review and clean code
3. Final testing with sample session

## 5. File Structure

```
calculator.py                 # Single file containing all components
├── Module-level constants
│   ├── OPERATIONS = {'+', '-', '*', '/'}
│   ├── EXIT_COMMANDS = {'q', 'quit', 'exit'}
│   └── PRECISION = 2
├── Core Functions
│   ├── add(a: float, b: float) -> float
│   ├── subtract(a: float, b: float) -> float
│   ├── multiply(a: float, b: float) -> float
│   └── divide(a: float, b: float) -> float
├── Input Functions
│   ├── get_number(prompt: str) -> float
│   ├── get_operation() -> str
│   └── should_exit(user_input: str) -> bool
├── Display Functions
│   ├── display_menu()
│   ├── display_result(result: float)
│   └── display_error(message: str)
├── Utility Functions
│   ├── format_result(value: float) -> str
│   └── clear_screen() [optional]
└── Entry Point
    └── main() -> None
    └── if __name__ == "__main__": main()
```

### 5.1 Function Specifications

#### `add(a: float, b: float) -> float`
- **Purpose**: Perform addition
- **Parameters**: Two float numbers
- **Returns**: Sum as float
- **Raises**: None

#### `get_number(prompt: str) -> float`
- **Purpose**: Get validated numeric input
- **Parameters**: Display prompt string
- **Returns**: Valid float number
- **Raises**: SystemExit on exit command

#### `format_result(value: float) -> str`
- **Purpose**: Format calculation result
- **Parameters**: Raw float result
- **Returns**: String with 2 decimal places
- **Example**: `5.6` → `"5.60"`

### 5.2 Testing Checklist

- [ ] Addition: `2 + 3 = 5.00`
- [ ] Subtraction: `5.5 - 2.1 = 3.40`
- [ ] Multiplication: `3 * 4 = 12.00`
- [ ] Division: `10 / 3 = 3.33`
- [ ] Division by zero handled
- [ ] Invalid input re-prompts
- [ ] Exit commands work at all prompts
- [ ] Negative numbers supported
- [ ] Decimal precision maintained