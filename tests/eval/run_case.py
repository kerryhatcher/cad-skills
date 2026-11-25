# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Plan the scheduled runs, classify their readiness, refuse held or unauthorized cells before any
provider dispatch, enforce the budget ledger and write run records.

This revision has no provider adapter. No provider call happens from this file. The tests inject a
provider stub with usage records. A stub that receives a held run fails the test.

Three counts stay separate (lead decision, root review R1):

- scheduled: the accepted design, 210 runs.
- fixture-ready: runs whose skill is accepted and whose artifact fixture is frozen (or whose routing is
  ready). A held run never reaches the provider.
- authorized: runs the lead allows for provider dispatch. Zero until the lead authorizes a batch.

Accounting limits, stated in every report:

- Tokens are host-reported. They are not provider billing and not a measure of all provider use.
- Each dispatched run reserves its full ceiling before it starts. The batch stops before a run whose
  reserve does not fit.
- A started request is not cut off. Its overrun is recorded. A missing count is unavailable and is
  charged at the full ceiling.
- Wall-clock time is measured by the harness. Turn limits depend on a host adapter, which this
  revision does not have.
- No automatic retry runs. A failed attempt stays on disk.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from adapters import baseline_policy
from common import counts, load_matrix

ARTIFACT_CELL = {"pcb-design": "A1", "pcb-fab-package": "A2", "pcba-design": "A3"}
ISOLATION_LIMIT = ("Repository files, credentials and sibling skills stay readable when the host "
                   "tools can reach them. Isolation does not change trust or permissions. "
                   "A bwrap boundary is measured locally on this host (tests/test_release_isolation.py). "
                   "That measurement does not isolate any provider run.")
TOKEN_ENFORCEMENT = ("post-request. The harness stops before the next request. A started request "
                     "is not cut off, so the final overrun is recorded.")
USAGE_SOURCE = "host-reported. Not provider billing and not a measure of all provider use."


class BudgetStop(Exception):
    """The ledger refuses to start another run. The message gives the reason."""


class ProviderNotAuthorized(Exception):
    """No provider adapter exists in this revision. A paid batch cannot start."""


class HeldCellReachedProvider(AssertionError):
    """Raised by the held-cell stub. A held run must never reach a provider."""


def live_provider(run: dict) -> dict:
    """Placeholder for the live adapter. It refuses every call until the adapter is reviewed."""
    raise ProviderNotAuthorized(
        "No provider adapter in this revision. A paid batch needs an adapter review and "
        "lead authorization after the integrated artifacts pass review."
    )


def held_stub(run: dict) -> dict:
    """Stub provider for tests. It fails if a held run reaches it. It makes no external call."""
    raise HeldCellReachedProvider(f"held run {run.get('run_id')} reached the provider stub")


@dataclass
class Ledger:
    """Reported-token ledger for one batch. Each dispatched run reserves its full ceiling."""

    batch_tokens: int
    max_runs: int
    used: int = 0
    started: int = 0
    _reserved: dict[str, int] = field(default_factory=dict)

    def remaining(self) -> int:
        """Batch tokens that no dispatched run has reported or reserved yet."""
        return self.batch_tokens - self.used - sum(self._reserved.values())

    def start(self, run_id: str, ceiling: int) -> None:
        if self.started >= self.max_runs:
            raise BudgetStop(f"batch run ceiling reached ({self.max_runs}). Stopping before {run_id}.")
        if self.remaining() < ceiling:
            raise BudgetStop(
                f"remaining batch budget {self.remaining()} is below the reserve {ceiling}. "
                f"Stopping before {run_id}."
            )
        self.started += 1
        self._reserved[run_id] = ceiling

    def finish(self, run_id: str, reported_tokens: int) -> None:
        """Replace the reserve with the reported tokens of the finished run."""
        if reported_tokens < 0:
            raise ValueError("reported tokens cannot be negative")
        self._reserved.pop(run_id, None)
        self.used += reported_tokens


