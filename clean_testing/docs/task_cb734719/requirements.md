# requirements.md

## 1. Project Overview
Create a minimal, self-contained Python utility module named `utils.py` that provides two reusable helper functions (`is_even` and `reverse_string`) and a built-in self-test routine.

## 2. Functional Requirements
| ID | Requirement | Description | Acceptance Test |
|---|---|---|---|
| FR-1 | Provide `is_even` function | Accepts an integer and returns `True` if the number is even, otherwise `False`. | `is_even(4)` → `True`, `is_even(7)` → `False` |
| FR-2 | Provide `reverse_string` function | Accepts a string and returns the reversed string. | `reverse_string("hello")` → `"olleh"` |
| FR-3 | Provide `main` function | When executed, runs a short, deterministic test suite that demonstrates both functions work correctly. | Running `python utils.py` prints clear pass/fail messages. |
| FR-4 | Module usability | The file can be imported without side effects; functions are available for reuse. | `from utils import is_even, reverse_string` works without running tests. |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language & Version | Pure Python 3 (no external dependencies). |
| TR-2 | File name | Exactly `utils.py` in the project root. |
| TR-3 | Code style | PEP 8 compliant, ≤ 79 chars per line, clear variable names. |
| TR-4 | Entry point guard | Use `if __name__ == "__main__":` to protect `main()` invocation. |
| TR-5 | Docstrings | Each public function has a concise one-line docstring. |
| TR-6 | Error handling | Functions should not raise unhandled exceptions for valid inputs (int for `is_even`, str for `reverse_string`). |

## 4. Success Criteria
- [ ] `python utils.py` runs without errors and prints confirmation that both tests passed.
- [ ] `python -c "from utils import is_even, reverse_string; print(is_even(2), reverse_string('abc'))"` outputs `True cba`.
- [ ] `flake8 utils.py` reports zero style violations (if flake8 is installed).
- [ ] File size ≤ 50 lines of code (excluding blank lines and comments).