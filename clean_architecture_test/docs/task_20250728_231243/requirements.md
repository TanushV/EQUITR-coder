# requirements.md

## 1. Project Overview

Build a lightweight, end-to-end data-analysis pipeline that demonstrates the full lifecycle of a data project: data generation → cleaning → analysis → visualization → reporting.  
The deliverable is a single Git repository that can be cloned and executed with one command to produce a self-contained report.

### Scope
- **In-scope**: Synthetic sales data, CSV I/O, basic statistics, matplotlib/seaborn charts, markdown report, CLI runner.  
- **Out-of-scope**: Real-time ingestion, databases, authentication, web UI, advanced ML models.

---

## 2. Functional Requirements

| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-1 | Generate sample CSV data | Script creates `data/raw/sales_data.csv` with ≥1 000 rows and columns: `order_id`, `customer_id`, `product`, `quantity`, `unit_price`, `order_date`, `region`. |
| FR-2 | Clean & filter data | Module removes rows with nulls, negative prices/quantities, and filters by optional date range. Output saved to `data/processed/clean_sales.csv`. |
| FR-3 | Compute statistics | Calculates total revenue, average order value, top 5 products by revenue, monthly revenue trend. |
| FR-4 | Create visualizations | Saves two PNG files to `reports/figures/`: `revenue_by_product.png` (horizontal bar) and `monthly_revenue_trend.png` (line chart). |
| FR-5 | Generate markdown report | Creates `reports/sales_report.md` with summary tables, embedded figures, and a “How to Reproduce” section. |
| FR-6 | CLI orchestration | Running `python main.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]` executes the entire pipeline idempotently. |
| FR-7 | Logging | All steps emit timestamped logs to `logs/pipeline.log` at INFO level. |

---

## 3. Technical Requirements

### 3.1 Language & Core Libraries
- Python 3.9+
- pandas ≥ 2.0
- matplotlib ≥ 3.7
- seaborn ≥ 0.12
- click ≥ 8.0 (CLI)
- pytest ≥ 7.0 (tests)

### 3.2 Directory Layout
```
sales_analysis/
├── data/
│   ├── raw/
│   └── processed/
├── reports/
│   └── figures/
├── logs/
├── src/
│   ├── __init__.py
│   ├── generate_data.py
│   ├── process_data.py
│   ├── analyze.py
│   ├── visualize.py
│   └── report.py
├── tests/
├── requirements.txt
├── README.md
└── main.py
```

### 3.3 Code Standards
- PEP 8 compliant; enforced via `flake8`.
- Type hints on all public functions.
- Docstrings in Google style.
- Unit tests ≥ 80 % coverage (`pytest --cov=src`).

### 3.4 Configuration
- Default date range: last 12 months.
- Configurable via CLI flags or environment variables (`START_DATE`, `END_DATE`).

### 3.5 Reproducibility
- `requirements.txt` pinned with exact versions.
- Random seed fixed (`np.random.seed(42)`) for deterministic synthetic data.

---

## 4. Success Criteria

| Checkpoint | Metric | Pass Threshold |
|---|---|---|
| 1. Data Generation | `data/raw/sales_data.csv` exists and has 1 000 ≤ rows ≤ 1 050 | ✓ |
| 2. Data Cleaning | No nulls, no negative values in `clean_sales.csv` | ✓ |
| 3. Statistics | Report shows non-zero total revenue and ≥5 products | ✓ |
| 4. Visualizations | Two PNG files generated, each < 500 kB | ✓ |
| 5. Report | `sales_report.md` renders correctly on GitHub with images | ✓ |
| 6. CLI | `python main.py` completes in < 10 s on a modern laptop | ✓ |
| 7. Tests | `pytest` passes with ≥ 80 % coverage | ✓ |
| 8. Linting | `flake8 src/` returns zero warnings | ✓ |

When all eight checkpoints pass, the project is considered complete.