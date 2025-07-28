# Project Tasks

## Project Setup & Infrastructure
- [ ] Initialize project structure
  - Create the directory structure as specified in TR-2: calculator/ with subdirectories calculator/, tests/, and .github/workflows/. Add empty __init__.py files and .gitignore
- [ ] Set up Python virtual environment (can work in parallel)
  - Create and activate Python virtual environment (python -m venv venv) to ensure clean dependency management
- [ ] Create GitHub repository (can work in parallel)
  - Initialize git repository, create initial commit with project skeleton, and set up remote repository on GitHub

## Core Calculator Implementation
- [ ] Implement DivisionByZeroError exception
  - Create custom DivisionByZeroError class in calculator/core.py that subclasses ValueError for division by zero handling
- [ ] Implement add function (can work in parallel)
  - Create add(a, b) function in calculator/core.py that accepts int/float and returns int/float with proper type hints
- [ ] Implement subtract function (can work in parallel)
  - Create subtract(a, b) function in calculator/core.py that accepts int/float and returns int/float with proper type hints
- [ ] Implement multiply function (can work in parallel)
  - Create multiply(a, b) function in calculator/core.py that accepts int/float and returns int/float with proper type hints
- [ ] Implement divide function (can work in parallel)
  - Create divide(a, b) function in calculator/core.py that accepts int/float, returns int/float, and raises DivisionByZeroError when b=0
- [ ] Add type hints and documentation (can work in parallel)
  - Add comprehensive type hints using Union[int, float] and docstrings to all core functions for clarity

## Unit Testing Suite
- [ ] Set up test structure
  - Create tests/test_core.py with proper unittest.TestCase structure and necessary imports for testing core functionality
- [ ] Test add function (can work in parallel)
  - Write comprehensive unit tests for add() covering positive numbers, negative numbers, zero, floats, and mixed int/float combinations
- [ ] Test subtract function (can work in parallel)
  - Write comprehensive unit tests for subtract() covering various scenarios including edge cases like subtracting negative numbers
- [ ] Test multiply function (can work in parallel)
  - Write comprehensive unit tests for multiply() including zero multiplication, negative numbers, and float precision
- [ ] Test divide function (can work in parallel)
  - Write unit tests for divide() covering normal division, division with floats, and verify DivisionByZeroError is raised when dividing by zero
- [ ] Test DivisionByZeroError exception (can work in parallel)
  - Create specific tests to verify DivisionByZeroError is properly raised and is a subclass of ValueError
- [ ] Achieve 100% test coverage
  - Run coverage analysis and ensure 100% line coverage for calculator/core.py, adding any missing test cases

## CLI Interface Development
- [ ] Implement input parsing function
  - Create parse_input(line: str) function in calculator.py that splits input string and validates format, raising ValueError for invalid input
- [ ] Implement REPL main loop (can work in parallel)
  - Create main() function in calculator.py that implements the interactive REPL loop, handles 'exit' command, and manages program flow
- [ ] Implement result formatting (can work in parallel)
  - Add logic to format results as integers when no fractional part exists, otherwise display as float with full precision
- [ ] Add error handling for CLI (can work in parallel)
  - Implement try-catch blocks in CLI to handle DivisionByZeroError, ValueError (invalid input), and KeyboardInterrupt gracefully
- [ ] Add CLI usage messages (can work in parallel)
  - Implement appropriate user feedback messages for invalid input, division by zero errors, and welcome/goodbye messages

## CI/CD & Documentation
- [ ] Create GitHub Actions workflow
  - Set up .github/workflows/ci.yml with Python 3.8+ testing, flake8 linting, unittest discovery, and coverage reporting with 100% requirement
- [ ] Configure flake8 linting (can work in parallel)
  - Set up flake8 configuration to ensure code style compliance with default settings across all Python files
- [ ] Create comprehensive README (can work in parallel)
  - Write README.md with installation instructions, usage examples, example session transcript, and CI status badge
- [ ] Final integration testing
  - Perform end-to-end testing of the complete application, verifying all functional requirements FR-1 through FR-6 work correctly
- [ ] Tag version 1.0.0 (can work in parallel)
  - Create git tag v1.0.0 after all tests pass and CI is green, marking the stable release

