# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust, user-friendly, and fully tested.

## 2. Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| FR-1 | CLI Entry Point | Provide an executable script (`calc` or `python -m calculator`) that starts the calculator. |
| FR-2 | Interactive Mode | When launched with no arguments, prompt the user repeatedly until they type `exit` or `quit`. |
| FR-3 | Single-Expression Mode | When launched with arguments (e.g., `calc 3 + 4`), compute the result, print it, and exit. |
| FR-4 | Supported Operations | Accept the symbols `+`, `-`, `*`, `/` (case-insensitive). |
| FR-5 | Input Validation | Reject non-numeric operands and unsupported operators with a clear error message. |
| FR-6 | Division by Zero | Detect and report “Error: Division by zero is undefined.” |
| FR-7 | Result Display | Print results to stdout with at least 6 decimal places of precision when needed. |
| FR-8 | Help & Usage | Display concise usage instructions when the user types `help` or provides invalid CLI arguments. |

## 3. Technical Requirements

| ID | Requirement | Description |
|---|---|---|
| TR-1 | Language | Python 3.8+ (for broad compatibility). |
| TR-2 | Project Layout | Follow standard Python package structure: <br>`calculator/`<br>&nbsp;&nbsp;`__init__.py`<br>&nbsp;&nbsp;`cli.py` (argparse + REPL)<br>&nbsp;&nbsp;`core.py` (pure arithmetic functions)<br>&nbsp;&nbsp;`exceptions.py` (custom errors)<br>`tests/`<br>&nbsp;&nbsp;`test_core.py`<br>&nbsp;&nbsp;`test_cli.py` |
| TR-3 | Core API | Expose four pure functions in `core.py`:<br>`add(a: float, b: float) -> float`<br>`subtract(a: float, b: float) -> float`<br>`multiply(a: float, b: float) -> float`<br>`divide(a: float, b: float) -> float` |
| TR-4 | Error Handling | Raise custom `CalculatorError` (or subclasses) for all invalid states; never crash with raw Python exceptions. |
| TR-5 | CLI Framework | Use `argparse` for argument parsing and `input()` for interactive prompts. |
| TR-6 | Testing Framework | Use `pytest`. Aim for 100 % branch coverage on `core.py` and `cli.py`. |
| TR-7 | Continuous Integration | Provide a GitHub Actions workflow that runs tests and coverage on push/PR. |
| TR-8 | Packaging | Include `pyproject.toml` so the project can be installed via `pip install .` and exposes the console script `calc`. |

## 4. Success Criteria

| ID | Criterion | How to Verify |
|---|---|---|
| SC-1 | All Operations Correct | `pytest` passes with assertions covering positive, negative, integer, and floating-point operands. |
| SC-2 | Division by Zero Handled | Unit test confirms `divide(5, 0)` raises `DivisionByZeroError`. |
| SC-3 | CLI Usable | Manual test: running `calc` without args enters REPL; `calc 7 / 0` prints the expected error and exits with non-zero status. |
| SC-4 | Coverage ≥ 95 % | `pytest --cov=calculator` reports ≥ 95 % line coverage. |
| SC-5 | Clean Exit Codes | Return 0 on success, 1 on user error, 2 on CLI misuse (per argparse conventions). |
| SC-6 | Packaging Works | After `pip install .`, the command `calc 2 + 3` outputs `5.0`.