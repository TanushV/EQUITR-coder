# Project Tasks

## Core Implementation
- [ ] Create calculator.py file with basic structure
  - Create the main calculator.py file with proper shebang, imports, and basic function stubs including main(), display_menu(), get_choice(), get_number(), and calculate() functions
- [ ] Implement display_menu() function (can work in parallel)
  - Create the display_menu() function that prints the numbered menu showing: 1) Add, 2) Subtract, 3) Multiply, 4) Divide, 5) Exit
- [ ] Implement get_choice() function (can work in parallel)
  - Create the get_choice() function that prompts 'Enter choice (1-5):', validates input is integer 1-5, and re-prompts on invalid entry
- [ ] Implement get_number() function (can work in parallel)
  - Create the get_number(prompt: str) function that takes a prompt string, handles float/int input with try/except for ValueError, and re-prompts on non-numeric input
- [ ] Implement calculate() function (can work in parallel)
  - Create the calculate(op: str, a: float, b: float) function that performs the four arithmetic operations based on op parameter and raises ZeroDivisionError for division by zero

## Integration & Main Loop
- [ ] Implement main() function with menu loop
  - Create the main() function that orchestrates the interactive loop: displays menu, gets choice, handles exit (choice 5), gets numbers, calls calculate(), displays results, and continues looping
- [ ] Add entry point and final integration
  - Add the if __name__ == '__main__': main() entry point, ensure all functions are properly integrated, and verify the complete program flow works together

## Testing & Validation
- [ ] Test basic functionality (can work in parallel)
  - Manually test all four arithmetic operations with sample inputs to verify correct results for addition, subtraction, multiplication, and division
- [ ] Test error handling scenarios (can work in parallel)
  - Test division by zero (should show error message), non-numeric input (should re-prompt), and invalid menu choices (should re-prompt)
- [ ] Test complete user flow (can work in parallel)
  - Test the complete user experience: menu display, multiple operations in sequence, exit functionality, and verify the program runs without crashing
- [ ] Verify PEP 8 compliance and syntax (can work in parallel)
  - Run python -m py_compile calculator.py to check for syntax errors, verify PEP 8 compliance, and ensure proper docstrings and comments are included

## Documentation & Final Polish
- [ ] Add comprehensive docstrings and comments (can work in parallel)
  - Add detailed docstrings to all functions including parameter descriptions and return values, add inline comments for complex logic, and ensure overall code clarity
- [ ] Create README.md with usage instructions (can work in parallel)
  - Create a simple README.md file containing instructions: 'Run python calculator.py and follow on-screen prompts' and basic project description
- [ ] Final code review and cleanup (can work in parallel)
  - Review the complete calculator.py file for any redundant code, improve variable names if needed, ensure consistent formatting, and prepare for final delivery

