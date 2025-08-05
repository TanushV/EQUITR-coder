# EQUITR Coder

*A clean-architecture autonomous coding framework for multi-agent, LLM-powered software generation*

---

## ✨ Why EQUITR Coder?
EQUITR Coder orchestrates one or many AI agents to plan, implement, test and document complete software projects while maintaining professional Git history.  It is designed for:

* **Single-agent** rapid prototyping.
* **Multi-agent** parallel development with inter-agent communication.
* Fully **scriptable** programmatic control *and* an interactive **TUI**.
* Strict **clean-architecture**: each layer (agents, tools, orchestrator, UI) is testable and replaceable.

---

## 🗂️ Repository Layout
```
equitrcoder/
  core/               # CleanAgent, CleanOrchestrator, session + planning logic
  tools/              # Built-in & custom tool implementations
  programmatic/       # OOP interface (EquitrCoder) for Python scripts / back-end use
  ui/                 # Textual & ASCII TUIs (core, not legacy!)
  utils/              # Git & environment helpers

testing/
  comprehensive_mode_testing/   # End-to-end single & multi-agent suites
  run_parallel_tests.py         # Example runner

tests/              # Legacy fast unit/integration tests (still runnable)
examples/           # Usage demos (optional)
```
---

## 🔑 Core Components
| Layer | Module | Highlights |
|-------|--------|------------|
| **Agent** | `core/clean_agent.py` | Executes tool calls, tracks cost/iterations, communicates via message bus |
| **Orchestrator** | `core/clean_orchestrator.py` | Decomposes tasks into *task-groups*, resolves dependencies, coordinates agents |
| **Tools** | `tools/builtin/*.py` | File system, Git, shell, search, todo management & more.  Add your own via entry-points |
| **Programmatic API** | `programmatic/interface.py` | `EquitrCoder.execute_task()` for single tasks; factory helpers for single/multi modes |
| **TUI** | `ui/tui.py` (simple) & `ui/advanced_tui.py` (Textual) | Real-time status, cost tracking, git diff viewer |
| **Testing** | `testing/comprehensive_mode_testing/` | Creates isolated workspaces, runs single & multi-agent flows, produces Markdown reports |

---

## 🚀 Installation
```bash
# 1. Clone
git clone https://github.com/equitr/EQUITR-coder.git
cd EQUITR-coder

# 2. Create & activate virtual-env
python -m venv equitr-dev
source equitr-dev/bin/activate

# 3. Install runtime deps
pip install -r requirements.txt

# (Optional) Dev / lint / test extras
pip install -r requirements-dev.txt
pre-commit install  # for Ruff, black, etc.
```

### Environment variables
Set your model keys (OpenAI, Anthropic, Moonshot, …) as needed:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="..."
```

---

## ⚡ Quick Start
```python
from equitrcoder.programmatic import EquitrCoder, TaskConfiguration

coder = EquitrCoder(repo_path="my_project", git_enabled=True)
config = TaskConfiguration(max_cost=5, model="gpt-4o-mini")

result = await coder.execute_task(
    "Build a CLI calculator with tests and docs", config=config
)
print(result.success, result.cost)
```

### Multi-Agent Parallel
```python
from equitrcoder.programmatic import EquitrCoder, MultiAgentTaskConfiguration

coder = EquitrCoder(repo_path="multi_project")
ma_cfg = MultiAgentTaskConfiguration(num_agents=4, max_cost=20)
await coder.execute_task("Create REST API + React UI + Dockerfile", ma_cfg)
```

### TUI Mode
```bash
python -m equitrcoder.ui.tui   # simple ASCII
python -m equitrcoder.ui.advanced_tui  # rich Textual interface
```

### Simulated CLI Session

```text
$ equitrcoder --mode multi --agents 3 --task "Add OAuth login to my Flask app"
📄 Planning...
   ▸ Created requirements.md, design.md, todos.md
🤖 Spawning 3 agents in parallel
   🧠  backend_agent → finished (3 iterations, $0.08)
   🎨  frontend_agent → finished (2 iterations, $0.05)
   🛠️  tester_agent   → finished (1 iteration, $0.02)
✅ All task-groups complete.  Auto-commit created: `feat(auth): OAuth login`
💰 Total cost: $0.15   ⏱ 35 s
```

### Simulated TUI Walk-through

```text
$ python -m equitrcoder.ui.advanced_tui

┌──────────────────────────────────────────────────────────┐
│  EQUITR CODER ‑ PROJECT DASHBOARD                       │
├──────────────────────────────────────────────────────────┤
│ Project path : /home/user/projects/mario_game_2025-08-05 │
│ Agents active : 4 (parallel)                             │
│ Current phase : 1 / ?                                    │
│ Cost so far   : $0.37                                    │
├──────────────────────────────────────────────────────────┤
│  LIVE LOG                                                │
│ 08:21:04 planner  ▸ Generated task-groups (graphics, ... │
│ 08:21:06 graphics ▸ send_message → physics "need jump…" │
│ 08:21:07 physics  ▸ update_todo_status(todo_17, done)    │
│ …                                                       │
└──────────────────────────────────────────────────────────┘

Press <F1> to toggle agent logs • <F2> open git diff • <Ctrl+C> quit
```

---

## 🧪 Comprehensive Tests
Run the heavy end-to-end suite (requires real LLM keys):
```bash
python testing/run_parallel_tests.py  # runs multi-agent parallel suite
```
Outputs go to `testing/comprehensive_tests/run_<timestamp>/` (reports + artefacts).

---

## 🛠️ Developer Guide
* **Lint / format**  `ruff check . --fix`, `black .`
* **Unit tests**     `pytest tests/`
* **Docs**           `sphinx-build -b html docs/ build/docs`
* **Release**        Update `CHANGELOG.md`, bump version, `python -m build && twine upload ...`

---

## �� License
Apache-2.0 