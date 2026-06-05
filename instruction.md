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

## Judge Feedback Format

After `sebench-submit`, the hidden judge returns aggregate score plus coarse
component feedback. The feedback is intentionally coarse: it helps you choose
what to improve next without revealing hidden target values or exact component
sub-scores.

Main fields:

- `TOTAL_SCORE`: overall score out of 100. For this continuous-score task, a
  higher score is better.
- `CASE aggregate OK score=<value>`: the same aggregate score in the format used
  by the SE-Bench `score_sum` parser.
- `TASK_RESULT model_prediction low|medium|high`: concentration prediction
  quality for hidden well/year/analyte requests. This is the largest component
  (45 points).
- `TASK_RESULT risk_classification low|medium|high`: threshold exceedance
  classification quality, based on whether each predicted concentration crosses
  its analyte threshold (20 points).
- `TASK_RESULT plume_metrics low|medium|high`: quality of plume-front,
  centerline, and mass-proxy estimates in `plume_metrics.json` (26 points).
- `TASK_RESULT monitoring_design low|medium|high`: quality of the selected
  candidate monitoring wells under budget and max-well constraints (6 points).
- `TASK_RESULT report low|medium|high`: completeness of the technical report and
  `answer.json` summary (1 point).
- `MODEL_FEEDBACK`, `RISK_FEEDBACK`, `METRIC_FEEDBACK`, `PLAN_FEEDBACK`, and
  `REPORT_FEEDBACK`: short directional comments about what to improve.

Band meanings:

- `low`: below 35% of that component's maximum score.
- `medium`: 35% to 72% of that component's maximum score.
- `high`: at least 72% of that component's maximum score.

Use these bands as a prioritization signal. For example, `model_prediction low`
means point concentration predictions need work; `plume_metrics low` means the
spatial plume-front/centerline/mass estimates need work. The bands do not reveal
hidden truth values, per-target errors, exact sub-scores, or hidden candidate
utilities.