def readiness(run: dict, matrix: dict) -> tuple[str, str]:
    """Return (state, reason). State is 'fixture-ready' or 'held'. A held run never dispatches."""
    ready = matrix["readiness"]
    skill_state = ready["skills"][run["skill"]]
    if run["group"] in ("routing", "explicit"):
        ok = skill_state["integrated_accepted"] and skill_state["routing_ready"]
        return ("fixture-ready", "") if ok else ("held", "skill not integrated, or routing not ready")
    cell = ready["artifact_fixtures"][ARTIFACT_CELL[run["skill"]]]
    deps = all(ready["skills"][dep]["integrated_accepted"] for dep in cell["depends_on"])
    ok = cell["frozen"] and deps and skill_state["integrated_accepted"]
    if ok:
        return "fixture-ready", ""
    return "held", f"artifact fixture {ARTIFACT_CELL[run['skill']]} not frozen, or a dependency is not accepted"


def plan_runs(matrix: dict) -> list[dict]:
    """Expand the matrix into the 210 scheduled runs. Each run carries its readiness state, its hold
    reason and the lead's authorization flag. Install checks are not scheduled runs."""
    short = matrix["limits"]["routing_and_explicit"]
    long = matrix["limits"]["artifact_baseline_compaction"]
    plan: list[dict] = []
    for skill in matrix["skills"]:
        for host in matrix["hosts"]:
            for case in matrix["routing"]["cases"]:
                for repeat in range(1, matrix["routing"]["repeats"] + 1):
                    plan.append(_entry("routing", skill, host, short, repeat, case=case["id"]))
            for repeat in range(1, matrix["explicit"]["repeats"] + 1):
                plan.append(_entry("explicit", skill, host, short, repeat))
            plan.append(_entry("artifact", skill, host, long, 1, arm="skill"))
            plan.append(_entry("baseline", skill, host, long, 1, arm="baseline"))
    for host in matrix["hosts"]:
        plan.append(_entry("compaction", matrix["compaction"]["skill"], host, long, 1))
    for run in plan:
        _attach_expectations(run, matrix)
        run["state"], run["hold_reason"] = readiness(run, matrix)
        run["authorized"] = bool(matrix["readiness"]["paid_batch_authorized"])
        # B-1. The baseline policy is enforced at planning, whatever the other gates say.
        if run["group"] == "baseline":
            policy = baseline_policy(run["host"])
            if policy["status"].startswith("refused"):
                run["state"] = "refused-by-policy"
                run["hold_reason"] = policy["reason"]
    return plan


def _attach_expectations(run: dict, matrix: dict) -> None:
    """Attach the expected skill names of each run (B-1). Names are compared with host output that
    has been normalized to names. A baseline expects none. An R3 run expects none. An R2 run expects
    the owner of its cross-skill task, and carries that task text."""
    owners = {item["target"]: item for item in matrix["r2_tasks"]}
    group = run["group"]
    if group == "routing":
        case = run["case"]
        if case == "R2":
            item = owners[run["skill"]]
            run["expected_paths"] = [item["expected_owner"]]
            run["r2_task"] = item["task"]
        elif case == "R3":
            run["expected_paths"] = []
        else:
            run["expected_paths"] = [run["skill"]]
    elif group == "baseline":
        run["expected_paths"] = []
    else:
        run["expected_paths"] = [run["skill"]]


ISOLATION_MODE = {"routing": "all-three", "explicit": "single-skill", "artifact": "single-skill",
                  "compaction": "single-skill", "baseline": "none"}


