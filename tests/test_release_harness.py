# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Static tests for the B12 release harness. Mock results. No provider call.

  uv run tests/test_release_harness.py            # all tests
  uv run tests/test_release_harness.py ledger     # only tests with 'ledger' in their name

Every result here carries the label `mock`. A test uses project-authored fixture skills, fixture
outputs, injected usage records and a held-cell stub. No result from these tests is provider
evidence, and no result enters the release table (AC-16).

The filesystem restriction and the sentinel boundary test are NOT implemented. They are recorded
as incomplete, and authorization stays at zero (see test_mock_sentinel_boundary_stays_incomplete).
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "eval"))

import common as C  # noqa: E402
import check_artifacts as CA  # noqa: E402
import isolate as I  # noqa: E402
import run_case as R  # noqa: E402
import score as S  # noqa: E402

MATRIX = C.load_matrix()
LABEL = "mock"
FREEZE = ROOT / "docs" / "reviews" / "b12-distribution-integration-freeze-r2-root.sha256"


def skill(base: Path, name: str, description: str = "A fixture skill.") -> Path:
    path = base / name
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n", encoding="utf-8")
    (path / "scripts").mkdir()
    (path / "scripts" / "run.py").write_text("print('fixture')\n", encoding="utf-8")
    return path


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fake_usage(tokens: int, turns: int = 1, elapsed: float = 1.0, ok: bool = True):
    """An injected usage provider. It declares itself mock, so its records are never live evidence."""
    def provider(run: dict) -> dict:
        return {"reported_tokens": tokens, "turns": turns, "elapsed_seconds": elapsed, "ok": ok}
    provider.evidence = "mock"
    return provider


def open_matrix(paid: bool) -> dict:
    """A test-only copy of the matrix with every skill and fixture marked ready. It proves the gate
    opens only when all three inputs agree. No file of the repository changes."""
    matrix = copy.deepcopy(MATRIX)
    for state in matrix["readiness"]["skills"].values():
        state["integrated_accepted"] = True
        state["routing_ready"] = True
    for cell in matrix["readiness"]["artifact_fixtures"].values():
        cell["frozen"] = True
    matrix["readiness"]["paid_batch_authorized"] = paid
    return matrix


# ------------------------------------------------------------------ matrix and counts (AC-01)


def test_mock_counts_match_the_accepted_matrix(tmp: Path):
    value = C.counts(MATRIX)
    expected = {"routing": 162, "artifact_skill": 9, "artifact_baseline": 9, "core": 180,
                "explicit": 27, "compaction": 3, "paid_total": 210, "install_copy": 9,
                "install_symlink": 6, "install_user": 9, "install_total": 24}
    expect(value == expected, f"{LABEL}: counts {value} differ from {expected}")


def test_mock_plan_has_210_runs_in_the_accepted_groups(tmp: Path):
    plan = R.plan_runs(MATRIX)
    groups = R.check_plan(MATRIX, plan)
    expect(len(plan) == 210, f"{LABEL}: plan has {len(plan)} runs")
    expect(groups == {"routing": 162, "explicit": 27, "artifact": 9, "baseline": 9, "compaction": 3},
           f"{LABEL}: groups {groups}")


def test_mock_limits_are_the_accepted_values(tmp: Path):
    short = MATRIX["limits"]["routing_and_explicit"]
    long = MATRIX["limits"]["artifact_baseline_compaction"]
    expect((short["turns"], short["wall_clock_seconds"], short["reported_tokens"]) == (10, 300, 30000),
           f"{LABEL}: routing limits {short}")
    expect((long["turns"], long["wall_clock_seconds"], long["reported_tokens"]) == (30, 1200, 250000),
           f"{LABEL}: long limits {long}")


def test_mock_worst_case_fits_the_batch_ceiling(tmp: Path):
    worst = C.worst_case_tokens(MATRIX)
    ceiling = MATRIX["limits"]["batch"]["reported_tokens"]
    expect(worst == 10920000, f"{LABEL}: per-run sum is {worst}, expected 10920000")
    expect(worst <= ceiling, f"{LABEL}: per-run sum {worst} exceeds the batch ceiling {ceiling}")


def test_mock_no_automatic_retries(tmp: Path):
    expect(MATRIX["limits"]["batch"]["automatic_retries"] == 0, f"{LABEL}: retries are not zero")
    expect(MATRIX["limits"]["batch"]["scheduled_runs"] == 210, f"{LABEL}: scheduled ceiling differs")


def test_mock_plan_rejects_a_wrong_count(tmp: Path):
    plan = R.plan_runs(MATRIX)[:-1]
    try:
        R.check_plan(MATRIX, plan)
    except ValueError:
        return
    raise AssertionError(f"{LABEL}: a 209-run plan was accepted")


# ------------------------------------------------------------------ readiness gate (C-1, C-2)


def test_mock_real_matrix_has_zero_fixture_ready_and_zero_authorized(tmp: Path):
    """C-2. Scheduled 210. Fixture-ready 0. Authorized 0. A fixture-ready count is not an executable count."""
    plan = R.plan_runs(MATRIX)
    counts_now = R.readiness_counts(plan)
    expect(counts_now == {"scheduled": 210, "fixture_ready": 0, "authorized": 0},
           f"{LABEL}: readiness counts {counts_now}")


