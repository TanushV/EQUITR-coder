# Project Tasks

## Project Setup & Configuration
- [ ] Initialize project structure
  - Create the calculator directory structure with all required folders and files as specified in the design. This includes calculator/, tests/, and configuration files like pyproject.toml and requirements.txt
- [ ] Set up build configuration
  - Create pyproject.toml with proper PEP 517 build configuration, project metadata, and Python version requirements. Also create empty requirements.txt as placeholder
- [ ] Configure development environment (can work in parallel)
  - Set up virtual environment, install development dependencies (flake8, pytest if needed), and configure pip install -e . for editable installs

## Core Arithmetic Implementation
- [ ] Create exceptions module
  - Implement custom exception classes in calculator/exceptions.py: CalculatorError (base), InvalidInputError, and DivisionByZeroError as specified in the design
- [ ] Implement arithmetic operations
  - Create calculator/operations.py with four pure functions: add(a, b), sub(a, b), mul(a, b), and div(a, b) that perform basic arithmetic operations on float inputs
- [ ] Write unit tests for operations (can work in parallel)
  - Create tests/test_operations.py with comprehensive unit tests for all four arithmetic operations, covering positive/negative numbers, floats, and edge cases

## Input Parsing & Validation
- [ ] Implement input parsing logic
  - Create parse_input() function in calculator/cli.py that uses regex to parse space-separated expressions into (float, float, str) tuple, handling scientific notation and validating format
- [ ] Write unit tests for input parsing (can work in parallel)
  - Create tests/test_parse_input.py with unit tests covering valid inputs (integers, floats, scientific notation), invalid formats, edge cases, and operator validation
- [ ] Implement calculate function
  - Create calculate() function in calculator/cli.py that takes parsed inputs (a, b, op) and returns result using operations module, with proper error handling for division by zero and invalid operators

## CLI Interface & User Experience
- [ ] Implement argument parsing
  - Create main() function in calculator/cli.py with argparse to handle both interactive mode (no args) and command-line mode (3 positional args), plus --help flag
- [ ] Implement error handling and messaging (can work in parallel)
  - Add comprehensive error handling in main() to catch CalculatorError exceptions, print user-friendly messages to stderr, and exit with appropriate codes (0 for success, 1 for errors)
- [ ] Add continuous operation mode (can work in parallel)
  - Implement optional REPL loop in main() that prompts 'Continue? (y/n)' after each calculation, allowing users to perform multiple calculations in one session
- [ ] Write CLI integration tests (can work in parallel)
  - Create tests/test_cli.py with unit tests for main() function, covering both interactive and argument modes, error scenarios, and help flag functionality

## Testing & Quality Assurance
- [ ] Set up test runner configuration (can work in parallel)
  - Configure unittest discovery in tests/__init__.py and ensure python -m unittest discover -s tests works correctly from project root
- [ ] Achieve 100% test coverage (can work in parallel)
  - Ensure all branches of calculate() and parse_input() are covered by tests. Run coverage report to verify 100% coverage target is met
- [ ] Set up linting configuration (can work in parallel)
  - Configure flake8 or pylint to ensure code quality. Create setup.cfg or .flake8 file with appropriate rules, and ensure zero warnings across calculator/ and tests/ directories
- [ ] Create comprehensive test suite (can work in parallel)
  - Review and expand test cases to cover all edge cases including boundary values, malformed inputs, and error conditions as specified in requirements

## Documentation & Distribution
- [ ] Write comprehensive README (can work in parallel)
  - Create README.md with installation instructions (pip install -e .), usage examples for both interactive and argument modes, testing instructions (python -m unittest), and project description
- [ ] Create GitHub Actions CI workflow (can work in parallel)
  - Set up .github/workflows/ci.yml for continuous integration that runs linting (flake8) and unit tests on push/PR for Python 3.8+
- [ ] Final packaging verification (can work in parallel)
  - Test complete distribution: verify python -m calculator.cli works from any directory after pip install -e ., test --help flag, and validate all entry points work correctly

