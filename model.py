from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def _load_public():
    wells = pd.read_csv(ROOT / "data" / "public_wells.csv")
    obs = pd.read_csv(ROOT / "data" / "public_observations.csv")
    obs = obs.merge(wells, on="well_id", how="left")
    obs["value"] = pd.to_numeric(obs["value"], errors="coerce")
    obs = obs.dropna(subset=["value", "x_m", "y_m", "screen_depth_m", "year"])
    obs.loc[obs["remark"].eq("less_than_detection"), "value"] *= 1.4
    return obs


def predict_values(requests: pd.DataFrame) -> pd.Series:
    obs = _load_public()
    medians = obs.groupby("analyte")["value"].median().to_dict()
    recent = obs[obs["year"] >= 2002].groupby("analyte")["value"].median().to_dict()
    outputs = []
    for req in requests.itertuples(index=False):
        # Deliberately weak starter: an analyte-level historical baseline with
        # only a coarse downgradient multiplier. It is valid but not a transport model.
        pred = float(0.65 * medians.get(req.analyte, 0.0) + 0.35 * recent.get(req.analyte, medians.get(req.analyte, 0.0)))
        x_factor = 1.0 + 0.10 * max(min((float(req.x_m) - 1200.0) / 3600.0, 1.0), 0.0)
        future_decay = max(0.45, 1.0 - 0.035 * max(float(req.year) - 2008.0, 0.0))
        pred *= x_factor * future_decay
        outputs.append(max(0.0, pred))
    return pd.Series(outputs)


def estimate_metrics(metric_requests: pd.DataFrame) -> list[dict]:
    metrics = []
    for req in metric_requests.itertuples(index=False):
        # Coarse placeholder metrics: schema-correct but intentionally weak.
        year = float(req.year)
        front = max(0.0, 1850.0 + 25.0 * (year - 2010.0))
        center_y = 0.0
        mass_proxy = max(0.0, 4500.0 - 55.0 * (year - 2010.0))
        metrics.append(
            {
                "request_id": req.request_id,
                "plume_front_x_m": round(front, 3),
                "centerline_y_m": round(center_y, 3),
                "mass_proxy": round(mass_proxy, 6),
            }
        )
    return metrics
