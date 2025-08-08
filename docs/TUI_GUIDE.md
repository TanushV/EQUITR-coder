# TUI Guide (Advanced)

Note: Throughout the codebase and examples, we standardize on:
- Short name/title (task_name) via config.description
- Detailed task body entered in the TUI task input (the long prompt)

The advanced TUI provides an interactive interface for running single, multi-agent, and research (ML) workflows.

## Launch

- Single: `equitrcoder tui --mode single`
- Multi: `equitrcoder tui --mode multi`
- Research (ML): `equitrcoder tui --mode research`

## Layout

- Left: Todo Progress
- Center: Task input, agent logs, model selector, status messages
- Right: Running agents
- Bottom: Status bar (mode, models, profiles, stage, agents, cost)

## Inputs (Research Mode)

- Datasets: comma-separated paths
- Experiments: semicolon-separated `name:command` pairs (e.g., `baseline:python train.py; aug:python train.py --augment`)

## Simulated Screens

### Startup
```
🖥️ EQUITR Coder - Advanced TUI
Mode: single | Models: Not set | Profiles: default | Stage: ready | Agents: 1 | Cost: $0.0000/$5.00

[Task Input]
> Enter your task description...
[Datasets] (research mode)
[Experiments] (research mode)
[Execute Single] [Execute Multi] [Execute Research] [Clear]
```

### Model Selection (press 'm')
```
Select Models
Supervisor model: moonshot/kimi-k2-0711-preview
Worker model: moonshot/kimi-k2-0711-preview
[Confirm] [Cancel]
```

### Execution Logs
```
[USER] Create a minimal Mario-style platformer using Pygame
[INFO] Starting multi mode task
[INFO] Iteration 1 | Current Cost: $0.1234
[TOOL] list_task_groups ✓
[TOOL] update_todo_status ✓
[SUCCESS] Task completed successfully! Cost: $1.2345, Time: 120.5s
```

### Research Mode Completion
```
[INFO] Experiments complete, generating supervisor report
[SUCCESS] Researcher mode completed successfully!
Report: docs/task_20250101_120000/research_report.md
Cost: $3.2100
``` 