def test_mock_held_cells_never_reach_the_provider(tmp: Path):
    """C-1. Every held cell is refused before the ledger reserve. The held stub is never called."""
    plan = R.plan_runs(MATRIX)
    ledger = R.Ledger(batch_tokens=10**7, max_runs=210)
    records = R.execute(plan, ledger, tmp / "held", provider=R.held_stub)
    expect(len(records) == 210, f"{LABEL}: {len(records)} records")
    expect(all(r["status"] in ("held", "refused-by-policy") for r in records), f"{LABEL}: an open status appeared")
    expect(ledger.started == 0 and ledger.used == 0, f"{LABEL}: a held cell reserved budget")


def test_mock_unauthorized_cells_never_reach_the_provider(tmp: Path):
    """C-1 and C-2. Fixture-ready but unauthorized: refused, and the held stub is not called."""
    plan = R.plan_runs(open_matrix(paid=False))
    ledger = R.Ledger(batch_tokens=10**7, max_runs=210)
    records = R.execute(plan, ledger, tmp / "unauth", provider=R.held_stub)
    expect(all(r["status"] in ("not-authorized", "refused-by-policy") for r in records), f"{LABEL}: {records[0]}")
    expect(ledger.started == 0, f"{LABEL}: an unauthorized cell reserved budget")


def test_mock_authorized_fixture_ready_cells_dispatch(tmp: Path):
    """With every input agreed and authorization set in a test copy, the gate opens."""
    open_plan = R.plan_runs(open_matrix(paid=True))
    counts_open = R.readiness_counts(open_plan)
    expect(counts_open == {"scheduled": 210, "fixture_ready": 207, "authorized": 207},
           f"{LABEL}: open counts {counts_open}")
    ledger = R.Ledger(batch_tokens=MATRIX["limits"]["batch"]["reported_tokens"], max_runs=210)
    records = R.execute(open_plan, ledger, tmp / "open", provider=fake_usage(tokens=0))
    expect(all(r["status"] == "complete" for r in records if r["status"] != "refused-by-policy"),
           f"{LABEL}: an open cell did not dispatch")
    expect(sum(r["status"] == "refused-by-policy" for r in records) == 3,
           f"{LABEL}: the Codex baseline was not refused by policy")


def test_mock_held_stub_fails_if_it_is_reached(tmp: Path):
    """The stub is a tripwire. If a held cell reaches it, the test fails loudly."""
    run = R.plan_runs(MATRIX)[0]
    try:
        R.held_stub(run)
    except R.HeldCellReachedProvider:
        return
    raise AssertionError(f"{LABEL}: the held stub did not fail")


def test_mock_hold_reasons_name_the_missing_input(tmp: Path):
    plan = R.plan_runs(MATRIX)
    reasons = {run["hold_reason"] for run in plan}
    expect(any("not integrated" in r for r in reasons), f"{LABEL}: routing hold reason missing")
    expect(any("artifact fixture" in r for r in reasons), f"{LABEL}: artifact hold reason missing")


# ------------------------------------------------------------------ R2 owners (C-3)


def test_mock_r2_owner_is_not_in_the_prompt(tmp: Path):
    """C-3. Each R2 task names a different owner. The expected owner stays out of the prompt text."""
    for item in MATRIX["r2_tasks"]:
        expect(item["expected_owner"] != item["target"], f"{LABEL}: R2 repeats the direct owner for {item}")
        expect(item["expected_owner"] not in item["task"].lower(), f"{LABEL}: owner leaked into the task")


def test_mock_r2_table_matches_the_root_review(tmp: Path):
    owners = {item["target"]: item["expected_owner"] for item in MATRIX["r2_tasks"]}
    expect(owners == {"pcb-design": "pcb-fab-package", "pcb-fab-package": "pcba-design",
                      "pcba-design": "pcb-design"}, f"{LABEL}: owners {owners}")


# ------------------------------------------------------------------ isolation (AC-02 to AC-04, M-3, M-5)


def test_mock_copy_install_hash_equals_source(tmp: Path):
    source = skill(tmp / "src", "pcb-design")
    root = I.new_root(tmp / "run1")
    record = I.install(source, root, "codex", "project")
    expect(record["skill_sha256"] == C.aggregate_digest(C.tree_digest(source)),
           f"{LABEL}: installed hash differs from source")
    expect(record["installed_path"] == ".agents/skills/pcb-design", f"{LABEL}: {record['installed_path']}")
    expect(record["filesystem_selected_path"] == record["installed_path"], f"{LABEL}: selection differs")


def test_mock_install_record_separates_inventory_from_host_selection(tmp: Path):
    """C-3. An install record holds a filesystem inventory only. Host discovery and host selection are absent."""
    source = skill(tmp / "src", "pcb-design")
    record = I.install(source, I.new_root(tmp / "run15"), "pi", "project")
    expect("filesystem_selected_path" in record and "scanned_paths" in record, f"{LABEL}: fields missing")
    expect("host_selected_paths" not in record and "host_discovered_paths" not in record,
           f"{LABEL}: a local scan entered a host field")


