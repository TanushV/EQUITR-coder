Requirements defect: FR-004 upper bound incompatible with FR-005 generator

Summary
-------
While implementing the deterministic dataset generator (seed=42) per FR-005, the generated dataset fails the correlation bounds check in FR-004. The observed Pearson correlation between f1 and f2 is 0.9587085708325869, which exceeds the FR-004 upper bound of 0.95.

Reproduction
-----------
- Code: scripts/run_lr.py generate_dataset() using numpy.random.default_rng(seed=42)
- Observed correlations (n=1000):
  - pearson_f1_f2 = 0.9587085708325869
  - pearson_f1_f3 = 0.0034181332345671177
  - pearson_f2_f3 = 0.01551615800269778

Mathematical analysis
---------------------
Given the construction in FR-005:
  f1 = z + e1
  f2 = z + e2
with z ~ N(0,1) and e1,e2 ~ N(0, 0.2^2) independent, the population Pearson correlation is

  rho = Var(z) / sqrt(Var(f1) Var(f2)) = 1 / sqrt((1 + 0.2^2)(1 + 0.2^2))
      = 1 / (1 + 0.2^2) = 1 / 1.04 = 0.9615384615...

This population value (≈0.9615) is strictly greater than the FR-004 upper bound 0.95, making the bound impossible to satisfy for any sufficiently large sample or any seed that reflects the population.

Observed sampling variability with n=1000 (Fisher z-space):
  se_z = 1 / sqrt(n - 3) ≈ 0.0317
Hence, realizations will commonly fall near 0.96; seed=42 yields ≈0.9587.

Impact
------
- The code correctly implements FR-005 and TR constraints. However, the check in FR-004 is mathematically incompatible with FR-005.
- Until FR-004 is corrected, the generator will raise DataError and dataset/dataset.csv cannot be produced, causing experiment scripts to fail (as observed).

Proposed fix (product/requirements change)
-----------------------------------------
Change FR-004 upper bound for pearson_f1_f2 from 0.95 to 0.97 (or 0.975/0.98 for more margin). Suggested new interval:
  pearson_f1_f2 in [0.80, 0.97]

This preserves the intent of ensuring f1 and f2 are strongly positively correlated while accommodating the true population correlation arising from FR-005.

Recommended next steps
----------------------
1. Product/requirements owner to approve amended FR-004 (e.g., upper bound 0.97).
2. After approval, update requirements.md and adjust the bounds check in scripts/run_lr.py (one-line change).
3. Re-run the dataset generation and test suite.

Attachments / Evidence
----------------------
- Observed correlation values (see above)
- Implementation: scripts/run_lr.py generate_dataset() uses exactly the RNG and process specified in FR-005 (seed=42, e1/e2 std=0.2, noise std=1.0).

Author: data_engineer_agent_implement_dataset_pipeline
Date: automated diagnostic
