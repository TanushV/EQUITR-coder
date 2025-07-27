# design.md

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Calculator App                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  GUI Layer (Tkinter)                 │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │   Display   │  │ Button Grid  │  │  Keyboard  │ │   │
│  │  │   Widget    │  │   Manager    │  │  Handler   │ │   │
│  │  └─────────────┘  └──────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Controller Layer                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │   Parser     │  │   Engine     │  │  Memory  │ │   │
│  │  │ (Expression) │  │ (Calculator) │  │  Store   │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Model Layer                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │   Decimal    │  │   State      │  │  Error   │ │   │
│  │  │   Numbers    │  │   Machine    │  │  Types   │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 2. Components

### 2.1 GUI Components
- **CalculatorGUI**: Main application window
  - `display_label`: tk.Label for showing input/result
  - `button_frame`: tk.Frame containing all buttons
  - `root`: tk.Tk main window
- **ButtonFactory**: Creates standardized buttons with consistent styling
- **KeyboardHandler**: Binds keyboard events to calculator functions

### 2.2 Controller Components
- **CalculatorController**: Mediates between GUI and business logic
  - `handle_digit(digit: str)`: Process digit input
  - `handle_operator(op: str)`: Process operator input
  - `handle_equals()`: Calculate result
  - `handle_clear()`: Reset calculator
  - `handle_memory(op: str)`: Memory operations
- **ExpressionParser**: Validates and parses input sequences
- **CalculatorEngine**: Performs actual calculations using Decimal

### 2.3 Model Components
- **CalculatorState**: Tracks current state
  - `current_value: Decimal`
  - `stored_value: Decimal | None`
  - `pending_operator: str | None`
  - `waiting_for_operand: bool`
- **ErrorHandler**: Manages error states and messages
- **DecimalPrecision`: Configures Decimal context (10-digit precision)

## 3. Data Flow

```
User Input (Button/Keyboard)
         │
         ▼
┌─────────────────┐
│  Event Handler  │ (CalculatorController)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──┐
│Parser │ │State│
└───┬───┘ └──┬──┘
    │        │
    │   ┌────┴────┐
    │   │Engine   │
    │   └────┬────┘
    │        │
┌───▼────────▼───┐
│   Display      │
└────────────────┘
```

### 3.1 Input Processing Flow
1. User presses button/key
2. Event handler determines input type (digit, operator, action)
3. State machine updates based on input
4. If equals pressed, expression is parsed and calculated
5. Result/error displayed on screen

### 3.2 State Transitions
```
[Start] ──digit──> [Input1] ──op──> [OpPending] ──digit──> [Input2]
   │                 │              │                       │
   │                 │              │                       └──equals──> [Result]
   │                 │              │                                   │
   │                 │              └─────digit------------------------┘
   │                 │                                                  │
   └─clear----------┘                                                  │
                                                                       │
[Error] <─invalid input/division by zero──────────────────────────────┘
```

## 4. Implementation Plan

### Phase 1: Core Structure (Day 1)
- [ ] Create `calculator.py` main file
- [ ] Set up basic Tkinter window with title and geometry
- [ ] Implement CalculatorState class
- [ ] Create basic display widget

### Phase 2: Basic Operations (Day 2)
- [ ] Implement CalculatorEngine with Decimal operations
- [ ] Create button grid layout (4×5)
- [ ] Wire digit buttons (0-9, .)
- [ ] Implement basic operators (+, -, *, /)
- [ ] Add equals functionality

### Phase 3: Error Handling & Polish (Day 3)
- [ ] Implement error handling for division by zero
- [ ] Add clear functionality
- [ ] Add display formatting (8+ digits)
- [ ] Implement keyboard bindings

### Phase 4: Memory & Percentage (Day 4)
- [ ] Add memory operations (M+, M-, MR, MC)
- [ ] Implement percentage calculation
- [ ] Add visual feedback for memory state

### Phase 5: Testing & Packaging (Day 5)
- [ ] Write unit tests for CalculatorEngine
- [ ] Write integration tests for GUI
- [ ] Create PyInstaller spec file
- [ ] Test on Windows/Mac/Linux

## 5. File Structure

```
calculator/
├── calculator.py              # Main application file
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py     # Unit tests for CalculatorEngine
│   ├── test_parser.py         # Tests for ExpressionParser
│   └── test_gui.py           # GUI integration tests
├── build/
│   ├── calculator.spec       # PyInstaller spec
│   └── dist/                 # Generated executables
├── docs/
│   └── README.md
└── requirements.txt          # Empty (standard library only)
```

### 5.1 calculator.py Structure
```python
#!/usr/bin/env python3
"""
Simple Calculator - A GUI calculator using Tkinter and Decimal.

This module provides a complete calculator implementation with:
- Basic arithmetic operations
- Memory functions
- Keyboard support
- Error handling
"""

import tkinter as tk
from decimal import Decimal, getcontext
from typing import Optional, Dict, Callable
import sys

# Constants
WINDOW_TITLE = "Simple Calculator"
WINDOW_SIZE = "300x400"
DISPLAY_FONT = ("Arial", 24)
BUTTON_FONT = ("Arial", 14)
MAX_DIGITS = 10

class CalculatorState:
    """Manages the calculator's state machine."""
    ...

class CalculatorEngine:
    """Performs arithmetic operations with Decimal precision."""
    ...

class CalculatorGUI:
    """Main GUI class using Tkinter."""
    ...

def main():
    """Entry point for the calculator application."""
    ...

if __name__ == "__main__":
    main()
```

### 5.2 Key Classes and Methods

#### CalculatorState
- `__init__()`: Initialize state variables
- `reset()`: Clear all state
- `add_digit(digit: str)`: Add digit to current input
- `set_operator(op: str)`: Store pending operation
- `get_expression() -> str`: Get current expression for display

#### CalculatorEngine
- `add(a: Decimal, b: Decimal) -> Decimal`
- `subtract(a: Decimal, b: Decimal) -> Decimal`
- `multiply(a: Decimal, b: Decimal) -> Decimal`
- `divide(a: Decimal, b: Decimal) -> Decimal | str`
- `percentage(value: Decimal) -> Decimal`

#### CalculatorGUI
- `create_widgets()`: Build UI components
- `create_button(text: str, row: int, col: int, command: Callable)`
- `bind_keyboard_events()`: Set up key bindings
- `update_display(value: str)`: Refresh display label