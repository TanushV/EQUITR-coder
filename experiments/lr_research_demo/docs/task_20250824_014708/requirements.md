# Project Overview
This project implements a deterministic, CPU-only machine learning pipeline that generates a simple correlated synthetic dataset once, trains and evaluates a linear regression model twice with different seeds, and produces per-run metrics (MSE and R2) and a machine-readable comparison report across the two runs, with all inputs/outputs confined to the project folder.

# Functional Requirements (FR)

- FR-001: The project root MUST be defined at runtime as the absolute directory containing this requirements.md file and all read/write operations MUST occur within this directory or its subdirectories.
- FR-002: The synthetic dataset generator MUST create a dataset with exactly 1,000 rows and 3 numeric features named f1, f2, f3 and a numeric target column named y, saved to data/dataset.csv under the project root.
- FR-003: The dataset MUST be generated deterministically using a fixed generator seed equal to 42 and MUST NOT be regenerated if data/dataset.csv already exists; subsequent runs MUST reuse the existing file.
- FR-004: The dataset MUST satisfy the following statistical properties computed on the full dataset: the Pearson correlation coefficient between f1 and f2 MUST be in the closed interval [0.80, 0.97]; the Pearson correlation between f3 and each of f1 and f2 MUST be in the closed interval [-0.20, 0.20].
- FR-005: The dataset generation MUST follow this exact process when data/dataset.csv does not exist:
  - Draw z ~ N(0, 1) as a length-1000 vector; draw e1 ~ N(0, 0.2^2), e2 ~ N(0, 0.2^2), e3 ~ N(0, 1^2) as independent length-1000 vectors using numpy.random.default_rng(seed=42).
  - Set f1 = z + e1; set f2 = z + e2; set f3 = e3.
  - Set y = 5.0 + 3.0*f1 - 2.0*f2 + 0.5*f3 + n, where n ~ N(0, 1^2) is an independent length-1000 vector using the same RNG.
  - Save columns in CSV with header order exactly: f1,f2,f3,y and with comma separators, LF line endings, and no index column.
