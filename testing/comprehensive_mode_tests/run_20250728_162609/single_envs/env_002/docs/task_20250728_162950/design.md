# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** composed of two layers:

```
┌────────────────────────────────────────────┐
│  CLI Layer (calculator.py)                 │
│  • Handles I/O                             │
│  • Parses user input                       │
│  • Loops until exit                        │
└────────────────┬───────────────────────────┘
                 │ function calls
┌────────────────┴───────────────────────────┐
│  Core Layer (calculator/core.py)           │
│  • Pure arithmetic functions               │
│  • Raises DivisionByZeroError              │
│  • No side effects                         │
└────────────────────────────────────────────┘
```

The architecture enforces **strict separation of concerns**:  
- **CLI Layer** is responsible for all user interaction and input/output formatting.  
- **Core Layer** is a stateless library of arithmetic operations with no knowledge of the CLI.

## 2. Components

| Component | File | Responsibility |
|---|---|---|
| CLI Entry Point | `calculator.py` | `main()` function that implements the REPL loop, parses user input, calls core functions, prints results/errors, and handles exit. |
| Core Library | `calculator/core.py` | Four pure functions (`add`, `subtract`, `multiply`, `divide`) plus custom exception `DivisionByZeroError`. |
| Unit Tests | `tests/test_core.py` | `unittest.TestCase` subclasses covering all core functions and the custom exception. |
| Package Metadata | `calculator/__init__.py` | Exposes public API (`__all__ = ["add", "subtract", "multiply", "divide", "DivisionByZeroError"]`). |
| CI Workflow | `.github/workflows/ci.yml` | GitHub Actions job that installs Python 3.8+, runs `flake8`, then `python -m unittest discover`, and uploads coverage. |

### 2.1 Data Structures

- **DivisionByZeroError**  
  ```python
  class DivisionByZeroError(ValueError):
      """Raised when attempting to divide by zero."""
  ```

- **Input Token**  
  Internal representation inside CLI loop after parsing:  
  `(number1: float, operator: str, number2: float)`

## 3. Data Flow

### 3.1 Happy Path (e.g., `3 + 4`)

```
User Input: "3 + 4"
        │
        ▼
calculator.py:parse_input() → (3.0, "+", 4.0)
        │
        ▼
calculator.core.add(3.0, 4.0) → 7.0
        │
        ▼
calculator.py:print("7")
```

### 3.2 Division-by-Zero Path (e.g., `5 / 0`)

```
User Input: "5 / 0"
        │
        ▼
calculator.py:parse_input() → (5.0, "/", 0.0)
        │
        ▼
calculator.core.divide(5.0, 0.0) raises DivisionByZeroError
        │
        ▼
calculator.py catches → print("Error: Division by zero is undefined.")
```

### 3.3 Invalid Input Path (e.g., `abc + 3`)

```
User Input: "abc + 3"
        │
        ▼
calculator.py:parse_input() raises ValueError
        │
        ▼
calculator.py catches → print("Invalid input. Usage: <number> <+,-,*,/> <number>")
```

## 4. Implementation Plan

### Phase 1 – Project Skeleton (Day 1)
1. `mkdir calculator && cd calculator`
2. `python -m venv venv && source venv/bin/activate`
3. Create directory structure per TR-2.
4. Add empty `__init__.py` files.
5. Create `.gitignore` (Python template).
6. Commit initial skeleton.

### Phase 2 – Core Library (Day 2)
1. Implement `calculator/core.py`:
   - `add`, `subtract`, `multiply`, `divide` functions with type hints.
   - `DivisionByZeroError` exception.
2. Run `flake8 calculator/core.py` and fix style issues.
3. Commit.

### Phase 3 – Unit Tests (Day 3)
1. Implement `tests/test_core.py`:
   - Test cases for each arithmetic function (positive, negative, zero, float, int).
   - Test `DivisionByZeroError` is raised.
   - Achieve 100 % coverage via `coverage run -m unittest discover && coverage report`.
2. Commit.

### Phase 4 – CLI Layer (Day 4)
1. Implement `calculator.py`:
   - `parse_input(line: str) -> tuple[float, str, float]`
   - `main()` REPL loop.
   - Handle `KeyboardInterrupt` gracefully (print newline + exit).
2. Manual QA checklist:
   - [ ] `python calculator.py` starts prompt.
   - [ ] `3 + 4` → `7`.
   - [ ] `5 / 0` → division error.
   - [ ] `abc + 3` → invalid input.
   - [ ] `exit` → goodbye.
3. Commit.

### Phase 5 – CI & Polish (Day 5)
1. Add `.github/workflows/ci.yml`:
   - Trigger on push/PR to `main`.
   - Steps: checkout, setup-python, flake8, unittest, coverage.
2. Create `README.md`:
   - Installation, usage, example session, badge.
3. Push to GitHub and verify CI passes.
4. Tag v1.0.0.

## 5. File Structure

```
calculator/
├── .github/
│   └── workflows/
│       └── ci.yml
├── calculator/
│   ├── __init__.py
│   └── core.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── .gitignore
├── README.md
└── calculator.py
```

### 5.1 File Details

#### `calculator/core.py`
```python
from typing import Union

Number = Union[int, float]

class DivisionByZeroError(ValueError):
    """Raised when attempting to divide by zero."""

def add(a: Number, b: Number) -> Number:
    return a + b

def subtract(a: Number, b: Number) -> Number:
    return a - b

def multiply(a: Number, b: Number) -> Number:
    return a * b

def divide(a: Number, b: Number) -> Number:
    if b == 0:
        raise DivisionByZeroError("Cannot divide by zero.")
    return a / b
```

#### `calculator.py`
```python
#!/usr/bin/env python3
import sys
from calculator.core import add, subtract, multiply, divide, DivisionByZeroError

OPERATIONS = {
    '+': add,
    '-': subtract,
    '*': multiply,
    '/': divide,
}

def parse_input(line: str) -> tuple[float, str, float]:
    parts = line.strip().split()
    if len(parts) != 3:
        raise ValueError
    num1, op, num2 = parts
    if op not in OPERATIONS:
        raise ValueError
    try:
        return float(num1), op, float(num2)
    except ValueError:
        raise ValueError

def main() -> None:
    print("Simple CLI Calculator. Type 'exit' to quit.")
    while True:
        try:
            line = input("> ")
            if line.lower() == "exit":
                print("Goodbye!")
                break
            num1, op, num2 = parse_input(line)
            result = OPERATIONS[op](num1, num2)
            # Format: int if no fractional part, else float
            if isinstance(result, float) and result.is_integer():
                print(int(result))
            else:
                print(result)
        except DivisionByZeroError:
            print("Error: Division by zero is undefined.")
        except ValueError:
            print("Invalid input. Usage: <number> <+,-,*,/> <number>")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
```

#### `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.8"
      - run: pip install flake8 coverage
      - run: flake8 .
      - run: coverage run -m unittest discover
      - run: coverage report --fail-under=100
```

This design satisfies all functional and technical requirements while remaining minimal and maintainable.