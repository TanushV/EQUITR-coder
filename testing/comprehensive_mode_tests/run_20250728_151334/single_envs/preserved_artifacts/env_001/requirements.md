# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers. The application must be robust, user-friendly, and fully tested.

## 2. Functional Requirements
| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | CLI Entry Point | Provide a single executable script that starts the calculator | `python calculator.py` launches interactive prompt |
| FR-2 | Operation Selection | Present a menu with numbered choices for each operation | Menu shows: 1) Add 2) Subtract 3) Multiply 4) Divide 5) Exit |
| FR-3 | Number Input | Accept two floating-point numbers from the user | Accepts integers, decimals, and scientific notation (e.g., 3, 3.5, 1e-3) |
| FR-4 | Addition | Compute the sum of two numbers | `add(2, 3)` → `5` |
| FR-5 | Subtraction | Compute the difference between two numbers | `subtract(5, 2)` → `3` |
| FR-6 | Multiplication | Compute the product of two numbers | `multiply(4, 3)` → `12` |
| FR-7 | Division | Compute the quotient of two numbers | `divide(6, 2)` → `3.0` |
| FR-8 | Division by Zero Handling | Detect and report division by zero | Returns clear error message: `"Error: Division by zero is undefined"` |
| FR-9 | Input Validation | Reject non-numeric input gracefully | Prompts user again with message `"Invalid input. Please enter a number."` |
| FR-10 | Result Display | Show the operation and result in a readable format | `"2 + 3 = 5"` |
| FR-11 | Loop Until Exit | Allow multiple calculations in one session | Returns to main menu after each calculation until user chooses Exit |
| FR-12 | Exit Gracefully | Provide a clean way to quit | Option 5 exits with message `"Goodbye!"` |

## 3. Technical Requirements
### 3.1 Language & Environment
- **Language**: Python 3.8+
- **Dependencies**: Only Python standard library (no external packages)

### 3.2 Project Structure
```
calculator/
├── calculator.py          # CLI entry point
├── operations.py          # Core arithmetic functions
├── input_handler.py       # Input validation & parsing
├── tests/
│   ├── test_operations.py
│   ├── test_input_handler.py
│   └── test_integration.py
└── README.md
```

### 3.3 Core Functions (operations.py)
```python
def add(a: float, b: float) -> float: ...
def subtract(a: float, b: float) -> float: ...
def multiply(a: float, b: float) -> float: ...
def divide(a: float, b: float) -> float: ...
```

### 3.4 Input Validation Rules
- Accepts: integers, floats, scientific notation
- Rejects: strings, empty input, special characters
- Max input length: 50 characters
- Precision: 15 decimal places max

### 3.5 Error Handling
- **Division by Zero**: Custom exception `DivisionByZeroError`
- **Invalid Input**: Custom exception `InvalidInputError`
- **Unexpected Errors**: Catch-all with user-friendly message

### 3.6 Unit Testing Requirements
- **Coverage Target**: 100% for operations.py and input_handler.py
- **Test Framework**: unittest (standard library)
- **Test Categories**:
  - Happy path tests for all operations
  - Edge cases (very large/small numbers, negative numbers)
  - Error cases (division by zero, invalid input)
  - Integration tests for full CLI workflow

### 3.7 Code Quality
- **Style**: PEP 8 compliant
- **Type Hints**: All functions must have type annotations
- **Docstrings**: Google style for all public functions
- **Linting**: Passes flake8 with default settings

## 4. Success Criteria
### 4.1 Functional Verification
- [ ] All FR-1 through FR-12 pass manual testing
- [ ] All operations produce mathematically correct results
- [ ] Division by zero shows error message and returns to menu
- [ ] Non-numeric input triggers re-prompt without crashing

### 4.2 Testing Verification
- [ ] All unit tests pass (`python -m unittest discover tests`)
- [ ] Test coverage report shows 100% for core modules
- [ ] No skipped or failing tests

### 4.3 User Experience
- [ ] First-time user can complete a calculation in under 30 seconds
- [ ] Error messages are clear and actionable
- [ ] Program exits cleanly with Ctrl+C (KeyboardInterrupt handled)

### 4.4 Code Quality
- [ ] No linting errors (`flake8 .`)
- [ ] All public functions have docstrings
- [ ] README includes installation and usage instructions
- [ ] Repository has clean commit history with descriptive messages