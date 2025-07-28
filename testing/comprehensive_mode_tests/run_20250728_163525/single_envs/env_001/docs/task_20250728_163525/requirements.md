# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust: it validates all user input, handles division-by-zero gracefully, and ships with a complete suite of unit tests to guarantee correctness.

## 2. Functional Requirements

| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | Launch CLI | User starts the program from a terminal. | `python calculator.py` prints a welcome banner and usage instructions. |
| FR-2 | Interactive Mode | After launch, the program enters a REPL loop. | Prompt `calc> ` appears; user can enter multiple expressions until typing `exit`. |
| FR-3 | Single-Expression Mode | User can run one calculation directly from the shell. | `python calculator.py 3 + 4` prints `7` and exits. |
| FR-4 | Supported Operations | Recognize tokens `+`, `-`, `*`, `/`. | Each operator performs the corresponding arithmetic operation on two operands. |
| FR-5 | Input Validation | Reject malformed or non-numeric input. | Entering `abc + 3` prints `Error: invalid number 'abc'` and re-prompts. |
| FR-6 | Division-by-Zero Handling | Detect and report divide-by-zero attempts. | Entering `5 / 0` prints `Error: division by zero` and re-prompts. |
| FR-7 | Result Display | Show results with appropriate precision. | `1 / 3` prints `0.333333` (6 decimal places). |
| FR-8 | Help Command | Provide built-in help. | Typing `help` lists supported operators and usage examples. |
| FR-9 | Exit Command | Allow graceful termination. | Typing `exit` or sending `EOF` (Ctrl-D) terminates with exit code 0. |

## 3. Technical Requirements

### 3.1 Language & Runtime
- Python 3.8+ (for `typing` and `unittest` features).

### 3.2 Project Structure
```
calculator/
├── calculator.py          # CLI entry point
├── calc/
│   ├── __init__.py
│   ├── engine.py          # Core arithmetic functions
│   └── cli.py             # Command-line interface logic
└── tests/
    ├── __init__.py
    └── test_engine.py     # Unit tests for engine.py
```

### 3.3 Core Module (`calc.engine`)
- Functions:
  - `add(a: float, b: float) -> float`
  - `subtract(a: float, b: float) -> float`
  - `multiply(a: float, b: float) -> float`
  - `divide(a: float, b: float) -> float`
- All functions raise `TypeError` on non-numeric inputs and `ZeroDivisionError` when `b == 0` in `divide`.

### 3.4 CLI Module (`calc.cli`)
- Parse command-line arguments via `argparse`.
- Tokenize interactive input with `shlex.split`.
- Validate tokens: exactly three parts (`<number> <op> <number>`).
- Convert numbers with `float()` and catch `ValueError`.

### 3.5 Testing
- Use Python’s built-in `unittest`.
- Achieve **100 % line coverage** for `calc.engine` and `calc.cli`.
- Test cases must include:
  - Positive, negative, and floating-point operands.
  - Division by zero.
  - Invalid operator and operand formats.
  - CLI argument parsing (both valid and invalid).

### 3.6 Packaging & Tooling
- `requirements.txt` empty (standard library only).
- `Makefile` with targets:
  - `make test` – runs `python -m unittest discover -s tests`.
  - `make lint` – runs `flake8` (optional but recommended).
  - `make run` – runs `python calculator.py`.

## 4. Success Criteria

| Checkpoint | Metric | Definition of Done |
|---|---|---|
| C-1 | All Functional Requirements | Each FR-1 … FR-9 passes its acceptance criteria in manual testing. |
| C-2 | Unit Test Coverage | `coverage report` shows 100 % for `calc/` directory. |
| C-3 | Zero Runtime Errors | Running the full test suite produces no uncaught exceptions. |
| C-4 | Clean Exit Codes | Program exits with `0` on success and `1` on CLI argument errors. |
| C-5 | Documentation | README.md explains installation, usage (interactive & single-expression), and running tests.