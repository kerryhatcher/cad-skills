# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Local tests for the host adapters and the measured filesystem and network boundary.
No provider, no network, no external endpoint.

  uv run tests/test_release_isolation.py           # all tests
  uv run tests/test_release_isolation.py boundary  # only tests with 'boundary' in their name

Host requirement: the boundary tests need the host `bwrap` on PATH (bubblewrap 0.13.1 measured on
this host). Without it the probe records the route as unavailable and the tests fail, not pass.

The boundary tests run the real bubblewrap route. A probe that fails makes the test fail, not pass.
Results here are local measurements, not provider evidence.
"""

from __future__ import annotations

import os
import socket
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "eval"))

import adapters as A  # noqa: E402
import sandbox as SB  # noqa: E402


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _probe(tmp: Path) -> dict:
    return SB.probe_bwrap(tmp / "probe-root")


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ------------------------------------------------------------------ filesystem boundary (I-1 to I-4, C-3, C-4)


def test_boundary_control_sentinel_is_readable_outside(tmp: Path):
    """I-1. Without the boundary the repository sentinel is readable. The test is meaningful."""
    expect(SB.SENTINEL.is_file() and os.access(SB.SENTINEL, os.R_OK),
           f"the sentinel {SB.SENTINEL} is not readable outside the boundary")


def test_boundary_bwrap_route_is_established_on_this_host(tmp: Path):
    """I-2 and I-4. The measured bwrap probe establishes the boundary. The record names the route."""
    probe = _probe(tmp)
    expect(probe["route"] == "bwrap", f"route {probe['route']}")
    expect(probe["boundary_established"] is True, f"boundary not established: {probe}")
    for key in ("host_version", "argv", "flags", "argv_sha256", "exit_code", "stdout_sha256",
                "stderr_sha256", "elapsed_seconds", "probe_stderr", "probe_stderr_sha256"):
        expect(key in probe and probe[key] is not None, f"record lacks {key}")
    expect(probe["sentinel_hidden_inside"] and probe["run_root_readable_inside"], f"{probe}")


def test_boundary_probe_error_is_retained_with_its_hash(tmp: Path):
    """C-4. The probe's stderr is kept as text and hash, and it names the missing sentinel."""
    probe = _probe(tmp)
    expect(probe["exit_code"] == 0, f"probe exit {probe['exit_code']}")
    expect("No such file or directory" in probe["probe_stderr"],
           f"the probe error does not name the missing sentinel: {probe['probe_stderr']!r}")
    expect(probe["probe_stderr_sha256"] == SB.sha256_text(probe["probe_stderr"]),
           "the probe error hash does not match its text")


def test_boundary_record_holds_the_full_argv_and_flags(tmp: Path):
    """C-3. The record keeps the full bwrap argv, the flags, and the argv hash. No placeholder."""
    probe = _probe(tmp)
    expect("<boundary args>" not in probe["command"], "the command is still redacted")
    expect(probe["argv"][0].endswith("bwrap") and "--unshare-all" in probe["argv"], f"{probe['argv'][:4]}")
    expect("--unshare-all" in probe["flags"] and "--die-with-parent" in probe["flags"], f"{probe['flags']}")
    expect(probe["argv_sha256"] == SB.sha256_argv(probe["argv"]), "argv hash does not match the argv")


def test_boundary_subprocess_cannot_read_the_repository_sentinel(tmp: Path):
    """I-2. Inside the boundary the stub's read of the repository sentinel fails. Measured, not assumed."""
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-sentinel", ["--read", str(SB.SENTINEL)], 20, probe)
    expect(run["execution_status"] == "exited-0", f"stub did not run: {run}")
    stdout = (tmp / "run-sentinel" / "proc" / "stdout.txt").read_text()
    expect("read=no" in stdout, f"the sentinel was readable inside the boundary: {stdout!r}")


def test_boundary_owned_outside_control_file_is_hidden_inside(tmp: Path):
    """C-6. A project-authored control file outside the run root: readable outside, hidden inside.
    The test owns this file. No user home file is used."""
    control = _write(tmp / "owned-control" / "control.txt", "owned control marker\n")
    expect(os.access(control, os.R_OK), "control is not readable outside the boundary")
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-owned", ["--read", str(control)], 20, probe)
    expect(run["execution_status"] == "exited-0", f"{run}")
    stdout = (tmp / "run-owned" / "proc" / "stdout.txt").read_text()
    expect("read=no" in stdout, f"the owned control was readable inside: {stdout!r}")


