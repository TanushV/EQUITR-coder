# design.md

## 1. System Architecture

The calculator is a **single-process, command-line Python application** split into three logical layers:

```
┌────────────────────────────────────────────┐
│  CLI Layer (cli.py)                        │
│  • argparse for one-shot mode              │
│  • REPL loop for interactive mode          │
│  • Input/output formatting                 │
└────────────────┬───────────────────────────┘
                 │
┌────────────────┴───────────────────────────┐
│  Core Layer (core.py)                      │
│  • Pure arithmetic functions               │
│  • No I/O, no side effects                 │
└────────────────┬───────────────────────────┘
                 │
┌────────────────┴───────────────────────────┐
│  Exception Layer (exceptions.py)           │
│  • Custom exception hierarchy              │
│  • Centralized error handling              │
└────────────────────────────────────────────┘
```

- **CLI Layer** is the only component that interacts with `sys.argv`, `stdin`, `stdout`, `stderr`.
- **Core Layer** is 100 % unit-testable with no mocks.
- **Exception Layer** ensures all failures are expressed as domain-specific errors.

## 2. Components

| Component | File | Responsibility |
|---|---|---|
| Package metadata | `pyproject.toml` | Build system, dependencies, entry-point script `calc`. |
| Public API | `calculator/__init__.py` | Re-exports `add`, `subtract`, `multiply`, `divide` for library usage. |
| Core logic | `calculator/core.py` | Four pure functions, each ~3 lines, fully type-annotated. |
| Exceptions | `calculator/exceptions.py` | `CalculatorError`, `InvalidOperandError`, `UnsupportedOperatorError`, `DivisionByZeroError`. |
| CLI front-end | `calculator/cli.py` | `main(argv: list[str] \| None = None) -> int`, plus private helpers `_interactive_loop()` and `_parse_args()`. |
| Unit tests | `tests/test_core.py` | Parametrized pytest cases for all arithmetic paths. |
| CLI tests | `tests/test_cli.py` | Uses `pytest-console-scripts` to invoke `calc` in both modes. |
| CI workflow | `.github/workflows/ci.yml` | Runs on `ubuntu-latest`, `python 3.8–3.12`, installs package, runs `pytest --cov`. |

## 3. Data Flow

### 3.1 Single-Expression Mode

```
argv ──► argparse.ArgumentParser ──► (a, op, b)
                                   │
                                   ▼
                        float(a) ──┬── float(b)
                                   │
                                   ▼
                        core.dispatch(op, a, b) ──► result
                                   │
                                   ▼
                        stdout << format(result)
                                   │
                                   ▼
                        exit(0) or exit(1) on error
```

### 3.2 Interactive Mode

```
stdin ──► input() ──► str.strip().lower()
                         │
                         ├─ "exit" / "quit" ──► exit(0)
                         ├─ "help" ──► stdout << usage
                         └─ expression ──► _tokenize()
                                           │
                                           ▼
                                    validate tokens
                                           │
                                           ▼
                                    core.dispatch(...)
                                           │
                                           ▼
                                    stdout << result
                                           │
                                           ▼
                                    loop repeats
```

### 3.3 Error Flow

Any exception raised in `core` or during parsing is wrapped into a `CalculatorError` subclass, printed to `stderr`, and mapped to exit code 1.

## 4. Implementation Plan

| Phase | Task | Deliverable | Time |
|---|---|---|---|
| 0 | Bootstrap repo | `pyproject.toml`, `.gitignore`, `README.md` | 30 min |
| 1 | Core arithmetic | `calculator/core.py` + `tests/test_core.py` (100 % coverage) | 1 h |
| 2 | Exceptions | `calculator/exceptions.py` + unit tests | 30 min |
| 3 | CLI single-shot | `calculator/cli.py::_parse_args` + `tests/test_cli.py` (argparse path) | 1 h |
| 4 | CLI interactive | `_interactive_loop()` + integration tests via `pexpect` or `pytest-console-scripts` | 1.5 h |
| 5 | Packaging | `pyproject.toml` entry-point `[project.scripts] calc = "calculator.cli:main"` | 30 min |
| 6 | CI/CD | `.github/workflows/ci.yml` + badge in README | 30 min |
| 7 | Polish | Docstrings, `--help` text, final coverage check | 30 min |

Total estimated effort: **5 hours**.

## 5. File Structure

```
calculator/
├── pyproject.toml
├── README.md
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── calculator/
│   ├── __init__.py          # re-exports core functions
│   ├── core.py              # add, subtract, multiply, divide
│   ├── exceptions.py        # custom exception classes
│   └── cli.py               # main(), _interactive_loop(), _parse_args()
└── tests/
    ├── __init__.py
    ├── test_core.py         # pytest parametrize for all numeric cases
    ├── test_cli.py          # script runner tests
    └── fixtures/
        └── expressions.txt  # sample valid/invalid expressions for fuzzing
```

### 5.1 Key File Snippets

**calculator/core.py**
```python
from typing import Final

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

def multiply(a: float, b: float) -> float:
    return a * b

def divide(a: float, b: float) -> float:
    if b == 0:
        from .exceptions import DivisionByZeroError
        raise DivisionByZeroError("Division by zero is undefined.")
    return a / b
```

**calculator/cli.py**
```python
import argparse
import sys
from typing import Sequence

from .core import add, subtract, multiply, divide
from .exceptions import CalculatorError

OPERATIONS = {
    "+": add,
    "-": subtract,
    "*": multiply,
    "/": divide,
}

def _parse_args(argv: Sequence[str] | None = None) -> tuple[float, str, float]:
    parser = argparse.ArgumentParser(prog="calc", description="Simple CLI calculator.")
    parser.add_argument("a", type=float, help="First operand")
    parser.add_argument("op", choices=OPERATIONS.keys(), help="Operator")
    parser.add_argument("b", type=float, help="Second operand")
    ns = parser.parse_args(argv)
    return ns.a, ns.op, ns.b

def _interactive_loop() -> None:
    print("Calculator REPL. Type 'exit' or 'quit' to leave, 'help' for usage.")
    while True:
        try:
            line = input("calc> ").strip()
            if line.lower() in {"exit", "quit"}:
                break
            if line.lower() == "help":
                print("Usage: <number> <op> <number>")
                continue
            a_str, op, b_str = line.split()
            a, b = float(a_str), float(b_str)
            func = OPERATIONS[op]
            result = func(a, b)
            print(f"{result:.6f}".rstrip("0").rstrip("."))
        except ValueError:
            print("Error: Operands must be numbers.", file=sys.stderr)
        except KeyError:
            print("Error: Unsupported operator.", file=sys.stderr)
        except CalculatorError as e:
            print(f"Error: {e}", file=sys.stderr)

def main(argv: Sequence[str] | None = None) -> int:
    try:
        if argv is None:
            argv = sys.argv[1:]
        if not argv:
            _interactive_loop()
            return 0
        a, op, b = _parse_args(argv)
        result = OPERATIONS[op](a, b)
        print(f"{result:.6f}".rstrip("0").rstrip("."))
        return 0
    except CalculatorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SystemExit as e:
        return e.code or 2
```

**pyproject.toml (excerpt)**
```toml
[project]
name = "calculator"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = []

[project.scripts]
calc = "calculator.cli:main"

[project.optional-dependencies]
test = ["pytest>=7", "pytest-cov", "pytest-console-scripts"]

[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"
```

This design satisfies all functional and technical requirements while remaining minimal and maintainable.