def test_mock_scan_is_not_host_selection(tmp: Path):
    """C-3. A local scan that finds a skill does not score as host selection. S1 is not measured."""
    run = {"evidence": "live", "expected_paths": ["pcb-design"], "trace": [],
           "filesystem_selected_paths": ["pcb-design"]}
    result = S.score_run(run)
    expect(result["S1"] is None, f"{LABEL}: a local scan was scored as selection: {result}")


def test_mock_duplicate_name_stops_before_the_provider(tmp: Path):
    source = skill(tmp / "src", "pcb-design")
    root = I.new_root(tmp / "run2")
    I.install(source, root, "codex", "project")
    try:
        I.install(source, root, "codex", "user")
    except I.DuplicateSkillName:
        return
    raise AssertionError(f"{LABEL}: a duplicate name was installed")


def test_mock_missing_skill_file_is_refused(tmp: Path):
    source = tmp / "src" / "pcb-design"
    source.mkdir(parents=True)
    root = I.new_root(tmp / "run3")
    try:
        I.install(source, root, "pi", "project")
    except I.MissingSkillFile:
        return
    raise AssertionError(f"{LABEL}: a skill without SKILL.md was installed")


def test_mock_user_scope_uses_the_temporary_home_only(tmp: Path):
    """M-5. The user-scope install stays in the run's temporary home."""
    source = skill(tmp / "src", "pcb-fab-package")
    real_target = Path.home() / ".agents" / "skills" / "pcb-fab-package"
    existed = real_target.exists()
    root = I.new_root(tmp / "run4")
    record = I.install(source, root, "codex", "user")
    expect(record["installed_path"] == "home/.agents/skills/pcb-fab-package", f"{LABEL}: {record}")
    expect(record["filesystem_selected_path"] == record["installed_path"], f"{LABEL}: user scope not selected")
    expect(real_target.exists() == existed, f"{LABEL}: the real home was written")


def test_mock_symlink_is_limited_to_codex_and_pi(tmp: Path):
    source = skill(tmp / "src", "pcb-design")
    root = I.new_root(tmp / "run5")
    try:
        I.install(source, root, "claude-code", "symlink")
    except I.IsolationError:
        pass
    else:
        raise AssertionError(f"{LABEL}: claude-code symlink was accepted")
    record = I.install(source, I.new_root(tmp / "run6"), "pi", "symlink")
    expect(record["install_mode"] == "symlink", f"{LABEL}: {record}")


def test_mock_routing_installs_all_three_candidates(tmp: Path):
    """Routing runs install pcb-design, pcb-fab-package and pcba-design together (lead decision)."""
    names = ["pcb-design", "pcb-fab-package", "pcba-design"]
    sources = [skill(tmp / "src", n) for n in names]
    root = I.new_root(tmp / "run7")
    records = I.install_set(sources, root, "claude-code", "project")
    expect(len(records) == 3, f"{LABEL}: {len(records)} records")
    scanned = sorted(n for n, _ in I.scan_installed(root, "claude-code"))
    expect(scanned == sorted(names), f"{LABEL}: scanned {scanned}")


def test_mock_standalone_run_installs_one_skill(tmp: Path):
    source = skill(tmp / "src", "pcb-design")
    root = I.new_root(tmp / "run8")
    I.install(source, root, "pi", "project")
    expect([n for n, _ in I.scan_installed(root, "pi")] == ["pcb-design"], f"{LABEL}: standalone scan")


def test_mock_baseline_installs_no_skill(tmp: Path):
    """M-3. A baseline root holds no skill package, so the scan finds nothing."""
    root = I.new_root(tmp / "run9")
    expect(I.scan_installed(root, "codex") == [], f"{LABEL}: baseline root has a skill")
    expect(I.scan_installed(root, "pi") == [], f"{LABEL}: baseline root has a skill")


def test_mock_malformed_skill_md_is_diagnosed(tmp: Path):
    """M-6. A missing description and malformed frontmatter are reported, not passed."""
    missing = skill(tmp / "a", "pcb-design", description="")
    problems = I.diagnose_skill_md(missing)
    expect("description is missing or empty" in problems, f"{LABEL}: {problems}")
    broken = tmp / "b" / "pcb-fab-package"
    broken.mkdir(parents=True)
    (broken / "SKILL.md").write_text("---\nname: [unclosed\n---\n", encoding="utf-8")
    expect(any("malformed" in p for p in I.diagnose_skill_md(broken)), f"{LABEL}: malformed not reported")


def test_mock_user_scope_per_host_and_real_home_unchanged(tmp: Path):
    """Each host installs under its temporary home. The real home stays unchanged."""
    source = skill(tmp / "src", "pcb-fab-package")
    real_home_entries = sorted(p.name for p in Path.home().iterdir()) if Path.home().exists() else []
    for host in ("codex", "pi", "claude-code"):
        root = I.new_root(tmp / f"user-{host}")
        record = I.install(source, root, host, "user")
        expect(record["installed_path"].startswith("home/"), f"{LABEL}: {host} not under home")
    after = sorted(p.name for p in Path.home().iterdir()) if Path.home().exists() else []
    expect(after == real_home_entries, f"{LABEL}: the real home changed")


