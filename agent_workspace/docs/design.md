# design.md

## 1. System Architecture

```
┌─────────────────────────────┐
│        hello.py             │
│  ┌─────────────────────┐    │
│  │  Shebang (optional) │    │
│  ├─────────────────────┤    │
│  │  Main Logic         │    │
│  │  print("Hello...")  │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

The system is a single-file, zero-dependency Python script that leverages the built-in `print()` function to satisfy all functional requirements.

## 2. Components

| Component | Purpose | Lines of Code |
|-----------|---------|---------------|
| Shebang line | Enables direct execution on Unix-like systems | 1 |
| Main statement | Prints required string to stdout | 1 |

## 3. Data Flow

```
1. OS launches Python interpreter
2. Interpreter reads hello.py
3. AST executes print("Hello, World!")
4. Built-in print() writes to sys.stdout
5. OS flushes buffer → terminal
6. Interpreter exits with code 0
```

## 4. Implementation Plan

### Phase 1 – File Creation
1. Create empty file `hello.py`
2. Set file encoding to UTF-8 (default on most editors)

### Phase 2 – Content
1. Add shebang line `#!/usr/bin/env python3`
2. Add single statement `print("Hello, World!")`

### Phase 3 – Validation
1. Run `python hello.py` → verify output
2. Run `chmod +x hello.py && ./hello.py` → verify output
3. Run `wc -c hello.py` → confirm ≤ 100 bytes
4. Run `flake8 hello.py` → confirm no warnings
5. Run `python -m py_compile hello.py` → confirm syntax OK

### Phase 4 – Delivery
1. Commit to version control
2. Tag release v1.0.0

## 5. File Structure

```
hello-world/
├── hello.py          # Main script (2–3 lines)
├── README.md         # Optional usage instructions
└── .gitignore        # Ignore Python cache
```

### hello.py (exact content)
```python
#!/usr/bin/env python3
print("Hello, World!")
```

Byte count: 47 bytes (including newline)