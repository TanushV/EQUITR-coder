# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust: it validates all user input, gracefully handles division-by-zero, and ships with a full suite of unit tests to guarantee correctness.

## 2. Functional Requirements

| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | CLI Entry Point | A single executable script or command that starts the calculator. | Typing `python calculator.py` (or equivalent) launches the program and shows a usage prompt. |
| FR-2 | Operation Selection | User can choose one of four operations via a short text command. | Allowed commands: `add`, `sub`, `mul`, `div` (case-insensitive). |
| FR-3 | Operand Input | User supplies two numeric operands. | Program accepts integers or floats in standard or scientific notation (e.g., `3`, `-4.5`, `1e-3`). |
| FR-4 | Input Validation | Reject non-numeric or malformed input. | If either operand is invalid, print “Error: invalid number” and exit with code 1. |
| FR-5 | Division-by-Zero Handling | Detect and report division by zero. | If operation is `div` and second operand is 0, print “Error: division by zero” and exit with code 1. |
| FR-6 | Result Display | Print the computed result to stdout. | Output format: `Result: <value>` with full precision (no rounding). |
| FR-7 | Help / Usage | Provide concise usage instructions when no arguments or `-h/--help` is supplied. | Example: `Usage: calculator.py <operation> <num1> <num2>` |
| FR-8 | Exit Codes | Return appropriate shell exit codes. | `0` on success, `1` on any error. |

## 3. Technical Requirements

### 3.1 Language & Runtime
- Python 3.8+ (for broad compatibility and `unittest`/`pytest` support).

### 3.2 Project Structure
```
calculator/
├── calculator.py          # CLI entry point
├── calc/
│   ├── __init__.py
│   └── core.py            # Pure functions: add, sub, mul, div
└── tests/
    ├── __init__.py
    └── test_core.py       # Unit tests for core.py
```

### 3.3 Core Module (`calc/core.py`)
- Four pure functions:
  - `add(a: float, b: float) -> float`
  - `sub(a: float, b: float) -> float`
  - `mul(a: float, b: float) -> float`
  - `div(a: float, b: float) -> float`
- `div` must raise `ValueError("division by zero")` when `b == 0`.

### 3.4 CLI (`calculator.py`)
- Uses `argparse` to parse positional arguments: `<operation> <num1> <num2>`.
- Converts `num1` and `num2` to `float`; catches `ValueError` for invalid input.
- Maps operation strings to core functions.
- Prints results or error messages to `stdout`/`stderr` respectively.

### 3.5 Testing
- Framework: `unittest` (standard library) or `pytest` (if preferred).
- Coverage target: 100 % of `calc/core.py` lines.
- Test cases must include:
  - Positive, negative, and floating-point operands.
  - Division by zero scenario.
  - Invalid string inputs.

### 3.6 Packaging & Tooling
- `requirements.txt` (empty except for optional `pytest`).
- `README.md` with installation and run instructions.
- Makefile or shell script to run tests: `make test` or `./run_tests.sh`.

## 4. Success Criteria

| Checkpoint | How to Verify |
|---|---|
| 1. Runs from CLI | `python calculator.py add 2 3` prints `Result: 5` |
| 2. Handles bad input | `python calculator.py add x 3` prints `Error: invalid number` and exits 1 |
| 3. Handles division by zero | `python calculator.py div 5 0` prints `Error: division by zero` and exits 1 |
| 4. All tests pass | `python -m pytest tests/` (or `python -m unittest discover`) shows 100 % success |
| 5. Code coverage | `coverage report` shows 100 % on `calc/core.py` |
| 6. Clean repository | No `.pyc` files, committed to Git, tagged `v1.0` upon completion |