def _entry(group, skill, host, limit, repeat, case=None, arm=None) -> dict:
    parts = [group, skill, host["id"], case or "-", arm or "-", f"r{repeat}"]
    return {
        "run_id": "-".join(parts),
        "group": group,
        "skill": skill,
        "host": host["host"],
        "pair": host["id"],
        "assigned_model": host["assigned_model"],
        "case": case,
        "arm": arm,
        "repeat": repeat,
        "isolation_mode": ISOLATION_MODE[group],
        # B-2. Host discovery and host selection are unavailable until a host reports them.
        "host_discovery_status": "unavailable",
        "host_discovered_paths": None,
        "host_selection_status": "unavailable",
        "host_selected_paths": None,
        "isolation_limit": ISOLATION_LIMIT,
        "token_enforcement": TOKEN_ENFORCEMENT,
        "usage_source": USAGE_SOURCE,
        "turn_limit": limit["turns"],
        "wall_clock_seconds": limit["wall_clock_seconds"],
        "reported_token_ceiling": limit["reported_tokens"],
    }


def readiness_counts(plan: list[dict]) -> dict[str, int]:
    """Three counts, kept apart. Authorized is zero unless the lead authorized the batch."""
    fixture_ready = sum(1 for run in plan if run["state"] == "fixture-ready")
    # Authorized is the fixture-ready subset that the lead has allowed to dispatch.
    authorized = sum(1 for run in plan if run["state"] == "fixture-ready" and run["authorized"])
    return {"scheduled": len(plan), "fixture_ready": fixture_ready, "authorized": authorized}


def check_plan(matrix: dict, plan: list[dict]) -> dict[str, int]:
    """Compare the plan with the derived counts. Return the group counts for the report."""
    value = counts(matrix)
    by_group: dict[str, int] = {}
    for run in plan:
        by_group[run["group"]] = by_group.get(run["group"], 0) + 1
    expected = {
        "routing": value["routing"],
        "explicit": value["explicit"],
        "artifact": value["artifact_skill"],
        "baseline": value["artifact_baseline"],
        "compaction": value["compaction"],
    }
    if by_group != expected:
        raise ValueError(f"plan groups {by_group} differ from the matrix {expected}")
    if len(plan) != value["paid_total"]:
        raise ValueError(f"plan has {len(plan)} runs. The accepted total is {value['paid_total']}")
    if len(plan) != matrix["limits"]["batch"]["scheduled_runs"]:
        raise ValueError("plan size differs from the batch scheduled run ceiling")
    if matrix["limits"]["batch"]["automatic_retries"] != 0:
        raise ValueError("automatic retries must be zero")
    # The executable set is the fixture-ready set intersected with authorization.
    executable = [run for run in plan if run["state"] == "fixture-ready" and run["authorized"]]
    if len(executable) != readiness_counts(plan)["authorized"]:
        raise ValueError("executable set differs from the authorized count")
    return by_group


def next_attempt(run_dir: Path) -> int:
    """Attempt numbers start at 1. Existing attempt folders are never replaced."""
    if not run_dir.exists():
        return 1
    existing = [int(p.name.split("-", 1)[1]) for p in run_dir.glob("attempt-*") if p.is_dir()]
    return max(existing, default=0) + 1


