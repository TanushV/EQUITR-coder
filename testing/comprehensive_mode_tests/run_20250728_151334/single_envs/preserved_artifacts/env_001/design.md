# design.md

## 1. System Architecture

The calculator application follows a **layered architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           CLI Layer (calculator.py)      │
│  ┌─────────────────────────────────────┐ │
│  │        User Interface               │ │
│  │  - Menu display                     │ │
│  │  - Input prompts                    │ │
│  │  - Result formatting                │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
           │ uses
┌─────────────────────────────────────────┐
│        Input Handler Layer              │
│  ┌─────────────────────────────────────┐ │
│  │    Input Validation & Parsing       │ │
│  │  - Number validation                │ │
│  │  - Error handling                   │ │
│  │  - Type conversion                  │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
           │ uses
┌─────────────────────────────────────────┐
│        Operations Layer                 │
│  ┌─────────────────────────────────────┐ │
│  │    Core Arithmetic Functions        │ │
│  │  - add, subtract, multiply, divide  │ │
│  │  - Division by zero handling        │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 2. Components

### 2.1 Core Components

#### 2.1.1 CLI Entry Point (`calculator.py`)
- **Purpose**: Main executable script
- **Responsibilities**:
  - Display interactive menu
  - Coordinate between input handler and operations
  - Manage application lifecycle
  - Handle graceful exit

#### 2.1.2 Operations Module (`operations.py`)
- **Purpose**: Core arithmetic logic
- **Responsibilities**:
  - Implement four arithmetic operations
  - Handle division by zero with custom exception
  - Provide type-safe function signatures

#### 2.1.3 Input Handler (`input_handler.py`)
- **Purpose**: User input validation and parsing
- **Responsibilities**:
  - Validate numeric input
  - Parse various number formats
  - Provide clear error messages
  - Handle retry logic

#### 2.1.4 Custom Exceptions (`exceptions.py`)
- **Purpose**: Domain-specific error handling
- **Responsibilities**:
  - Define `DivisionByZeroError`
  - Define `InvalidInputError`

### 2.2 Test Components

#### 2.2.1 Unit Tests (`tests/test_operations.py`)
- Test all arithmetic operations
- Edge cases (very large/small numbers)
- Negative numbers
- Floating-point precision

#### 2.2.2 Input Tests (`tests/test_input_handler.py`)
- Valid number formats
- Invalid input rejection
- Scientific notation parsing
- Boundary value testing

#### 2.2.3 Integration Tests (`tests/test_integration.py`)
- Full CLI workflow testing
- Menu navigation
- Error recovery scenarios
- Exit behavior

## 3. Data Flow

### 3.1 Happy Path Flow
```
User → CLI → Input Handler → Operations → CLI → User
  │      │         │            │         │      │
  │   Display    Validate    Calculate  Format  │
  │   Menu       Numbers     Result     Output  │
  │      │         │            │         │      │
  └── Select 1 → "2" → 2.0 → add(2,3) → "2 + 3 = 5" → Display
```

### 3.2 Error Handling Flow
```
User → CLI → Input Handler → Error → CLI → User
  │      │         │          │        │      │
  │   Display    Validate   Raise    Handle  │
  │   Prompt     "abc"      Error    Message │
  │      │         │          │        │      │
  └── Input → "abc" → InvalidInputError → "Invalid input..." → Retry
```

### 3.3 Division by Zero Flow
```
User → CLI → Input Handler → Operations → Error → CLI → User
  │      │         │            │          │        │      │
  │   Display    Validate    Calculate   Raise    Handle  │
  │   Prompt     Numbers     divide(5,0) Error    Message │
  │      │         │            │          │        │      │
  └── Input → 5,0 → 5.0,0.0 → DivisionByZeroError → "Error: Division..." → Menu
```

## 4. Implementation Plan

### Phase 1: Foundation (Day 1)
1. **Project Setup**
   - Create directory structure
   - Initialize git repository
   - Create virtual environment
   - Set up flake8 configuration

2. **Core Operations**
   - Implement `operations.py` with four functions
   - Add type hints and docstrings
   - Create `exceptions.py` with custom exceptions

3. **Basic Tests**
   - Write `test_operations.py`
   - Achieve 100% coverage for operations

### Phase 2: Input Handling (Day 2)
1. **Input Validation**
   - Implement `input_handler.py`
   - Add number parsing with regex
   - Handle scientific notation
   - Add input length validation

2. **Input Tests**
   - Write `test_input_handler.py`
   - Test all valid/invalid cases
   - Achieve 100% coverage

### Phase 3: CLI Interface (Day 3)
1. **Menu System**
   - Implement main calculator loop
   - Add menu display function
   - Connect components

2. **Integration**
   - Write `test_integration.py`
   - Test full workflows
   - Handle KeyboardInterrupt

### Phase 4: Polish & Documentation (Day 4)
1. **Code Quality**
   - Run flake8 and fix issues
   - Add comprehensive docstrings
   - Review test coverage

2. **Documentation**
   - Write README.md
   - Add usage examples
   - Create installation guide

## 5. File Structure

```
calculator/
├── calculator.py              # CLI entry point
├── operations.py              # Core arithmetic functions
├── input_handler.py           # Input validation & parsing
├── exceptions.py              # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_operations.py     # Unit tests for arithmetic
│   ├── test_input_handler.py  # Unit tests for input handling
│   ├── test_integration.py    # End-to-end CLI tests
│   └── fixtures/              # Test data files
│       ├── valid_numbers.txt
│       └── invalid_inputs.txt
├── .gitignore
├── .flake8                    # Linting configuration
├── requirements.txt           # Empty (standard library only)
└── README.md                  # Project documentation

Detailed file contents:

calculator.py:
- main() function
- display_menu()
- get_operation_choice()
- run_calculator_loop()
- handle_exit()

operations.py:
- add(a: float, b: float) -> float
- subtract(a: float, b: float) -> float
- multiply(a: float, b: float) -> float
- divide(a: float, b: float) -> float

input_handler.py:
- get_number(prompt: str) -> float
- validate_number(input_str: str) -> float
- parse_scientific_notation(input_str: str) -> float

exceptions.py:
- class DivisionByZeroError(ArithmeticError)
- class InvalidInputError(ValueError)

tests/test_operations.py:
- TestAdd class
- TestSubtract class
- TestMultiply class
- TestDivide class
- Edge case tests

tests/test_input_handler.py:
- TestValidInput class
- TestInvalidInput class
- TestScientificNotation class
- TestBoundaryValues class

tests/test_integration.py:
- TestCalculatorFlow class
- TestErrorRecovery class
- TestExitBehavior class
```