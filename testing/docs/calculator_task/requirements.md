# requirements.md

## 1. Project Overview
Build a minimal command-line calculator that performs only two arithmetic operations: addition and subtraction. The tool must be immediately usable from a terminal or console window without any external dependencies beyond the standard runtime of the chosen language.

## 2. Functional Requirements
| ID | Requirement | Details |
|----|-------------|---------|
| FR-1 | Accept two numeric inputs | Read two numbers from the user (integers or floating-point). |
| FR-2 | Accept operation choice | Prompt the user to choose either “add” or “subtract”. |
| FR-3 | Perform addition | When “add” is chosen, return the sum of the two numbers. |
| FR-4 | Perform subtraction | When “subtract” is chosen, return the difference (first number minus second number). |
| FR-5 | Display result | Print the computed result to the console in a clear, human-readable format. |
| FR-6 | Handle invalid input | Detect non-numeric input or unrecognized operation choices and display a concise error message, then exit gracefully. |

## 3. Technical Requirements
| ID | Requirement | Details |
|----|-------------|---------|
| TR-1 | Language | Use Python 3 (≥ 3.8) for simplicity and portability. |
| TR-2 | Single file | Deliver the entire program in one file named `calculator.py`. |
| TR-3 | No external libraries | Restrict to Python’s standard library only. |
| TR-4 | Entry point | Allow execution via `python calculator.py` from any shell. |
| TR-5 | Input method | Use `input()` for interactive prompts. |
| TR-6 | Output format | Example: `Result: 42.5` |
| TR-7 | Error handling | On invalid input, print `Error: <reason>` and exit with code 1. |

## 4. Success Criteria
- [ ] Running `python calculator.py` starts an interactive session that prompts for two numbers and an operation.
- [ ] Entering `5`, `3`, and choosing “add” prints `Result: 8`.
- [ ] Entering `10`, `4`, and choosing “subtract” prints `Result: 6`.
- [ ] Entering non-numeric text (e.g., “abc”) prints `Error: Invalid number` and exits.
- [ ] Entering an unrecognized operation (e.g., “multiply”) prints `Error: Invalid operation` and exits.
- [ ] The program terminates immediately after displaying the result or error.