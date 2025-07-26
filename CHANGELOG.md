# CHANGELOG

## v1.1.0 (2025-10-15)
- Completed TUI enhancements: Made the TUI look nice but still like a terminal with enhanced CSS in advanced_tui.py and more color variety in tui.py.
- Set default models: o3 for supervisor, moonshot/kimi-k2-0711-preview for worker/single agent mode.
- Added TUI header: Shows current mode, available API keys, and selected models at the top.
- Added git installation: Documented in README.md with 'pip install git+https://github.com/TanushV/EQUITR-coder.git'.
- Implemented live prices in TUI: Added on_iteration callback for real-time cost updates in advanced_tui.py.
- Enhanced file edit display: Full contents with red/green highlights for diffs in TUI.
- Limited modes to programmatic and TUI: Removed CLI from docs, dereferenced in setup.py (code remains but not exposed).

## v1.0.0 (2025-10-13)
- Initial release with multi-agent system, TUI, programmatic API, git integration 