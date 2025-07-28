# design.md

## 1. System Architecture

```
┌────────────────────────────────────────────┐
│              Calculator App                │
│  ┌────────────────────────────────────┐   │
│  │           GUI Layer (Tk)           │   │
│  │  ┌────────────────────────────┐   │   │
│  │  │   View (tkinter widgets)   │   │   │
│  │  └────────────┬───────────────┘   │   │
│  │  ┌────────────┴───────────────┐   │   │
│  │  │ Controller (event handler) │   │   │
│  │  └────────────┬───────────────┘   │   │
│  │  ┌────────────┴───────────────┐   │   │
│  │  │      Model (Calculator)    │   │   │
│  │  └────────────────────────────┘   │   │
│  └────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

**Pattern**: Minimal MVC inside a single file  
- **View**: Tkinter widgets (buttons, entry, labels)  
- **Controller**: Button/keyboard event handlers that delegate to the model  
- **Model**: Pure-Python `Calculator` class with no GUI dependencies  

## 2. Components

| Component | Responsibility | Public Interface |
|---|---|---|
| `Calculator` | Core arithmetic logic | `push(value_or_op)`, `evaluate()`, `clear()`, `memory_add()`, `memory_sub()`, `memory_recall()`, `memory_clear()` |
| `CalculatorGUI` | Tkinter window, widgets, layout | `__init__()`, `_create_widgets()`, `_bind_events()`, `_on_click(btn)`, `_on_key(event)` |
| `main()` | Entry point, instantiates GUI | `main()` |
| `tests/test_calculator.py` | Unit tests | `TestCalculator` class with 8 test methods |

## 3. Data Flow

1. **User presses button or key**  
   → `CalculatorGUI._on_click(btn)` or `_on_key(event)`  
   → `Calculator.push()` or `Calculator.evaluate()`  
   → Internal state updated (stack or accumulator)  
   → `CalculatorGUI` refreshes display via `StringVar`

2. **State machine inside `Calculator`**  
   ```
   [start] --digit--> [operand1] --op--> [operator] --digit--> [operand2] --=--> [result]
   ```

3. **Error propagation**  
   Any exception in `Calculator` → return `"Error"` → GUI displays it → next valid input clears error.

## 4. Implementation Plan

| Step | Task | Deliverable | Time |
|---|---|---|---|
| 1 | Scaffold repo, `calculator.py`, `tests/` | Git repo with README | 30 min |
| 2 | Implement `Calculator` class + unit tests | `test_calculator.py` green | 1 h |
| 3 | Build minimal Tk GUI (buttons 0-9, +, -, *, /, =, C) | Working GUI | 1 h |
| 4 | Wire GUI to model, keyboard bindings | Full FR-1..FR-7 | 1 h |
| 5 | Add memory functions (M+, M-, MR, MC) | FR-8 optional | 30 min |
| 6 | Accessibility & styling (font, colors) | TR-8 satisfied | 30 min |
| 7 | Package with PyInstaller for 3 OS | `dist/` executables | 1 h |
| 8 | Manual QA on 3 platforms | QA checklist signed | 1 h |
| 9 | Tag v1.0, create GitHub release | Release page | 30 min |

Total: ~6 hours.

## 5. File Structure

```
simple-calculator/
├── calculator.py          # single source file (< 300 lines)
├── requirements.txt       # empty (only stdlib)
├── tests/
│   └── test_calculator.py
├── build/
│   ├── build.py          # PyInstaller build script
│   └── icons/
│       ├── icon.ico
│       ├── icon.icns
│       └── icon.png
├── dist/                 # generated executables
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions: unittest + build
├── README.md
└── design.md             # this file
```

### Key Design Decisions
- **Single file**: Easier distribution, meets TR-9.  
- **Tkinter**: Cross-platform, zero-dependency, meets TR-1.  
- **State machine**: Keeps model tiny; avoids regex parsing.  
- **StringVar**: Tk variable for automatic display refresh.