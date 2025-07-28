# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** built on Python’s standard library only.  
It is split into three logical layers:

```
┌────────────────────────────┐
│        CLI Layer           │  calculator.py (entry point)
│  - argparse / shlex        │
│  - REPL loop               │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│      Interface Layer       │  calc/cli.py
│  - Input tokenization      │
│  - Validation & dispatch   │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│      Engine Layer          │  calc/engine.py
│  - Pure arithmetic fns     │
│  - Exception contracts     │
└────────────────────────────┘
```

- **CLI Layer** decides *how* the program is invoked (interactive vs single-expression).  
- **Interface Layer** decides *what* the user meant and translates it into engine calls.  
- **Engine Layer** performs *pure* arithmetic and raises strongly-typed exceptions.

## 2. Components

| Component | File | Responsibility |
|---|---|---|
| Entry Point | `calculator.py` | Parse `sys.argv`; delegate to either single-expression handler or interactive REPL. |
| Engine | `calc/engine.py` | Four public functions (`add`, `subtract`, `multiply`, `divide`) with strict contracts. |
| CLI Logic | `calc/cli.py` | `parse_cli_args`, `interactive_loop`, `evaluate_expression`, `print_help`. |
| Unit Tests | `tests/test_engine.py`, `tests/test_cli.py` | Exhaustive test cases + coverage. |
| Build Glue | `Makefile`, `requirements.txt`, `README.md` | Automation and documentation. |

### 2.1 Engine Module (`calc.engine`)

```python
def add(a: float, b: float) -> float: ...
def subtract(a: float, b: float) -> float: ...
def multiply(a: float, b: float) -> float: ...
def divide(a: float, b: float) -> float: ...
```

**Contracts**  
- All parameters must be `int` or `float`; otherwise `TypeError`.  
- `divide` raises `ZeroDivisionError` when `b == 0`.  
- Return value is always `float`.

### 2.2 CLI Module (`calc.cli`)

Key internal helpers:

| Helper | Signature | Purpose |
|---|---|---|
| `tokenize` | `(line: str) -> list[str]` | `shlex.split` with safety. |
| `validate_tokens` | `(tokens: list[str]) -> tuple[float, str, float]` | Raises `ValueError` on malformed input. |
| `dispatch` | `(a: float, op: str, b: float) -> float` | Maps operator string to engine call. |
| `interactive_loop` | `(istream, ostream) -> None` | Reads until EOF/`exit`. |
| `print_help` | `(ostream) -> None` | Prints usage banner. |

## 3. Data Flow

### 3.1 Single-Expression Mode

```
[Shell]  $ python calculator.py 3 + 4
   │
   │ argv = ["calculator.py", "3", "+", "4"]
   │
   ▼
calculator.py::main
   │
   ├─ calc.cli.parse_cli_args(argv)  → tokens = ["3", "+", "4"]
   │
   ├─ calc.cli.validate_tokens(tokens) → (3.0, "+", 4.0)
   │
   ├─ calc.cli.dispatch → calc.engine.add(3.0, 4.0) → 7.0
   │
   └─ print("7.000000") → exit 0
```

### 3.2 Interactive Mode

```
[Shell]  $ python calculator.py
   │
   │ argv = ["calculator.py"]
   │
   ▼
calculator.py::main
   │
   └─ calc.cli.interactive_loop(stdin, stdout)
        │
        ├─ print(banner)
        │
        ├─ while True:
        │     line = input("calc> ")
        │     if line == "exit": break
        │     tokens = tokenize(line)
        │     (a, op, b) = validate_tokens(tokens)
        │     result = dispatch(a, op, b)
        │     print(f"{result:.6f}")
```

### 3.3 Error Flow

Any exception raised in `validate_tokens`, `dispatch`, or engine functions is caught in the CLI layer, printed to `stderr`, and the loop continues (or exits with code 1 in single-expression mode).

## 4. Implementation Plan

| Phase | Task | Deliverable |
|---|---|---|
| **P0** | Bootstrap repo structure | `calculator/`, `calc/`, `tests/`, `README.md`, `Makefile` |
| **P1** | Engine implementation | `calc/engine.py` + `tests/test_engine.py` (100 % coverage) |
| **P2** | CLI helpers | `calc/cli.py` internal functions + unit tests |
| **P3** | Single-expression mode | `calculator.py` handles `len(argv) == 4` |
| **P4** | Interactive mode | REPL loop with `readline` support (optional) |
| **P5** | Error handling polish | Colorized errors (optional), consistent exit codes |
| **P6** | Packaging & docs | `README.md`, `make test`, CI badge (GitHub Actions) |

### 4.1 Test-Driven Checklist

1. Write failing unit test for `add(2, 3) -> 5`.  
2. Implement `calc.engine.add`.  
3. Repeat for `subtract`, `multiply`, `divide`.  
4. Add negative, float, and boundary tests.  
5. Add `TypeError` and `ZeroDivisionError` tests.  
6. Move to CLI layer tests:  
   - `validate_tokens` happy path.  
   - Malformed tokens raise `ValueError`.  
   - Integration: `python calculator.py 1 / 0` exits 1 and prints error.

## 5. File Structure

```
calculator/
├── calculator.py           # Entry point (<= 80 lines)
├── calc/
│   ├── __init__.py         # Empty
│   ├── engine.py           # Pure arithmetic
│   └── cli.py              # All CLI logic
├── tests/
│   ├── __init__.py
│   ├── test_engine.py      # Tests for engine
│   └── test_cli.py         # Tests for CLI helpers + modes
├── requirements.txt        # Empty (stdlib only)
├── Makefile                # test, lint, run targets
├── README.md               # Installation & usage
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions (optional)
```

### 5.1 Example `calculator.py`

```python
#!/usr/bin/env python3
import sys
from calc.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

### 5.2 Makefile Snippet

```make
.PHONY: test lint run

test:
	python -m unittest discover -s tests -v

lint:
	flake8 calculator.py calc/ tests/

run:
	python calculator.py
```

This design satisfies all functional and technical requirements while remaining minimal, testable, and extensible.