# design.md

## 1. System Architecture

The calculator is a **single-process, interactive CLI application** built in Python 3.9+.  
It is split into three logical layers:

```
┌────────────────────────────────────────────┐
│  Presentation Layer  (calculator.py)       │
│  • CLI prompts / banners                   │
│  • Input sanitization & re-prompt loops    │
│  • Output formatting                       │
├────────────────────────────────────────────┤
│  Business Logic Layer  (operations.py)     │
│  • Pure arithmetic functions               │
│  • Domain-specific exceptions              │
├────────────────────────────────────────────┤
│  Test Layer  (tests/)                      │
│  • Unit tests for every public function    │
│  • Coverage & regression guards            │
└────────────────────────────────────────────┘
```

No external state (files, DB, network) is used; the entire program is stateless between calculations.

---

## 2. Components

| Component | File | Responsibility |
|---|---|---|
| **Entry Point** | `calculator.py` | `main()` orchestrates the REPL loop, delegates to `operations`, handles Ctrl-C. |
| **Arithmetic Engine** | `operations.py` | Four pure functions (`add`, `subtract`, `multiply`, `divide`) with type hints and docstrings. |
| **Unit Tests** | `tests/test_operations.py` | `unittest.TestCase` subclasses covering normal, edge, and error cases. |
| **Package Metadata** | `__init__.py` (root & tests) | Makes directories importable packages; root `__init__.py` exposes version (`__version__ = "1.0.0"`). |

---

## 3. Data Flow

### 3.1 Happy Path

```
User → stdin → calculator.py
                │
                ├─ parse_number() ──► float a
                ├─ parse_number() ──► float b
                ├─ parse_operator() ─► str op ∈ {+,-,*,/}
                │
                └─ dispatch(op, a, b) ──► operations.py
                                           │
                                           ├─ add/sub/mul/div
                                           │
                                           └─ float result ──► calculator.py
                                                              │
                                                              └─ format_result() ──► stdout
```

### 3.2 Error Path

```
Invalid input ──► calculator.py
                    │
                    ├─ print(error_msg)
                    └─ re-prompt (loop)

Division by zero ──► operations.divide() raises ValueError
                      │
                      └─ calculator.py catches, prints
                         "Error: Division by zero is undefined."
```

---

## 4. Implementation Plan

| Step | Task | Deliverable | Notes |
|---|---|---|---|
| 1 | Scaffold repo | `calculator/`, `tests/`, `__init__.py` files | Follow structure in §3.2 |
| 2 | Implement `operations.py` | Four typed functions + docstrings | 100 % pure, no I/O |
| 3 | Write unit tests | `test_operations.py` | Achieve 100 % coverage |
| 4 | Build CLI loop | `calculator.py` | Use `while True`, `try/except` |
| 5 | Input helpers | `parse_number()`, `parse_operator()` | Re-prompt until valid |
| 6 | Formatting | `format_result()` | 10-decimal rounding, scientific notation rules |
| 7 | Graceful exit | `KeyboardInterrupt` handler | `signal.signal` or `try/except KeyboardInterrupt` |
| 8 | Manual QA | Run 10 distinct cases | Document in README |
| 9 | Final polish | PEP 8 lint, docstrings, version bump | `python -m flake8 --max-line-length=88` |

---

## 5. File Structure

```
calculator/
├── calculator.py
├── operations.py
├── __init__.py
└── tests/
    ├── __init__.py
    └── test_operations.py
```

### 5.1 `calculator.py` (high-level outline)

```python
#!/usr/bin/env python3
"""
Interactive command-line calculator.

Usage:
    $ python calculator.py
"""

import sys
from operations import add, subtract, multiply, divide

WELCOME_BANNER = """
====================================
      Simple CLI Calculator
====================================
Supported operations: +  -  *  /
Press Ctrl-C to quit
"""

def parse_number(prompt: str) -> float:
    ...

def parse_operator(prompt: str) -> str:
    ...

def format_result(value: float) -> str:
    ...

def main() -> None:
    print(WELCOME_BANNER)
    try:
        while True:
            ...
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### 5.2 `operations.py`

```python
"""
Core arithmetic operations exposed by the calculator.
"""

from typing import Final

def add(a: float, b: float) -> float:
    """Return the sum of two floats."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Return the difference of two floats."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Return the product of two floats."""
    return a * b

def divide(a: float, b: float) -> float:
    """
    Return the quotient of two floats.

    Raises
    ------
    ValueError
        If `b` is zero.
    """
    if b == 0.0:
        raise ValueError("Division by zero is undefined.")
    return a / b
```

### 5.3 `tests/test_operations.py`

```python
import unittest
from operations import add, subtract, multiply, divide

class TestOperations(unittest.TestCase):
    def test_add(self):
        self.assertAlmostEqual(add(0.1, 0.2), 0.3, places=10)

    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)

    def test_multiply(self):
        self.assertEqual(multiply(-2, 3), -6)

    def test_divide(self):
        self.assertAlmostEqual(divide(1, 3), 0.3333333333, places=10)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(1, 0)

if __name__ == "__main__":
    unittest.main()
```

---

## 6. Future Extensibility Hooks

- **Non-interactive mode**: Add `argparse` in `calculator.py` to accept `calculator.py 3 + 4`.
- **Additional operations**: Extend `operations.py` with `power`, `sqrt`, etc.
- **History**: Persist last N calculations to a local JSON file.
- **GUI**: Reuse `operations.py` in a Tkinter or web front-end.

All such additions will keep the three-layer architecture intact.