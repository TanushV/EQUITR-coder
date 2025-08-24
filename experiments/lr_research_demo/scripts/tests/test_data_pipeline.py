from pathlib import Path
import pandas as pd

from scripts.data_pipeline.ingest import load_and_split


def test_load_and_split_reproducible():
    examples = Path(__file__).parents[1] / "examples"
    cfg = examples / "dataset.yaml"

    train1, val1, test1 = load_and_split(str(cfg))
    train2, val2, test2 = load_and_split(str(cfg))

    # DataFrames should be identical across repeated calls (deterministic splits)
    assert train1.equals(train2)
    assert val1.equals(val2)
    assert test1.equals(test2)

    # Sizes should sum to the original row count
    total = len(train1) + len(val1) + len(test1)
    df = pd.read_csv(examples / "tiny_sample.csv", encoding="utf-8")
    assert total == len(df)