def write_attempt(root: Path, run: dict, record: dict) -> Path:
    """Write run.json for one attempt. Refuse to overwrite an existing attempt."""
    run_dir = Path(root) / "runs" / run["run_id"]
    attempt = next_attempt(run_dir)
    target = run_dir / f"attempt-{attempt}"
    target.mkdir(parents=True, exist_ok=False)
    payload = {**run, **record, "attempt": attempt}
    with open(target / "run.json", "x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return target


def execute(plan: list[dict], ledger: Ledger, root: Path, provider=None) -> list[dict]:
    """Run the plan in order.

    A held run is recorded and refused before the ledger reserve. An unauthorized run is recorded and
    refused the same way. Neither reaches the provider. Without a provider, every authorized run is
    recorded as not executed. The batch stops only at the ledger ceiling.
    """
    records: list[dict] = []
    for run in plan:
        # B-3. Non-executed records carry evidence "not-executed", never a live or mock label.
        # B-1. The baseline policy is enforced again at dispatch. The run never reaches the adapter and
        # never reserves budget, whatever the other gates say.
        if run["state"] == "refused-by-policy":
            record = {"run_id": run["run_id"], "status": "refused-by-policy", "evidence": "not-executed",
                      "stop_reason": run["hold_reason"], "reported_tokens": 0}
        elif run["state"] == "held":
            record = {"run_id": run["run_id"], "status": "held", "evidence": "not-executed",
                      "stop_reason": run["hold_reason"], "reported_tokens": 0}
        elif not run["authorized"]:
            record = {"run_id": run["run_id"], "status": "not-authorized", "evidence": "not-executed",
                      "stop_reason": "the lead has not authorized provider dispatch", "reported_tokens": 0}
        else:
            try:
                ledger.start(run["run_id"], run["reported_token_ceiling"])
            except BudgetStop as stop:
                records.append({"run_id": run["run_id"], "status": "batch-stopped",
                                "evidence": "not-executed", "stop_reason": str(stop)})
                break
            record = _one_run(run, ledger, provider)
        write_attempt(root, run, record)
        records.append(record)
    return records


def _evidence_of(provider) -> str:
    """A provider declares its evidence type: 'live' or 'mock'. An undeclared provider is unavailable.
    Nothing is assumed to be live."""
    declared = getattr(provider, "evidence", None)
    return declared if declared in ("live", "mock") else "unavailable"


def _one_run(run: dict, ledger: Ledger, provider) -> dict:
    if provider is None:
        ledger.finish(run["run_id"], 0)
        return {"run_id": run["run_id"], "status": "not-executed", "evidence": "not-executed",
                "stop_reason": "no provider adapter in this revision", "reported_tokens": 0}
    evidence = _evidence_of(provider)
    try:
        usage = provider(run)
    except Exception as error:  # noqa: BLE001 - a failed attempt is recorded, never hidden
        # A failed request may still have used tokens. Its count is unknown, so it is charged at the ceiling.
        ledger.finish(run["run_id"], run["reported_token_ceiling"])
        return {"run_id": run["run_id"], "status": "failed", "evidence": evidence,
                "stop_reason": f"provider error: {error.__class__.__name__}: {error}",
                "reported_tokens": None,
                "token_status": "unavailable after provider error (charged at the ceiling)"}
    raw = usage.get("reported_tokens")
    # A missing count is unavailable. It is charged at the full ceiling, the conservative choice.
    tokens_known = raw is not None
    tokens = int(raw) if tokens_known else run["reported_token_ceiling"]
    turns = int(usage.get("turns", 0))
    elapsed = float(usage.get("elapsed_seconds", 0.0))
    ledger.finish(run["run_id"], tokens)
    stop = None
    if tokens > run["reported_token_ceiling"]:
        stop = (f"reported tokens {tokens} exceed the ceiling {run['reported_token_ceiling']}. "
                "The overrun is the size of the last request.")
    elif turns > run["turn_limit"]:
        stop = f"turns {turns} exceed the limit {run['turn_limit']}"
    elif elapsed > run["wall_clock_seconds"]:
        stop = f"elapsed {elapsed} s exceeds the limit {run['wall_clock_seconds']} s"
    status = "stopped" if stop else ("complete" if usage.get("ok", False) else "failed")
    return {"run_id": run["run_id"], "status": status, "evidence": evidence, "stop_reason": stop or "",
            "reported_tokens": raw if tokens_known else None,
            "token_status": "reported" if tokens_known else "unavailable (charged at the ceiling)",
            "turns": turns, "elapsed_seconds": elapsed}


def main() -> int:
    matrix = load_matrix()
    plan = plan_runs(matrix)
    groups = check_plan(matrix, plan)
    print(json.dumps({"groups": groups, **readiness_counts(plan)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
