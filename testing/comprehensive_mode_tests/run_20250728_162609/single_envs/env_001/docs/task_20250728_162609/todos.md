# Project Tasks

## Project Setup & Configuration
- [ ] Initialize project structure
  - Create the basic project directory structure including calculator/ package directory, tests/ directory, and all necessary __init__.py files. Create .gitignore file with Python-specific patterns.
- [ ] Setup build configuration
  - Create pyproject.toml with project metadata, dependencies, build system configuration, console script entry point for 'calc', and optional test dependencies.
- [ ] Create README and documentation (can work in parallel)
  - Write comprehensive README.md with installation instructions, usage examples for both interactive and single-expression modes, and development setup guide.

## Core Arithmetic Implementation
- [ ] Implement core arithmetic functions
  - Create calculator/core.py with four pure functions: add(a: float, b: float) -> float, subtract(a: float, b: float) -> float, multiply(a: float, b: float) -> float, and divide(a: float, b: float) -> float. Include proper type annotations and docstrings.
- [ ] Create exception hierarchy (can work in parallel)
  - Implement calculator/exceptions.py with custom exception classes: CalculatorError (base), DivisionByZeroError, InvalidOperandError, and UnsupportedOperatorError. Ensure all inherit from CalculatorError.
- [ ] Add division by zero handling
  - Implement division by zero detection in divide() function that raises DivisionByZeroError with appropriate message when b == 0.

## CLI Interface Development
- [ ] Implement argument parser
  - Create _parse_args() function in cli.py using argparse to handle single-expression mode with three arguments: operand1, operator, operand2. Include proper validation and help text.
- [ ] Build interactive REPL loop
  - Implement _interactive_loop() function that provides interactive calculator mode with input prompts, handles 'exit'/'quit' commands, 'help' command, and processes expressions in format 'number operator number'.
- [ ] Create main CLI entry point
  - Implement main() function that serves as the CLI entry point, determines whether to run in single-expression mode (with arguments) or interactive mode (no arguments), handles all exceptions, and returns appropriate exit codes.
- [ ] Add input validation and formatting (can work in parallel)
  - Implement input validation for numeric operands and supported operators in both CLI modes. Add result formatting to display at least 6 decimal places with proper trailing zero removal.

## Testing Suite
- [ ] Create core arithmetic tests
  - Write comprehensive unit tests in tests/test_core.py using pytest with parametrized tests covering all arithmetic operations, edge cases (zero, negative numbers, floating point precision), and exception scenarios including division by zero.
- [ ] Implement CLI argument parsing tests (can work in parallel)
  - Create tests in tests/test_cli.py for argument parsing functionality including valid inputs, invalid operands, unsupported operators, and help text display.
- [ ] Add CLI integration tests (can work in parallel)
  - Write integration tests for CLI using pytest-console-scripts to test both single-expression mode and interactive mode, including exit codes, error messages, and edge cases.
- [ ] Achieve 100% test coverage
  - Run pytest with coverage reporting to ensure 100% branch coverage on core.py and cli.py. Add any missing test cases to achieve coverage target.

## CI/CD & Packaging
- [ ] Setup GitHub Actions workflow
  - Create .github/workflows/ci.yml that runs tests on Python 3.8-3.12 on ubuntu-latest, installs the package, runs pytest with coverage reporting, and enforces minimum 95% coverage requirement.
- [ ] Test packaging and installation (can work in parallel)
  - Verify that pip install . works correctly, the console script 'calc' is properly exposed, and can be executed from command line in both interactive and single-expression modes.
- [ ] Add final polish and validation (can work in parallel)
  - Complete final validation including docstrings, --help text verification, manual testing of all requirements, and final coverage check to ensure all success criteria are met.

