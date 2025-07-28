# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations—addition, subtraction, multiplication, and division—on two numbers entered by the user. The application must validate all inputs, gracefully handle division-by-zero errors, and be accompanied by a complete suite of unit tests.

## 2. Functional Requirements
| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | CLI Entry Point | Provide a single executable script that starts the calculator. | Running `python calculator.py` (or equivalent) launches the interactive prompt. |
| FR-2 | Operation Selection | Present a menu listing the four operations. | Menu displays: 1) Add 2) Subtract 3) Multiply 4) Divide 5) Exit |
| FR-3 | Number Input | Prompt the user for two numbers. | Accepts integers or floats; rejects non-numeric strings with a clear error message. |
| FR-4 | Addition | Compute the sum of two numbers. | `add(3, 4)` → `7` |
| FR-5 | Subtraction | Compute the difference of two numbers. | `subtract(10, 4)` → `6` |
| FR-6 | Multiplication | Compute the product of two numbers. | `multiply(2.5, 4)` → `10.0` |
| FR-7 | Division | Compute the quotient of two numbers. | `divide(8, 2)` → `4.0`; `divide(5, 0)` → raises `ZeroDivisionError` |
| FR-8 | Division-by-Zero Handling | Detect and report division by zero. | Displays “Error: Cannot divide by zero.” and returns to the menu. |
| FR-9 | Result Display | Show the computed result to the user. | Output format: `Result: <value>` |
| FR-10 | Loop Until Exit | Allow repeated calculations until the user chooses to exit. | After each result, re-display the menu until option 5 is selected. |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language | Python 3.8+ |
| TR-2 | Project Structure | ```
calculator/
├── calculator.py          # CLI entry point
├── operations.py          # Core arithmetic functions
└── tests/
    └── test_operations.py # Unit tests
``` |
| TR-3 | Core Functions | Each arithmetic operation must be a pure function in `operations.py` with signature `def op(a: float, b: float) -> float`. |
| TR-4 | Input Validation | Use `try/except` to catch `ValueError` on `float(input(...))`; re-prompt until valid. |
| TR-5 | Error Handling | Raise `ZeroDivisionError` in `divide`; catch in CLI layer and print friendly message. |
| TR-6 | Unit Test Framework | `pytest` |
| TR-7 | Test Coverage | Achieve 100 % line coverage for `operations.py`; include positive, negative, and edge cases. |
| TR-8 | Continuous Integration | GitHub Actions workflow that runs `pytest` on every push/PR. |
| TR-9 | Packaging | Provide `requirements.txt` listing only `pytest` (if any). |
| TR-10 | Code Style | Follow PEP 8; enforce with `flake8` or `ruff`. |

## 4. Success Criteria
- [ ] All functional requirements (FR-1 through FR-10) pass manual testing.
- [ ] All unit tests pass (`pytest` exits with code 0).
- [ ] Code coverage report shows 100 % for `operations.py`.
- [ ] CI pipeline is green on the main branch.
- [ ] README.md explains how to install, run, and test the application.
- [ ] No linting errors (`flake8` or `ruff` clean).