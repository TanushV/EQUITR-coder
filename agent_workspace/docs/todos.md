# todos.md

## Phase 1: Project Setup and Core Structure

- [ ] Create project directory structure:
  - `calculator/`
  - `calculator/calculator.py`
  - `calculator/tests/`
  - `calculator/tests/__init__.py`
  - `calculator/build/`
  - `calculator/docs/`
  - `calculator/requirements.txt` (empty file)

- [ ] Create `calculator.py` with initial file structure:
  - Add shebang line `#!/usr/bin/env python3`
  - Add module docstring
  - Import required modules: `tkinter as tk`, `decimal.Decimal`, `getcontext`, `Optional`, `Dict`, `Callable`, `sys`
  - Define constants: `WINDOW_TITLE`, `WINDOW_SIZE`, `DISPLAY_FONT`, `BUTTON_FONT`, `MAX_DIGITS`

- [ ] Implement `CalculatorState` class:
  - Create `__init__()` method with state variables:
    - `self.current_value: Decimal = Decimal('0')`
    - `self.stored_value: Optional[Decimal] = None`
    - `self.pending_operator: Optional[str] = None`
    - `self.waiting_for_operand: bool = False`
    - `self.memory_value: Decimal = Decimal('0')`
    - `self.has_memory: bool = False`
  - Add `reset()` method to clear state
  - Add `add_digit(digit: str)` method
  - Add `set_operator(op: str)` method
  - Add `get_display_text() -> str` method

- [ ] Implement `CalculatorEngine` class:
  - Create `__init__()` method
  - Add `add(a: Decimal, b: Decimal) -> Decimal` method
  - Add `subtract(a: Decimal, b: Decimal) -> Decimal` method
  - Add `multiply(a: Decimal, b: Decimal) -> Decimal` method
  - Add `divide(a: Decimal, b: Decimal) -> Decimal | str` method (returns "Error" for division by zero)
  - Add `percentage(value: Decimal) -> Decimal` method

- [ ] Create basic Tkinter window in `CalculatorGUI` class:
  - Add `__init__(self, root: tk.Tk)` method
  - Set window title and size
  - Configure grid layout weights
  - Create display label widget with font and styling
  - Add basic `update_display(self, value: str)` method

## Phase 2: Button Grid and Basic Operations

- [ ] Create button layout constants:
  - Define `BUTTONS` list with tuples of (text, row, col, colspan, command_type)
  - Include all digit buttons (0-9)
  - Include decimal point button
  - Include operator buttons (+, -, *, /)
  - Include equals button
  - Include clear button

- [ ] Implement `create_widgets()` method in `CalculatorGUI`:
  - Create button frame with grid layout
  - Add method `create_button(self, text: str, row: int, col: int, colspan: int = 1)` to create styled buttons
  - Position display label at top
  - Position button frame below display

- [ ] Implement `CalculatorController` class:
  - Create `__init__(self, gui: CalculatorGUI, state: CalculatorState, engine: CalculatorEngine)` method
  - Add `handle_digit(self, digit: str)` method
  - Add `handle_operator(self, op: str)` method
  - Add `handle_equals(self)` method
  - Add `handle_clear(self)` method
  - Add `handle_decimal(self)` method

- [ ] Wire button commands:
  - Connect digit buttons to `handle_digit`
  - Connect operator buttons to `handle_operator`
  - Connect equals button to `handle_equals`
  - Connect clear button to `handle_clear`
  - Connect decimal button to `handle_decimal`

- [ ] Implement display formatting:
  - Add `format_display_value(self, value: Decimal) -> str` method
  - Handle max digits (10)
  - Handle decimal formatting
  - Handle scientific notation for very large/small numbers

## Phase 3: Error Handling and Polish

- [ ] Implement error handling in `CalculatorEngine`:
  - Update `divide()` to return "Error" for division by zero
  - Add validation for invalid operations

- [ ] Add error state to `CalculatorState`:
  - Add `self.error: bool = False`
  - Add `set_error()` and `clear_error()` methods

- [ ] Update display to show "Error":
  - Modify `update_display()` to handle error state
  - Ensure error clears on next input

- [ ] Implement keyboard support:
  - Add `bind_keyboard_events()` method to `CalculatorGUI`
  - Bind number keys (0-9) to digit handlers
  - Bind operator keys (+, -, *, /) to operator handlers
  - Bind Enter/Return to equals
  - Bind Escape to clear
  - Bind period (.) to decimal

- [ ] Add visual feedback:
  - Highlight active operator button
  - Show memory indicator when memory is non-zero

## Phase 4: Memory Functions

- [ ] Add memory methods to `CalculatorController`:
  - Add `handle_memory_add(self)` method (M+)
  - Add `handle_memory_subtract(self)` method (M-)
  - Add `handle_memory_recall(self)` method (MR)
  - Add `handle_memory_clear(self)` method (MC)

- [ ] Add memory buttons to layout:
  - Add M+, M-, MR, MC buttons to button grid
  - Position in appropriate locations (typically above number buttons)

- [ ] Update display for memory:
  - Add small indicator (e.g., "M") when memory is non-zero
  - Update display formatting to include memory indicator

- [ ] Implement percentage functionality:
  - Add `handle_percentage(self)` method to `CalculatorController`
  - Add percentage button to layout
  - Implement percentage calculation logic

## Phase 5: Testing and Packaging

- [ ] Create test files:
  - `tests/test_calculator.py` for `CalculatorEngine` tests
  - `tests/test_parser.py` for expression parsing tests
  - `tests/test_gui.py` for GUI integration tests

- [ ] Write unit tests for `CalculatorEngine`:
  - Test addition with various inputs
  - Test subtraction with various inputs
  - Test multiplication with various inputs
  - Test division with valid inputs
  - Test division by zero returns "Error"
  - Test percentage calculations

- [ ] Write unit tests for `CalculatorState`:
  - Test state transitions
  - Test digit accumulation
  - Test operator setting
  - Test reset functionality
  - Test memory operations

- [ ] Write integration tests:
  - Test complete calculation sequences
  - Test error handling scenarios
  - Test keyboard input
  - Test memory operations

- [ ] Create PyInstaller configuration:
  - Create `build/calculator.spec` file
  - Configure for single-file executable
  - Test executable generation

- [ ] Final testing:
  - Run all tests with `python -m pytest tests/`
  - Test GUI manually with success criteria:
    - Launch calculator with `python calculator.py`
    - Verify 7 + 3 = 10
    - Verify 5 / 0 = Error
    - Verify C resets to 0
    - Test keyboard input works
    - Test memory functions work

- [ ] Add docstrings:
  - Add docstrings to all public classes
  - Add docstrings to all public methods
  - Ensure PEP 8 compliance throughout

- [ ] Create README.md in docs/:
  - Add usage instructions
  - Add keyboard shortcuts list
  - Add build instructions for executable