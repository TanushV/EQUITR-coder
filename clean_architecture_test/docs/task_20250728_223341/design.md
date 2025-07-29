# Technical Design Document – Calculator Program (`calculator.py`)

---

## 1. System Architecture

```
┌────────────────────────────────────────────┐
│                calculator.py               │
│  ┌────────────────────────────────────┐   │
│  │            main()                   │   │
│  │  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  REPL Loop  │  │  Exit Hook  │ │   │
│  │  └─────┬───────┘  └─────┬───────┘ │   │
│  └────────┼────────────────┼─────────┘   │
│           │                │              │
│  ┌────────┼────────────────┼─────────┐   │
│  │        │                │         │   │
│  │  ┌─────┴──────┐  ┌────┴────┐    │   │
│  │  │  Parser    │  │  Eval   │    │   │
│  │  └─────┬──────┘  └────┬────┘    │   │
│  │        │              │          │   │
│  │  ┌─────┴──────────────┴────┐   │   │
│  │  │   Arithmetic Functions  │   │   │
│  │  └─────────────────────────┘   │   │
│  └──────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

---

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| **main()** | Entry point; orchestrates REPL loop | `main() -> None` |
| **repl_loop()** | Repeatedly prompts, parses, evaluates, prints | `repl_loop() -> None` |
| **parse_input(raw: str) -> tuple[float, str, float]** | Tokenize & validate user input | raises `ValueError` |
| **evaluate(a: float, op: str, b: float) -> float** | Dispatch to arithmetic functions | raises `ZeroDivisionError` |
| **add(a: float, b: float) -> float** | Addition | |
| **subtract(a: float, b: float) -> float** | Subtraction | |
| **multiply(a: float, b: float) -> float** | Multiplication | |
| **divide(a: float, b: float) -> float** | Division | raises `ZeroDivisionError` |
| **format_result(value: float) -> str** | Format float to ≤10 decimals, strip trailing zeros | |
| **print_usage() -> None** | Display concise help message | |

---

## 3. Data Flow

```
User Input
    │
    ▼
┌────────────────────────────┐
│        parse_input         │
│  1. split → tokens         │
│  2. validate length == 3   │
│  3. float(tokens[0])       │
│  4. validate operator      │
│  5. float(tokens[2])       │
└────────┬───────────────────┘
         │ tuple(float, str, float)
         ▼
┌────────────────────────────┐
│        evaluate            │
│  switch(op):               │
│    "+" → add(a,b)          │
│    "-" → subtract(a,b)     │
│    "*" → multiply(a,b)     │
│    "/" → divide(a,b)       │
└────────┬───────────────────┘
         │ float result
         ▼
┌────────────────────────────┐
│      format_result         │
│  f"{value:g}"              │
└────────┬───────────────────┘
         │ str
         ▼
      Display
```

---

## 4. Implementation Plan

| Step | Task | Deliverable |
|---|---|---|
| 1 | Skeleton file with shebang, docstring, imports | `calculator.py` (empty functions) |
| 2 | Implement arithmetic functions (`add`, `subtract`, `multiply`, `divide`) | Unit-testable functions |
| 3 | Implement `format_result` | Helper function |
| 4 | Implement `parse_input` | Tokenizer & validator |
| 5 | Implement `evaluate` | Dispatcher |
| 6 | Implement `print_usage` | Help text |
| 7 | Implement `repl_loop` | Interactive loop |
| 8 | Implement `main` | Entry point |
| 9 | Manual testing against success criteria | Pass SC-1..SC-8 |
| 10 | PEP 8 linting & final docstrings | Clean commit |

---

## 5. File Structure

```
calculator.py
├── Docstring (module-level)
├── Imports (none beyond stdlib)
├── Constants
│   └── VALID_OPERATORS = {"+", "-", "*", "/"}
├── Arithmetic Functions
│   ├── add
│   ├── subtract
│   ├── multiply
│   └── divide
├── Utility Functions
│   ├── format_result
│   └── print_usage
├── Core Logic
│   ├── parse_input
│   └── evaluate
├── REPL
│   └── repl_loop
└── Entry Point
    └── main()
    └── if __name__ == "__main__":
```

---

## 6. Pseudocode Snippets

### parse_input
```python
def parse_input(raw: str) -> tuple[float, str, float]:
    tokens = raw.strip().split()
    if len(tokens) != 3:
        raise ValueError("Invalid format")
    try:
        left = float(tokens[0])
        right = float(tokens[2])
    except ValueError as e:
        raise ValueError(f"Invalid number '{e.args[0].split()[-1]}'")
    op = tokens[1]
    if op not in VALID_OPERATORS:
        raise ValueError(f"Invalid operator '{op}'")
    return left, op, right
```

### repl_loop
```python
def repl_loop() -> None:
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
        except ZeroDivisionError:
            print("Error: Division by zero is undefined.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
```

---

## 7. Risk & Mitigation

| Risk | Mitigation |
|---|---|
| Floating-point precision artifacts | Use `format_result` with `g` specifier to hide insignificant digits. |
| Infinite loop on malformed input | `parse_input` raises `ValueError`; loop continues safely. |
| Unhandled exceptions | All exceptions caught inside `repl_loop`; program never crashes. |

---

## 8. Future Extensibility Hooks

- Replace `float` with `decimal.Decimal` for exact arithmetic (swap type in `parse_input`).
- Add unary operators by extending `parse_input` grammar.
- Export history to file by appending each equation to a list in `repl_loop`.

---

End of Design