- FR-006: The dataset generator MUST write a JSON metadata file at data/dataset_meta.json describing the dataset with the schema below and MUST overwrite it whenever the dataset is (re)generated.
```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["n_rows", "n_features", "feature_names", "target_name", "generation_seed", "correlations", "coefficients", "intercept", "noise_std"],
  "properties": {
    "n_rows": {"type": "integer", "const": 1000},
    "n_features": {"type": "integer", "const": 3},
    "feature_names": {"type": "array", "items": {"type": "string"}, "const": ["f1", "f2", "f3"]},
    "target_name": {"type": "string", "const": "y"},
    "generation_seed": {"type": "integer", "const": 42},
    "correlations": {
      "type": "object",
      "required": ["pearson_f1_f2", "pearson_f1_f3", "pearson_f2_f3"],
      "properties": {
        "pearson_f1_f2": {"type": "number", "minimum": 0.80, "maximum": 0.97},
        "pearson_f1_f3": {"type": "number", "minimum": -0.20, "maximum": 0.20},
        "pearson_f2_f3": {"type": "number", "minimum": -0.20, "maximum": 0.20}
      }
    },
    "coefficients": {
      "type": "object",
      "required": ["f1", "f2", "f3"],
      "properties": {
        "f1": {"type": "number", "const": 3.0},
        "f2": {"type": "number", "const": -2.0},
        "f3": {"type": "number", "const": 0.5}
      }
    },
    "intercept": {"type": "number", "const": 5.0},
    "noise_std": {"type": "number", "const": 1.0}
  }
}
```
- FR-007: The training script scripts/run_lr.py MUST accept a required CLI argument --seed <int> and optional arguments --data-dir <path> (default: "./data"), --out-dir <path> (default: "./experiments"), --test-size <float in (0,1)> (default: 0.2), and --run-id <string> (default: "lr_run_{seed}").
- FR-008: The script scripts/run_lr.py MUST validate that --data-dir and --out-dir resolve to subdirectories of the project root and MUST create them if they do not exist.
- FR-009: The script scripts/run_lr.py MUST load data/dataset.csv from --data-dir and MUST fail with exit code 3 if the file is missing and cannot be generated due to write permission or other I/O errors.
- FR-010: The script scripts/run_lr.py MUST split the dataset into train and test sets with a single call to sklearn.model_selection.train_test_split using test_size equal to --test-size, shuffle=True, and random_state equal to --seed.
- FR-011: The script scripts/run_lr.py MUST train sklearn.linear_model.LinearRegression (with default parameters) on the training set with features [f1, f2, f3] and target y using float64 precision.
- FR-012: The script scripts/run_lr.py MUST compute mean squared error (MSE) and R2 score on the test set using sklearn.metrics.mean_squared_error and sklearn.metrics.r2_score with default parameters.
- FR-013: After training and evaluation, the script MUST write a per-run artifact directory at {--out-dir}/{--run-id}/ that contains exactly the following files: config.json, metrics.json, coefficients.json, and logs.txt.
- FR-014: The file config.json MUST conform to the following schema and values used for the run.
```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["run_id", "seed", "data_dir", "out_dir", "test_size", "model_type", "dataset_path", "timestamp_utc"],
  "properties": {
    "run_id": {"type": "string", "pattern": "^[A-Za-z0-9_\\-]+$"},
    "seed": {"type": "integer"},
    "data_dir": {"type": "string"},
    "out_dir": {"type": "string"},
    "test_size": {"type": "number", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
    "model_type": {"type": "string", "const": "LinearRegression"},
    "dataset_path": {"type": "string"},
    "timestamp_utc": {"type": "string", "format": "date-time"}
  }
}
```
- FR-015: The file coefficients.json MUST contain the learned intercept and coefficients mapped by feature name with the following schema.
```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["intercept", "coef"],
  "properties": {
    "intercept": {"type": "number"},
    "coef": {
      "type": "object",
      "required": ["f1", "f2", "f3"],
      "properties": {
        "f1": {"type": "number"},
        "f2": {"type": "number"},
        "f3": {"type": "number"}
      }
    }
  }
}
```
- FR-016: The file metrics.json MUST contain evaluation metrics and dataset split counts following the schema below and MUST use ISO 8601 UTC timestamp with "Z" suffix.
```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["run_id", "seed", "model_type", "metrics", "counts", "timestamp_utc"],
  "properties": {
    "run_id": {"type": "string"},
    "seed": {"type": "integer"},
    "model_type": {"type": "string", "const": "LinearRegression"},
    "metrics": {
      "type": "object",
      "required": ["mse", "r2"],
      "properties": {
        "mse": {"type": "number"},
        "r2": {"type": "number", "minimum": -1.0, "maximum": 1.0}
      }
    },
    "counts": {
      "type": "object",
      "required": ["train_rows", "test_rows", "n_features"],
      "properties": {
        "train_rows": {"type": "integer", "minimum": 1},
        "test_rows": {"type": "integer", "minimum": 1},
        "n_features": {"type": "integer", "const": 3}
      }
    },
    "timestamp_utc": {"type": "string", "format": "date-time"}
  }
}
```
- FR-017: The script scripts/run_lr.py MUST write JSON files (config.json, metrics.json, coefficients.json) with UTF-8 encoding, newline at end of file, indent=2 spaces, and with keys in insertion order as defined in the schemas.
- FR-018: The script scripts/run_lr.py MUST append plain-text log lines to logs.txt including at least: dataset path, run_id, seed, test_size, train_rows, test_rows, MSE, and R2.
- FR-019: The script scripts/run_lr.py MUST print a single-line JSON object to stdout that exactly matches the metrics.json content without indentation or newlines (compact separators) and MUST not print any other stdout content.
- FR-020: The script scripts/run_lr.py MUST exit with code 0 on success; MUST exit with code 2 on argument validation errors; MUST exit with code 3 on dataset generation or loading errors; MUST exit with code 4 on training errors; MUST exit with code 5 on evaluation errors; MUST exit with code 6 on file I/O write errors.
- FR-021: The script scripts/run_lr.py MUST update a comparison report at {--out-dir}/lr_runs_comparison.json after each successful run by scanning subdirectories under --out-dir whose names start with "lr_run_" and contain a metrics.json file.
- FR-022: The comparison report lr_runs_comparison.json MUST conform to the schema below and MUST include all discovered runs.
```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["runs", "ranking_by_mse", "ranking_by_r2", "best_by_mse", "best_by_r2", "pairwise"],
  "properties": {
    "runs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["run_id", "seed", "mse", "r2"],
        "properties": {
          "run_id": {"type": "string"},
          "seed": {"type": "integer"},
          "mse": {"type": "number"},
          "r2": {"type": "number"}
        }
      }
    },
    "ranking_by_mse": {"type": "array", "items": {"type": "string"}},
    "ranking_by_r2": {"type": "array", "items": {"type": "string"}},
    "best_by_mse": {"type": "string"},
    "best_by_r2": {"type": "string"},
    "pairwise": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["delta_mse", "delta_r2"],
        "properties": {
          "delta_mse": {"type": "number"},
          "delta_r2": {"type": "number"}
        }
      }
    }
  }
}
```
- FR-023: The comparison report MUST compute ranking_by_mse as run_ids sorted by ascending MSE and ranking_by_r2 as run_ids sorted by descending R2, and MUST set best_by_mse and best_by_r2 to the first element of each respective ranking.
- FR-024: The comparison report MUST include pairwise deltas for every ordered pair of distinct runs in the format "{a}_vs_{b}" with delta_mse = mse[a] - mse[b] and delta_r2 = r2[a] - r2[b].
- FR-025: The script scripts/run_lr.py MUST ensure reproducibility such that executing the script twice with the same --seed, --test-size, and fixed dataset produces identical metrics.json content byte-for-byte.
- FR-026: The script scripts/run_lr.py MUST default to out-dir "./experiments" and MUST ensure that two runs "lr_run_1" and "lr_run_2" are comparable by using the same dataset.csv file.
- FR-027: The function generate_dataset(config: dict) MUST be implemented and MUST accept a config matching the schema below and MUST return a result matching the schema below.
```
Input Schema (generate_dataset):
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["data_dir", "force_regenerate"],
  "properties": {
    "data_dir": {"type": "string"},
    "force_regenerate": {"type": "boolean"}
  }
}

Return Schema (generate_dataset):
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["dataset_path", "meta_path", "generated"],
  "properties": {
    "dataset_path": {"type": "string"},
    "meta_path": {"type": "string"},
    "generated": {"type": "boolean"}
  }
}
```
- FR-028: The function run_experiment(config: dict) MUST be implemented and MUST accept a config matching the schema below and MUST return a result matching the schema below.
```
Input Schema (run_experiment):
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["seed", "data_dir", "out_dir", "test_size", "run_id"],
  "properties": {
    "seed": {"type": "integer"},
    "data_dir": {"type": "string"},
    "out_dir": {"type": "string"},
    "test_size": {"type": "number", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
    "run_id": {"type": "string", "pattern": "^[A-Za-z0-9_\\-]+$"}
  }
}

Return Schema (run_experiment):
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["artifacts_dir", "config_path", "metrics_path", "coefficients_path", "stdout_json"],
  "properties": {
    "artifacts_dir": {"type": "string"},
    "config_path": {"type": "string"},
    "metrics_path": {"type": "string"},
    "coefficients_path": {"type": "string"},
    "stdout_json": {
      "type": "object",
      "required": ["run_id", "seed", "model_type", "metrics", "counts", "timestamp_utc"],
      "properties": {
        "run_id": {"type": "string"},
        "seed": {"type": "integer"},
        "model_type": {"type": "string"},
        "metrics": {"type": "object"},
        "counts": {"type": "object"},
        "timestamp_utc": {"type": "string"}
      }
    }
  }
}
```
- FR-029: The script scripts/run_lr.py MUST implement the CLI by calling run_experiment() and MUST propagate its success or failure exit codes as defined in FR-020.
- FR-030: The two experiment commands "python scripts/run_lr.py --seed 1" and "python scripts/run_lr.py --seed 2" executed from the project root MUST produce artifact directories "./experiments/lr_run_1" and "./experiments/lr_run_2" and MUST update "./experiments/lr_runs_comparison.json".

