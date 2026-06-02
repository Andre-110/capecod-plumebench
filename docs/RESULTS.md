# CapeCod-PlumeBench Verification Results

## Task Registration

Task JSON:

```text
/root/SE-bench-main/tasks/capecod_plumebench.json
```

`uv run sebench list --all` shows:

```text
capecod_plumebench   CapeCod-PlumeBench   python   ready   score_sum
```

## Built Images

Verified with `docker images`:

```text
sebench.base.python:latest
sebench.work.capecod_plumebench:latest
sebench.judge.capecod_plumebench:latest
```

Build command:

```bash
cd /root/SE-bench-main
SEBENCH_APT_MIRROR_URL="http://mirrors.ivolces.com" \
SEBENCH_PYPI_INDEX_URL="https://mirrors.ivolces.com/pypi/simple/" \
uv run sebench build --task capecod_plumebench --force-rebuild
```

## Work/Judge Isolation

The work image contains public data and starter code only. It does not contain `/opt/capecod_hidden`.

The judge image contains hidden truth under:

```text
/opt/capecod_hidden
```

That directory is root-only (`drwx------`). A `runner` user check returned:

```text
cat: /opt/capecod_hidden/hidden_targets.csv: Permission denied
runner_exit=1
```

The scorer runs submitted code as `runner`, then root-owned scoring code reads hidden data.

## Baseline Evaluation

Archive:

```text
/root/SE-bench-main/task_blueprints/capecod_plumebench/empty_baseline.tar.gz
```

Command:

```bash
docker run --rm sebench.judge.capecod_plumebench:latest \
  /bin/bash -lc 'python /opt/capecod_scoring/evaluate.py'
```

Result:

```text
score: 6.499 / 100
cases: 1/1 parsed
```

Output:

```text
CASE aggregate OK score=6.499 aggregate score only
TOTAL_SCORE 6.499
CASES_OK 1
CASES_TOTAL 1
```

This post-hardening check was run directly against the rebuilt judge image because the sandboxed
`uv run sebench eval` command was denied Docker socket access during this pass. Earlier SE-Bench CLI
evaluation had already verified the task plumbing; this direct judge-image run verifies the current
scoring behavior after the difficulty changes.

## Reference Evaluation

Archive:

```text
/root/SE-bench-main/task_blueprints/capecod_plumebench/reference_submission.tar.gz
```

Command:

```bash
docker run --rm \
  -v /root/SE-bench-main/task_blueprints/capecod_plumebench/reference_submission.tar.gz:/tmp/submission.tar.gz:ro \
  sebench.judge.capecod_plumebench:latest \
  /bin/bash -lc 'cd /home/workspace/capecod_plumebench && tar xzf /tmp/submission.tar.gz && python /opt/capecod_scoring/evaluate.py'
```

Result:

```text
score: 100.000 / 100
cases: 1/1 parsed
```

Output:

```text
CASE aggregate OK score=100.000 aggregate score only
TOTAL_SCORE 100.000
CASES_OK 1
CASES_TOTAL 1
```

## Regeneration

The task JSON, generator script, acceptance note, and reference submission can be regenerated with:

```bash
python3 /root/SE-bench-main/task_blueprints/capecod_plumebench/build_task.py --write-reference
```