# ------------------------------------------------------------------ ledger, ceilings and stops (M-1, M-2)


def test_mock_ledger_runs_every_scheduled_run_within_the_ceiling(tmp: Path):
    plan = R.plan_runs(open_matrix(paid=True))
    ledger = R.Ledger(batch_tokens=MATRIX["limits"]["batch"]["reported_tokens"], max_runs=210)
    records = R.execute(plan, ledger, tmp / "run10", provider=fake_usage(tokens=0))
    expect(len(records) == 210, f"{LABEL}: {len(records)} records")
    expect(all(r["status"] == "complete" for r in records if r["status"] != "refused-by-policy"),
           f"{LABEL}: a dispatchable run did not complete")
    expect(sum(r["status"] == "refused-by-policy" for r in records) == 3, f"{LABEL}: policy refusals")


def test_mock_ledger_stops_before_a_run_that_does_not_fit(tmp: Path):
    """Injected usage at the routing ceiling. The batch stops before the run that does not fit."""
    plan = R.plan_runs(open_matrix(paid=True))
    ledger = R.Ledger(batch_tokens=1_000_000, max_runs=210)
    records = R.execute(plan, ledger, tmp / "run11", provider=fake_usage(tokens=30000))
    expect(records[-1]["status"] == "batch-stopped", f"{LABEL}: last record {records[-1]['status']}")
    complete = sum(r["status"] == "complete" for r in records)
    refused = sum(r["status"] == "refused-by-policy" for r in records)
    expect(complete == 33 and refused == 1 and len(records) == 35,
           f"{LABEL}: expected 33 complete, 1 policy refusal and 1 stop, found {complete}, {refused}, {len(records)}")
    expect("reserve" in records[-1]["stop_reason"], f"{LABEL}: reason {records[-1]['stop_reason']}")


def test_mock_run_over_its_token_ceiling_is_stopped(tmp: Path):
    """M-1. Injected usage above the ceiling. The run is marked, and the overrun is reported."""
    run = R.plan_runs(MATRIX)[0]
    ledger = R.Ledger(batch_tokens=10_000_000, max_runs=210)
    ledger.start(run["run_id"], run["reported_token_ceiling"])
    record = R._one_run(run, ledger, fake_usage(tokens=run["reported_token_ceiling"] + 1))
    expect(record["status"] == "stopped", f"{LABEL}: {record}")
    expect("exceed" in record["stop_reason"], f"{LABEL}: {record['stop_reason']}")


def test_mock_run_over_its_turn_limit_is_stopped(tmp: Path):
    run = R.plan_runs(MATRIX)[0]
    ledger = R.Ledger(batch_tokens=10_000_000, max_runs=210)
    ledger.start(run["run_id"], run["reported_token_ceiling"])
    record = R._one_run(run, ledger, fake_usage(tokens=100, turns=11))
    expect(record["status"] == "stopped" and "turns" in record["stop_reason"], f"{LABEL}: {record}")


def test_mock_run_over_its_wall_clock_is_stopped(tmp: Path):
    run = R.plan_runs(MATRIX)[0]
    ledger = R.Ledger(batch_tokens=10_000_000, max_runs=210)
    ledger.start(run["run_id"], run["reported_token_ceiling"])
    record = R._one_run(run, ledger, fake_usage(tokens=100, elapsed=301.0))
    expect(record["status"] == "stopped" and "elapsed" in record["stop_reason"], f"{LABEL}: {record}")


def test_mock_provider_error_is_a_kept_failure(tmp: Path):
    """M-2. A provider error is recorded as a failed attempt. No success record exists."""
    plan = R.plan_runs(open_matrix(paid=True))[:1]
    root = tmp / "run12"

    def failing(run: dict) -> dict:
        raise RuntimeError("injected timeout")

    records = R.execute(plan, R.Ledger(batch_tokens=10**7, max_runs=210), root, provider=failing)
    expect(records[0]["status"] == "failed", f"{LABEL}: {records[0]}")
    attempt = root / "runs" / plan[0]["run_id"] / "attempt-1" / "run.json"
    expect(attempt.is_file(), f"{LABEL}: failed attempt was not kept")
    expect(json.loads(attempt.read_text())["status"] == "failed", f"{LABEL}: record says otherwise")


def test_mock_no_provider_means_no_call_and_no_success(tmp: Path):
    plan = R.plan_runs(open_matrix(paid=True))[:2]
    records = R.execute(plan, R.Ledger(batch_tokens=10**7, max_runs=210), tmp / "run13", provider=None)
    expect(all(r["status"] == "not-executed" for r in records), f"{LABEL}: {records}")
    expect(all(r["reported_tokens"] == 0 for r in records), f"{LABEL}: tokens without a call")


def test_mock_live_provider_refuses_every_call(tmp: Path):
    try:
        R.live_provider({"run_id": "x"})
    except R.ProviderNotAuthorized:
        return
    raise AssertionError(f"{LABEL}: the live adapter accepted a call")


