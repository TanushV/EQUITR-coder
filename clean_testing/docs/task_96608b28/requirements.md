# requirements.md

## 1. Project Overview
Build a command-line calculator program named `calculator.py` written in Python 3.  
The program must provide an interactive menu that lets a user repeatedly perform the four basic arithmetic operations (add, subtract, multiply, divide) on two floating-point numbers. It must be self-contained in a single file, runnable from the command line, and include robust error handling for invalid input and division-by-zero.

## 2. Functional Requirements
| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-1 | Display menu | On start, print a numbered menu listing: 1) Add, 2) Subtract, 3) Multiply, 4) Divide, 5) Exit. |
| FR-2 | Accept user choice | Prompt `Enter choice (1-5):` and accept integer 1-5. Re-prompt on invalid entry. |
| FR-3 | Accept two numbers | After valid choice 1-4, prompt `Enter first number:` and `Enter second number:`. Accept any float or int. Re-prompt on non-numeric input. |
| FR-4 | Perform addition | When choice = 1, compute `a + b` and display `Result: <value>`. |
| FR-5 | Perform subtraction | When choice = 2, compute `a - b` and display `Result: <value>`. |
| FR-6 | Perform multiplication | When choice = 3, compute `a * b` and display `Result: <value>`. |
| FR-7 | Perform division | When choice = 4, compute `a / b` and display `Result: <value>`. |
| FR-8 | Handle division by zero | If choice = 4 and `b == 0`, print `Error: Cannot divide by zero.` and return to menu. |
| FR-9 | Loop until exit | After each operation or error, re-display menu. Exit cleanly when choice = 5. |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language & version | Python 3.x (tested on 3.8+). |
| TR-2 | Entry point | File must be named `calculator.py` and contain `if __name__ == "__main__": main()`. |
| TR-3 | Function structure | Implement `main()` function that orchestrates the menu loop. Arithmetic may be inline or in helper functions. |
| TR-4 | Input validation | Use `try/except` to catch `ValueError` for non-numeric input. |
| TR-5 | Error handling | Division-by-zero must raise and catch `ZeroDivisionError`. |
| TR-6 | Command-line execution | Script must run via `python calculator.py` with no additional arguments. |
| TR-7 | Code style | Follow PEP 8; include concise comments and docstring for `main()`. |
| TR-8 | Portability | Use only Python standard library. |

## 4. Success Criteria
- [ ] `python calculator.py` launches and shows the menu.
- [ ] Each operation (add, subtract, multiply, divide) produces correct results for sample inputs.
- [ ] Entering `0` as second number in division prints the error message and does not crash.
- [ ] Typing non-numeric input re-prompts without crashing.
- [ ] Choosing 5 exits the program.
- [ ] All functional requirements FR-1 through FR-9 pass manual test checklist.
- [ ] Code passes `python -m py_compile calculator.py` without syntax errors.
- [ ] README (optional) contains instructions: “Run `python calculator.py` and follow on-screen prompts.”