# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust: it will validate all user input, gracefully handle division-by-zero attempts, and be fully covered by unit tests.

## 2. Functional Requirements
| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-1 | CLI entry point | Running `python calculator.py` starts an interactive prompt that repeatedly asks the user for input until the user types `exit`. |
| FR-2 | Supported operations | The prompt accepts expressions in the form `<number1> <operator> <number2>` where `<operator>` is one of `+`, `-`, `*`, or `/`. |
| FR-3 | Input validation | Any non-numeric input, unsupported operator, or malformed expression prints `Invalid input. Usage: <number> <+,-,*,/> <number>` and re-prompts. |
| FR-4 | Division-by-zero handling | Attempting to divide by zero prints `Error: Division by zero is undefined.` and re-prompts. |
| FR-5 | Result display | Valid expressions print the exact result (integer if no decimals, otherwise float with full precision). |
| FR-6 | Exit command | Typing `exit` (case-insensitive) prints `Goodbye!` and terminates the program. |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language & version | Python 3.8+ |
| TR-2 | Project layout | ```
calculator/
├── calculator.py          # CLI entry point
├── calculator/
│   ├── __init__.py
│   └── core.py            # Arithmetic functions
└── tests/
    ├── __init__.py
    └── test_core.py       # Unit tests
``` |
| TR-3 | Core API | `calculator/core.py` exposes four pure functions: `add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)` that accept `int` or `float` and return `int` or `float`. |
| TR-4 | Error propagation | `divide` raises a custom exception `DivisionByZeroError` (subclass of `ValueError`) when `b == 0`. |
| TR-5 | CLI parsing | Use `argparse` or manual string splitting; no third-party CLI libraries. |
| TR-6 | Testing framework | `unittest` (standard library). |
| TR-7 | Test coverage | 100 % line coverage for `calculator/core.py`; at least one test per happy path and each error/edge case. |
| TR-8 | Continuous integration | GitHub Actions workflow that runs `python -m unittest discover` on push/PR to `main`. |

## 4. Success Criteria
- [ ] All functional requirements pass manual QA (run through the scenarios in FR-1 to FR-6).
- [ ] `python -m unittest discover` exits with code 0 and reports 100 % coverage for `calculator/core.py`.
- [ ] Repository README contains:
  - Installation instructions (`git clone …`, `python calculator.py`)
  - Example session transcript
  - Badge showing CI status
- [ ] No `print` statements inside `calculator/core.py`; all I/O is isolated to `calculator.py`.
- [ ] Code style passes `flake8` with default settings.