def test_mock_attempts_are_kept_not_overwritten(tmp: Path):
    """AC-09. A second attempt adds attempt-2. The first record stays unchanged."""
    run = R.plan_runs(MATRIX)[0]
    root = tmp / "run14"
    first = R.write_attempt(root, run, {"status": "failed"})
    before = (first / "run.json").read_text()
    second = R.write_attempt(root, run, {"status": "complete"})
    expect(second.name == "attempt-2", f"{LABEL}: {second}")
    expect((first / "run.json").read_text() == before, f"{LABEL}: attempt-1 changed")


def test_mock_negative_usage_is_refused(tmp: Path):
    ledger = R.Ledger(batch_tokens=100, max_runs=2)
    ledger.start("r", 10)
    try:
        ledger.finish("r", -1)
    except ValueError:
        return
    raise AssertionError(f"{LABEL}: negative usage was accepted")


def test_mock_missing_token_count_is_charged_at_the_ceiling(tmp: Path):
    """A missing count is unavailable. The ledger charges the full ceiling, not zero."""
    run = R.plan_runs(MATRIX)[0]
    ledger = R.Ledger(batch_tokens=10_000_000, max_runs=210)
    ledger.start(run["run_id"], run["reported_token_ceiling"])
    record = R._one_run(run, ledger, lambda r: {"ok": True, "turns": 1, "elapsed_seconds": 1.0})
    expect(record["reported_tokens"] is None, f"{LABEL}: {record}")
    expect(ledger.used == run["reported_token_ceiling"], f"{LABEL}: ledger used {ledger.used}")


def test_mock_isolation_limit_and_token_rules_are_in_every_plan_entry(tmp: Path):
    for run in R.plan_runs(MATRIX):
        expect("stay readable" in run["isolation_limit"], f"{LABEL}: {run['run_id']} lacks the limit")
        expect(run["token_enforcement"].startswith("post-request"), f"{LABEL}: enforcement missing")
        expect(run["usage_source"].startswith("host-reported"), f"{LABEL}: usage source missing")


def test_mock_isolation_mode_per_group(tmp: Path):
    modes = {}
    for run in R.plan_runs(MATRIX):
        modes.setdefault(run["group"], set()).add(run["isolation_mode"])
    expect(modes == {"routing": {"all-three"}, "explicit": {"single-skill"},
                     "artifact": {"single-skill"}, "baseline": {"none"},
                     "compaction": {"single-skill"}}, f"{LABEL}: modes {modes}")


# ------------------------------------------------------------------ expectations and host fields (B-1, B-2)


def test_mock_planned_runs_carry_their_expected_paths(tmp: Path):
    """B-1. R1, R4, R5, R6, explicit and artifact expect the skill. R3 and baseline expect none.
    R2 expects the owner of its cross-skill task, and carries that task text."""
    owners = {item["target"]: item for item in MATRIX["r2_tasks"]}
    for run in R.plan_runs(MATRIX):
        group, skill, case = run["group"], run["skill"], run["case"]
        if group == "routing" and case == "R2":
            expect(run["expected_paths"] == [owners[skill]["expected_owner"]], f"{LABEL}: R2 {run['run_id']}")
            expect(run["r2_task"] == owners[skill]["task"], f"{LABEL}: R2 task text missing")
        elif group == "routing" and case == "R3":
            expect(run["expected_paths"] == [], f"{LABEL}: R3 expects a skill")
        elif group == "baseline":
            expect(run["expected_paths"] == [], f"{LABEL}: baseline expects a skill")
        else:
            expect(run["expected_paths"] == [skill], f"{LABEL}: {run['run_id']} expects {run['expected_paths']}")


def test_mock_host_discovery_and_selection_are_unavailable(tmp: Path):
    """B-2. Every planned run states that host discovery and host selection are unavailable."""
    for run in R.plan_runs(MATRIX):
        expect(run["host_discovery_status"] == "unavailable" and run["host_discovered_paths"] is None,
               f"{LABEL}: discovery not unavailable for {run['run_id']}")
        expect(run["host_selection_status"] == "unavailable" and run["host_selected_paths"] is None,
               f"{LABEL}: selection not unavailable for {run['run_id']}")


def test_mock_null_host_selection_is_not_measured(tmp: Path):
    """B-2. A missing or null host selection scores S1 as not measured (None), never as a pass."""
    base = {"evidence": "live", "expected_paths": ["pcb-design"], "trace": []}
    for run in ({**base}, {**base, "host_selected_paths": None}):
        expect(S.score_run(run)["S1"] is None, f"{LABEL}: missing or null host selection was scored")


def test_mock_authorized_is_the_fixture_ready_subset(tmp: Path):
    """Minor. Authorized counts only fixture-ready runs that are authorized."""
    closed = R.readiness_counts(R.plan_runs(open_matrix(paid=False)))
    expect(closed == {"scheduled": 210, "fixture_ready": 207, "authorized": 0}, f"{LABEL}: {closed}")
    opened = R.readiness_counts(R.plan_runs(open_matrix(paid=True)))
    expect(opened == {"scheduled": 210, "fixture_ready": 207, "authorized": 207}, f"{LABEL}: {opened}")