def test_boundary_unshare_route_is_refused(tmp: Path):
    """I-3. unshare gives a user namespace only. It is refused, not passed and not a fallback."""
    record = SB.refuse_unshare()
    expect(record["boundary_established"] is False, f"unshare passed: {record}")
    expect("Refused" in record["reason"], f"no refusal reason: {record}")


def test_boundary_refuses_to_start_when_the_probe_fails(tmp: Path):
    """I-3. A failed probe refuses the operation before any subprocess starts."""
    failed_probe = {"route": "bwrap", "boundary_established": False, "reason": "injected failure"}
    run = A.run_stub(tmp / "run-refused", ["--exit", "0"], 20, failed_probe)
    expect(run["execution_status"] == "refused" and run["attempts"] == 0, f"{run}")
    expect(not (tmp / "run-refused" / "proc").exists(), "a refused run produced process output")


def test_boundary_refused_run_is_not_a_pass(tmp: Path):
    failed_probe = {"route": "bwrap", "boundary_established": False, "reason": "injected failure"}
    run = SB.run_in_boundary(["/bin/true"], tmp / "run-pass", 5, failed_probe)
    expect(run["status"] == "refused" and run["started"] is False, f"{run}")


# ------------------------------------------------------------------ network isolation (C-7)


def test_boundary_network_interfaces_inside_are_loopback_only(tmp: Path):
    """C-7. Inside the boundary /proc/net/dev lists no external interface. Loopback alone is acceptable."""
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-net", ["--net-interfaces"], 20, probe)
    expect(run["execution_status"] == "exited-0", f"{run}")
    names = {line.strip() for line in (tmp / "run-net" / "proc" / "stdout.txt").read_text().splitlines() if line.strip()}
    expect(names and names <= {"lo"}, f"an external interface is visible inside the boundary: {sorted(names)}")


