# Todos for Agent 1

**Agent 1 of 3**

## Category 1 – Data Generation & Processing
- [ ] Create `src/generate_data.py` with `generate_sales_csv()` function that outputs 1000–1050 rows to `data/raw/sales_data.csv` using fixed random seed 42
- [ ] Implement `src/process_data.py` with `clean_and_filter()` that drops nulls, negative prices/quantities, and optional date-range filter, writing to `data/processed/clean_sales.csv`
- [ ] Add unit tests in `tests/test_generate_data.py` asserting row count, schema, and deterministic output
- [ ] Add unit tests in `tests/test_process_data.py` covering null handling, negative value removal, and date filtering
- [ ] Create `src/logger.py` singleton that writes timestamped INFO logs to `logs/pipeline.log`

## Instructions
- Complete ALL todos in your assigned categories
- Each category is self-contained
- Use communication tools to coordinate with other agents
- Mark todos complete with update_todo when finished
