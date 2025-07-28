# requirements.md

## 1. Project Overview
Build a **simple calculator application** that allows users to perform basic arithmetic operations through a graphical user interface (GUI). The application must be lightweight, intuitive, and run on Windows, macOS, and Linux without additional dependencies.

## 2. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | **Addition** – accept two numbers and return their sum. | Must |
| FR-2 | **Subtraction** – accept two numbers and return their difference. | Must |
| FR-3 | **Multiplication** – accept two numbers and return their product. | Must |
| FR-4 | **Division** – accept two numbers and return their quotient; handle divide-by-zero gracefully. | Must |
| FR-5 | **Clear (C)** – reset the current calculation. | Must |
| FR-6 | **Decimal Support** – allow entry and calculation of floating-point numbers. | Must |
| FR-7 | **Keyboard Input** – map number keys (0-9), operators (+, -, *, /), Enter (=), and Esc (clear). | Should |
| FR-8 | **Memory Functions** – M+, M-, MR, MC (store, recall, clear memory). | Could |
| FR-9 | **History** – display last 5 calculations. | Won’t (v1) |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | **Language & Framework** | Python 3.11+ with Tkinter (built-in, cross-platform). |
| TR-2 | **Packaging** | Single executable via PyInstaller for each OS. |
| TR-3 | **UI Layout** | 4×5 grid of buttons (digits 0-9, operators, clear, equals). |
| TR-4 | **Display** | Single-line text field (right-aligned, 20 chars max). |
| TR-5 | **Error Handling** | Show “Error” on invalid input or divide-by-zero; allow continuation. |
| TR-6 | **Precision** | IEEE-754 double precision; round to 10 decimal places for display. |
| TR-7 | **Performance** | Startup < 1 s; any calculation < 100 ms on 2020-era hardware. |
| TR-8 | **Accessibility** | Minimum font size 14 pt; high-contrast color scheme. |
| TR-9 | **Code Structure** | Single file `calculator.py` (< 300 lines) with clear separation of UI and logic. |
| TR-10 | **Testing** | Unit tests for each arithmetic operation using `unittest` (≥ 90 % coverage). |

## 4. Success Criteria
1. **Manual QA Checklist**  
   - All FR-1 to FR-6 pass on Windows 11, macOS 14, Ubuntu 22.04.  
   - Keyboard shortcuts work as specified.  
   - Divide-by-zero shows “Error” and does not crash.  
   - Executable size < 15 MB per platform.

2. **Automated Tests**  
   - `python -m unittest discover` passes with 0 failures.  
   - Coverage report ≥ 90 %.

3. **User Acceptance**  
   - 3 non-technical users can perform 10 random calculations without instruction in < 2 minutes.

4. **Delivery**  
   - GitHub repository tagged `v1.0` with release binaries attached.