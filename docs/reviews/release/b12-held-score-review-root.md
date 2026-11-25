# Held-run scoring defect

Date: 2026-11-15 UTC. Author: skill-dev-lead.

All 33 entries in `docs/reviews/b12-harness-freeze-claude.sha256` match.
The lead ran one local probe with `uv run --with pyyaml==6.0.3 python`.
The probe imported `run_case`, `score` and `common` from `tests/eval`.
It selected the first scheduled run from `plan_runs(load_matrix())`.
It called `execute` with `held_stub` and a temporary output directory.
Then it read the retained `run.json` and called `summarize` with that record.
No provider call occurred.

Measured result:

```json
{
  "execute_status": "held",
  "retained_evidence": null,
  "summary": {
    "table": {
      "routing": {
        "S1": {"pass": 0, "fail": 0, "na": 1},
        "S2": {"pass": 0, "fail": 0, "na": 1},
        "S3": {"pass": 0, "fail": 0, "na": 1},
        "S4": {"pass": 1, "fail": 0, "na": 0},
        "S5": {"pass": 1, "fail": 0, "na": 0}
      }
    },
    "hard_failures": 0
  }
}
```

The dispatcher correctly refuses this run. The scorer incorrectly counts two passes.
`summarize` excludes only records with `evidence: mock`.
`score_run` defaults absent evidence to `live`.

Correction: keep execution status and evidence type explicit.
A held, unauthorized or unexecuted record must not enter the measured release table.
Missing evidence must not mean live evidence.
Retain those records in a separate execution summary.
Test each refusal state, missing evidence, mock evidence and an explicit measured live record.
Preserve measured failures from live attempts. Do not exclude failures to improve the result.

This correction concerns the accepted separation between local tests and measured provider results.
The probe changed no product file.
