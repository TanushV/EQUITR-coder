# Project Tasks

## Project Setup & Structure
- [ ] Initialize project repository structure
  - Create the main project directory with subdirectories: calc/, tests/, and .github/workflows/. Create empty __init__.py files in calc/ and tests/ directories.
- [ ] Create Makefile with standard targets (can work in parallel)
  - Create Makefile with targets: test (runs unittest), lint (flake8), and run (python calculator.py). Include .PHONY declarations for all targets.
- [ ] Create requirements.txt and README.md (can work in parallel)
  - Create empty requirements.txt (stdlib only) and comprehensive README.md with installation instructions, usage examples for both interactive and single-expression modes, and testing instructions.
- [ ] Set up GitHub Actions CI workflow (can work in parallel)
  - Create .github/workflows/ci.yml for continuous integration that runs tests on Python 3.8+ and performs linting with flake8.

## Core Engine Implementation
- [ ] Implement add function in calc/engine.py
  - Create add(a: float, b: float) -> float function that adds two numbers. Include TypeError handling for non-numeric inputs. Write comprehensive unit tests covering positive, negative, and floating-point numbers.
- [ ] Implement subtract function in calc/engine.py (can work in parallel)
  - Create subtract(a: float, b: float) -> float function that subtracts b from a. Include TypeError handling for non-numeric inputs. Write comprehensive unit tests.
- [ ] Implement multiply function in calc/engine.py (can work in parallel)
  - Create multiply(a: float, b: float) -> float function that multiplies two numbers. Include TypeError handling for non-numeric inputs. Write comprehensive unit tests.
- [ ] Implement divide function in calc/engine.py (can work in parallel)
  - Create divide(a: float, b: float) -> float function that divides a by b. Include TypeError for non-numeric inputs and ZeroDivisionError when b is zero. Write comprehensive unit tests including edge cases.
- [ ] Achieve 100% test coverage for engine module
  - Run coverage analysis on calc/engine.py and ensure all lines are covered by tests. Add any missing test cases for edge conditions or error paths.

## CLI Interface Development
- [ ] Implement input tokenization in calc/cli.py
  - Create tokenize(line: str) -> list[str] function using shlex.split to safely parse user input. Write unit tests for various input formats including quoted strings and edge cases.
- [ ] Implement token validation in calc/cli.py (can work in parallel)
  - Create validate_tokens(tokens: list[str]) -> tuple[float, str, float] function that validates input format and converts strings to floats. Raise ValueError for malformed input. Write comprehensive unit tests.
- [ ] Implement operator dispatch in calc/cli.py (can work in parallel)
  - Create dispatch(a: float, op: str, b: float) -> float function that maps operator strings (+, -, *, /) to corresponding engine functions. Write unit tests for all operators and error cases.
- [ ] Implement print_help function in calc/cli.py (can work in parallel)
  - Create print_help(ostream) function that displays usage instructions, supported operators, and examples. Ensure output is properly formatted and user-friendly.
- [ ] Implement CLI argument parsing
  - Create parse_cli_args(argv: list[str]) function to handle both interactive mode (no args) and single-expression mode (3 args: num1, op, num2). Write unit tests for both modes and error cases.

## Interactive Mode & Main Entry
- [ ] Implement interactive REPL loop in calc/cli.py
  - Create interactive_loop(istream, ostream) function that provides a REPL interface with 'calc> ' prompt. Handle 'help', 'exit', and EOF (Ctrl-D) gracefully. Write unit tests using StringIO for input/output simulation.
- [ ] Create main entry point in calculator.py (can work in parallel)
  - Create calculator.py that imports and calls calc.cli.main function. Handle sys.argv properly and ensure correct exit codes (0 for success, 1 for CLI errors).
- [ ] Implement main function in calc/cli.py (can work in parallel)
  - Create main(argv: list[str]) -> int function that orchestrates the application flow. Delegate to single-expression mode or interactive mode based on argument count. Return appropriate exit codes.
- [ ] Integrate error handling and formatting
  - Ensure all errors are caught at the CLI layer, formatted appropriately (e.g., 'Error: division by zero'), and printed to stderr. Results should be displayed with 6 decimal places precision.

## Testing & Quality Assurance
- [ ] Write comprehensive CLI unit tests
  - Create tests/test_cli.py with unit tests for all CLI functions including tokenization, validation, dispatch, and interactive mode. Use StringIO for testing input/output streams.
- [ ] Create integration tests for both modes (can work in parallel)
  - Write integration tests that verify end-to-end functionality for both single-expression mode (python calculator.py 3 + 4) and interactive mode. Test error scenarios and edge cases.
- [ ] Achieve 100% test coverage for CLI module (can work in parallel)
  - Run coverage analysis on calc/cli.py and ensure all lines are covered. Add missing tests for any uncovered branches or error paths.
- [ ] Set up linting and code formatting (can work in parallel)
  - Configure flake8 for linting and ensure all code follows PEP 8 standards. Run linting across all Python files and fix any issues.
- [ ] Final validation and documentation review
  - Perform final manual testing of all functional requirements (FR-1 through FR-9). Review README.md for completeness and accuracy. Ensure all acceptance criteria are met.

