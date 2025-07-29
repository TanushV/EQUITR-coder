# Requirements Document – Calculator Program (`calculator.py`)

## 1. Project Overview
Build a **command-line calculator** named `calculator.py` that allows a user to perform basic arithmetic operations on decimal numbers.  
The program must be self-contained in a single file, run from the terminal, and provide a simple interactive loop until the user chooses to exit.

---

## 2. Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| FR-1 | Basic Operations | Support addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`). |
| FR-2 | Decimal Support | Accept and correctly compute floating-point numbers (e.g., `3.14`, `-0.001`). |
| FR-3 | Input Validation | Reject non-numeric operands and invalid operators; prompt again until valid. |
| FR-4 | Division Edge Cases | Detect and handle division by zero gracefully (display message, do not crash). |
| FR-5 | Interactive Loop | Provide a REPL-style interface: prompt → calculate → display → repeat. |
| FR-6 | Exit Command | Allow the user to type `exit` or `quit` (case-insensitive) to terminate. |
| FR-7 | Clear Feedback | After each calculation, display the full equation and result in a readable format. |
| FR-8 | Help/Usage | On invalid input, show concise usage instructions. |

---

## 3. Technical Requirements

| ID | Requirement | Specification |
|---|---|---|
| TR-1 | Language & Version | Python 3.8+ (standard library only). |
| TR-2 | File Name | Single file named `calculator.py`. |
| TR-3 | Entry Point | Include `if __name__ == "__main__":` guard that calls a `main()` function. |
| TR-4 | Error Handling | Use `try/except` to catch `ValueError`, `ZeroDivisionError`, and generic exceptions; never propagate unhandled errors to the user. |
| TR-5 | Precision | Use Python’s built-in `float` type; do not round unless displaying (format to ≤10 decimal places). |
| TR-6 | Code Style | Follow PEP 8; include concise docstrings for each function. |
| TR-7 | Input Parsing | Tokenize user input via `str.split()`; expect format: `<number> <operator> <number>`. |
| TR-8 | Unit-Testable Design | Core calculation logic should reside in separate functions (e.g., `add(a, b)`, `divide(a, b)`) to enable future unit tests. |

---

## 4. Success Criteria

| Checkpoint | How to Verify |
|---|---|
| SC-1 | Run `python calculator.py`; interactive prompt appears. |
| SC-2 | Enter `2 + 3` → output `2 + 3 = 5`. |
| SC-3 | Enter `7 / 0` → output `Error: Division by zero is undefined.` |
| SC-4 | Enter `abc + 5` → output `Error: Invalid number 'abc'. Please enter: <number> <+,-,*,/> <number>` |
| SC-5 | Enter `exit` → program terminates with exit code 0. |
| SC-6 | Enter `3.5 * -2.1` → output `3.5 * -2.1 = -7.35`. |
| SC-7 | Static analysis: `python -m py_compile calculator.py` compiles without syntax errors. |
| SC-8 | Manual code review confirms PEP 8 compliance and presence of docstrings.