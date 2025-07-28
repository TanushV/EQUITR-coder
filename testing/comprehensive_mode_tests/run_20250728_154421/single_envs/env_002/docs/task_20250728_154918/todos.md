# Project Tasks

## Project Setup & Configuration
- [ ] Initialize Git repository and project structure
  - Create calculator directory, initialize git repo, create tests/ and .github/workflows/ directories, add .gitignore with Python template
- [ ] Create project configuration files (can work in parallel)
  - Create requirements.txt with pytest, pytest-cov, and ruff dependencies. Create pyproject.toml with ruff and coverage configuration settings
- [ ] Set up GitHub Actions CI pipeline (can work in parallel)
  - Create .github/workflows/ci.yml with Python 3.8-3.11 matrix, steps for linting with ruff and running pytest with coverage

## Core Arithmetic Logic
- [ ] Implement operations.py with arithmetic functions
  - Create operations.py file with four pure functions: add(a: float, b: float) -> float, subtract(a: float, b: float) -> float, multiply(a: float, b: float) -> float, divide(a: float, b: float) -> float. Include proper type hints and docstrings
- [ ] Create comprehensive unit tests for operations (can work in parallel)
  - Create tests/test_operations.py with pytest test cases for all four arithmetic functions. Include parametrized tests for positive, negative, float, int, zero, and large number cases. Ensure 100% coverage of operations.py
- [ ] Test division by zero error handling (can work in parallel)
  - Add specific test case to verify divide(5, 0) raises ZeroDivisionError with proper exception handling

## CLI Interface Development
- [ ] Create calculator.py CLI entry point
  - Create calculator.py with main() function, shebang line, and proper CLI structure. Include infinite while loop for continuous operation until user exits
- [ ] Implement menu display and user input handling (can work in parallel)
  - Create print_menu() function to display operation choices 1-5. Implement get_number(prompt: str) -> float function with try/except for input validation and re-prompting on invalid input
- [ ] Implement operation dispatch and error handling (can work in parallel)
  - Create operations dictionary mapping choices to functions. Implement dispatch logic to call appropriate operation based on user choice. Handle ZeroDivisionError with friendly error message and return to menu

## Testing & Quality Assurance
- [ ] Run local testing and coverage verification
  - Execute pytest locally to ensure all tests pass. Run pytest --cov=operations tests/ to verify 100% line coverage for operations.py. Fix any failing tests or coverage gaps
- [ ] Perform manual CLI testing (can work in parallel)
  - Test all functional requirements manually: FR-1 through FR-10. Verify menu displays correctly, operations work with various inputs, division by zero shows proper error, and exit works cleanly
- [ ] Run linting and code style checks (can work in parallel)
  - Execute ruff . to check for PEP 8 compliance and code style issues. Fix any linting errors or warnings to ensure clean codebase

## Documentation & Final Polish
- [ ] Create comprehensive README.md
  - Write README.md with installation instructions, usage examples, testing commands, and project overview. Include badges for CI status and coverage
- [ ] Make calculator.py executable and add final touches (can work in parallel)
  - Add shebang line #!/usr/bin/env python3 to calculator.py and run chmod +x to make it executable. Verify the application can be run directly with ./calculator.py
- [ ] Push to GitHub and verify CI pipeline (can work in parallel)
  - Push all code to GitHub main branch. Verify GitHub Actions CI pipeline runs successfully with green status for all Python versions (3.8-3.11)

