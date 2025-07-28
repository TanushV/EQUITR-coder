# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations—addition, subtraction, multiplication, and division—on two numbers entered by the user. The application must validate all inputs, gracefully handle division-by-zero errors, and be accompanied by a comprehensive suite of unit tests to ensure correctness.

## 2. Functional Requirements

| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | Launch CLI | The program starts from the command line and presents a clear prompt. | `python calculator.py` prints a welcome banner and usage instructions. |
| FR-2 | Accept two numbers | Read two floating-point numbers from the user. | Any valid float (e.g., `3`, `-4.5`, `1e-3`) is accepted; non-numeric input triggers re-prompt. |
| FR-3 | Accept operator | Read a single operator token (`+`, `-`, `*`, `/`). | Case-insensitive; invalid tokens trigger re-prompt. |
| FR-4 | Perform addition | Compute `a + b`. | Result matches Python’s native float addition. |
| FR-5 | Perform subtraction | Compute `a - b`. | Result matches Python’s native float subtraction. |
| FR-6 | Perform multiplication | Compute `a * b`. | Result matches Python’s native float multiplication. |
| FR-7 | Perform division | Compute `a / b`. | Returns correct quotient; division by zero prints “Error: Division by zero is undefined.” |
| FR-8 | Display result | Print the result rounded to 10 decimal places (or scientific notation if magnitude > 1e10 or < 1e-5). | Output format: `Result: <value>` |
| FR-9 | Loop or exit | After each calculation, ask the user whether to perform another calculation or exit. | Accepts `y`/`yes` (case-insensitive) to loop, anything else to exit gracefully. |
| FR-10 | Input validation | Reject non-numeric inputs and invalid operators with clear error messages. | Error message: “Invalid input. Please enter a valid number.” or “Invalid operator. Use +, -, *, /.” |

## 3. Technical Requirements

### 3.1 Language & Environment
- **Language**: Python 3.9+
- **OS**: Cross-platform (Windows, macOS, Linux)

### 3.2 Project Structure
```
calculator/
├── calculator.py          # Main CLI entry point
├── operations.py          # Core arithmetic functions
├── __init__.py
└── tests/
    ├── __init__.py
    └── test_operations.py # Unit tests
```

### 3.3 Core Functions (`operations.py`)
```python
def add(a: float, b: float) -> float
def subtract(a: float, b: float) -> float
def multiply(a: float, b: float) -> float
def divide(a: float, b: float) -> float  # raises ValueError on b == 0
```

### 3.4 CLI Behavior (`calculator.py`)
- Use `argparse` only if non-interactive mode is added later; for now, pure interactive REPL.
- Handle `KeyboardInterrupt` (Ctrl-C) gracefully: print “Goodbye!” and exit with code 0.

### 3.5 Testing
- **Framework**: `unittest` (standard library)
- **Coverage Target**: 100 % of `operations.py`
- **Test Cases**:
  - Positive, negative, and zero operands
  - Large and small floating-point magnitudes
  - Division by zero raises `ValueError`
  - Commutative property for add/multiply
  - Precision checks (e.g., `0.1 + 0.2 == 0.3` within 1e-10 tolerance)

### 3.6 Code Quality
- Follow PEP 8
- Type hints on all public functions
- Docstrings for all modules, classes, and functions
- No external dependencies beyond Python standard library

## 4. Success Criteria

| Checkpoint | Metric | Definition of Done |
|---|---|---|
| C-1 | Manual CLI test | Running the program end-to-end produces correct results for at least 10 distinct input pairs covering all four operations. |
| C-2 | Unit tests pass | `python -m unittest discover tests` exits with OK status and 100 % statement coverage of `operations.py`. |
| C-3 | Error handling | Division by zero, non-numeric input, and invalid operators are handled without crashing; appropriate messages displayed. |
| C-4 | Clean exit | Ctrl-C terminates the program gracefully with a friendly message. |
| C-5 | Code review | A second developer can clone the repo, run the tests, and use the calculator without additional instructions.