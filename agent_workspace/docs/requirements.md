# requirements.md

## 1. Project Overview
Build a **simple calculator** that allows a user to perform basic arithmetic operations through a graphical user interface (GUI). The calculator must be self-contained, run locally, and require no external dependencies beyond the chosen language’s standard library.

## 2. Functional Requirements
| ID | Requirement | Description | Priority |
|---|---|---|---|
| FR-1 | Basic Operations | Support addition, subtraction, multiplication, and division of two numbers. | Must |
| FR-2 | Input | Accept numeric input via on-screen buttons (0–9, decimal point). | Must |
| FR-3 | Clear | Provide a “C” button that resets the display to 0. | Must |
| FR-4 | Display | Show current input and result on a single-line display (≥8 digits). | Must |
| FR-5 | Error Handling | Display “Error” for division by zero or invalid sequences (e.g., “5+”). | Must |
| FR-6 | Keyboard Support | Allow the same operations via keyboard (0–9, +, −, *, /, Enter, Esc). | Should |
| FR-7 | Memory | Provide M+, M−, MR, MC buttons for single-memory storage. | Could |
| FR-8 | Percentage | Add “%” button that computes x% of the current value. | Could |

## 3. Technical Requirements
| ID | Requirement | Description |
|---|---|---|
| TR-1 | Language & GUI Toolkit | Use **Python 3.11+** with **Tkinter** (standard library) for cross-platform GUI. |
| TR-2 | Packaging | Deliver as a single `.py` file or a platform-specific executable (via PyInstaller) with no extra installs. |
| TR-3 | Layout | Grid layout: 4×5 button matrix (digits, operators, actions). |
| TR-4 | Responsiveness | All buttons respond within 100 ms on a mid-range laptop. |
| TR-5 | Precision | Use Python’s `decimal.Decimal` to avoid floating-point artifacts; default to 10-digit precision. |
| TR-6 | Code Style | Follow PEP 8; include docstrings for every public function/class. |
| TR-7 | Testing | Provide unit tests (pytest) covering all arithmetic operations and edge cases. |

## 4. Success Criteria
- [ ] User can launch the calculator with a double-click (or `python calculator.py`) and see a window with a display and buttons.
- [ ] Entering `7`, `+`, `3`, `=` shows `10` on the display.
- [ ] Entering `5`, `/`, `0`, `=` shows `Error`.
- [ ] Pressing `C` resets the display to `0`.
- [ ] All unit tests pass (`pytest tests/`).
- [ ] No external packages are required beyond the Python standard library.