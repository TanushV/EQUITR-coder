import json
import os
import subprocess
import tempfile
from pathlib import Path


def test_cli_smoke(tmp_path):
    # Run dataset generation
    cwd = Path.cwd()
    # Ensure we run from project root
    assert (cwd / "requirements.md").exists(), "Run tests from project root"

    # Force regenerate dataset
    subprocess.check_call(["python", "-m", "scripts.run_lr", "--generate-dataset", "--force-regenerate"])

    # Run via runner.py to execute an experiment with seed 0
    subprocess.check_call(["python", "runner.py", "run", "--seed", "0"]) 

    # Verify artifacts directory and at least one run exists
    artifacts_dir = Path("./artifacts")
    assert artifacts_dir.exists(), "artifacts dir missing"
    runs = [d for d in artifacts_dir.iterdir() if d.is_dir()]
    assert len(runs) > 0, "No run directories created"

    # Find a metrics.json in any run and validate keys
    found = False
    for r in runs:
        mp = r / "metrics.json"
        if mp.exists():
            found = True
            with mp.open("r", encoding="utf-8") as f:
                m = json.load(f)
            # Check expected keys
            for k in ("seed", "mse", "r2", "n_parameters", "train_samples", "val_samples", "created"):
                assert k in m, f"Key {k} missing in metrics.json"
            break
    assert found, "No metrics.json found in any run dir"
