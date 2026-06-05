# CapeCod-PlumeBench

You are a groundwater remediation modeling engineer.

This task is inspired by the USGS Cape Cod treated-wastewater groundwater plume monitoring program.
The benchmark is offline and deterministic: public files are a partial observation set from a
physics-inspired synthetic derivative of that real monitoring setting, while the judge keeps hidden
wells, hidden years, hidden perturbed plume scenarios, and the scoring data.

## Goal

Build a model that reconstructs and extrapolates a contaminant plume in a sand-and-gravel aquifer.
You must predict hidden well/year/analyte concentrations, estimate plume-scale metrics, and propose
the next monitoring campaign under a fixed budget.

## Files You Can See

- `data/public_wells.csv`: monitor well locations and screen depths visible during model fitting.
- `data/public_observations.csv`: measured/censored historical concentrations through mostly 2008.
- `data/prediction_requests.csv`: well/year/analyte points to predict. It includes hidden wells and
  future years, but not their values.
- `data/plume_metric_requests.csv`: plume metric requests for hidden judge scoring.
- `data/candidate_monitoring_wells.csv`: candidate wells for the next sampling campaign.
- `data/public_site_config.json`: units, thresholds, budget, and site metadata.
- `schemas/output_schema.json`: required output structure.

## Required Outputs

Create or update these files in the task root:

- `model.py`
- `predict.py`
- `monitoring_plan.py`
- `predictions.csv`
- `plume_metrics.json`
- `monitoring_plan.json`
- `answer.json`
- `report.md`

`predictions.csv` must contain:

```text
target_id,predicted_value
```

`plume_metrics.json` must contain a `metrics` list. Each item must include:

```json
{
  "request_id": "M001",
  "plume_front_x_m": 0.0,
  "centerline_y_m": 0.0,
  "mass_proxy": 0.0
}
```

`monitoring_plan.json` must contain:

```json
{
  "selected_wells": [
    {"candidate_id": "C001", "reason": "front uncertainty"}
  ],
  "total_cost_usd": 0.0,
  "method": "brief method"
}
```

Select at most 8 candidate wells and keep total cost under the budget in
`data/public_site_config.json`.

## Modeling Hints

The hidden reference contains advection, dispersion, attenuation, plume bending, depth effects,
source shutdown, rebound, future plume acceleration, and a strong hidden scenario shift. A constant discount or a pure global
mean is intentionally weak. Strong submissions usually combine:

- robust handling of censored low values and missing data;
- space-time interpolation or parametric advection-dispersion features;
- analyte-specific retardation/attenuation behavior;
- plume-front and margin-aware monitoring design;
- validation against public historical years instead of fitting only one analyte.

Do not try to read hidden judge files or scoring code. Your code is run as a restricted user during
evaluation, and hidden truth files are outside the workspace.

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
