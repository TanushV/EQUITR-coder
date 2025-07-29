# design.md

## 1. System Architecture

The pipeline is a **batch-oriented, single-machine ETLA** (Extract-Transform-Load-Analyze) system implemented in pure Python.  
It follows a **modular, functional-core / imperative-shell** pattern:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CLI Flags  │────▶│  Data Gen    │────▶│  Processing  │────▶│   Analysis   │
│  (click)     │     │ (generate)   │     │  (process)   │     │  (analyze)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
        │                    │                     │                     │
        │                    │                     │                     │
        ▼                    ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Shared File System (CSV, PNG, MD)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

Key architectural decisions:
- **Stateless modules**: Each stage reads from disk and writes to disk; no in-memory state sharing.
- **Idempotent execution**: Re-running `main.py` always yields identical outputs for identical inputs (fixed random seed).
- **Fail-fast**: Any exception aborts the pipeline and logs the stack trace.

---

## 2. Components

| Component | Responsibility | Public API | Internal Details |
|---|---|---|---|
| `generate_data.py` | Create deterministic synthetic sales CSV | `generate_sales_csv(path: Path, rows: int = 1000)` | Uses `Faker` for names, `numpy` for numeric columns, fixed seed. |
| `process_data.py` | Clean & filter raw CSV | `clean_and_filter(src: Path, dst: Path, start: date | None, end: date | None) -> None` | `pandas` pipeline: dropna, price>0, quantity>0, date mask. |
| `analyze.py` | Compute KPIs | `compute_stats(df: pd.DataFrame) -> dict[str, Any]` | Returns typed dataclass `StatsResult` with totals, averages, top-N. |
| `visualize.py` | Generate charts | `plot_revenue_by_product(df: pd.DataFrame, out: Path)` <br> `plot_monthly_trend(df: pd.DataFrame, out: Path)` | Uses `seaborn` barplot & lineplot, saves 300 DPI PNG. |
| `report.py` | Render markdown | `render_report(stats: StatsResult, fig_dir: Path, out: Path) -> None` | Jinja2 template embedded as string literal. |
| `main.py` | CLI orchestration | `@click.command()` entrypoint | Parses flags, sets up logging, calls stages in sequence. |
| `logger.py` | Centralized logging | `get_logger(name: str) -> logging.Logger` | Rotating file handler to `logs/pipeline.log`, INFO level. |

---

## 3. Data Flow

### 3.1 File-Level Flow

```
data/raw/sales_data.csv
        │
        │ read_csv
        ▼
process_data.py ──filter──▶ data/processed/clean_sales.csv
        │
        │ read_csv
        ▼
analyze.py ──compute──▶ StatsResult (dict)
        │
        │ pass object
        ▼
visualize.py ──plot──▶ reports/figures/*.png
        │
        │ paths
        ▼
report.py ──template──▶ reports/sales_report.md
```

### 3.2 Row-Level Transformations

| Stage | Input Schema | Transformations | Output Schema |
|---|---|---|---|
| Generate | `order_id,customer_id,product,quantity,unit_price,order_date,region` | — | Same |
| Clean | Same | 1. Drop rows with nulls <br> 2. Remove `quantity <= 0` <br> 3. Remove `unit_price <= 0` <br> 4. Date range filter | Same, fewer rows |
| Analyze | Same | 1. Add `revenue = quantity * unit_price` <br> 2. Group by product & month | Aggregated frames |
| Visualize | Aggregated frames | Plotting | PNG binaries |
| Report | Stats dict + PNG paths | Markdown templating | `.md` text |

---

## 4. Implementation Plan

### Sprint 0 – Project Skeleton (Day 0)
1. `mkdir -p sales_analysis/{data/{raw,processed},reports/figures,logs,src,tests}`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install --upgrade pip && pip install pandas matplotlib seaborn click pytest flake8`
4. `pip freeze > requirements.txt`
5. Add `.gitignore`, `README.md`, `pyproject.toml` (for flake8 & pytest).

### Sprint 1 – Data Generation (Day 1)
- Implement `generate_sales_csv()` with fixed seed.
- Unit test: assert 1000 ≤ rows ≤ 1050, schema correct.
- Run `python -m src.generate_data` → verify `data/raw/sales_data.csv`.

### Sprint 2 – Data Processing (Day 2)
- Implement `clean_and_filter()` with optional date CLI args.
- Unit tests: null handling, negative price/quantity, date mask.
- Run `python -m src.process_data --start-date 2023-01-01 --end-date 2023-12-31`.

### Sprint 3 – Analysis (Day 3)
- Create `StatsResult` dataclass.
- Implement `compute_stats()` returning totals, averages, top-5.
- Unit test with fixture CSV.

### Sprint 4 – Visualization (Day 4)
- Implement `plot_revenue_by_product()` and `plot_monthly_trend()`.
- Style: seaborn whitegrid, 300 DPI, tight layout.
- Unit test: assert PNG files created, size < 500 kB.

### Sprint 5 – Report Generation (Day 5)
- Embed Jinja2 template string in `report.py`.
- Implement `render_report()` with GitHub-flavored markdown.
- Manual inspection of `reports/sales_report.md`.

### Sprint 6 – CLI & Logging (Day 6)
- Wire everything in `main.py` using `click`.
- Add `logger.py` with rotating file handler.
- End-to-end test: `time python main.py` < 10 s.

### Sprint 7 – QA & Polish (Day 7)
- `pytest --cov=src` → ≥ 80 %.
- `flake8 src/` → 0 warnings.
- Update `README.md` with one-liner usage.

---

## 5. File Structure (Final)

```
sales_analysis/
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
├── main.py
├── logs/
│   └── pipeline.log
├── data/
│   ├── raw/
│   │   └── sales_data.csv
│   └── processed/
│       └── clean_sales.csv
├── reports/
│   ├── figures/
│   │   ├── revenue_by_product.png
│   │   └── monthly_revenue_trend.png
│   └── sales_report.md
├── src/
│   ├── __init__.py
│   ├── logger.py
│   ├── generate_data.py
│   ├── process_data.py
│   ├── analyze.py
│   ├── visualize.py
│   └── report.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_generate_data.py
    ├── test_process_data.py
    ├── test_analyze.py
    ├── test_visualize.py
    └── test_report.py
```

### Key Files Explained
- `main.py`: Thin orchestration layer; no business logic.
- `src/logger.py`: Singleton logger to avoid duplicate handlers.
- `tests/conftest.py`: Pytest fixtures for temp CSVs and deterministic frames.
- `pyproject.toml`: Centralizes tool configs (flake8, pytest, coverage).

---

## 6. Risk & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Non-deterministic data | QA failures | Fix random seed & test row counts. |
| Large PNG files | GitHub storage | 300 DPI + tight layout + `.gitattributes` filter=lfs. |
| CLI date parsing errors | User confusion | Use `click.DateTime` with clear `--help`. |
| Missing dependencies | Runtime crash | Pin exact versions in `requirements.txt`. |

---

## 7. Future Enhancements (Post-MVP)
- Add `Makefile` with `make run`, `make test`, `make clean`.
- Package as pip-installable (`setup.cfg`).
- Support parquet I/O for speed.
- Add CI via GitHub Actions (pytest + flake8).