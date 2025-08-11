# EQUITR Coder Docs

- USAGE_GUIDE.md: CLI, TUI (advanced-only), and programmatic usage
- PROGRAMMATIC_USAGE_GUIDE.md: API usage patterns, including ML researcher mode
- CREATING_MODES.md: How to create custom modes
- CREATING_PROFILES.md: How to create specialized agent profiles
- TOOL_LOGGING_AND_MULTI_MODEL_GUIDE.md: Tool logging and multi-model usage
- CONFIGURATION_GUIDE.md: Config system overview
- ASK_SUPERVISOR_GUIDE.md: Supervisor communication patterns

Notes:
- The TUI is advanced-only (`textual`-based). Use `equitrcoder tui` (no flags). Startup screen handles models and mode.
- Researcher mode is ML-focused and produces `research_plan.yaml`, `experiments.yaml`, and `research_report.md`. 