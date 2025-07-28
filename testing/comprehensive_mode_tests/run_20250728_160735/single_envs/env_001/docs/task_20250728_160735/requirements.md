# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust: it validates all user input, gracefully handles division-by-zero attempts, and ships with a complete suite of unit tests to guarantee correctness.

## 2. Functional Requirements

| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | CLI Entry Point | The program starts from the command line and presents a simple menu. | `python calculator.py` prints a numbered menu and waits for user choice. |
| FR-2 | Addition | Adds two real numbers. | User selects “1”, enters two numbers, sees correct sum. |
| FR-3 | Subtraction | Subtracts second number from first. | User selects “2”, enters two numbers, sees correct difference. |
| FR-4 | Multiplication | Multiplies two real numbers. | User selects “3”, enters two numbers, sees correct product. |
| FR-5 | Division | Divides first number by second. | User selects “4”, enters two numbers, sees correct quotient. |
| FR-6 | Division-by-Zero Handling | Detects and reports division by zero. | When divisor is 0, program prints “Error: Cannot divide by zero.” and returns to menu. |
| FR-7 | Input Validation | Rejects non-numeric input. | If user types “abc”, program prints “Invalid input. Please enter a number.” and re-prompts. |
| FR-8 | Continuous Operation | After each calculation, menu reappears until user chooses to quit. | User can perform multiple calculations in one session. |
| FR-9 | Graceful Exit | Provides an option to quit. | Selecting “5” prints “Goodbye!” and exits with status code 0. |

## 3. Technical Requirements

### 3.1 Language & Runtime
- Python 3.8+ (cross-platform).

### 3.2 Project Structure
```
calculator/
├── calculator/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   └── core.py         # Arithmetic functions
├── tests/
│   ├── __init__.py
│   └── test_core.py    # Unit tests
├── requirements.txt    # Only pytest
└── README.md
```

### 3.3 Core Module (`core.py`)
- Functions:
  - `add(a: float, b: float) -> float`
  - `subtract(a: float, b: float) -> float`
  - `multiply(a: float, b: float) -> float`
  - `divide(a: float, b: float) -> float`
- All functions raise `TypeError` on non-numeric inputs.
- `divide` raises `ZeroDivisionError` when `b == 0`.

### 3.4 CLI Module (`cli.py`)
- Uses `argparse` or simple `input()` loop.
- Re-prompts until valid numeric input is received.
- Catches `ZeroDivisionError` and prints friendly message.

### 3.5 Testing
- Framework: pytest.
- Coverage target: 100 % for `core.py`.
- Test cases:
  - Positive, negative, and floating-point numbers.
  - Division by zero.
  - Non-numeric inputs (strings, None).

### 3.6 Packaging & Distribution
- Single-file execution: `python -m calculator.cli`.
- No external runtime dependencies except Python standard library.
- Optional: `pip install -e .` for development.

## 4. Success Criteria

| Checkpoint | Metric | Definition of Done |
|---|---|---|
| C1 | All FRs Implemented | Each functional requirement passes its acceptance criteria via manual CLI test. |
| C2 | Unit Tests Pass | `pytest` exits with 0 errors and ≥ 90 % coverage. |
| C3 | Static Analysis | `flake8` reports zero warnings. |
| C4 | User Workflow | A new user can clone repo, run `python calculator/cli.py`, and successfully perform 2 + 3, 5 / 0, and exit without reading docs. |
| C5 | Documentation | README contains installation, usage, and test instructions.