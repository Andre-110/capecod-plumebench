# CapeCod-PlumeBench Acceptance Note

## Data source and realism

The task is anchored in the USGS Cape Cod treated-wastewater groundwater plume monitoring program.
The benchmark data are an offline, deterministic, physics-inspired derivative rather than a live
download. This avoids fragile network dependencies while preserving the real research workflow:
well chemistry, sand-and-gravel aquifer transport, plume reconstruction, future concentration
prediction, and monitoring design.

## Why this is a long-horizon research-agent task

A strong solution requires more than fitting one CSV. The agent must clean censored observations,
infer analyte-specific plume behavior, extrapolate to hidden wells and future years, estimate plume
front metrics, and optimize a monitoring plan under budget. A human-quality solution would normally
take more than 20 hours: site understanding, exploratory analysis, model design, validation,
uncertainty analysis, monitoring-plan optimization, report writing, and debugging.

## Hidden judge and anti-leakage

The work image contains only public data. Hidden truths and candidate utilities are generated in the
judge image under `/opt/capecod_hidden`; scoring code is under `/opt/capecod_scoring`. During grading,
submitted code runs as an unprivileged `runner` user, while hidden files are readable only by root.
The root-owned scorer reads hidden data after submitted outputs are produced.

## Scoring

The judge emits a coarse aggregate `CASE ... score=...` line, qualitative `TASK_RESULT`/`*_FEEDBACK`
bands, and `TOTAL_SCORE`, parsed by the SE-Bench `score_sum` parser. It does not expose hidden truth
values or exact component scores. Internally, the score totals 100:

- format and constraints: 2
- hidden concentration prediction: 45
- threshold exceedance classification: 20
- plume metric estimation: 26
- monitoring well plan: 6
- report and explanation: 1

The task is deterministic and fully automated. Environment idle time is low because the generated
dataset is small and scoring typically runs in seconds to minutes after image build.

## Verified baseline and reference scores

After the hard-v3 pass, the starter baseline is expected to remain below 15/100. The score budget is concentrated in
hidden concentration prediction, threshold-risk classification, and plume metrics. Format, report,
and simple monitoring-plan points are intentionally capped. The judge returns coarse feedback bands
so agents can learn directionally without seeing hidden targets or exact sub-scores.

The reference submission scores 100.000/100. It uses the hidden plume generator to validate that the
score is attainable for a physically correct solution, including concentration prediction,
threshold-risk classification, plume metrics, budget-feasible monitoring design, and reporting.
