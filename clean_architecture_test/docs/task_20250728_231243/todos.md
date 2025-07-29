## Category 1 – Data Generation & Processing
- [ ] Create `src/generate_data.py` with `generate_sales_csv()` function that outputs 1000–1050 rows to `data/raw/sales_data.csv` using fixed random seed 42
- [ ] Implement `src/process_data.py` with `clean_and_filter()` that drops nulls, negative prices/quantities, and optional date-range filter, writing to `data/processed/clean_sales.csv`
- [ ] Add unit tests in `tests/test_generate_data.py` asserting row count, schema, and deterministic output
- [ ] Add unit tests in `tests/test_process_data.py` covering null handling, negative value removal, and date filtering
- [ ] Create `src/logger.py` singleton that writes timestamped INFO logs to `logs/pipeline.log`

## Category 2 – Analysis & Visualization
- [ ] Implement `src/analyze.py` with `compute_stats()` returning typed `StatsResult` dataclass containing total revenue, average order value, top 5 products by revenue, and monthly revenue trend
- [ ] Create `src/visualize.py` with `plot_revenue_by_product()` saving horizontal bar chart to `reports/figures/revenue_by_product.png` (300 DPI, <500 kB)
- [ ] Add `plot_monthly_trend()` in `src/visualize.py` saving line chart to `reports/figures/monthly_revenue_trend.png` (300 DPI, <500 kB)
- [ ] Write unit tests in `tests/test_analyze.py` validating computed statistics against fixture data
- [ ] Write unit tests in `tests/test_visualize.py` asserting PNG files are created with correct size constraints

## Category 3 – Reporting & Orchestration
- [ ] Implement `src/report.py` with `render_report()` using embedded Jinja2 template to generate `reports/sales_report.md` including summary tables, embedded figures, and "How to Reproduce" section
- [ ] Create `main.py` CLI entrypoint using `click` with `--start-date` and `--end-date` flags, orchestrating full pipeline idempotently in <10 seconds
- [ ] Add unit tests in `tests/test_report.py` verifying markdown report renders correctly with all required sections
- [ ] Create end-to-end test in `tests/` ensuring `python main.py` completes successfully and produces all expected outputs
- [ ] Finalize repository: add `requirements.txt` with pinned versions, `README.md` with one-liner usage, `.gitignore`, and ensure `flake8 src/` passes with zero warnings