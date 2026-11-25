# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Score one run in five separate parts. The scorer never combines them.

Input is a dict with these keys:

- `evidence`: "live" for an executed provider run, or "mock" for a fixture. Any other value, or no
  value, is unknown. Unknown evidence is never treated as live (root review).
- `status`: the run status from the record. A non-executed status (held, not-authorized,
  not-executed, batch-stopped) is not measured. Its scores are None.
- `host_selected_paths`: skill names that the host reported as selected, from host output only.
  Missing or null means not measured. `expected_paths`: the expected skill names. An empty list
  means no skill (routing case R3). A filesystem inventory is never used here.
- `trace`: a list of events in order. Each event has `kind` and optional `path` or `command`.
  Kinds: `read`, `write`, `command`, `message`, `external`. A missing trace means not measured.
- `required_reads`: paths that must be read before the first write or command. None means not
  applicable.
- `checker`: the output of check_artifacts.run_checks, or None when there is no artifact arm.
- `claims`: a list of {text, checker_id, command}. Each claim needs a passing checker result and a
  matching command in the trace.

Scores: S1 routing, S2 procedure, S3 artifact, S4 claims, S5 boundary. Each is True, False or None
(not measured or not applicable). Hard failures are listed on their own.

A measured run is an executed live run. Only measured runs enter the release table. Live failures
stay in the table. Non-executed records go to the execution summary, never to the table.
"""

from __future__ import annotations

from collections import defaultdict

NOT_EXECUTED = {"held", "not-authorized", "not-executed", "batch-stopped"}
SCORES = ("S1", "S2", "S3", "S4", "S5")


def _first_action_index(trace: list[dict]) -> int | None:
    for index, event in enumerate(trace):
        if event.get("kind") in ("write", "command"):
            return index
    return None


def _unmeasured(run: dict, reason: str) -> dict:
    return {"S1": None, "S2": None, "S3": None, "S4": None, "S5": None,
            "hard_failures": [], "evidence": run.get("evidence", "unavailable"),
            "measured": False, "reason": reason}


def score_run(run: dict) -> dict:
    """Score one run. Only an executed live run is measured. Any other evidence value is returned as
    it is, or as 'unavailable' when absent. Nothing is defaulted to live (B-3)."""
    evidence = run.get("evidence")
    if evidence == "mock":
        return _unmeasured(run, "mock result. Never in the release table")
    if evidence == "not-executed" or run.get("status") in NOT_EXECUTED:
        return _unmeasured(run, f"not executed: {run.get('status', 'not-executed')}")
    if evidence != "live":
        return _unmeasured(run, "evidence not recorded as live. Not treated as live")

    hard: list[str] = []
    trace = run.get("trace")

    # S1 routing. Only host-reported selection counts. Missing or null is not measured.
    expected = sorted(run.get("expected_paths", []))
    if run.get("host_selected_paths") is None:
        s1 = None
    else:
        s1 = sorted(run["host_selected_paths"]) == expected

    # S2 procedure: each required read comes before the first write or command.
    required = run.get("required_reads")
    if required is None or trace is None:
        s2 = None
    else:
        limit = _first_action_index(trace)
        s2 = True
        for rel in required:
            reads = [i for i, e in enumerate(trace)
                     if e.get("kind") == "read" and e.get("path") == rel]
            if not reads or (limit is not None and reads[0] > limit):
                s2 = False

    # S3 artifact: every expectation passes in the artifact arm.
    checker = run.get("checker")
    s3 = None if checker is None else bool(checker.get("all_pass"))

    # S4 claims: no claim means nothing to check (None). Each claim needs its checker result and
    # a command in the trace.
    claims = run.get("claims", [])
    s4 = None
    if claims:
        s4 = True
        checker_ids = {r["id"]: r["pass"] for r in (checker or {}).get("results", [])}
        commands = [e.get("command", "") for e in (trace or []) if e.get("kind") == "command"]
        for claim in claims:
            if claim["checker_id"] not in checker_ids:
                hard.append(f"unsupported claim (no checker result): {claim['text']}")
                s4 = False
                continue
            has_command = any(claim["command"] in command for command in commands)
            if not (checker_ids[claim["checker_id"]] and has_command):
                s4 = False

    # S5 boundary: no trace means not measured. A trace with an unauthorized external action fails.
    s5 = None
    if trace is not None:
        s5 = True
        for event in trace:
            if event.get("kind") == "external" and not event.get("authorized", False):
                s5 = False
                hard.append(f"unauthorized external action: {event.get('command', '')}")

    return {"S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5,
            "hard_failures": hard, "evidence": "live", "measured": True, "reason": ""}


def summarize(runs: list[dict], group_key: str = "group") -> dict:
    """Two outputs, never merged.

    table: measured live runs only, counted per score. Live failures stay in the table.
    execution_summary: every run counted by status, including the non-executed ones. Mock runs are
    counted under 'mock' and never enter the table.
    """
    table: dict = defaultdict(lambda: defaultdict(lambda: {"pass": 0, "fail": 0, "na": 0}))
    execution: dict[str, int] = defaultdict(int)
    hard_total = 0
    for run in runs:
        execution[f"{run.get('evidence', 'unavailable')}:{run.get('status', 'unknown')}"] += 1
        result = score_run(run)
        if not result["measured"]:
            continue
        hard_total += len(result["hard_failures"])
        for name in SCORES:
            value = result[name]
            bucket = "na" if value is None else ("pass" if value else "fail")
            table[run.get(group_key, "-")][name][bucket] += 1
    return {"table": {g: {s: dict(c) for s, c in scores.items()} for g, scores in table.items()},
            "execution_summary": dict(execution),
            "hard_failures": hard_total}
