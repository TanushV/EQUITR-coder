# todos.md

- [ ] Create `calculator.py` file with shebang (`#!/usr/bin/env python3`) and module-level docstring
- [ ] Define `VALID_OPERATORS = {"+", "-", "*", "/"}` constant at top of file
- [ ] Implement `add(a: float, b: float) -> float` function with docstring
- [ ] Implement `subtract(a: float, b: float) -> float` function with docstring
- [ ] Implement `multiply(a: float, b: float) -> float` function with docstring
- [ ] Implement `divide(a: float, b: float) -> float` function with docstring and ZeroDivisionError handling
- [ ] Implement `format_result(value: float) -> str` helper function to format floats nicely
- [ ] Implement `print_usage() -> None` function to display help text
- [ ] Implement `parse_input(raw: str) -> tuple[float, str, float]` function with validation
- [ ] Implement `evaluate(a: float, op: str, b: float) -> float` dispatcher function
- [ ] Implement `repl_loop() -> None` function with interactive loop and exit handling
- [ ] Implement `main() -> None` function that calls `repl_loop()`
- [ ] Add `if __name__ == "__main__":` guard to call `main()`
- [ ] Test all success criteria manually (SC-1 through SC-8)
- [ ] Run `python -m py_compile calculator.py` to verify syntax
- [ ] Review code for PEP 8 compliance and add any missing docstrings