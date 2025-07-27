# design.md

## 1. System Architecture
A single-file, zero-dependency Python 3 program that runs in a standard CPython interpreter.  
No runtime services, network endpoints, or persistent storage are required.

```
┌────────────────────────────┐
│        hello.py            │
│  ┌────────────────────┐    │
│  │  UTF-8 source file │    │
│  │  2 logical lines   │    │
│  └────────────────────┘    │
└────────────────────────────┘
```

## 2. Components
| Component | Description | Lines of Code |
|-----------|-------------|---------------|
| **hello.py** | The only deliverable. Contains:<br>- Shebang (optional but recommended)<br>- Explanatory comment<br>- `print("Hello, World!")` | 3–4 |

## 3. Data Flow
1. **Input**: None (no CLI arguments, stdin, or config files).
2. **Processing**: Interpreter tokenizes → parses → executes the single `print` call.
3. **Output**: String `"Hello, World!\n"` written to `sys.stdout`.

```
stdin ─┐
       ├─► hello.py ──► stdout: "Hello, World!\n"
env  ──┘
```

## 4. Implementation Plan
| Step | Action | Command / Tool | Verification |
|------|--------|----------------|--------------|
| 1 | Create project root directory | `mkdir hello-world && cd hello-world` | Directory exists |
| 2 | Initialize Git repo | `git init` | `.git/` created |
| 3 | Create `hello.py` | `touch hello.py` | File listed in `ls` |
| 4 | Add shebang & encoding cookie | Editor | First line: `#!/usr/bin/env python3` |
| 5 | Add explanatory comment | Editor | `# This program prints "Hello, World!" to the console.` |
| 6 | Add print statement | Editor | `print("Hello, World!")` |
| 7 | Make executable (optional) | `chmod +x hello.py` | `ls -l` shows `rwxr-xr-x` |
| 8 | Run & test | `python hello.py` | Output matches SC-1 |
| 9 | Commit to VCS | `git add hello.py && git commit -m "feat: add hello.py"` | `git log --oneline` shows commit |

## 5. File Structure
```
hello-world/
├── hello.py          # Main (and only) source file
└── .git/             # Git metadata (auto-generated)
```

### hello.py (final content)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program prints "Hello, World!" to the console.
print("Hello, World!")
```