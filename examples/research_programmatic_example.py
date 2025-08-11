import asyncio
from datetime import datetime
from pathlib import Path
from equitrcoder.programmatic.interface import EquitrCoder, ResearchTaskConfiguration
import json
import random
import os


TASK_NAME = "Evaluate simple ML models on synthetic data"
TASK_DESCRIPTION = (
    "Generate a synthetic binary classification dataset, run multiple simple ML models "
    "(heuristic classifiers) against it, and report which performs best on a holdout split."
)


async def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = Path(f"generated_projects/research_{ts}").resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    # Sandbox all commands and file ops to the project directory
    os.chdir(str(project_dir))

    # --- Prepare synthetic data ---
    data_dir = project_dir / "data"
    results_dir = project_dir / "results"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic random seed
    rng = random.Random(42)
    num_samples = 1000
    num_features = 10
    weights = [0.6, -0.4, 0.3, -0.2, 0.5, -0.1, 0.2, -0.3, 0.1, 0.4]

    dataset_path = data_dir / "synthetic_classification.csv"
    with dataset_path.open("w", encoding="utf-8") as f:
        # Header
        f.write(",".join([f"f{i}" for i in range(num_features)]) + ",label\n")
        for _ in range(num_samples):
            features = [rng.uniform(-1.0, 1.0) for _ in range(num_features)]
            # Simple linear decision boundary with noise
            score = sum(w * x for w, x in zip(weights, features)) + 0.1 * rng.uniform(-1.0, 1.0)
            label = 1 if score >= 0 else 0
            f.write(",".join(f"{v:.6f}" for v in features) + f",{label}\n")

    # --- Create training/eval script (no external deps) ---
    train_script = project_dir / "train_eval.py"
    train_script.write_text(
        """
import argparse, csv, json

def load_dataset(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            *feat_str, label_str = row
            feats = [float(x) for x in feat_str]
            label = int(label_str)
            rows.append((feats, label))
    return rows

def split_data(rows, train_ratio=0.8):
    n = len(rows)
    cut = int(n * train_ratio)
    return rows[:cut], rows[cut:]

def predict(model, feats):
    if model == "feature0_sign":
        return 1 if feats[0] >= 0 else 0
    if model == "feature1_sign":
        return 1 if feats[1] >= 0 else 0
    if model == "sum_threshold":
        return 1 if sum(feats) >= 0 else 0
    if model == "two_feature_weighted":
        return 1 if (0.7*feats[0] + 0.3*feats[1]) >= 0 else 0
    if model == "all_weighted":
        weights = [0.5, 0.3, -0.2, 0.1, 0.4, -0.1, 0.2, -0.3, 0.1, 0.1]
        s = sum(w*x for w, x in zip(weights, feats))
        return 1 if s >= 0 else 0
    # default fallback
    return 1 if feats[0] >= 0 else 0

def evaluate(model, rows):
    correct = 0
    for feats, label in rows:
        pred = predict(model, feats)
        if pred == label:
            correct += 1
    return correct / max(1, len(rows))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default="data/synthetic_classification.csv")
    ap.add_argument("--model", type=str, required=True)
    ap.add_argument("--results", type=str, default="results")
    args = ap.parse_args()

    rows = load_dataset(args.data)
    train, test = split_data(rows)
    acc = evaluate(args.model, test)
    out = {"model": args.model, "accuracy": acc}
    print(json.dumps(out))
    # persist
    import os
    os.makedirs(args.results, exist_ok=True)
    with open(os.path.join(args.results, f"{args.model}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)

if __name__ == "__main__":
    main()
        """.strip()
    )

    # --- Configure research task ---
    coder = EquitrCoder(repo_path=str(project_dir), mode="research")
    config = ResearchTaskConfiguration(
        description=TASK_NAME,
        max_workers=3,
        max_cost=12.0,
        supervisor_model="openai/gpt-4o",
        worker_model="openai/gpt-4o-mini",
        team=["ml_researcher", "data_engineer", "experiment_runner"],
        research_context={
            "datasets": [
                {"path": str(dataset_path), "description": "Synthetic binary classification dataset"}
            ],
            "experiments": [
                {"name": "feature0_sign", "command": "python train_eval.py --model feature0_sign --data data/synthetic_classification.csv --results results"},
                {"name": "feature1_sign", "command": "python train_eval.py --model feature1_sign --data data/synthetic_classification.csv --results results"},
                {"name": "sum_threshold", "command": "python train_eval.py --model sum_threshold --data data/synthetic_classification.csv --results results"},
                {"name": "two_feature_weighted", "command": "python train_eval.py --model two_feature_weighted --data data/synthetic_classification.csv --results results"},
                {"name": "all_weighted", "command": "python train_eval.py --model all_weighted --data data/synthetic_classification.csv --results results"},
            ],
        },
    )
    result = await coder.execute_task(TASK_DESCRIPTION, config)
    print("Success:", result.success)
    print("Cost:", result.cost)
    print("Execution Time:", result.execution_time)

    # Summarize best model from results
    best = None
    for p in sorted((results_dir).glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            acc = float(data.get("accuracy", 0.0))
            if best is None or acc > best[1]:
                best = (data.get("model", p.stem), acc)
        except Exception:
            continue
    if best:
        print(f"Best model: {best[0]} with accuracy={best[1]:.4f}")
        print(f"Results folder: {results_dir}")


if __name__ == "__main__":
    asyncio.run(main()) 