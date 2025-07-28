# requirements.md

## 1. Project Overview
Build a **command-line calculator** that performs the four basic arithmetic operations (add, subtract, multiply, divide) on two numbers entered by the user. The application must validate all inputs, gracefully handle division-by-zero errors, and be accompanied by a complete suite of unit tests to ensure correctness.

---

## 2. Functional Requirements

| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | CLI Entry Point | Provide a single executable entry point (`calculator` or `python calculator.py`) that starts the program. | Typing the command launches the calculator and shows a welcome message. |
| FR-2 | Interactive Mode | After launch, repeatedly prompt the user for two numbers and an operator until the user chooses to exit. | Each cycle: <br>1. Prompt “Enter first number:” <br>2. Prompt “Enter operator (+, -, *, /):” <br>3. Prompt “Enter second number:” <br>4. Display result or error message. |
| FR-3 | Supported Operations | Implement four operations: addition, subtraction, multiplication, division. | Each operator symbol (`+`, `-`, `*`, `/`) maps to the correct arithmetic function. |
| FR-4 | Input Validation | Reject non-numeric input and invalid operators. | If the user enters “abc” for a number or “x” for an operator, display “Invalid input, please try again.” and re-prompt. |
| FR-5 | Division-by-Zero Handling | Detect and handle attempts to divide by zero. | Display “Error: Division by zero is undefined.” and re-prompt. |
| FR-6 | Exit Command | Allow the user to quit gracefully. | Typing `q`, `quit`, or `exit` at any prompt terminates the program with a goodbye message. |
| FR-7 | Result Display | Show the full equation and result in a clear format. | Example: `5 + 3 = 8` |

---

## 3. Technical Requirements

| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language | Python 3.8+ |
| TR-2 | Project Structure | ```
calculator/
├── calculator/
│   ├── __init__.py
│   ├── cli.py          # CLI loop & I/O
│   └── operations.py   # Core arithmetic functions
├── tests/
│   ├── __init__.py
│   └── test_operations.py
├── requirements.txt
└── README.md
``` |
| TR-3 | Core Functions | Implement four pure functions in `operations.py`: <br>`add(a: float, b: float) -> float` <br>`subtract(a: float, b: float) -> float` <br>`multiply(a: float, b: float) -> float` <br>`divide(a: float, b: float) -> float` |
| TR-4 | CLI Module | `cli.py` must: <br>- Parse user input <br>- Validate numbers via `float()` conversion <br>- Route to the correct operation <br>- Catch and display exceptions |
| TR-5 | Testing Framework | Use `pytest`. Achieve 100 % line coverage on `operations.py` and `cli.py`. |
| TR-6 | Test Cases | At minimum: <br>- Positive, negative, and floating-point numbers <br>- All four operations <br>- Division by zero <br>- Invalid operator <br>- Invalid numeric input |
| TR-7 | Packaging | Provide a `requirements.txt` listing only `pytest`. |
| TR-8 | Documentation | `README.md` must include: <br>- Installation steps <br>- How to run the calculator <br>- How to run tests |

---

## 4. Success Criteria

- [ ] User can start the calculator from the command line.
- [ ] All four arithmetic operations produce correct results for valid inputs.
- [ ] Division by zero is caught and handled without crashing.
- [ ] Non-numeric or invalid operator inputs prompt the user again.
- [ ] Typing `q`, `quit`, or `exit` terminates the program cleanly.
- [ ] `pytest` runs all tests successfully with 100 % coverage.
- [ ] Code is PEP 8 compliant and passes `flake8` linting.
- [ ] README provides clear setup and usage instructions.