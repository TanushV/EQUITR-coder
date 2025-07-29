# Project Tasks

## Core Implementation
- [ ] Create utils.py file with basic structure
  - Create the utils.py file with proper UTF-8 encoding, add module docstring, and set up the basic file structure with function stubs and entry point guard
- [ ] Implement is_even function (can work in parallel)
  - Create the is_even function that takes an integer and returns True if even, False if odd. Include proper type hints, docstring, and use modulo operator for efficiency
- [ ] Implement reverse_string function (can work in parallel)
  - Create the reverse_string function that takes a string and returns the reversed string. Include proper type hints, docstring, and use Python slice notation for reversal

## Testing & Validation
- [ ] Implement main function with test cases
  - Create the main() function that runs deterministic tests for both is_even and reverse_string functions. Include clear pass/fail messages and test edge cases like 0, negative numbers, empty strings, and single characters
- [ ] Add entry point guard (can work in parallel)
  - Add the if __name__ == '__main__': guard to ensure main() only runs when executed directly, not when imported as a module
- [ ] Verify PEP 8 compliance (can work in parallel)
  - Review the entire file for PEP 8 compliance including line length ≤ 79 characters, proper spacing, naming conventions, and overall code style

## Final Verification
- [ ] Run acceptance tests
  - Execute all required acceptance tests: run 'python utils.py' to verify main() works, test import functionality with 'python -c "from utils import is_even, reverse_string; print(is_even(2), reverse_string('abc'))"', and ensure both produce expected outputs
- [ ] Optional lint check (can work in parallel)
  - If flake8 is available, run 'flake8 utils.py' to verify zero style violations. Fix any issues found to ensure clean, professional code quality
- [ ] Final code review and cleanup (can work in parallel)
  - Perform final review of the complete utils.py file, ensure all requirements are met, verify file size is ≤ 50 lines (excluding blanks/comments), and confirm all functions work correctly with the provided test cases