# ------------------------------------------------------------------ baseline policy at dispatch (B-1)


def test_mock_codex_baseline_refused_with_every_gate_open(tmp: Path):
    """B-1. Every other gate is open: fixture-ready, authorized, and every skill accepted. The Codex
    baseline is still refused at planning and at dispatch. It never reaches the adapter stub, and it
    consumes no budget. The Claude and Pi baselines stay eligible."""
    plan = R.plan_runs(open_matrix(paid=True))
    codex_base = [r for r in plan if r["group"] == "baseline" and r["host"] == "codex"]
    expect(len(codex_base) == 3, f"{LABEL}: {len(codex_base)} Codex baseline runs")
    expect(all(r["state"] == "refused-by-policy" for r in codex_base), f"{LABEL}: planning did not refuse")
    others = [r for r in plan if r["group"] == "baseline" and r["host"] != "codex"]
    expect(all(r["state"] == "fixture-ready" for r in others), f"{LABEL}: an eligible baseline was refused")
    ledger = R.Ledger(batch_tokens=10**7, max_runs=210)
    records = R.execute(codex_base, ledger, tmp / "codex-base", provider=R.held_stub)
    expect(all(r["status"] == "refused-by-policy" for r in records), f"{LABEL}: dispatch did not refuse")
    expect(ledger.started == 0 and ledger.used == 0, f"{LABEL}: a refused baseline consumed budget")


# ------------------------------------------------------------------ evidence states (B-3)


def _state_runs() -> list[dict]:
    """One record for each evidence state. Every record is in the routing group."""
    base = {"group": "routing", "expected_paths": ["pcb-design"], "host_selected_paths": ["pcb-design"],
            "trace": [{"kind": "message", "text": "done"}], "claims": []}
    return [
        {**base, "evidence": "live", "status": "complete",
         "checker": {"all_pass": False, "results": [{"id": "a", "pass": False}]}},          # measured failure
        {**base, "evidence": "not-executed", "status": "held"},
        {**base, "evidence": "not-executed", "status": "not-authorized"},
        {**base, "evidence": "not-executed", "status": "not-executed"},
        {"group": "routing", "expected_paths": ["pcb-design"], "status": "complete"},        # no evidence
        {**base, "evidence": "mock", "status": "complete"},
    ]


def test_mock_held_record_is_not_measured(tmp: Path):
    run = _state_runs()[1]
    result = S.score_run(run)
    expect(result["measured"] is False and all(result[s] is None for s in S.SCORES),
           f"{LABEL}: held record was scored: {result}")


def test_mock_unauthorized_record_is_not_measured(tmp: Path):
    result = S.score_run(_state_runs()[2])
    expect(result["measured"] is False and result["S5"] is None, f"{LABEL}: {result}")


def test_mock_unexecuted_record_is_not_measured(tmp: Path):
    result = S.score_run(_state_runs()[3])
    expect(result["measured"] is False, f"{LABEL}: {result}")


def test_mock_missing_evidence_is_not_treated_as_live(tmp: Path):
    """A record with no evidence value is 'unavailable'. S4 and S5 are not passes."""
    result = S.score_run(_state_runs()[4])
    expect(result["measured"] is False and result["evidence"] == "unavailable", f"{LABEL}: {result}")
    expect(result["S4"] is None and result["S5"] is None, f"{LABEL}: absent evidence counted a pass")


def test_mock_mock_record_is_not_measured(tmp: Path):
    result = S.score_run(_state_runs()[5])
    expect(result["measured"] is False, f"{LABEL}: mock record was measured")


def test_mock_only_live_enters_the_table_and_live_failure_stays(tmp: Path):
    """Only the measured live record enters the table. Its failure stays. The others never add a pass."""
    summary = S.summarize(_state_runs())
    routing = summary["table"]["routing"]
    expect(routing["S3"] == {"pass": 0, "fail": 1, "na": 0} or routing["S3"]["fail"] == 1,
           f"{LABEL}: live failure not kept: {routing['S3']}")
    # Only the one measured live record contributes. Its S1 and S5 passes are its own, and its S3 fails.
    # The other five records add no count anywhere. S2 and S4 are not measured for the live record.
    expect(routing["S1"] == {"pass": 1, "fail": 0, "na": 0}, f"{LABEL}: S1 {routing['S1']}")
    expect(routing["S5"] == {"pass": 1, "fail": 0, "na": 0}, f"{LABEL}: S5 {routing['S5']}")
    expect(routing.get("S4", {}).get("pass", 0) == 0 and routing.get("S4", {}).get("fail", 0) == 0,
           f"{LABEL}: S4 counted a non-live record: {routing.get('S4')}")
    expect(routing.get("S2", {}).get("pass", 0) == 0, f"{LABEL}: S2 counted a non-live record")
    expect(summary["execution_summary"].get("not-executed:held") == 1, f"{LABEL}: held not summarized")
    expect(summary["execution_summary"].get("not-executed:not-authorized") == 1, f"{LABEL}: unauthorized")
    expect(summary["execution_summary"].get("unavailable:complete") == 1, f"{LABEL}: missing evidence")
    expect(summary["execution_summary"].get("mock:complete") == 1, f"{LABEL}: mock not summarized")
    expect(summary["execution_summary"].get("live:complete") == 1, f"{LABEL}: live not summarized")


