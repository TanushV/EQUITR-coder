# Project Tasks

## Core Implementation
- [ ] Create project structure and main file
  - Create calculator.py file with proper shebang, imports, and main entry point structure. Add the if __name__ == "__main__" guard and basic file layout as specified in design.md.
- [ ] Implement input reading functions (can work in parallel)
  - Create read_number(prompt) function to read and validate numeric input with try/except for ValueError. Create read_operation() function to read and validate operation choice against VALID_OPERATIONS set.
- [ ] Implement calculation logic (can work in parallel)
  - Create calculate(a, b, operation) function that performs addition or subtraction based on the operation parameter. Use simple if/else structure as specified in design.
- [ ] Implement output functions (can work in parallel)
  - Create display_result(value) function to print formatted results (e.g., 'Result: 8'). Create display_error(reason) function to print error messages and exit with code 1 using sys.exit(1).

## Integration & Testing
- [ ] Wire components in main function
  - Implement the main() function to orchestrate the entire flow: call read_number() twice, call read_operation(), call calculate(), and call display_result() or display_error() as appropriate.
- [ ] Test success scenarios (can work in parallel)
  - Test the calculator with valid inputs: echo -e "5\n3\nadd" | python calculator.py should print 'Result: 8', and echo -e "10\n4\nsubtract" | python calculator.py should print 'Result: 6'.
- [ ] Test error scenarios (can work in parallel)
  - Test error handling: echo -e "abc\n3\nadd" | python calculator.py should print 'Error: Invalid number', and echo -e "5\n3\nmultiply" | python calculator.py should print 'Error: Invalid operation'.

## Documentation & Polish
- [ ] Add comprehensive docstrings (can work in parallel)
  - Add detailed docstrings to all functions explaining parameters, return values, and behavior. Include module-level docstring with usage instructions as shown in design.md.
- [ ] Final code review and cleanup (can work in parallel)
  - Review the entire calculator.py file for code quality, consistency, and adherence to Python style guidelines. Ensure all requirements from requirements.md are met.
- [ ] Create README with usage instructions (can work in parallel)
  - Create a simple README.md file documenting how to run the calculator, expected inputs, and example usage commands for both success and error cases.

