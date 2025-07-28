# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (addition, subtraction, multiplication, division) on two numbers. The application must be robust, user-friendly, and fully tested.

## 2. Functional Requirements
| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | CLI Entry Point | Provide a single executable script that starts the calculator | `python calculator.py` launches interactive prompt |
| FR-2 | Operation Selection | Present a menu with numbered choices for each operation | Menu displays: 1) Add 2) Subtract 3) Multiply 4) Divide 5) Exit |
| FR-3 | Number Input | Prompt user for two numeric inputs | Accepts integers and floats; rejects non-numeric strings |
| FR-4 | Addition | Compute `a + b` | Returns correct sum for any valid numbers |
| FR-5 | Subtraction | Compute `a - b` | Returns correct difference for any valid numbers |
| FR-6 | Multiplication | Compute `a * b` | Returns correct product for any valid numbers |
| FR-7 | Division | Compute `a / b` | Returns correct quotient; handles division by zero gracefully |
| FR-8 | Result Display | Show formatted result to user | Output: `Result: <value>` with 2 decimal places |
| FR-9 | Loop Until Exit | Allow repeated calculations until user chooses Exit | Returns to main menu after each operation |
| FR-10 | Input Validation | Reject invalid inputs immediately | Re-prompts user with clear error message |

## 3. Technical Requirements
### 3.1 Language & Environment
- **Language**: Python 3.8+
- **Dependencies**: Only standard library (no external packages)

### 3.2 Architecture
```
calculator/
├── calculator.py          # Main CLI entry point
├── operations.py          # Core arithmetic functions
├── validators.py          # Input validation utilities
└── tests/
    ├── test_operations.py
    ├── test_validators.py
    └── test_integration.py
```

### 3.3 Core Functions (operations.py)
```python
def add(a: float, b: float) -> float
def subtract(a: float, b: float) -> float
def multiply(a: float, b: float) -> float
def divide(a: float, b: float) -> float  # raises ValueError on b=0
```

### 3.4 Input Validation (validators.py)
- Validate numeric input using `float()` conversion
- Handle `ValueError` for non-numeric strings
- Validate divisor is non-zero before division

### 3.5 Error Handling
- **Division by zero**: Display "Error: Cannot divide by zero" and return to menu
- **Invalid input**: Display "Error: Please enter a valid number" and re-prompt
- **Keyboard interrupt (Ctrl+C)**: Gracefully exit with message "Goodbye!"

### 3.6 Testing Requirements
- **Framework**: `unittest` (standard library)
- **Coverage**: 100% for operations.py and validators.py
- **Test Cases**:
  - All operations with positive, negative, and zero values
  - Edge cases: very large numbers, floating-point precision
  - Division by zero raises ValueError
  - Invalid string inputs raise ValueError
- **Run tests**: `python -m unittest discover tests`

### 3.7 Code Style
- Follow PEP 8
- Type hints for all functions
- Docstrings for all public functions

## 4. Success Criteria
### 4.1 Functional Verification
- [ ] All four operations produce mathematically correct results
- [ ] Division by zero shows error message without crashing
- [ ] Non-numeric inputs are rejected with clear message
- [ ] User can perform multiple calculations in one session
- [ ] Exit option terminates program cleanly

### 4.2 Testing Verification
- [ ] All unit tests pass (`python -m unittest` shows OK)
- [ ] Test coverage report shows 100% for core modules
- [ ] Edge cases are covered (negative numbers, zero, floats)

### 4.3 User Experience
- [ ] Menu is intuitive and easy to read
- [ ] Error messages are helpful and non-technical
- [ ] Results are displayed clearly with proper formatting
- [ ] Program handles Ctrl+C gracefully

### 4.4 Code Quality
- [ ] No linting errors (`pylint` score ≥ 8/10)
- [ ] All functions have type hints
- [ ] README.md explains how to run and test the application