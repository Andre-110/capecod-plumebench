from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from model import estimate_metrics, predict_values


ROOT = Path(__file__).resolve().parent


def main() -> None:
    requests = pd.read_csv(ROOT / "data" / "prediction_requests.csv")
    preds = predict_values(requests)
    out = pd.DataFrame({"target_id": requests["target_id"], "predicted_value": preds})
    out.to_csv(ROOT / "predictions.csv", index=False)

    metric_requests = pd.read_csv(ROOT / "data" / "plume_metric_requests.csv")
    metrics = estimate_metrics(metric_requests)
    (ROOT / "plume_metrics.json").write_text(json.dumps({"metrics": metrics}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
