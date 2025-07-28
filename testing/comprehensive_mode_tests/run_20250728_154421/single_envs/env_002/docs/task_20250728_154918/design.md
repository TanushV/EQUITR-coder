# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** built in Python 3.8+.  
It is decomposed into two logical layers:

1. **Presentation Layer** (`calculator.py`)  
   Handles user interaction, menu rendering, input collection, and error presentation.

2. **Business Logic Layer** (`operations.py`)  
   Stateless, side-effect-free arithmetic functions exposed as a public API.

There is no persistent storage, network I/O, or concurrency. All state is transient and lives only during a single user session.

```
┌────────────────────────────┐
│        User (TTY)          │
└──────────┬─────────────────┘
           │ stdin / stdout
┌──────────┴─────────────────┐
│      calculator.py         │
│  ┌──────────────────────┐  │
│  │   CLI Loop & Menu    │  │
│  │  Input Validation    │  │
│  └──────────┬───────────┘  │
│             │ call          │
│  ┌──────────┴───────────┐  │
│  │   operations.py      │  │
│  │  add, subtract, …    │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| `calculator.py` | CLI bootstrap, main loop, user prompts, graceful error display | `main() -> None` |
| `operations.py` | Pure arithmetic implementations | `add(a: float, b: float) -> float`  <br> `subtract(a: float, b: float) -> float`  <br> `multiply(a: float, b: float) -> float`  <br> `divide(a: float, b: float) -> float` |
| `tests/test_operations.py` | Unit tests for all four functions | pytest test cases |
| `.github/workflows/ci.yml` | GitHub Actions workflow | Runs lint + tests on push/PR |
| `requirements.txt` | Runtime & dev dependencies | `pytest>=7.0` |
| `pyproject.toml` | Tool configuration (ruff, coverage) | `[tool.ruff]`, `[tool.coverage.run]` |

## 3. Data Flow

1. **Startup**  
   `python calculator.py` → `main()` is invoked.

2. **Menu Rendering**  
   `main()` prints the fixed menu to `stdout`.

3. **Operation Selection**  
   User enters `1-5`.  
   - Invalid choice → re-prompt.  
   - `5` → `sys.exit(0)`.

4. **Number Acquisition**  
   For choices `1-4`, `get_number(prompt: str) -> float` is called twice.  
   Internally uses `float(input())` wrapped in `try/except ValueError`; loops until valid.

5. **Dispatch**  
   Based on choice, the corresponding function from `operations.py` is invoked with the two floats.

6. **Result or Error**  
   - Success → `Result: <value>` printed.  
   - `ZeroDivisionError` caught → `Error: Cannot divide by zero.` printed.  
   Flow returns to step 2.

Sequence diagram (simplified):

```
User -> CLI: "1"
CLI -> CLI: get_number() # first
CLI -> CLI: get_number() # second
CLI -> operations: add(3, 4)
operations --> CLI: 7
CLI -> User: "Result: 7"
```

## 4. Implementation Plan

### Phase 0 – Repo Skeleton (Day 0)
1. `mkdir calculator && cd calculator`
2. `git init`
3. Create directories: `tests/`, `.github/workflows/`
4. Add `.gitignore` (Python template)

### Phase 1 – Core Logic (Day 1)
1. `operations.py`
   - Implement `add`, `subtract`, `multiply`, `divide` with type hints and docstrings.
   - Raise `ZeroDivisionError` explicitly in `divide`.

2. `tests/test_operations.py`
   - Parametrized pytest cases for all four functions.
   - Positive, negative, float, int, zero, large numbers.
   - Assert `divide(5, 0)` raises `ZeroDivisionError`.

3. Run `pytest` locally → green.

### Phase 2 – CLI Interface (Day 2)
1. `calculator.py`
   - `main()` with infinite `while True` loop.
   - `print_menu()` helper.
   - `get_number(prompt: str) -> float` helper with `try/except`.
   - Dispatch table: `choices = {"1": add, "2": subtract, ...}`.
   - Catch `ZeroDivisionError` and print friendly message.

2. Manual test checklist (walk through FR-1 to FR-10).

### Phase 3 – Tooling & CI (Day 3)
1. `requirements.txt`
   ```
   pytest>=7.0
   ruff
   ```
2. `pyproject.toml`
   ```
   [tool.ruff]
   line-length = 88
   select = ["E", "F", "I", "N", "UP", "ANN", "S", "B", "A", "C4", "T20"]
   ```
3. `.github/workflows/ci.yml`
   - Python matrix 3.8, 3.9, 3.10, 3.11
   - Steps: checkout → setup-python → `pip install -r requirements.txt` → `ruff .` → `pytest --cov=operations tests/`
4. Push to GitHub, verify Actions green.

### Phase 4 – Polish & Documentation (Day 4)
1. `README.md`
   - Installation, usage, test commands.
2. Add shebang to `calculator.py` (`#!/usr/bin/env python3`) and `chmod +x`.
3. Tag v1.0 release.

