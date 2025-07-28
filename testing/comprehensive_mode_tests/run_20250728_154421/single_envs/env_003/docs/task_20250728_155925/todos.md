# Project Tasks

## Project Setup & Structure
- [ ] Initialize project repository and directory structure
  - Create the calculator project directory with the specified structure: calculator/ package directory, tests/ directory, and root-level files. Create all necessary __init__.py files to make directories proper Python packages.
- [ ] Create requirements.txt and packaging files (can work in parallel)
  - Create requirements.txt with pytest==7.*, setup.cfg with metadata and console script entry point, and optional pyproject.toml for modern Python packaging.
- [ ] Set up .gitignore and initial README.md (can work in parallel)
  - Create .gitignore file for Python projects and initial README.md with project title and basic structure that will be filled out later.

## Core Arithmetic Implementation
- [ ] Implement operations.py with four arithmetic functions
  - Create calculator/operations.py file with four pure functions: add(a: float, b: float) -> float, subtract(a: float, b: float) -> float, multiply(a: float, b: float) -> float, and divide(a: float, b: float) -> float. Include proper docstrings and ZeroDivisionError handling in divide function.
- [ ] Write comprehensive unit tests for operations.py (can work in parallel)
  - Create tests/test_operations.py with pytest test cases covering: positive numbers, negative numbers, floating-point numbers, zero values, edge cases like very large/small numbers, and ZeroDivisionError for divide function. Ensure 100% line coverage.
- [ ] Add type hints and documentation to operations.py (can work in parallel)
  - Ensure all functions in operations.py have proper type hints, comprehensive docstrings following PEP 257, and are PEP 8 compliant. Run flake8 to verify code style.

## CLI Interface Development
- [ ] Implement CLI REPL loop in cli.py
  - Create calculator/cli.py with main() function that implements the REPL (Read-Eval-Print Loop). Include welcome message, input prompts for first number, operator, and second number, and proper formatting of results as 'a op b = result'.
- [ ] Implement input validation and error handling (can work in parallel)
  - Add input validation functions in cli.py to handle: non-numeric input (ValueError), invalid operators, and division by zero (ZeroDivisionError). Ensure graceful error messages and re-prompting without crashing.
- [ ] Implement exit command handling (can work in parallel)
  - Add support for exit commands (q, quit, exit) at any prompt. Ensure clean program termination with goodbye message when user chooses to exit.
- [ ] Create __main__.py for module execution (can work in parallel)
  - Create calculator/__main__.py that imports and calls cli.main() to enable 'python -m calculator' execution pattern.

## Testing & Quality Assurance
- [ ] Write comprehensive CLI tests
  - Create tests/test_cli.py with pytest test cases using monkeypatch to simulate user input and capsys to capture output. Test cases should cover: valid calculations, invalid numeric input, invalid operators, division by zero, exit commands at different prompts, and welcome/goodbye messages.
- [ ] Achieve 100% test coverage (can work in parallel)
  - Run pytest with coverage reporting to ensure 100% line coverage for both operations.py and cli.py. Add any missing test cases to achieve full coverage.
- [ ] Code style and linting compliance (can work in parallel)
  - Run black for code formatting, flake8 for linting, and ensure all code is PEP 8 compliant. Fix any style issues identified by these tools.

## Documentation & Final Polish
- [ ] Complete README.md documentation
  - Write comprehensive README.md including: project description, installation instructions (pip install -e .), usage examples (calculator command), how to run tests (pytest), supported operations, and exit commands. Include example session transcript.
- [ ] Test end-to-end functionality (can work in parallel)
  - Perform manual testing of the complete application: install via pip install -e ., run calculator command, test all operations with various inputs, verify error handling, and test exit functionality. Document any issues found.
- [ ] Final packaging verification (can work in parallel)
  - Verify that the console script entry point works correctly, all tests pass with 100% coverage, and the application can be successfully installed and run from a fresh virtual environment.