# Technical Requirements (TR)

- TR-001: The application MUST be written in Python 3.11.
- TR-002: The script scripts/run_lr.py MUST use argparse from the Python standard library for CLI parsing.
- TR-003: The dataset and model code MUST use numpy version 1.26.4.
- TR-004: The model training and evaluation MUST use scikit-learn version 1.4.2.
- TR-005: CSV I/O MUST use pandas version 2.2.2.
- TR-006: All numeric computations MUST use float64 precision.
- TR-007: Random number generation for dataset creation MUST use numpy.random.default_rng with seed=42; random operations for splitting MUST use scikit-learn's random_state set to the --seed value.
- TR-008: Timestamps written to JSON MUST be in UTC in ISO 8601 format with "Z" suffix (e.g., "2025-08-24T01:23:45.678901Z").
- TR-009: The code MUST be compatible with macOS 12+ and Linux x86_64 environments and MUST not require a GPU.
- TR-010: The project MUST not write files outside the project root; any provided absolute path arguments MUST resolve within the project root after normalization.
- TR-011: Logging MUST use Python's logging module with level INFO and format "%(asctime)s %(levelname)s %(message)s" in UTC.
- TR-012: File writes for JSON MUST use json.dump with indent=2, ensure_ascii=False, separators=(", ", ": "), and a trailing newline.
- TR-013: The repository MUST contain all code under the existing scripts/ and root directories and MUST not create new top-level folders other than "data" and "experiments".

