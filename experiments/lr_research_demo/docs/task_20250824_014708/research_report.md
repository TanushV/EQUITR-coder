# Linear Regression Mini-Project — Status and Plan

## Research Task
Finish a small ML project that:
- Generates a simple synthetic, correlated dataset.
- Trains linear regression models in two distinct runs.
- Evaluates each run with MSE and R2.
- Compares the two runs, all work contained within the project folder.

## Datasets
- Location: /Users/tanushvanarase/Documents/EQUITR-coder/experiments/lr_research_demo/data
- Status: Not generated yet.
- Target design:
  - Features: 2–5 correlated features (e.g., multivariate normal with off-diagonal covariance).
  - Target: Linear combination with Gaussian noise (e.g., y = 3x1 − 2x2 + ε).
  - Split: 70/15/15 train/val/test.
  - Reproducibility: Fixed seed (e.g., 42).
- Artifacts to save:
  - CSVs or NumPy npz: train/val/test.
  - Metadata: data_spec.json (n_samples, n_features, noise_std, seed, correlations).

## Hardware
- Local CPU preferred (no GPU required). Small data and linear models run in seconds.

## Experiments Executed
- Current status (from provided summary): No experiments executed or passed.
  - baseline: not run
  - lr_high: not run
  - reg_high: not run
  - more_epochs: not run
  - seed_variation: not run

## Planned Experiments (minimum to satisfy task)
- Run A — baseline:
  - Model: SGDRegressor (squared_loss), modest learning rate, light L2 (alpha=1e-4), max_iter≈200, early stopping off.
- Run B — lr_high (or reg_high):
  - Option 1 (lr_high): Increase learning rate (eta0) and/or change schedule; same epochs.
  - Option 2 (reg_high): Increase L2 regularization (alpha 1e-2 to 1e-1).
- Notes:
  - Using SGDRegressor enables learning-rate and epoch controls. Alternatively, Ridge for reg_high if not varying epochs.
  - Ensure identical train/val/test splits across runs (same seed).

## Evaluation and Comparison
- Metrics: MSE and R2 on validation and test sets.
- Outputs per run:
  - metrics.json (train/val/test MSE, R2, timing, seed).
  - model.pkl (optional).
  - config.json (hyperparameters).
  - stdout log with final metrics.
- Comparison:
  - Tabulate MSE/R2 across runs; highlight best R2 on validation and generalization gap to test.
  - Expectation on well-behaved correlated data: R2 > 0.9 for reasonable noise levels.

## Minimal Implementation Plan (actionable)
- Environment: Python 3.9+, numpy, scikit-learn, pandas (optional), joblib.
- Scripts (inside lr_research_demo):
  - data/generate.py — create correlated data and splits; save under data/.
  - train_eval.py — load split, fit model, compute MSE/R2, save artifacts.
  - run_experiments.sh or makefile — invoke two runs and a comparison.
- Suggested commands:
  - python data/generate.py --n-samples 3000 --n-features 3 --noise-std 0.5 --seed 42
  - python train_eval.py --exp baseline --model sgd --alpha 1e-4 --eta0 0.01 --max-iter 200 --seed 42
  - python train_eval.py --exp lr_high --model sgd --alpha 1e-4 --eta0 0.1 --max-iter 200 --seed 42
  - (Optional) python train_eval.py --exp reg_high --model sgd --alpha 1e-2 --eta0 0.01 --max-iter 200 --seed 42
- Pass/Fail heuristic for CI:
  - Mark run as passed if test R2 ≥ 0.9 and test MSE ≤ validation MSE × 1.2 (prevents overfitting on tiny noise).
  - Record return_code=0 only when metrics.json exists and pass criteria met.

## Outcomes
- None yet. All runs in the provided summary show null command, not executed, and not passed.
- No MSE/R2 available for reporting.

## Conclusion
The project is not yet finished. The dataset has not been generated and no experiments have been executed. To fulfill the task, generate a correlated synthetic dataset, run at least two linear regression experiments (baseline and one variation), compute MSE and R2 on validation and test, and produce an artifact-backed comparison.

## Next Steps
1. Implement and run data generation to create train/val/test under data/.
2. Implement train_eval.py using scikit-learn (SGDRegressor or Ridge), saving metrics.json and config.json per run in an outputs/exp_name/ directory.
3. Execute two runs (baseline and lr_high or reg_high) on CPU with fixed seed; log MSE/R2.
4. Add a simple comparer script to print a two-row summary table and mark a winner by validation R2.
5. Update the experiment summary by recording commands, return codes, stdout/stderr tails, and set all_passed=true once both runs meet the pass criteria.