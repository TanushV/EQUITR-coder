Experiment run results for task_20250824_014708

Overview
--------
This folder contains the artifacts produced by running the experiment batch described in experiments.yaml. The baseline run plus four variations were executed using the project-local runner.

Location
--------
- experiments YAML: experiments.yaml
- Generated dataset: data/dataset.csv and data/dataset_meta.json
- Run outputs (stdout JSON saved): runs/
- Combined logs per run: logs/
- Batch summary CSV: runs_summary.csv
- Batch metadata: metadata.json
- Validation outputs: validation_report.json and validation_status.txt

How to reproduce
----------------
From the project root run:

1) Generate dataset (first time only):
   python3 scripts/run_lr.py --generate-dataset --data-dir ./data

2) Execute the experiment batch (exec_experiments reads experiments.yaml):
   python3 scripts/exec_experiments.py --task-dir docs/task_20250824_014708

3) Validate run results against thresholds:
   python3 scripts/validate_results.py --task-dir docs/task_20250824_014708

What was executed
-----------------
The experiments.yaml file defines 5 experiments (baseline, lr_high, reg_high, more_epochs, seed_variation). The exec_experiments script invoked the project runner for each experiment and captured stdout/stderr; per-run compact metrics JSON was saved in docs/task_20250824_014708/runs/<run_id>.json and logs in docs/task_20250824_014708/logs/<run_id>.log. A runs_summary.csv aggregates key values for quick inspection.

Key artifacts
-------------
- data/dataset.csv — Synthetic dataset (1000 rows, features f1,f2,f3 and target y). Generated deterministically using RNG seed 42.
- docs/task_20250824_014708/runs_summary.csv — CSV summary with columns: run_id, seed, mse, r2, train_samples, val_samples, created, name, lr, regularization, epochs, data_dir, test_size, exit_code, artifacts_root
- docs/task_20250824_014708/validation_report.json — JSON report listing per-run thresholds and pass/fail reasons.
- docs/task_20250824_014708/validation_status.txt — Single-line PASS/FAIL indicator; the current batch result is the authoritative pass/fail.
- docs/task_20250824_014708/metadata.json — Reproducibility metadata for the batch run (git commit, timestamps, user).

Validation summary (current run)
--------------------------------
- Default thresholds used: max_mse=2.0, min_r2=0.60
- Of 5 runs, 4 passed and 1 failed (seed_variation had r2 below 0.60).
- validation_status.txt contains either PASS or FAIL; in the last execution it contains FAIL.

Notes & guidance
----------------
- All commands should be run from the project root so that the project root is located by the scripts (requirements.md presence).
- The dataset generator will not overwrite data/dataset.csv unless --force-regenerate is used.
- The exec_experiments tool writes to docs/task_20250824_014708/runs/ and logs/; the runner writes run-level artifacts under the configured artifacts root (default ./artifacts).

Contact
-------
If you have questions about how the experiments were executed or the validation thresholds, please contact the experiment_runner agent responsible for this task group.