# Non-Functional Requirements (NFR)

- NFR-001: Each run of scripts/run_lr.py with default settings MUST complete in under 5 seconds on a single CPU core of a 2019+ consumer laptop.
- NFR-002: Peak resident memory usage per run MUST not exceed 256 MB.
- NFR-003: Re-executing scripts/run_lr.py twice with identical arguments and unchanged dataset files MUST produce identical bytes for config.json, metrics.json, and coefficients.json.
- NFR-004: The correlation checks in FR-004 MUST be computed with absolute tolerance 1e-12 for bounds comparison and MUST trigger an error if out of bounds.
- NFR-005: Floating-point values written to JSON MUST preserve full double precision as produced by Python's default float to string conversion and MUST not be rounded or truncated.
- NFR-006: The comparison report lr_runs_comparison.json update operation MUST complete in under 200 ms for up to 50 runs in the --out-dir.
- NFR-007: The stdout single-line JSON printed by scripts/run_lr.py MUST be under 2 KB in size with default settings.
- NFR-008: The project MUST not create or modify any files other than those specified in FR-013, FR-016, FR-021, and FR-006.

# Success Criteria

- All CLI arguments defined in FR-007 are accepted, validated, and applied, and "python scripts/run_lr.py --seed 1" and "python scripts/run_lr.py --seed 2" exit with code 0.
- The data/dataset.csv and data/dataset_meta.json files exist after first run and match the schemas and properties defined in FR-005 and FR-006.
- The artifact directories "./experiments/lr_run_1" and "./experiments/lr_run_2" contain config.json, metrics.json, coefficients.json, and logs.txt files that validate against the schemas in FR-014, FR-015, and FR-016.
- The stdout from each run is a single-line JSON identical to the corresponding metrics.json content.
- The comparison report "./experiments/lr_runs_comparison.json" exists after both runs and validates against the schema in FR-022, with correct rankings per FR-023 and pairwise deltas per FR-024.
- Re-running either command with the same arguments produces byte-identical JSON artifacts, satisfying NFR-003.