## 5. File Structure

```
calculator/
├── calculator.py              # CLI entry point
├── operations.py              # Arithmetic functions
├── tests/
│   ├── __init__.py
│   └── test_operations.py     # pytest unit tests
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions
├── .gitignore
├── pyproject.toml             # Ruff & coverage config
├── requirements.txt           # Dependencies
└── README.md                  # User & dev docs
```

### File Details

#### `calculator.py`
```python
#!/usr/bin/env python3
"""
Interactive command-line calculator.
"""

from operations import add, subtract, multiply, divide

MENU = """\
Select operation:
1) Add
2) Subtract
3) Multiply
4) Divide
5) Exit
"""

def print_menu() -> None:
    print(MENU)

def get_number(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid number, please try again.")

def main() -> None:
    operations = {
        "1": add,
        "2": subtract,
        "3": multiply,
        "4": divide,
    }

    while True:
        print_menu()
        choice = input("Enter choice (1-5): ").strip()
        if choice == "5":
            print("Goodbye!")
            break
        if choice not in operations:
            print("Invalid choice.")
            continue

        a = get_number("Enter first number: ")
        b = get_number("Enter second number: ")

        try:
            result = operations[choice](a, b)
        except ZeroDivisionError:
            print("Error: Cannot divide by zero.")
        else:
            print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

#### `operations.py`
```python
"""
Pure arithmetic functions.
"""

def add(a: float, b: float) -> float:
    """Return the sum of a and b."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Return the difference of a and b."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Return the product of a and b."""
    return a * b

def divide(a: float, b: float) -> float:
    """Return the quotient of a and b. Raises ZeroDivisionError if b is zero."""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b
```

#### `tests/test_operations.py`
```python
import pytest
from operations import add, subtract, multiply, divide

@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (-1, 1, 0),
    (0.5, 0.5, 1.0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected

@pytest.mark.parametrize("a,b,expected", [
    (10, 4, 6),
    (-1, -1, 0),
    (2.5, 1.5, 1.0),
])
def test_subtract(a, b, expected):
    assert subtract(a, b) == expected

@pytest.mark.parametrize("a,b,expected", [
    (3, 4, 12),
    (-2, 3, -6),
    (2.5, 4, 10.0),
])
def test_multiply(a, b, expected):
    assert multiply(a, b) == expected

@pytest.mark.parametrize("a,b,expected", [
    (8, 2, 4.0),
    (5, 2, 2.5),
    (-6, -3, 2.0),
])
def test_divide(a, b, expected):
    assert divide(a, b) == expected

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(5, 0)
```

#### `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: ruff .
      - run: pytest --cov=operations tests/
```

#### `requirements.txt`
```
pytest>=7.0
pytest-cov>=4.0
ruff>=0.1
```

#### `pyproject.toml`
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B", "A", "C4", "T20"]

[tool.coverage.run]
source = ["operations"]
```

This design satisfies all functional and technical requirements while remaining minimal and maintainable.