def test_boundary_local_listener_is_unreachable_inside_and_reachable_outside(tmp: Path):
    """C-7. A listener the test owns on 127.0.0.1. The boundary blocks it. The control reaches it.
    No external endpoint is used."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        outside = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            outside.settimeout(3)
            outside.connect(("127.0.0.1", port))
            reached_outside = True
        except OSError:
            reached_outside = False
        finally:
            outside.close()
        expect(reached_outside, "the control connect to the local listener failed")
        probe = _probe(tmp)
        run = A.run_stub(tmp / "run-listener", ["--connect", str(port)], 20, probe)
        expect(run["execution_status"] == "exited-0", f"{run}")
        stdout = (tmp / "run-listener" / "proc" / "stdout.txt").read_text()
        expect("connect=no" in stdout, f"the local listener was reachable inside: {stdout!r}")
    finally:
        listener.close()


# ------------------------------------------------------------------ process and output adapters (A-1 to A-5, C-5)


def test_adapter_records_command_exit_hashes_and_time(tmp: Path):
    """A-1. The adapter records the command, the exit code, the output hashes and the measured time."""
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-a1", ["hello"], 20, probe)
    expect(run["exit_code"] == 0 and run["execution_status"] == "exited-0", f"{run}")
    expect(run["elapsed_seconds"] > 0, "elapsed time is not measured")
    stdout = (tmp / "run-a1" / "proc" / "stdout.txt").read_text()
    expect(run["stdout_sha256"] == SB.sha256_text(stdout), "stdout hash does not match the retained output")
    expect(run["argv"] and run["flags"] is not None and run["argv_sha256"], "argv, flags or hash missing")


def test_adapter_timeout_stops_the_process_without_a_retry(tmp: Path):
    """A-2. A long stub under the timeout utility is stopped. The record gives the reason. One attempt."""
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-a2", ["--sleep", "10"], 1, probe)
    expect(run["execution_status"] == "timeout", f"not stopped by timeout: {run}")
    expect(run["exit_code"] == 124 and "timeout" in run["stop_reason"], f"{run}")
    expect(run["attempts"] == 1 and run["automatic_retry"] is False, f"retried: {run}")


def test_adapter_child_ticks_are_observed_live_then_stop(tmp: Path):
    """B-3. The tick count increases while the stub runs (at least two live increases). The immediate
    post-return count equals the count after the declared observation interval. Taken after the return,
    not before a sleep. One attempt, no retry, exit 124, the stop reason recorded."""
    probe = _probe(tmp)
    run_root = tmp / "run-child"
    run = A.run_stub_observed(run_root, ["--spawn-child", "30"], 2, probe,
                              sample_seconds=0.2, observe_seconds=1.5)
    expect(run["execution_status"] == "timeout" and run["exit_code"] == 124, f"{run}")
    counts = [sample["ticks"] for sample in run["live_samples"]]
    increases = sum(1 for prev, cur in zip(counts, counts[1:]) if cur > prev)
    expect(increases >= 2, f"the child ticks did not increase while the stub ran: {counts}")
    expect(run["immediate_post_return_count"] > 0, "the child wrote no ticks")
    expect(run["immediate_post_return_count"] == run["later_count"],
           f"the tick count changed after the return: {run['immediate_post_return_count']} then {run['later_count']}")
    expect(run["attempts"] == 1 and run["automatic_retry"] is False, f"retried: {run}")
    expect("timeout" in run["stop_reason"] and "124" in run["stop_reason"], f"{run['stop_reason']}")
    expect(run["observation_interval_seconds"] == 1.5, f"{run['observation_interval_seconds']}")


def test_adapter_pi_baseline_rejects_a_nonempty_skill_path_list(tmp: Path):
    """B-2. A Pi baseline with explicit skill paths is rejected. The argv carries no --skill."""
    try:
        A.command_for("pi", "p", mode="none", skill_paths=["/work/skill"])
    except ValueError:
        pass
    else:
        raise AssertionError("the Pi baseline accepted a nonempty skill path list")
    argv = A.command_for("pi", "p", mode="none")
    expect("--skill" not in argv and "--no-skills" in argv, f"baseline argv {argv}")


def test_adapter_pi_skill_mode_attaches_only_the_declared_skill(tmp: Path):
    """B-2. --skill appears only in skill mode, once for each declared path."""
    argv = A.command_for("pi", "p", mode="skill", skill_paths=["/work/one", "/work/two"])
    expect(argv.count("--skill") == 2 and "--no-skills" not in argv, f"skill argv {argv}")


def test_adapter_missing_host_is_unavailable_not_a_pass(tmp: Path):
    """A-3. A missing host binary is recorded as unavailable."""
    status = A.host_status("no-such-host-binary-for-this-test")
    expect(status["status"] == "unavailable" and status["path"] == "", f"{status}")


def test_adapter_failure_stays_on_disk_and_is_not_retried(tmp: Path):
    """A-4. A failing process keeps its output. The adapter does not run it again."""
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-a4", ["--exit", "3"], 20, probe)
    expect(run["execution_status"] == "failed" and run["exit_code"] == 3, f"{run}")
    expect((tmp / "run-a4" / "proc" / "stdout.txt").is_file(), "the failed output was not kept")
    expect(run["attempts"] == 1, f"{run}")


def test_adapter_makes_no_network_or_provider_import(tmp: Path):
    """A-5. The adapter and the boundary modules import no network client and no provider SDK."""
    for name in ("adapters.py", "sandbox.py"):
        source = (ROOT / "tests" / "eval" / name).read_text(encoding="utf-8")
        for forbidden in ("import requests", "import urllib", "import http", "import anthropic",
                          "import openai", "from urllib", "from http"):
            expect(forbidden not in source, f"{name} imports {forbidden}")


# ------------------------------------------------------------------ flags, host rules and separation (C-1, C-2)


def test_adapter_command_flags_come_from_installed_help(tmp: Path):
    """Every flag of every built command appears in the retained installed CLI help."""
    for host in ("codex", "claude-code", "pi"):
        argv = A.command_for(host, "fixture prompt", mode="skill", skill_paths=["/work/skill"])
        missing = A.flags_missing_from_help(host, argv)
        expect(missing == [], f"{host} flags not in the installed help: {missing}")


def test_adapter_codex_keeps_host_rules_and_permission_defaults(tmp: Path):
    """C-1. No trust bypass and no permission override in the Codex command."""
    argv = A.command_for("codex", "fixture prompt")
    for token in ("--ignore-user-config", "--ignore-rules", "-s", "workspace-write", "--dangerously-bypass-approvals-and-sandbox"):
        expect(token not in argv, f"the Codex command sets {token}")


def test_adapter_claude_skills_enabled_for_skill_runs_and_disclosed_in_baseline(tmp: Path):
    """C-2. Skill runs keep skills enabled. The baseline flag is present only in the baseline mode, and
    its effect is disclosed."""
    skill_argv = A.command_for("claude-code", "p", mode="skill")
    expect("--disable-slash-commands" not in skill_argv, "a skill run disables skills")
    baseline_argv = A.command_for("claude-code", "p", mode="none")
    expect("--disable-slash-commands" in baseline_argv, "the baseline does not disable skills")
    policy = A.baseline_policy("claude-code")
    expect(policy["status"] == "allowed-with-disclosure" and "disables" in policy["effect"]
           and "not remove" in policy["effect"], f"{policy}")


def test_adapter_codex_baseline_is_refused_for_measured_evaluation(tmp: Path):
    """Codex user-level skills are unmeasured, so its baseline cannot claim an empty skill set."""
    policy = A.baseline_policy("codex")
    expect(policy["status"] == "refused-for-measured-evaluation", f"{policy}")


def test_adapter_host_commands_never_override_home_or_config(tmp: Path):
    """No host command sets HOME, and none passes a setenv or a config path override."""
    for host in ("codex", "claude-code", "pi"):
        for mode in ("skill", "none"):
            argv = A.command_for(host, "p", mode=mode, skill_paths=["/work/s"] if mode == "skill" else None)
            expect("HOME" not in " ".join(argv) and "--setenv" not in argv, f"{host} {mode} overrides the environment")


def test_adapter_sets_no_model_flag_and_no_credential(tmp: Path):
    """Models and credentials are preserved. No built command carries a model or a credential flag."""
    for host in ("codex", "claude-code", "pi"):
        argv = A.command_for(host, "fixture prompt")
        for token in argv:
            expect(token not in ("-m", "--model", "--api-key", "--provider"), f"{host} sets {token}")


def test_adapter_baseline_mode_disables_skills_for_pi(tmp: Path):
    expect("--no-skills" in A.command_for("pi", "p", mode="none"), "baseline does not disable skills")
    expect("--skill" in A.command_for("pi", "p", mode="skill", skill_paths=["/work/x"]),
           "single-skill mode does not attach the skill")


def test_adapter_output_keeps_each_fact_separate(tmp: Path):
    """S-1 and S-2. Discovery, selection, trace, tokens and execution status are separate fields.
    A host that reports none of them leaves each one unavailable."""
    parsed = A.parse_output('{"type":"message"}\nplain line\n')
    expect(parsed["host_discovery_status"] == "unavailable" and parsed["host_discovered_paths"] is None,
           f"{parsed}")
    expect(parsed["host_selection_status"] == "unavailable" and parsed["host_selected_paths"] is None,
           f"{parsed}")
    expect(parsed["reported_tokens"] is None and parsed["token_status"].startswith("unavailable"),
           f"{parsed}")
    expect(parsed["trace_status"] == "raw-lines" and parsed["trace_line_count"] == 2, f"{parsed}")
    expect("execution_status" not in parsed, "execution status leaked into the output parser")


def test_adapter_local_scan_is_not_host_selection(tmp: Path):
    """S-3. A local skill inventory never fills a host field."""
    parsed = A.parse_output("")
    expect(parsed["host_selected_paths"] is None and parsed["host_discovered_paths"] is None,
           "a local scan filled a host field")


def test_adapter_process_time_is_measured_not_inferred(tmp: Path):
    """S-4. The elapsed time is measured by the adapter around the process."""
    probe = _probe(tmp)
    run = A.run_stub(tmp / "run-s4", ["--sleep", "1"], 20, probe)
    expect(run["elapsed_seconds"] >= 1.0, f"elapsed {run['elapsed_seconds']} is not measured around a 1 s sleep")


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
