# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** written in Python 3.8+.  
It is split into three logical layers:

```
┌────────────────────────────┐
│        CLI Layer           │  (I/O, argument parsing)
│  cli.py  ──►  parse_input  │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│      Core Logic Layer      │  (pure arithmetic)
│      calculate()           │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│      Test Layer            │  (unit tests)
│  test_calculator.py        │
└────────────────────────────┘
```

- **CLI Layer** handles all user interaction and translates raw text into validated data.
- **Core Logic Layer** is stateless and side-effect-free; it performs arithmetic only.
- **Test Layer** exercises both layers with mocked I/O where necessary.

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| `calculator/__init__.py` | Package marker, exposes `__version__` | `__version__ = "1.0.0"` |
| `calculator/cli.py` | Entry point, argument parsing, REPL loop | `main(argv=None)` |
| `calculator/operations.py` | Pure arithmetic functions | `add(a,b)`, `sub(a,b)`, `mul(a,b)`, `div(a,b)` |
| `calculator/exceptions.py` | Custom exceptions | `CalculatorError`, `InvalidInputError`, `DivisionByZeroError` |
| `tests/test_calculator.py` | Unit tests | `unittest.TestCase` subclasses |

## 3. Data Flow

### 3.1 Interactive Mode
```
User types:  5.2 * -3<Enter>
     │
     ▼
sys.stdin ──► cli.py:read_input() ──► "5.2 * -3"
     │
     ▼
parse_input("5.2 * -3") ──► (5.2, -3, "*")
     │
     ▼
calculate(5.2, -3, "*") ──► -15.6
     │
     ▼
print(-15.6) ──► stdout
```

### 3.2 Argument Mode
```
$ python -m calculator.cli 10 / 0
     │
     ▼
sys.argv == ["calculator/cli.py", "10", "/", "0"]
     │
     ▼
parse_input("10 / 0") ──► (10, 0, "/")
     │
     ▼
calculate() raises DivisionByZeroError
     │
     ▼
main() catches, prints "Error: Division by zero is undefined."
     │
     ▼
sys.exit(1)
```

## 4. Implementation Plan

### Phase 1 – Skeleton & Tooling (0.5 day)
1. `mkdir calculator && cd calculator`
2. `python -m venv venv && source venv/bin/activate`
3. `pip install --upgrade pip`
4. Create `pyproject.toml` (PEP 517 build) with:
   ```
   [build-system]
   requires = ["setuptools>=45", "wheel"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "calculator"
   version = "1.0.0"
   description = "Simple CLI calculator"
   requires-python = ">=3.8"
   ```
5. `pip install -e .`

### Phase 2 – Core Arithmetic (0.5 day)
1. Create `calculator/operations.py`
   ```python
   def add(a: float, b: float) -> float: ...
   def sub(a: float, b: float) -> float: ...
   def mul(a: float, b: float) -> float: ...
   def div(a: float, b: float) -> float: ...
   ```
2. Create `calculator/exceptions.py`
   ```python
   class CalculatorError(Exception): ...
   class InvalidInputError(CalculatorError): ...
   class DivisionByZeroError(CalculatorError): ...
   ```
3. Write unit tests for `operations.py` (TDD).

### Phase 3 – Input Parsing (0.5 day)
1. Implement `parse_input(raw: str) -> tuple[float, float, str]` in `cli.py`.
2. Add regex pattern `r'^([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*([+*/-])\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)$'`
3. Unit tests for valid/invalid strings.

### Phase 4 – CLI Glue & Error Handling (0.5 day)
1. Implement `main(argv=None)`:
   - If `argv` has 3 extra args, run non-interactive.
   - Else, enter REPL loop.
   - Catch `CalculatorError` subclasses → print friendly message → `sys.exit(1)`.
2. Add `--help` via `argparse.ArgumentParser`.

### Phase 5 – Continuous Operation (optional) (0.25 day)
1. After printing result, prompt `Continue? (y/n): `.
2. Loop until `n` or `Ctrl-C`.

### Phase 6 – QA & Packaging (0.25 day)
1. Run `python -m unittest discover -s tests -v`
2. `flake8 calculator tests`
3. Update `README.md`
4. Tag v1.0.0

## 5. File Structure

```
calculator/
├── pyproject.toml               # PEP 517 build config
├── requirements.txt             # (empty for now, placeholder)
├── README.md                    # Usage, install, test
├── calculator/
│   ├── __init__.py              # __version__, exports
│   ├── cli.py                   # main(), parse_input(), REPL
│   ├── operations.py            # add, sub, mul, div
│   └── exceptions.py            # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_operations.py       # Unit tests for arithmetic
│   ├── test_parse_input.py      # Unit tests for parsing
│   └── test_cli.py              # Tests for main() & REPL
└── .github/
    └── workflows/
        └── ci.yml               # GitHub Actions: lint + test
```

### Key Files Detail

#### `calculator/cli.py`
```python
import argparse
import re
import sys
from typing import Tuple

from .exceptions import InvalidInputError, DivisionByZeroError
from .operations import add, sub, mul, div

OPERATOR_MAP = {
    '+': add,
    '-': sub,
    '*': mul,
    '/': div,
}

PATTERN = re.compile(
    r'^([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*([+*/-])\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)$'
)

def parse_input(raw: str) -> Tuple[float, float, str]:
    match = PATTERN.match(raw.strip())
    if not match:
        raise InvalidInputError("Invalid input.")
    a, op, b = match.groups()
    return float(a), float(b), op

def calculate(a: float, b: float, op: str) -> float:
    if op not in OPERATOR_MAP:
        raise InvalidInputError("Invalid operator.")
    if op == '/' and b == 0:
        raise DivisionByZeroError("Division by zero is undefined.")
    return OPERATOR_MAP[op](a, b)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Simple CLI calculator")
    parser.add_argument("a", nargs="?")
    parser.add_argument("op", nargs="?")
    parser.add_argument("b", nargs="?")
    args = parser.parse_args(argv)

    if args.a and args.op and args.b:
        raw = f"{args.a} {args.op} {args.b}"
    else:
        raw = input("Enter expression (e.g., 5 + 3): ")

    try:
        a, b, op = parse_input(raw)
        result = calculate(a, b, op)
        print(result)
    except CalculatorError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

#### `.github/workflows/ci.yml`
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.8"
      - run: pip install -e . flake8
      - run: flake8 calculator tests
      - run: python -m unittest discover -s tests
```

This design satisfies all functional and technical requirements while remaining minimal and maintainable.