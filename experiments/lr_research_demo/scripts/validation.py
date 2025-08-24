from typing import Dict, Any
import math


def validate_run_metrics(metrics: Dict[str, Any]) -> bool:
    """Validate that metrics dict contains finite mse, r2 in [-1,1], and train+val==1000.

    Returns True if metrics pass, False otherwise.
    """
    try:
        mse = float(metrics.get("mse"))
        r2 = float(metrics.get("r2"))
        train = int(metrics.get("train_samples"))
        val = int(metrics.get("val_samples"))
    except Exception:
        return False

    if math.isnan(mse) or math.isinf(mse):
        return False
    if not (-1.0 <= r2 <= 1.0):
        return False
    if train + val != 1000:
        return False
    return True
