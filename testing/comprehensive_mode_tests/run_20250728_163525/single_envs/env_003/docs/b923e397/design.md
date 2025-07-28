# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** composed of two logical layers:

```
┌─────────────────────────────┐
│        CLI Layer            │  (calculator/cli.py)
│  - Interactive prompt       │
│  - Input validation         │
│  - Menu loop                │
└──────────────┬──────────────┘
               │ function calls
┌──────────────┴──────────────┐
│       Core Layer            │  (calculator/core.py)
│  - Pure arithmetic ops      │
│  - Zero-division detection  │
└─────────────────────────────┘
```

No external services, databases, or network I/O are involved.  
All state is transient and lives only during a single CLI session.

## 2. Components

| Component | Responsibility | Public Interface |
|-----------|----------------|------------------|
| `calculator.core` | Business logic for arithmetic | `add`, `subtract`, `multiply`, `divide` |
| `calculator.cli` | User interaction loop | `main()` (entry point) |
| `tests.test_core` | Unit tests for core | `unittest.TestCase` subclasses |
| `tests.test_cli` | Unit tests for CLI | `unittest.TestCase` subclasses + mocks |
| `__main__.py` | Enables `python -m calculator` | delegates to `cli.main()` |

## 3. Data Flow

```
User → stdin → CLI
                │
                ├─ parse operation choice (1-5)
                ├─ parse two numbers (float)
                │
                ├─ call core.<op>(a, b)
                │        │
                │        └─ returns float or raises ValueError
                │
                ├─ format result or error
                │
                └─ print → stdout → User
```

Sequence diagram (happy path):

```
User          CLI                Core
----          ---                ----
              display_menu()
1<enter>      read_choice() → 1
              prompt("a: ")
3<enter>      read_number() → 3.0
              prompt("b: ")
4<enter>      read_number() → 4.0
              add(3.0, 4.0) ───────────► 7.0
              print("Result: 7.00")
```

Error path (division by zero):

```
CLI            Core
---            ----
divide(5,0) ──► ValueError("Cannot divide by zero")
catch
print("Error: Cannot divide by zero")
```

## 4. Implementation Plan

### Phase 0 – Project Skeleton
1. `mkdir calculator && cd calculator`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install --upgrade pip`
4. Create directories/files per TR-2.

### Phase 1 – Core Module
1. Implement `calculator/core.py`:
   - `add`, `subtract`, `multiply` as one-liners.
   - `divide` with explicit `if b == 0: raise ValueError(...)`.
2. Add docstrings and type hints.

### Phase 2 – Unit Tests for Core
1. `pip install pytest coverage flake8`
2. `tests/test_core.py`:
   - Parametrized tests for all four functions.
   - Edge cases: negative numbers, floats, large numbers.
   - `test_divide_by_zero_raises`.

### Phase 3 – CLI Module
1. `calculator/cli.py`:
   - `display_menu()` prints numbered options.
   - `read_choice()` loops until valid 1-5.
   - `read_number(prompt)` loops until float parsable.
   - `main()` orchestrates loop.
2. Use `try/except` around `divide` to catch `ValueError`.

### Phase 4 – CLI Tests
1. `tests/test_cli.py`:
   - `unittest.mock.patch('builtins.input')` to simulate user.
   - `unittest.mock.patch('builtins.print')` to capture output.
   - Test happy paths and error paths.

### Phase 5 – Packaging & Tooling
1. `pyproject.toml` (PEP 621):
   ```
   [project]
   name = "calculator"
   version = "1.0.0"
   dependencies = []
   [project.scripts]
   calculator = "calculator.cli:main"
   ```
2. `__main__.py`:
   ```
   from calculator.cli import main
   if __name__ == "__main__":
       main()
   ```
3. `requirements-dev.txt`:
   ```
   pytest>=7.0
   coverage[toml]>=6.0
   flake8>=5.0
   ```

### Phase 6 – QA & Release
1. Run `pytest --cov=calculator --cov-report=term-missing` → ≥ 95 %.
2. `flake8 calculator tests` → clean.
3. Manual QA checklist against FR-1…FR-10.
4. Tag `v1.0.0`.

## 5. File Structure

```
calculator/
├── calculator/
│   ├── __init__.py          # version, exports nothing
│   ├── __main__.py          # python -m calculator
│   ├── core.py              # arithmetic functions
│   └── cli.py               # interactive loop
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── test_cli.py
├── pyproject.toml           # packaging & tool configs
├── requirements-dev.txt     # dev dependencies
├── README.md                # usage, install, test
└── .gitignore               # venv, __pycache__, .coverage
```

### Example `calculator/core.py`

```python
from typing import Union

Number = Union[int, float]

def add(a: Number, b: Number) -> float:
    """Return a + b."""
    return float(a + b)

def subtract(a: Number, b: Number) -> float:
    """Return a - b."""
    return float(a - b)

def multiply(a: Number, b: Number) -> float:
    """Return a * b."""
    return float(a * b)

def divide(a: Number, b: Number) -> float:
    """Return a / b, raising ValueError if b == 0."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return float(a / b)
```

### Example `calculator/cli.py`

```python
import sys
from typing import Dict, Callable

from .core import add, subtract, multiply, divide

MENU = {
    "1": ("Add", add),
    "2": ("Subtract", subtract),
    "3": ("Multiply", multiply),
    "4": ("Divide", divide),
    "5": ("Exit", None),
}

def display_menu() -> None:
    for key, (label, _) in MENU.items():
        print(f"{key}) {label}")

def read_choice() -> str:
    while True:
        choice = input("Select operation: ").strip()
        if choice in MENU:
            return choice
        print("Invalid choice. Please select 1-5.")

def read_number(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Not a valid number. Try again.")

def main() -> None:
    print("=== Simple CLI Calculator ===")
    while True:
        display_menu()
        choice = read_choice()
        if choice == "5":
            print("Goodbye!")
            sys.exit(0)

        op_name, op_func = MENU[choice]
        a = read_number("Enter first number: ")
        b = read_number("Enter second number: ")

        try:
            result = op_func(a, b)
            print(f"Result: {result:.2f}")
        except ValueError as e:
            print(f"Error: {e}")
```

This design satisfies all functional and technical requirements while remaining minimal and maintainable.