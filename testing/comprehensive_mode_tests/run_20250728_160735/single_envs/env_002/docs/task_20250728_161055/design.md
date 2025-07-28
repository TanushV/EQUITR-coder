# design.md

## 1. System Architecture

The calculator is a **single-process, command-line application** built with a layered architecture:

```
┌─────────────────────────────────────────┐
│           CLI Layer (calculator.py)     │
│  ┌─────────────────────────────────────┐ │
│  │        Menu Controller              │ │
│  │  ┌───────────────────────────────┐  │ │
│  │  │     Input Handler             │  │ │
│  │  └───────────────────────────────┘  │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│        Business Logic Layer             │
│  ┌─────────────────────────────────────┐ │
│  │      Operations Module              │ │
│  │  (add, subtract, multiply, divide)  │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │      Validation Module              │ │
│  │  (numeric validation, zero check)   │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Key Design Decisions:**
- **Pure Python 3.8+**: No external dependencies for maximum portability
- **Modular Design**: Separate concerns into distinct modules for testability
- **Exception-Based Error Handling**: Use Python exceptions for flow control
- **Type Safety**: Full type hints for static analysis and IDE support

## 2. Components

### 2.1 Core Components

#### calculator.py (CLI Entry Point)
- **Purpose**: Main executable script
- **Responsibilities**:
  - Display interactive menu
  - Handle user input flow
  - Coordinate between components
  - Graceful shutdown handling

#### operations.py (Business Logic)
- **Purpose**: Core arithmetic operations
- **Functions**:
  ```python
  def add(a: float, b: float) -> float
  def subtract(a: float, b: float) -> float
  def multiply(a: float, b: float) -> float
  def divide(a: float, b: float) -> float
  ```
- **Design**: Pure functions with no side effects for easy testing

#### validators.py (Input Validation)
- **Purpose**: Validate and sanitize user input
- **Functions**:
  ```python
  def validate_number(input_str: str) -> float
  def validate_non_zero(value: float) -> None
  ```

### 2.2 Test Components

#### tests/test_operations.py
- **Purpose**: Unit tests for arithmetic operations
- **Test Categories**:
  - Basic functionality tests
  - Edge cases (zero, negative, large numbers)
  - Floating-point precision tests

#### tests/test_validators.py
- **Purpose**: Unit tests for validation functions
- **Test Categories**:
  - Valid numeric string conversion
  - Invalid string handling
  - Zero validation for division

#### tests/test_integration.py
- **Purpose**: End-to-end testing of CLI interactions
- **Test Categories**:
  - Menu navigation flows
  - Complete calculation cycles
  - Error handling scenarios

## 3. Data Flow

### 3.1 Happy Path Flow
```
User → CLI → Validator → Operation → CLI → User
  │      │        │          │        │      │
  │   Display   Validate   Compute   Format  │
  │   Menu      Number     Result    Output │
  │      │        │          │        │      │
  └──────┴────────┴──────────┴────────┴──────┘
```

### 3.2 Error Handling Flow
```
User → CLI → Validator → Error → CLI → User
  │      │        │        │       │      │
  │   Display   Invalid   Raise   Show   │
  │   Prompt    Input     Error   Error  │
  │      │        │        │       │      │
  └──────┴────────┴────────┴───────┴──────┘
