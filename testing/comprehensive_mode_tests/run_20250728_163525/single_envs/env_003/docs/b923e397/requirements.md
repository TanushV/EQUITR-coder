# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust: it must validate all user input, handle division-by-zero gracefully, and be fully covered by unit tests.

## 2. Functional Requirements
| ID | Requirement | Description | Acceptance Criteria |
|--|--|--|--|
| FR-1 | CLI Entry Point | Provide an executable script that starts the calculator from the command line. | Running `python -m calculator` or `./calculator` launches the interactive prompt. |
| FR-2 | Operation Selection | Present a menu listing the four operations. | Menu displays: 1) Add 2) Subtract 3) Multiply 4) Divide 5) Exit. |
| FR-3 | Number Input | Prompt for two numbers. | Accepts integers and floats; rejects non-numeric strings. |
| FR-4 | Addition | Compute `a + b`. | Returns correct sum for any valid pair. |
| FR-5 | Subtraction | Compute `a - b`. | Returns correct difference for any valid pair. |
| FR-6 | Multiplication | Compute `a * b`. | Returns correct product for any valid pair. |
| FR-7 | Division | Compute `a / b`. | Returns correct quotient; shows friendly error if `b == 0`. |
| FR-8 | Result Display | Print the result to stdout. | Format: `Result: <value>` with 2-decimal rounding. |
| FR-9 | Loop Until Exit | Allow repeated calculations until user chooses Exit. | After each result, re-display menu. |
| FR-10 | Input Validation | Re-prompt on invalid input. | Clear error message shown; previous invalid entry ignored. |

## 3. Technical Requirements
| ID | Requirement | Details |
|--|--|--|
| TR-1 | Language & Version | Python 3.8+ |
| TR-2 | Project Layout | Standard package structure: <br>`calculator/`<br>&nbsp;&nbsp;`__init__.py`<br>&nbsp;&nbsp;`cli.py` (entry point)<br>&nbsp;&nbsp;`core.py` (business logic)<br>`tests/`<br>&nbsp;&nbsp;`test_core.py`<br>&nbsp;&nbsp;`test_cli.py`<br>`requirements.txt`<br>`README.md` |
| TR-3 | Core Module API | `calculator.core` exposes four pure functions:<br>`add(a: float, b: float) -> float`<br>`subtract(a: float, b: float) -> float`<br>`multiply(a: float, b: float) -> float`<br>`divide(a: float, b: float) -> float` |
| TR-4 | Error Handling | `divide` raises `ValueError("Cannot divide by zero")` when `b == 0`. |
| TR-5 | CLI Module | Uses `argparse` or simple `input()` loop; no third-party CLI libraries. |
| TR-6 | Testing Framework | `unittest` or `pytest`; tests located in `tests/` directory. |
| TR-7 | Test Coverage | Minimum 95 % line coverage reported by `coverage.py`. |
| TR-8 | Static Analysis | Passes `flake8` with default settings. |
| TR-9 | Packaging | `setup.py` or `pyproject.toml` so `pip install .` works. |

## 4. Success Criteria
- [ ] All functional requirements (FR-1 … FR-10) pass manual QA checklist.
- [ ] All unit tests pass (`pytest` exits with code 0).
- [ ] Coverage report shows ≥ 95 %.
- [ ] `flake8` reports zero warnings.
- [ ] README contains installation, usage, and test instructions.
- [ ] Repository tagged `v1.0.0` after final review.