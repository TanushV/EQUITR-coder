# Project Tasks

## Project Setup & Configuration
- [ ] Initialize project structure
  - Create the basic directory structure: calculator/ package directory, tests/ directory, and all required files (__init__.py, __main__.py, core.py, cli.py, test_core.py, test_cli.py)
- [ ] Set up Python environment (can work in parallel)
  - Create virtual environment (.venv), upgrade pip, and create requirements-dev.txt with pytest, coverage, and flake8 dependencies
- [ ] Configure packaging files (can work in parallel)
  - Create pyproject.toml with project metadata, dependencies, and console script entry point. Create .gitignore file for Python artifacts
- [ ] Create README.md (can work in parallel)
  - Write comprehensive README with installation instructions, usage examples, testing commands, and project description

## Core Business Logic Implementation
- [ ] Implement arithmetic functions in core.py
  - Create the four pure arithmetic functions: add(a, b), subtract(a, b), multiply(a, b), divide(a, b) with proper type hints, docstrings, and error handling for division by zero
- [ ] Add comprehensive docstrings and type hints (can work in parallel)
  - Ensure all functions in core.py have complete docstrings explaining parameters, return values, and exceptions raised. Add proper type annotations using Union[int, float] for numeric inputs

## Core Module Testing
- [ ] Create test_core.py with unit tests
  - Implement comprehensive unit tests for all four arithmetic functions using pytest. Include tests for positive numbers, negative numbers, floats, zero values, and edge cases
- [ ] Test division by zero error handling (can work in parallel)
  - Create specific test cases for divide() function to ensure it properly raises ValueError with the exact message 'Cannot divide by zero' when denominator is zero
- [ ] Test edge cases and boundary conditions (can work in parallel)
  - Add tests for very large numbers, very small numbers, floating point precision issues, and type validation for the core arithmetic functions

## CLI Interface Implementation
- [ ] Implement CLI menu system
  - Create display_menu() function to show numbered options (Add, Subtract, Multiply, Divide, Exit) and read_choice() function to handle user input validation for menu selection
- [ ] Implement number input handling (can work in parallel)
  - Create read_number(prompt) function that repeatedly prompts user until a valid float is entered, with appropriate error messages for invalid input
- [ ] Implement main CLI loop (can work in parallel)
  - Create main() function that orchestrates the interactive calculator loop: display menu, get operation choice, get two numbers, perform calculation, display result, and handle exit
- [ ] Add error handling in CLI (can work in parallel)
  - Implement try-except blocks in CLI to handle ValueError from divide() function and display user-friendly error messages for division by zero

## CLI Testing & Validation
- [ ] Create test_cli.py with CLI unit tests
  - Implement unit tests for CLI module using unittest.mock to patch input() and print() functions. Test menu display, input validation, calculation flows, and error scenarios
- [ ] Test interactive flows with mocked inputs (can work in parallel)
  - Create tests that simulate complete user sessions with various input sequences to verify correct behavior for each operation and error handling paths
- [ ] Test input validation in CLI (can work in parallel)
  - Add specific tests for invalid menu choices and invalid number inputs to ensure the CLI properly re-prompts users until valid input is provided

## Quality Assurance & Release
- [ ] Run test suite and generate coverage report
  - Execute pytest with coverage reporting to ensure all tests pass and achieve minimum 95% line coverage. Generate and review coverage report for any gaps
- [ ] Run static analysis with flake8 (can work in parallel)
  - Execute flake8 on both calculator/ and tests/ directories to ensure code follows PEP 8 standards and resolve any warnings or style issues
- [ ] Perform manual QA testing (can work in parallel)
  - Manually test all functional requirements (FR-1 through FR-10) by running the calculator interactively and verifying each acceptance criterion is met
- [ ] Create final release package (can work in parallel)
  - Install the package locally with pip install ., verify console script entry point works, tag repository with v1.0.0, and prepare final release

