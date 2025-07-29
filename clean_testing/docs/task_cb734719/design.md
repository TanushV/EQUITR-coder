# design.md

## 1. System Architecture

The system is a single-file Python module (`utils.py`) that exposes two utility functions and a self-test routine.  
It follows a minimal, flat architecture:

```
┌─────────────────────────────┐
│        utils.py             │
│  ┌─────────────┐            │
│  │  is_even    │            │
│  └─────────────┘            │
│  ┌─────────────┐            │
│  │reverse_string│            │
│  └─────────────┘            │
│  ┌─────────────┐            │
│  │    main     │            │
│  └─────────────┘            │
└─────────────────────────────┘
```

No external packages, no sub-modules, no persistent state.

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| `is_even` | Determine if an integer is even | `is_even(n: int) -> bool` |
| `reverse_string` | Reverse any given string | `reverse_string(s: str) -> str` |
| `main` | Run deterministic self-tests and print results | `main() -> None` |
| Entry-point guard | Prevent `main()` from running on import | `if __name__ == "__main__":` |

## 3. Data Flow

1. **Import Flow**  
   `import utils` → symbols `is_even`, `reverse_string` become available; `main()` is *not* executed.

2. **Direct Execution Flow**  
   `python utils.py`  
   → Entry-point guard evaluates to `True`  
   → `main()` is invoked  
   → `main()` calls `is_even` and `reverse_string` with test data  
   → Results are printed to `stdout`.

3. **Function Call Flow**  
   - `is_even(n)`  
     `n % 2 == 0` → boolean result  
   - `reverse_string(s)`  
     `s[::-1]` → reversed string result

## 4. Implementation Plan

| Step | Task | Deliverable |
|---|---|---|
| 1 | Create project root directory | `simple-utils/` |
| 2 | Create `utils.py` stub | Empty file with UTF-8 encoding |
| 3 | Implement `is_even` | Function + docstring + inline test |
| 4 | Implement `reverse_string` | Function + docstring + inline test |
| 5 | Implement `main` | Test cases + print statements |
| 6 | Add entry-point guard | `if __name__ == "__main__":` |
| 7 | Manual acceptance tests | Run checklist in requirements |
| 8 | Optional lint check | `flake8 utils.py` |

## 5. File Structure

```
simple-utils/
└── utils.py
```

Content outline (`utils.py`):

```python
"""
Simple utility functions for demonstration purposes.
"""

def is_even(n: int) -> bool:
    """Return True if n is even, else False."""
    ...


def reverse_string(s: str) -> str:
    """Return the reverse of the input string s."""
    ...


def main() -> None:
    """Run self-tests for is_even and reverse_string."""
    ...


if __name__ == "__main__":
    main()
```

Total expected lines: ~25–30 (well below 50-line limit).