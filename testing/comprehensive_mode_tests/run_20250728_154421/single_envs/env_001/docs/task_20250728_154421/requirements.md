# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust: it validates all user input, gracefully handles division-by-zero attempts, and ships with a complete suite of unit tests to guarantee correctness.

## 2. Functional Requirements

| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-1 | Launch CLI | When the user runs the program, a prompt appears that accepts two numbers and an operator. |
| FR-2 | Addition | Given two numbers `a` and `b`, the program outputs `a + b`. |
| FR-3 | Subtraction | Given two numbers `a` and `b`, the program outputs `a - b`. |
| FR-4 | Multiplication | Given two numbers `a` and `b`, the program outputs `a * b`. |
| FR-5 | Division | Given two numbers `a` and `b` where `b ≠ 0`, the program outputs `a / b`. |
| FR-6 | Division-by-zero protection | When `b = 0`, the program prints “Error: Division by zero is undefined.” and exits with code 1. |
| FR-7 | Input validation | If the user enters non-numeric values or an invalid operator, the program prints “Error: Invalid input.” and exits with code 1. |
| FR-8 | Continuous operation (optional) | After displaying a result, the program may ask “Continue? (y/n)”; if `y`, it loops back to FR-1. |
| FR-9 | Help flag | Running the program with `--help` or `-h` prints usage instructions. |

## 3. Technical Requirements

### 3.1 Language & Tooling
- **Language**: Python 3.8+ (for simplicity and built-in `unittest` framework).  
- **Package Manager**: `pip` with a `requirements.txt` file (even if empty).  
- **Test Runner**: `python -m unittest discover`.

### 3.2 Project Structure
```
calculator/
├── calculator/
│   ├── __init__.py
│   └── cli.py          # Entry point
├── tests/
│   ├── __init__.py
│   └── test_calculator.py
├── README.md
└── requirements.txt
```

### 3.3 Core Modules
- `calculator.cli`  
  - `main()` – parses CLI args, orchestrates I/O.  
  - `parse_input(raw)` – returns `(float, float, str)` or raises `ValueError`.  
  - `calculate(a, b, op)` – returns `float` or raises `ZeroDivisionError`.

### 3.4 Input Parsing Rules
- Numbers: Accept integers or floats in standard or scientific notation (`3`, `3.14`, `-2.5e-3`).  
- Operators: Case-insensitive single characters `+`, `-`, `*`, `/`.  
- Delimiter: Space-separated input (`3.5 * 2`) or positional CLI args (`python -m calculator.cli 3.5 * 2`).

### 3.5 Error Handling
- All exceptions bubble up to `main()` and are caught; user-friendly messages printed to `stderr`.  
- Exit codes: `0` success, `1` any error.

### 3.6 Unit Tests
- **Coverage Target**: 100 % of `calculate` and `parse_input` branches.  
- **Test Cases** (minimum):
  - Valid operations for all four operators with positive, negative, and floating-point numbers.  
  - Division by zero raises `ZeroDivisionError`.  
  - Invalid operator raises `ValueError`.  
  - Malformed numeric input raises `ValueError`.  
  - CLI argument parsing with `sys.argv` variations.

### 3.7 Build & Run Commands
```bash
# Install (if any deps added)
pip install -r requirements.txt

# Run
python -m calculator.cli 5 + 3
# or interactive
python -m calculator.cli

# Test
python -m unittest discover -s tests
```

## 4. Success Criteria

| Checkpoint | Definition of Done |
|---|---|
| 1. Functionality | All FR-1 through FR-7 pass manual acceptance tests. |
| 2. Tests | `python -m unittest` reports 100 % success with no failures or errors. |
| 3. Linting | `flake8` or `pylint` passes with zero warnings. |
| 4. Documentation | README contains installation, usage, and test instructions. |
| 5. Distribution | A single `python -m calculator.cli` invocation works from any directory after `pip install -e .`.