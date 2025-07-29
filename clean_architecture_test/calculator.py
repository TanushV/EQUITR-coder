#!/usr/bin/env python3
"""
Calculator Program

A command-line calculator that performs basic arithmetic operations on decimal numbers.
Provides an interactive REPL (Read-Eval-Print Loop) interface for users to perform
addition, subtraction, multiplication, and division operations.

Usage:
    Run the program with: python calculator.py
    Enter expressions in the format: <number> <operator> <number>
    Supported operators: +, -, *, /
    Type 'exit' or 'quit' to terminate the program.

Examples:
    2 + 3
    3.5 * -2.1
    7 / 0  # Will show division by zero error
"""

# Constants will be defined in the next todo
VALID_OPERATORS = {"+", "-", "*", "/"}

# Arithmetic functions will be implemented in subsequent todos

def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Return the difference between two numbers."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""
    return a * b

def divide(a: float, b: float) -> float:
    """Return the quotient of two numbers.
    
    Raises:
        ZeroDivisionError: If the divisor (b) is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero is undefined")
    return a / b

def format_result(value: float) -> str:
    """Format a float value for display, removing unnecessary decimal places."""
    return f"{value:g}"

def print_usage() -> None:
    """Display usage instructions for the calculator."""
    print("Usage: <number> <+,-,*,/> <number>")
    print("Example: 2 + 3")
    print("Type 'exit' or 'quit' to terminate.")

def parse_input(raw: str) -> tuple[float, str, float]:
    """Parse and validate user input.
    
    Args:
        raw: The raw input string from the user.
        
    Returns:
        A tuple of (left_operand, operator, right_operand).
        
    Raises:
        ValueError: If the input format is invalid or contains non-numeric values.
    """
    tokens = raw.strip().split()
    
    if len(tokens) != 3:
        raise ValueError("Invalid format. Expected: <number> <operator> <number>")
    
    try:
        left = float(tokens[0])
        right = float(tokens[2])
    except ValueError as e:
        invalid_token = str(e).split("'")[-2] if "'" in str(e) else "input"
        raise ValueError(f"Invalid number '{invalid_token}'. Please enter valid numbers.")
    
    op = tokens[1]
    if op not in VALID_OPERATORS:
        raise ValueError(f"Invalid operator '{op}'. Supported operators: +, -, *, /")
    
    return left, op, right

def evaluate(a: float, op: str, b: float) -> float:
    """Evaluate an arithmetic expression.
    
    Args:
        a: The left operand.
        op: The arithmetic operator (+, -, *, /).
        b: The right operand.
        
    Returns:
        The result of the arithmetic operation.
        
    Raises:
        ZeroDivisionError: If attempting to divide by zero.
    """
    if op == "+":
        return add(a, b)
    elif op == "-":
        return subtract(a, b)
    elif op == "*":
        return multiply(a, b)
    elif op == "/":
        return divide(a, b)
    else:
        # This should never happen if parse_input is working correctly
        raise ValueError(f"Unsupported operator: {op}")

def repl_loop() -> None:
    """Run the interactive Read-Eval-Print Loop."""
    print("Welcome to Calculator!")
    print("Enter expressions like: 2 + 3")
    print("Type 'exit' or 'quit' to terminate.\n")
    
    while True:
        try:
            raw = input("calc> ")
            
            if raw.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break
            
            left, op, right = parse_input(raw)
            result = evaluate(left, op, right)
            
            print(f"{format_result(left)} {op} {format_result(right)} = {format_result(result)}")
            
        except ValueError as ve:
            print(f"Error: {ve}")
            print_usage()
        except ZeroDivisionError as zde:
            print(f"Error: {zde}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            print_usage()

def main() -> None:
    """Main entry point for the calculator program."""
    repl_loop()

if __name__ == "__main__":
    main()