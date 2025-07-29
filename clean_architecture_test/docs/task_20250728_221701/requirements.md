# Requirements Document – Calculator Program (`calculator.py`)

## 1. Project Overview
Build a **command-line calculator** that allows a user to perform the four basic arithmetic operations on decimal numbers.  
The program must be delivered as a single file named `calculator.py`, written in Python 3, and must be runnable from the terminal with `python calculator.py`.

## 2. Functional Requirements
| ID | Requirement | Description | Acceptance Criteria |
|---|---|---|---|
| FR-1 | Basic Operations | Support addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`) | Each operation returns the correct mathematical result for any two valid operands |
| FR-2 | Decimal Support | Accept and return floating-point numbers with at least 2-decimal precision | `3.5 + 2.1` → `5.6` |
| FR-3 | Input Validation | Reject non-numeric or malformed input | Prompt user again until valid numbers are entered |
| FR-4 | Division Edge Case | Prevent division by zero | Display clear error message and re-prompt |
| FR-5 | Interactive Loop | Provide a main menu loop | User can perform multiple calculations or exit cleanly |
| FR-6 | Exit Command | Allow user to quit at any prompt | Typing `q`, `quit`, or `exit` terminates the program gracefully |

## 3. Technical Requirements
| ID | Requirement | Specification |
|---|---|---|
| TR-1 | Language & Version | Python 3.8+ |
| TR-2 | File Name | Exactly `calculator.py` in project root |
| TR-3 | Entry Point | `if __name__ == "__main__":` block that calls `main()` |
| TR-4 | Function Structure | At minimum: <br>`add(a, b)` <br>`subtract(a, b)` <br>`multiply(a, b)` <br>`divide(a, b)` <br>`main()` |
| TR-5 | Error Handling | Use `try/except` for:<br>- `ValueError` on invalid numeric input<br>- `ZeroDivisionError` on division by zero |
| TR-6 | Output Formatting | Results printed with ≤2 decimal places (e.g., `12.00`, `7.5`) |
| TR-7 | Code Style | PEP 8 compliant; no external dependencies |

## 4. Success Criteria
The project is considered **complete** when all of the following are true:

1. **Functionality**  
   - All four operations produce mathematically correct results.  
   - Division by zero is caught and handled without crashing.  
   - Decimal inputs and outputs are accurate to at least two decimal places.

2. **User Experience**  
   - A first-time user can run `python calculator.py` and successfully perform at least three calculations in one session.  
   - Typing `q` at any prompt exits the program immediately.

3. **Code Quality**  
   - `pylint calculator.py` returns a score ≥ 8.0 (or `flake8` shows no warnings).  
   - All functions have docstrings explaining purpose, parameters, and return values.

4. **Deliverable**  
   - A single file `calculator.py` exists in the repository root and is executable on a clean Python 3.8+ environment with no additional packages.