from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from model import predict_values


ROOT = Path(__file__).resolve().parent


def main() -> None:
    config = json.loads((ROOT / "data" / "public_site_config.json").read_text())
    candidates = pd.read_csv(ROOT / "data" / "candidate_monitoring_wells.csv")
    # Deliberately weak starter: select a cheap geographically broad plan rather
    # than optimizing hidden information value.
    candidates["total_cost"] = candidates["install_cost_usd"] + candidates["annual_sampling_cost_usd"]
    candidates["score"] = -candidates["total_cost"] + 120.0 * (candidates["zone"] == "front").astype(float)
    candidates = candidates.sort_values("score", ascending=False)
    selected = []
    total = 0.0
    for row in candidates.itertuples(index=False):
        cost = float(row.install_cost_usd) + float(row.annual_sampling_cost_usd)
        if len(selected) >= int(config["monitoring_budget"]["max_new_wells"]):
            break
        if total + cost > float(config["monitoring_budget"]["budget_usd"]):
            continue
        selected.append({"candidate_id": row.candidate_id, "reason": "low-cost broad baseline coverage"})
        total += cost
    payload = {
        "selected_wells": selected,
        "total_cost_usd": round(total, 2),
        "method": "Weak baseline selects low-cost candidate wells with a small plume-front preference.",
    }
    (ROOT / "monitoring_plan.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
