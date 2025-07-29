# Todos for Agent 3

**Agent 3 of 3**

## Category 3 – Reporting & Orchestration
- [ ] Implement `src/report.py` with `render_report()` using embedded Jinja2 template to generate `reports/sales_report.md` including summary tables, embedded figures, and "How to Reproduce" section
- [ ] Create `main.py` CLI entrypoint using `click` with `--start-date` and `--end-date` flags, orchestrating full pipeline idempotently in <10 seconds
- [ ] Add unit tests in `tests/test_report.py` verifying markdown report renders correctly with all required sections
- [ ] Create end-to-end test in `tests/` ensuring `python main.py` completes successfully and produces all expected outputs
- [ ] Finalize repository: add `requirements.txt` with pinned versions, `README.md` with one-liner usage, `.gitignore`, and ensure `flake8 src/` passes with zero warnings

## Instructions
- Complete ALL todos in your assigned categories
- Each category is self-contained
- Use communication tools to coordinate with other agents
- Mark todos complete with update_todo when finished
