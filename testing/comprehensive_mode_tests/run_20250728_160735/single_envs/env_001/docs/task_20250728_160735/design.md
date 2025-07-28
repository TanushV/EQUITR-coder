# design.md

## 1. System Architecture

The calculator is a **single-process, console-only Python 3.8+ application** composed of two logical layers:

```
┌────────────────────────────────────────────┐
│  CLI Layer (cli.py)                        │
│  • Menu loop                               │
│  • Input sanitization                      │
│  • Error presentation                      │
└────────────────┬───────────────────────────┘
                 │ function calls
┌────────────────┴───────────────────────────┐
│  Core Layer (core.py)                      │
│  • Pure arithmetic functions               │
│  • Type & domain validation                │
│  • Exception raising                       │
└────────────────────────────────────────────┘
```

- **No external state** (no DB, no files, no network).  
- **No concurrency** (single-threaded REPL).  
- **No third-party dependencies** at runtime; only `pytest` for tests.

---

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| `calculator.core` | Arithmetic logic | `add`, `subtract`, `multiply`, `divide` |
| `calculator.cli`  | User interaction | `main()` entry point, `get_number()` helper |
| `tests.test_core` | Unit tests       | pytest test functions |

### 2.1 Core Module (`calculator/core.py`)
- **Type enforcement**: every function checks `isinstance(x, (int, float))`.
- **Domain enforcement**: `divide` raises `ZeroDivisionError` on `b == 0`.
- **Return type**: always `float` (even for integer inputs to keep interface simple).

### 2.2 CLI Module (`calculator/cli.py`)
- **Menu loop**:
  ```
  1) Add
  2) Subtract
  3) Multiply
  4) Divide
  5) Quit
  ```
- **Input loop** (`get_number(prompt: str) -> float`):
  - Uses `try/except ValueError` to trap non-numeric strings.
  - Re-prompts until valid float is entered.
- **Error handling**:
  - Catches `ZeroDivisionError` → prints “Error: Cannot divide by zero.”
  - Catches `TypeError` from core → prints “Internal error: invalid operands.”

---

## 3. Data Flow

```
User
  │
  │ stdin
  ▼
┌────────────────────────────┐
│ cli.py                     │
│ 1. Display menu            │
│ 2. Read choice             │
│ 3. Read two numbers via    │
│    get_number()            │
│ 4. Call core.fn(a, b)      │
│ 5. Print result            │
└────────────────────────────┘
  │ function call
  ▼
┌────────────────────────────┐
│ core.py                    │
│ • Validate types           │
│ • Compute result           │
│ • Raise if needed          │
└────────────────────────────┘
  │ return / raise
  ▼
┌────────────────────────────┐
│ cli.py                     │
│ • Catch exceptions         │
│ • Print message            │
│ • Loop or exit             │
└────────────────────────────┘
```

---

## 4. Implementation Plan

| Phase | Task | Deliverable | Est. Effort |
|---|---|---|---|
| P0 | Bootstrap repo | `calculator/`, `__init__.py`, `requirements.txt`, `README.md` skeleton | 15 min |
| P1 | Core functions | `core.py` with 4 functions + docstrings | 30 min |
| P2 | Unit tests | `tests/test_core.py` achieving 100 % coverage | 45 min |
| P3 | CLI skeleton | `cli.py` with menu loop stub | 20 min |
| P4 | Input helpers | `get_number()` with validation | 30 min |
| P5 | Integrate core | Wire menu choices to core functions | 20 min |
| P6 | Error UX | Polish messages, colors (optional) | 15 min |
| P7 | QA | Manual run-through + `pytest` + `flake8` | 15 min |
| P8 | README | Usage, install, test instructions | 20 min |

Total: ~3 hours.

---

## 5. File Structure

```
calculator/
├── calculator/
│   ├── __init__.py          # version marker: __version__ = "1.0.0"
│   ├── core.py              # arithmetic functions
│   └── cli.py               # CLI entry point
├── tests/
│   ├── __init__.py
│   └── test_core.py         # pytest test cases
├── requirements.txt         # pytest>=7.0
├── setup.py                 # optional: pip install -e .
├── .gitignore
├── tox.ini                  # flake8 config
└── README.md
```

### 5.1 `calculator/__init__.py`
```python
__version__ = "1.0.0"
```

### 5.2 `calculator/core.py`
```python
from typing import Union

Number = Union[int, float]

def add(a: Number, b: Number) -> float:
    ...
```

### 5.3 `calculator/cli.py`
```python
import sys
from .core import add, subtract, multiply, divide

def get_number(prompt: str) -> float:
    ...

def main() -> None:
    ...
if __name__ == "__main__":
    main()
```

### 5.4 `tests/test_core.py`
```python
import pytest
from calculator.core import add, subtract, multiply, divide

class TestAdd:
    ...
```

---

## 6. Testing Strategy

- **pytest** as runner and assertion library.  
- **Parametrized tests** for edge cases (positive, negative, zero, floats).  
- **Exception tests** via `pytest.raises`.  
- **Coverage** enforced with `pytest --cov=calculator.core tests/`.

Example test snippet:
```python
@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (-1, 1, 0),
    (2.5, 2.5, 5.0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

---

## 7. Packaging & Distribution

- **No runtime dependencies** → `requirements.txt` only lists `pytest`.  
- **Entry point**: `python -m calculator.cli` (uses `__main__.py` if desired).  
- **Editable install**: `pip install -e .` via minimal `setup.py`.

---

## 8. Future Extensibility Hooks

- Add `__main__.py` to enable `python -m calculator`.  
- Extract `get_number` into `input_utils.py` for reuse.  
- Add history stack in CLI layer.  
- Support `Decimal` precision via pluggable backend.