```

### 3.3 Data Types
- **Input**: Raw strings from stdin
- **Validation**: Convert to float or raise ValueError
- **Processing**: float → float operations
- **Output**: Formatted strings to stdout

## 4. Implementation Plan

### Phase 1: Core Operations (Day 1)
1. Create `operations.py` with four arithmetic functions
2. Implement comprehensive unit tests for operations
3. Achieve 100% test coverage for operations module

### Phase 2: Input Validation (Day 2)
1. Create `validators.py` with validation functions
2. Implement unit tests for validation logic
3. Test edge cases and error conditions

### Phase 3: CLI Interface (Day 3)
1. Create `calculator.py` with menu system
2. Implement input flow with validation
3. Add error handling and graceful exit

### Phase 4: Integration & Polish (Day 4)
1. Write integration tests for complete flows
2. Add Ctrl+C handling
3. Format output consistently
4. Final testing and documentation

### Phase 5: Quality Assurance (Day 5)
1. Run full test suite
2. Check code coverage
3. Lint code with pylint
4. Create README.md
5. Final verification against requirements

## 5. File Structure

```
calculator/
├── calculator.py              # Main CLI application
├── operations.py              # Core arithmetic functions
├── validators.py              # Input validation utilities
├── README.md                  # Project documentation
├── requirements.txt           # Empty (standard library only)
├── .gitignore                 # Python gitignore
├── .pylintrc                  # Pylint configuration
└── tests/
    ├── __init__.py            # Test package marker
    ├── test_operations.py     # Unit tests for operations
    ├── test_validators.py     # Unit tests for validators
    └── test_integration.py    # End-to-end CLI tests
```

### 5.1 File Details

#### calculator.py
```python
#!/usr/bin/env python3
"""
Command-line calculator application.
Provides interactive menu for basic arithmetic operations.
"""

import sys
from typing import Dict, Callable, Tuple

from operations import add, subtract, multiply, divide
from validators import validate_number, validate_non_zero

# Constants
MENU = """
=== Calculator Menu ===
1) Add
2) Subtract
3) Multiply
4) Divide
5) Exit
======================
Enter choice (1-5): """

# Operation mapping
OPERATIONS: Dict[int, Tuple[str, Callable[[float, float], float]]] = {
    1: ("Add", add),
    2: ("Subtract", subtract),
    3: ("Multiply", multiply),
    4: ("Divide", divide),
}
```

#### operations.py
```python
"""
Core arithmetic operations module.
Provides pure functions for basic calculator operations.
"""

from typing import Union

Number = Union[int, float]


def add(a: Number, b: Number) -> float:
    """Return the sum of two numbers."""
    return float(a) + float(b)


def subtract(a: Number, b: Number) -> float:
    """Return the difference between two numbers."""
    return float(a) - float(b)


def multiply(a: Number, b: Number) -> float:
    """Return the product of two numbers."""
    return float(a) * float(b)


def divide(a: Number, b: Number) -> float:
    """
    Return the quotient of two numbers.
    
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return float(a) / float(b)
```

#### validators.py
```python
"""
Input validation utilities for calculator.
Handles conversion and validation of user input.
"""

from typing import Union

Number = Union[int, float]


def validate_number(input_str: str) -> float:
    """
    Convert string to float, raising ValueError for invalid input.
    
    Args:
        input_str: String representation of a number
        
    Returns:
        float: Validated numeric value
        
    Raises:
        ValueError: If input_str cannot be converted to float
    """
    try:
        return float(input_str.strip())
    except ValueError as e:
        raise ValueError("Please enter a valid number") from e


def validate_non_zero(value: float) -> None:
    """
    Ensure value is not zero for division operations.
    
    Args:
        value: Number to validate
        
    Raises:
        ValueError: If value is zero
    """
    if value == 0:
        raise ValueError("Cannot divide by zero")
```

### 5.2 Test Structure

Each test file follows the same pattern:
- Test class per module
- Test methods for each function
- Edge case testing
- Error condition testing

Example test structure:
```python
class TestOperations(unittest.TestCase):
    def test_add_positive_numbers(self):
        """Test addition with positive numbers."""
        self.assertEqual(add(2, 3), 5.0)
    
    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        self.assertEqual(add(-2, -3), -5.0)
    
    def test_add_float_precision(self):
        """Test floating-point addition precision."""
        self.assertAlmostEqual(add(0.1, 0.2), 0.3, places=10)
```

### 5.3 Development Environment Setup

```bash
# Create project structure
mkdir calculator && cd calculator
mkdir tests
touch calculator.py operations.py validators.py README.md
touch tests/__init__.py tests/test_operations.py tests/test_validators.py tests/test_integration.py

# Initialize git repository
git init
git add .
git commit -m "Initial project structure"

# Run tests
python -m unittest discover tests -v

# Check coverage
python -m coverage run -m unittest discover tests
python -m coverage report -m
```