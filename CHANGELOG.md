# CHANGELOG

## v1.0.2 (2025-10-15)
- Added dynamic model selection in TUI based on env keys
- Model updates: Workers to gpt-4.1, Supervisors to o3

## v1.0.1 (2025-10-14)
- Minor bug fixes

## v1.0.0 (2025-10-13)
- Initial release with multi-agent system, TUI, programmatic API, git integration 
- make the tui look nice but still like a terminal (completed: enhanced CSS in advanced_tui.py and colors in tui.py)
- make the default models the following(word for word): o3 for supervisor, moonshot/kimi-k2-0711-preview for worker/single agent mode (completed)
- at the top of the tui, it should show the current mode/avaliable api keys/selected models (completed)
- add an install with git, this is the url: @https://github.com/TanushV/EQUITR-coder.git (completed)
- in the tui, prices should be shown live (completed: added on_iteration callback for live updates)
- when edit file/create file commands are shown, the full contents of what happened should be shown in the tui, with red/green highlights for diffs (completed)
- only 2 modes should be programatic and tui. Remove the cli mode from the docs and dereference it in the code(do not remove all together however) (completed: removed from docs, dereferenced in setup.py) 