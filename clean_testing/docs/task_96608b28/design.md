# design.md

## 1. System Architecture

The calculator is a **single-process, console-based application** that runs in an infinite loop until the user explicitly exits.  
Architecture pattern: **Interactive CLI Loop**

```
┌────────────────────────────┐
│  calculator.py (single file) │
│  ┌──────────────────────┐   │
│  │  main()              │   │
│  │  ┌────────────────┐  │   │
│  │  │  Menu Loop     │  │   │
│  │  │  ┌──────────┐  │  │   │
│  │  │  │  Input   │  │  │   │
│  │  │  │  Parsing │  │  │   │
│  │  │  └──────────┘  │  │   │
│  │  │  ┌──────────┐  │  │   │
│  │  │  │  Math    │  │  │   │
│  │  │  │  Engine  │  │  │   │
│  │  │  └──────────┘  │  │   │
│  │  └────────────────┘  │   │
│  └──────────────────────┘   │
└────────────────────────────┘
```

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| `main()` | Entry point, orchestrates program flow | `main() -> None` |
| `display_menu()` | Prints numbered menu to stdout | `display_menu() -> None` |
| `get_choice()` | Prompts & validates menu choice 1-5 | `get_choice() -> int` |
| `get_number(prompt: str) -> float` | Prompts until valid float is entered | `get_number(prompt: str) -> float` |
| `calculate(op: str, a: float, b: float) -> float` | Performs arithmetic, raises on div/0 | `calculate(op: str, a: float, b: float) -> float` |

(Helper functions may be inlined for brevity; shown separately for clarity.)

## 3. Data Flow

```
1. User launches:  $ python calculator.py
2. main() starts
   a. display_menu() prints menu
   b. get_choice() reads stdin → int choice
   c. if choice == 5 → sys.exit(0)
   d. else:
        a = get_number("Enter first number: ")
        b = get_number("Enter second number: ")
        result = calculate(choice, a, b)
        print("Result:", result)
   e. loop to 2a
```

Error paths:
- Invalid choice → re-prompt inside get_choice()
- Non-numeric input → ValueError caught → re-prompt inside get_number()
- Division by zero → ZeroDivisionError caught → print error → continue loop

## 4. Implementation Plan

| Step | Task | Deliverable | Time |
|---|---|---|---|
| 1 | Create project directory & empty `calculator.py` | Directory + file | 2 min |
| 2 | Implement `display_menu()` | Prints static menu | 5 min |
| 3 | Implement `get_choice()` | Returns int 1-5 | 10 min |
| 4 | Implement `get_number(prompt)` | Returns float | 10 min |
| 5 | Implement `calculate(op, a, b)` | Returns float or raises | 10 min |
| 6 | Wire `main()` loop | Integrate components | 10 min |
| 7 | Add docstrings & comments | PEP 8 compliant | 5 min |
| 8 | Manual test checklist | All FR-x pass | 10 min |
| 9 | Freeze & commit | Final `calculator.py` | 2 min |

Total estimated effort: ~1 hour.

## 5. File Structure

```
calculator/
└── calculator.py   # single source file
```

Inside `calculator.py`:

```
#!/usr/bin/env python3
"""
calculator.py
A simple interactive command-line calculator supporting
add, subtract, multiply, and divide operations.
"""

import sys

def display_menu() -> None:
    ...

def get_choice() -> int:
    ...

def get_number(prompt: str) -> float:
    ...

def calculate(op: str, a: float, b: float) -> float:
    ...

def main() -> None:
    """Main interactive loop for the calculator."""
    ...

if __name__ == "__main__":
    main()
```

No additional directories or configuration files are required.