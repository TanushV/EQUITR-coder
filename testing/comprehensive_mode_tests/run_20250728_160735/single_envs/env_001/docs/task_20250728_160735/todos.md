# Project Tasks

## Project Setup & Core Implementation
- [ ] Initialize project structure
  - Create the calculator/ directory with __init__.py, core.py, and cli.py files. Set up the basic package structure with proper __version__ in __init__.py
- [ ] Implement core arithmetic functions
  - Create the four arithmetic functions in core.py: add(a, b), subtract(a, b), multiply(a, b), and divide(a, b) with proper type checking and ZeroDivisionError handling
- [ ] Add type validation to core functions
  - Implement isinstance checks in all core functions to raise TypeError for non-numeric inputs, ensuring consistent float return types

## Testing Infrastructure
- [ ] Set up pytest configuration
  - Create tests/ directory with __init__.py, configure pytest in requirements.txt, and set up basic test structure
- [ ] Write unit tests for addition (can work in parallel)
  - Create comprehensive test cases for add() function covering positive, negative, zero, and floating-point numbers
- [ ] Write unit tests for subtraction (can work in parallel)
  - Create comprehensive test cases for subtract() function covering various number combinations and edge cases
- [ ] Write unit tests for multiplication (can work in parallel)
  - Create comprehensive test cases for multiply() function including zero multiplication and negative numbers
- [ ] Write unit tests for division (can work in parallel)
  - Create comprehensive test cases for divide() function including division by zero, normal division, and edge cases
- [ ] Write exception handling tests (can work in parallel)
  - Create tests for TypeError on non-numeric inputs and ZeroDivisionError for division by zero in all core functions

## CLI Interface Development
- [ ] Create CLI menu system
  - Implement the main menu loop in cli.py that displays options 1-5 (Add, Subtract, Multiply, Divide, Quit) and handles user selection
- [ ] Implement input validation helper
  - Create get_number(prompt: str) -> float function that handles invalid input with try/except and re-prompts until valid numeric input is received
- [ ] Integrate core functions with CLI
  - Wire up menu choices to corresponding core functions, passing validated inputs and displaying results
- [ ] Implement error handling in CLI
  - Add proper exception handling for ZeroDivisionError and TypeError with user-friendly error messages

## Documentation & Packaging
- [ ] Create README.md (can work in parallel)
  - Write comprehensive README with installation instructions, usage examples, and testing commands
- [ ] Set up requirements.txt (can work in parallel)
  - Create requirements.txt with pytest>=7.0 as the only dependency for development
- [ ] Create setup.py for development install (can work in parallel)
  - Add minimal setup.py to enable pip install -e . for development purposes
- [ ] Add project configuration files (can work in parallel)
  - Create .gitignore, tox.ini for flake8 configuration, and any other necessary project files

## Quality Assurance & Final Polish
- [ ] Run comprehensive test suite
  - Execute pytest with coverage reporting to ensure 100% coverage of core.py and all tests pass
- [ ] Perform static code analysis
  - Run flake8 on the codebase to ensure zero warnings and adherence to PEP 8 standards
- [ ] Manual end-to-end testing
  - Test the complete user workflow: 2+3 calculation, 5/0 error handling, and graceful exit
- [ ] Final code review and cleanup
  - Review all code for consistency, add missing docstrings, and ensure clean, readable implementation

