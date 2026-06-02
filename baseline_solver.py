from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(script: str) -> None:
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)


def main() -> None:
    run("predict.py")
    run("monitoring_plan.py")
    if not (ROOT / "answer.json").exists():
        (ROOT / "answer.json").write_text(
            json.dumps(
                {
                    "schema_version": "capecod_plumebench.v1",
                    "model_summary": {
                        "approach": "space-time inverse-distance baseline",
                        "known_limitations": "weak extrapolation and no explicit transport calibration",
                    },
                    "monitoring_strategy": "rank candidates by predicted nitrate and plume-front coverage",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    if not (ROOT / "report.md").exists():
        (ROOT / "report.md").write_text(
            "# CapeCod-PlumeBench Baseline Report\n\n"
            "This starter baseline uses analyte-level historical medians, coarse placeholder plume metrics, "
            "and a low-cost monitoring rule. It is schema-valid but intentionally weak: it does not model "
            "advection, dispersion, plume bending, future source rebound, hidden scenario shift, or uncertainty. "
            "It should be replaced with a calibrated advection-dispersion or hybrid groundwater model.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