def test_mock_authorized_subset_counts_only_fixture_ready_runs(tmp: Path):
    """M-B. authorized counts fixture-ready runs that are authorized. A held run is never counted."""
    plan = R.plan_runs(open_matrix(paid=True))
    plan[0]["state"] = "held"
    counts_mixed = R.readiness_counts(plan)
    expect(counts_mixed["authorized"] == 206 and counts_mixed["fixture_ready"] == 206,
           f"{LABEL}: {counts_mixed}")


# ------------------------------------------------------------------ sentinel boundary (open)


def test_mock_sentinel_boundary_stays_incomplete(tmp: Path):
    """The filesystem restriction and the sentinel read are NOT implemented. The limit is recorded.

    This test does not prove isolation. It only checks that every record and the matrix keep the
    limit visible until a measured sentinel test passes.
    """
    expect("bwrap" in MATRIX["isolation_prototype_limit"], f"{LABEL}: limit not recorded")
    expect("bwrap" in R.ISOLATION_LIMIT, f"{LABEL}: run records do not carry the limit")


# ------------------------------------------------------------------ checker and scores (AC-05 to AC-08, AC-16)


def test_mock_stale_drill_fails_with_the_reason(tmp: Path):
    """AC-05. A manifest that records an old source hash fails the binding with the stated reason."""
    write = lambda p, d: (p.parent.mkdir(parents=True, exist_ok=True), p.write_bytes(d))  # noqa: E731
    write(tmp / "board.kicad_pcb", b"source changed")
    write(tmp / "manifest.json", json.dumps({"source_sha256": C.sha256_bytes(b"source original")}).encode())
    expectation = [{"id": "drill-binding", "kind": "sha256_binding", "path": "manifest.json",
                    "key": "source_sha256", "reference": "board.kicad_pcb",
                    "reason": "drill older than source"}]
    result = CA.run_checks(expectation, tmp)
    expect(not result["all_pass"], f"{LABEL}: stale drill passed")
    expect(result["results"][0]["reason"] == "drill older than source", f"{LABEL}: {result}")


def test_mock_matching_binding_and_hash_pass(tmp: Path):
    """AC-06. A manifest that records the current source hash passes. Timestamps do not decide."""
    write = lambda p, d: (p.parent.mkdir(parents=True, exist_ok=True), p.write_bytes(d))  # noqa: E731
    write(tmp / "board.kicad_pcb", b"source")
    write(tmp / "drill.drl", b"drill")
    write(tmp / "manifest.json", json.dumps({"source_sha256": C.sha256_bytes(b"source")}).encode())
    os.utime(tmp / "board.kicad_pcb", (1_000_000_000, 1_000_000_000))
    expectation = [
        {"id": "binding", "kind": "sha256_binding", "path": "manifest.json",
         "key": "source_sha256", "reference": "board.kicad_pcb"},
        {"id": "drill-hash", "kind": "sha256", "path": "drill.drl", "value": C.sha256_bytes(b"drill")},
        {"id": "present", "kind": "exists", "path": "drill.drl"},
    ]
    result = CA.run_checks(expectation, tmp)
    expect(result["all_pass"], f"{LABEL}: {result}")


def test_mock_missing_file_never_passes(tmp: Path):
    result = CA.run_checks([{"id": "a", "kind": "sha256", "path": "none.txt", "value": "0" * 64}], tmp)
    expect(not result["all_pass"], f"{LABEL}: an absent file passed")


def test_mock_scores_are_separate(tmp: Path):
    """AC-07. A correct artifact without a SKILL.md read keeps S3 true and S2 false."""
    run = {"evidence": "live", "expected_paths": ["pcb-design"], "host_selected_paths": ["pcb-design"],
           "required_reads": ["SKILL.md"],
           "trace": [{"kind": "write", "path": "board.kicad_pcb"}, {"kind": "read", "path": "SKILL.md"}],
           "checker": {"all_pass": True, "results": [{"id": "a", "pass": True}]}, "claims": []}
    result = S.score_run(run)
    expect(result["S2"] is False and result["S3"] is True, f"{LABEL}: {result}")
    expect(result["S1"] is True and result["S5"] is True, f"{LABEL}: {result}")


def test_mock_claim_needs_a_command_in_the_trace(tmp: Path):
    """AC-08. A DRC pass claim without a DRC command in the trace fails S4."""
    run = {"evidence": "live", "expected_paths": ["pcb-design"], "host_selected_paths": ["pcb-design"], "required_reads": None,
           "trace": [{"kind": "message", "text": "done"}],
           "checker": {"all_pass": True, "results": [{"id": "drc", "pass": True}]},
           "claims": [{"text": "DRC passed", "checker_id": "drc", "command": "pcb drc"}]}
    result = S.score_run(run)
    expect(result["S4"] is False, f"{LABEL}: {result}")
    expect(result["hard_failures"] == [], f"{LABEL}: a checked claim was called fabricated")


