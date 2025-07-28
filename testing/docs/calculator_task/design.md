# design.md

## 1. System Architecture

The calculator is a **single-process, console application** that follows a **linear control flow**:

```
┌─────────────────────────────┐
│  User runs calculator.py    │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  1. Read first number       │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  2. Read second number      │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  3. Read operation choice   │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  4. Validate all inputs     │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  5. Compute result          │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  6. Display result / error  │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  7. Exit                    │
└─────────────────────────────┘
```

## 2. Components

### 2.1 Core Components (all in `calculator.py`)

| Component | Responsibility | Lines (approx) |
|-----------|----------------|----------------|
| `main()` | Orchestrates the entire flow | 15-20 |
| `read_number(prompt)` | Reads and validates numeric input | 8-12 |
| `read_operation()` | Reads and validates operation choice | 6-10 |
| `calculate(a, b, op)` | Performs the arithmetic | 4-6 |
| `display_result(value)` | Prints formatted result | 2-3 |
| `display_error(reason)` | Prints formatted error and exits | 3-4 |

### 2.2 Helper Constants

```python
VALID_OPERATIONS = {"add", "subtract"}
```

## 3. Data Flow

### 3.1 Happy Path Flow
```
User Input → String → Float Conversion → Validation → Calculation → Output
```

### 3.2 Error Path Flow
```
User Input → String → Validation Failure → Error Message → Exit(1)
```

### 3.3 Data Types
| Stage | Type | Example |
|-------|------|---------|
| Raw input | `str` | `"5.2"` |
| Parsed number | `float` | `5.2` |
| Operation | `str` | `"add"` |
| Result | `float` | `8.7` |

## 4. Implementation Plan

### Phase 1: Skeleton (5 min)
1. Create `calculator.py`
2. Add shebang: `#!/usr/bin/env python3`
3. Add `if __name__ == "__main__":` guard
4. Create empty `main()` function

### Phase 2: Input Functions (10 min)
1. Implement `read_number(prompt)` with try/except for `ValueError`
2. Implement `read_operation()` with validation against `VALID_OPERATIONS`
3. Test both functions manually

### Phase 3: Core Logic (5 min)
1. Implement `calculate(a, b, op)` with simple if/else
2. Add basic tests in comments

### Phase 4: Output Functions (3 min)
1. Implement `display_result(value)` with format string
2. Implement `display_error(reason)` with `sys.exit(1)`

### Phase 5: Integration (5 min)
1. Wire all components in `main()`
2. Test success criteria cases

### Phase 6: Polish (2 min)
1. Add docstrings
2. Run final test suite

## 5. File Structure

```
calculator/
└── calculator.py          # Single file containing all code
```

### 5.1 File Layout (`calculator.py`)

```python
#!/usr/bin/env python3
"""
Simple command-line calculator for addition and subtraction.

Usage:
    python calculator.py
"""

import sys

VALID_OPERATIONS = {"add", "subtract"}

def read_number(prompt):
    """Read and validate a number from user input."""
    ...

def read_operation():
    """Read and validate the operation choice."""
    ...

def calculate(a, b, operation):
    """Perform the requested calculation."""
    ...

def display_result(value):
    """Display the calculation result."""
    ...

def display_error(reason):
    """Display an error message and exit."""
    ...

def main():
    """Main program entry point."""
    ...

if __name__ == "__main__":
    main()
```

### 5.2 Testing Commands

```bash
# Success cases
echo -e "5\n3\nadd" | python calculator.py      # Should print "Result: 8"
echo -e "10\n4\nsubtract" | python calculator.py # Should print "Result: 6"

# Error cases
echo -e "abc\n3\nadd" | python calculator.py     # Should print "Error: Invalid number"
echo -e "5\n3\nmultiply" | python calculator.py  # Should print "Error: Invalid operation"
```