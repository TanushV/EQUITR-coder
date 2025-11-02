# TUI Guide (Advanced)

Note: Throughout the codebase and examples, we standardize on:
- Short name/title (task_name) via config.description
- Detailed task body entered in the TUI task input (the long prompt)

The advanced TUI provides an interactive interface for running single, multi-agent, and research (ML) workflows.

## Launch

- Default: `equitrcoder tui` (no flags needed)
- Startup screen lets you select Supervisor, Worker, Mode, and enter the first task
- You can switch modes and models in chat via `/set mode <mode>`, `/set supervisor <model>`, `/set worker <model>`

## Layout

- Top: Header showing time, Supervisor, Worker, Mode, and Session Cost
- Left: Todo Progress
- Center: Chat history and agent logs
- Right: Running agents
- Bottom: Slash-command input (`/>`)

## Startup Screen

- Supervisor model: dropdown (populated via LiteLLM `get_valid_models(check_provider_endpoint=True)`)
- Worker model: dropdown (same list)
- Mode: `single`, `multi-parallel`, `multi-seq`, `research`
- First Task: text box; pressing Enter or clicking Start transitions to the main TUI

### Model Changes in Chat
```
/set supervisor moonshot/kimi-k2-0711-preview
/set worker moonshot/kimi-k2-0711-preview
/set mode multi-parallel
```

### Extension Scaffolding Commands
```
/scaffold init
/scaffold tool smoke_tester --force
/scaffold agent qa_specialist Responsible for regression testing
/scaffold mode focus_mode Runs targeted verification passes
```
- `init` ensures the extension workspace exists (defaults to `~/.EQUITR-coder/extensions/`).
- `tool`, `agent`, and `mode` create ready-to-edit templates respecting the same
  directory layout as the new CLI commands (`equitrcoder create-tool`, etc.).
- Use `--root <path>` to target a specific project and `--force` to overwrite files.

### Execution Logs
```
[USER] Create a minimal Mario-style platformer using Pygame
[INFO] Starting multi-parallel mode task
[INFO] Iteration 1 | Session Cost: $0.1234
[TOOL] list_task_groups ✓
[TOOL] update_todo_status ✓
[SUCCESS] Task completed successfully! Cost: $1.2345, Time: 120.5s
```