# CapeCod-PlumeBench Agent Instructions

You are a groundwater remediation modeling engineer. The workspace contains
partial public monitoring data from an offline benchmark inspired by the USGS
Cape Cod treated-wastewater groundwater plume.

Your job is to replace the weak baseline with a better, defensible modeling
workflow that:

1. Cleans and interprets public well, chemistry, and site-configuration data.
2. Predicts hidden well/year/analyte concentrations listed in
   `data/prediction_requests.csv`.
3. Estimates plume metrics requested in `data/plume_metric_requests.csv`.
4. Proposes up to 8 next monitoring wells under the budget in
   `data/public_site_config.json`.
5. Writes a concise technical report explaining your model, assumptions,
   validation, and monitoring logic.

Required outputs:

- `model.py`
- `predict.py`
- `monitoring_plan.py`
- `predictions.csv`
- `plume_metrics.json`
- `monitoring_plan.json`
- `answer.json`
- `report.md`

Run:

```bash
python baseline_solver.py
```

to regenerate outputs before submitting. The starter baseline is valid but
intentionally weak. Good solutions use space-time structure, analyte-specific
behavior, plume-front geometry, censored observations, and uncertainty-aware
monitoring selection.

Rules:

- Do not attempt to read hidden judge or scoring files.
- Do not hard-code target truth values or hidden candidate utilities.
- Keep all outputs finite, nonnegative, and schema-compliant.
- Respect the monitoring budget and maximum number of wells.
