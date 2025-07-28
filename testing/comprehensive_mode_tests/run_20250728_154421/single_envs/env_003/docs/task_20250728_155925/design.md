# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** written in Python 3.8+.  
It is split into two logical layers:

1. **Presentation Layer** (`cli.py`)  
   Handles all user interaction: prompting, parsing, validation, and display.

2. **Business Logic Layer** (`operations.py`)  
   Stateless, side-effect-free arithmetic functions that perform the actual calculations.

The architecture is intentionally minimal—no external services, no concurrency, no persistent storage—so the data flow is strictly **Input → Parse → Validate → Compute → Output**.

```
┌─────────────┐
│   Terminal  │
└──────┬──────┘
       │ text I/O
┌──────┴──────┐
│   cli.py    │  ← Presentation Layer
│  (REPL)     │
└──────┬──────┘
       │ pure function calls
┌──────┴──────┐
│operations.py│  ← Business Logic Layer
└─────────────┘
```

## 2. Components

| Component | File | Responsibility |
|---|---|---|
| **Entry Point** | `calculator/__main__.py` | `python -m calculator` bootstrap. Imports `cli.main()` and runs it. |
| **CLI Loop** | `calculator/cli.py` | Implements the REPL:<br>- Prints welcome/goodbye banners.<br>- Reads lines from stdin.<br>- Converts strings → floats.<br>- Maps operator symbols → functions.<br>- Catches `ZeroDivisionError`, `ValueError`.<br>- Loops until exit command. |
| **Arithmetic Core** | `calculator/operations.py` | Four pure functions:<br>`add`, `subtract`, `multiply`, `divide`.<br>Each takes two `float` and returns `float`.<br>`divide` raises `ZeroDivisionError` when `b == 0`. |
| **Unit Tests** | `tests/test_operations.py`<br>`tests/test_cli.py` | Pytest suites:<br>- `test_operations.py`: 100 % coverage of arithmetic edge cases.<br>- `test_cli.py`: 100 % coverage of input parsing, validation, exit commands, and error messages. |
| **Packaging** | `setup.cfg`<br>`pyproject.toml` (optional) | Declares console script entry point so `calculator` becomes a shell command. |
| **Documentation** | `README.md` | Installation, usage, test commands. |

## 3. Data Flow

```
1. User launches: $ python -m calculator
2. Welcome banner printed.
3. Loop:
   a. Prompt "Enter first number:" → raw string
   b. If raw string in {"q","quit","exit"} → print goodbye → sys.exit(0)
   c. float(raw) → first: float
   d. Prompt "Enter operator (+, -, *, /):" → op: str
   e. If op not in {"+","-","*","/"} → print "Invalid operator" → continue
   f. Prompt "Enter second number:" → second: float (same validation as c)
   g. Lookup table maps op → function in operations.py
   h. Call function(first, second)
      - On ZeroDivisionError → print error → continue
   i. Print "first op second = result"
4. Repeat loop.
```

All I/O is synchronous and blocking; no buffering beyond Python’s built-in `input()`.

## 4. Implementation Plan

| Phase | Task | Deliverable |
|---|---|---|
| **0. Repo Setup** | `mkdir calculator && cd calculator && git init` | Empty repo |
| **1. Skeleton** | Create directory layout per TR-2. Add empty `__init__.py` files. | `tree` matches spec |
| **2. Core Functions** | Implement `operations.py` with four functions + docstrings. | Passes `pytest tests/test_operations.py` |
| **3. CLI Loop** | Implement `cli.py` with REPL, input validation, exit commands. | Manual test: all FRs satisfied |
| **4. Unit Tests** | Write `test_operations.py` and `test_cli.py` to achieve 100 % coverage. | `pytest --cov=calculator` shows 100 % |
| **5. Packaging** | Add `__main__.py`, `setup.cfg`, `requirements.txt`. | `pip install -e .` exposes `calculator` command |
| **6. QA & Docs** | Run `flake8`, `black`, fill `README.md`. | All success criteria checked |

Suggested commit sequence:
1. `feat: add operations.py with arithmetic functions`
2. `feat: add cli.py REPL`
3. `test: 100 % coverage for operations`
4. `test: 100 % coverage for cli`
5. `build: packaging and entry point`
6. `docs: README and final polish`

## 5. File Structure

```
calculator/
├── calculator/
│   ├── __init__.py          # version, exposes nothing
│   ├── __main__.py          # python -m calculator entry
│   ├── cli.py               # REPL, I/O, validation
│   └── operations.py        # arithmetic functions
├── tests/
│   ├── __init__.py
│   ├── test_operations.py   # pytest for operations.py
│   └── test_cli.py          # pytest for cli.py (monkeypatch stdin/stdout)
├── requirements.txt         # pytest==7.*
├── setup.cfg                # [metadata] + [options.entry_points]
├── pyproject.toml           # optional build-system
├── README.md
└── .gitignore
```

### Key File Snippets

**calculator/operations.py**
```python
def add(a: float, b: float) -> float:
    """Return a + b."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Return a - b."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Return a * b."""
    return a * b

def divide(a: float, b: float) -> float:
    """Return a / b. Raises ZeroDivisionError if b == 0."""
    if b == 0:
        raise ZeroDivisionError("Division by zero is undefined.")
    return a / b
```

**calculator/cli.py**
```python
import sys
from typing import Dict, Callable
from .operations import add, subtract, multiply, divide

OPERATIONS: Dict[str, Callable[[float, float], float]] = {
    "+": add,
    "-": subtract,
    "*": multiply,
    "/": divide,
}

def read_number(prompt: str) -> float:
    while True:
        raw = input(prompt).strip().lower()
        if raw in {"q", "quit", "exit"}:
            print("Goodbye!")
            sys.exit(0)
        try:
            return float(raw)
        except ValueError:
            print("Invalid input, please try again.")

def read_operator() -> str:
    while True:
        op = input("Enter operator (+, -, *, /): ").strip()
        if op in OPERATIONS:
            return op
        print("Invalid operator, please try again.")

def main() -> None:
    print("Welcome to the CLI Calculator!")
    while True:
        a = read_number("Enter first number: ")
        op = read_operator()
        b = read_number("Enter second number: ")
        try:
            result = OPERATIONS[op](a, b)
            print(f"{a} {op} {b} = {result}")
        except ZeroDivisionError as e:
            print(f"Error: {e}")
```

**setup.cfg**
```
[metadata]
name = calculator
version = 1.0.0

[options]
packages = calculator

[options.entry_points]
console_scripts =
    calculator = calculator.cli:main
```

**requirements.txt**
```
pytest==7.*
```

This design satisfies all functional and technical requirements while remaining minimal and maintainable.