def test_mock_unsupported_claim_is_a_hard_failure(tmp: Path):
    run = {"evidence": "live", "expected_paths": [], "host_selected_paths": [], "required_reads": None, "trace": [],
           "checker": None, "claims": [{"text": "fabricated", "checker_id": "none", "command": "x"}]}
    result = S.score_run(run)
    expect(result["S4"] is False and result["hard_failures"], f"{LABEL}: {result}")


def test_mock_unauthorized_external_action_is_a_hard_failure(tmp: Path):
    run = {"evidence": "live", "expected_paths": [], "host_selected_paths": [], "required_reads": None,
           "trace": [{"kind": "external", "command": "send supplier email", "authorized": False}],
           "checker": None, "claims": []}
    result = S.score_run(run)
    expect(result["S5"] is False and result["hard_failures"], f"{LABEL}: {result}")


def test_mock_routing_r3_selects_no_skill(tmp: Path):
    """R3. An unrelated CAD task must select no PCB skill."""
    ok = S.score_run({"evidence": "live", "expected_paths": [], "host_selected_paths": [], "trace": []})
    bad = S.score_run({"evidence": "live", "expected_paths": [], "host_selected_paths": ["pcb-design"], "trace": []})
    expect(ok["S1"] is True and bad["S1"] is False, f"{LABEL}: R3 scoring")


def test_mock_mock_runs_stay_out_of_the_release_table(tmp: Path):
    """AC-16. A mock run never enters the release table."""
    runs = [{"group": "routing", "expected_paths": [], "host_selected_paths": [], "trace": [],
             "evidence": "mock"}]
    table = S.summarize(runs)
    expect(table["table"] == {}, f"{LABEL}: mock entered the table {table}")


# ------------------------------------------------------------------ freeze completeness (C-5)


def test_mock_freeze_lists_every_harness_input(tmp: Path):
    """C-5. The freeze holds every harness module, the matrix, the tests and the fixture files."""
    expect(FREEZE.is_file(), f"{LABEL}: the harness freeze file is missing")
    listed = {line.split(None, 1)[1].strip() for line in FREEZE.read_text(encoding="utf-8").splitlines()
              if line.strip()}
    required = {p.relative_to(ROOT).as_posix() for p in (ROOT / "tests" / "eval").glob("*.py")}
    required |= {p.relative_to(ROOT).as_posix() for p in (ROOT / "tests" / "eval").glob("*.yaml")}
    required |= {"tests/test_release_isolation.py",
                 "tests/test_release_harness.py", "tests/test_release_packaging.py",
                 "tests/eval/matrix.yaml", "tests/eval/distribution.yaml",
                 ".gitignore", ".github/workflows/test.yml", "skills/pcb-fab-package/sources.yaml",
                 "docs/reviews/b12-matrix-revision5-claude.md"}
    for fixture_root in ("tests/fixtures/pcb-design", "tests/fixtures/pcb-fab-package", "tests/eval/fixtures"):
        required |= {p.relative_to(ROOT).as_posix() for p in (ROOT / fixture_root).rglob("*") if p.is_file()}
    missing = sorted(required - listed)
    expect(not missing, f"{LABEL}: the freeze omits {missing}")


# ------------------------------------------------------------------ repository state (AC-17, AC-18, AC-21)


def test_mock_run_records_are_git_ignored(tmp: Path):
    """AC-17. The run directory is ignored and the fixtures are not."""
    rc = subprocess.run(["git", "check-ignore", "-q", "tests/eval/runs/x/run.json"], cwd=ROOT).returncode
    expect(rc == 0, f"{LABEL}: run records are not ignored")
    rc2 = subprocess.run(["git", "check-ignore", "-q", "tests/eval/matrix.yaml"], cwd=ROOT).returncode
    expect(rc2 != 0, f"{LABEL}: the matrix is ignored")


def test_mock_workflow_keeps_read_only_permissions(tmp: Path):
    """AC-18. The workflow keeps contents read and holds no secret reference."""
    import yaml
    text = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    expect(data.get("permissions") == {"contents": "read"}, f"{LABEL}: permissions {data.get('permissions')}")
    expect("secrets." not in text, f"{LABEL}: the workflow reads a secret")


def test_mock_image_identity_is_recorded(tmp: Path):
    """AC-21. The matrix holds the image tag, image ID and digest that were measured."""
    a2 = MATRIX["artifact_checks"]["A2"]
    expect(a2["image_tag"] == "localhost/cad-skills-pcb:b6", f"{LABEL}: tag")
    expect(len(a2["image_id"]) == 64, f"{LABEL}: image id length")
    expect(a2["image_digest"].startswith("sha256:") and len(a2["image_digest"]) == 71, f"{LABEL}: digest")
    expect(len(a2["repo_digests"]) == 2 and a2["image_digest"] in a2["repo_digests"], f"{LABEL}: digests")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and key in n]
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                fn(tmp)
                print(f"ok   {name}")
            except Exception as error:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(error).__name__}: {error}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
