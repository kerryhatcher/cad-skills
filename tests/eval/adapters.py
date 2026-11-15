# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Host process and output adapters. Local only. No provider call and no network.

The command builders take their flags from the retained installed CLI help (tests/eval/fixtures/
cli-help). A test checks each flag against that help text.

Host command construction preserves the host defaults (release record, 2026-11-15):

- No trust bypass. The Codex command does not set `--ignore-user-config` or `--ignore-rules`.
- No permission override. The Codex command does not set `-s`. The host default stays, and it is
  recorded as unmeasured.
- No model flag and no credential flag.
- No HOME override. The builders never set HOME. The temporary HOME exists only inside the stub
  boundary (sandbox.py), for credential-free stub tests.
- Skills stay enabled for skill runs. The Claude baseline may use `--disable-slash-commands`. That
  flag disables commands as well as skills, and it is recorded as such.
- The Codex baseline is refused for measured evaluation. Its user-level skills are unmeasured, so it
  cannot claim an empty skill set.

Facts stay separate and each one is recorded explicitly:

- discovery: `host_discovery_status`, `host_discovered_paths`. Not measured here: unavailable.
- selection: `host_selection_status`, `host_selected_paths`. Not measured here: unavailable.
- trace: `trace_status`. Raw output lines are retained. No structured event schema is measured.
- token usage: `reported_tokens`, `token_status`. No measured output schema: unavailable.
- execution status: `execution_status`, from the exit code, the timeout and the refusal.

No adapter retries. A failed attempt stays on disk.
"""

from __future__ import annotations

import json
import shutil
import threading
import time
from pathlib import Path

import sandbox as SB

HELP_DIR = Path(__file__).resolve().parent / "fixtures" / "cli-help"
HOST_HELP = {"codex": "codex-exec.txt", "claude-code": "claude.txt", "pi": "pi.txt"}
HOST_BINARY = {"codex": "codex", "claude-code": "claude", "pi": "pi"}
WORK = "/work"  # the run root inside the boundary


def host_status(binary_name: str) -> dict:
    """Presence of a host binary on PATH. A missing binary is unavailable, not a pass or a fail."""
    path = shutil.which(binary_name)
    return {"binary": binary_name, "status": "present" if path else "unavailable", "path": path or ""}


def baseline_policy(host: str) -> dict:
    """What an empty-skill baseline means for each host. A host that cannot state its skill set is
    refused for measured evaluation (release record)."""
    if host == "codex":
        return {"host": host, "status": "refused-for-measured-evaluation",
                "reason": "user-level skills are unmeasured. The baseline skill set is not established"}
    if host == "claude-code":
        return {"host": host, "status": "allowed-with-disclosure",
                "effect": "--disable-slash-commands disables all commands and skills. It disables them and does "
                          "not remove them"}
    if host == "pi":
        return {"host": host, "status": "allowed", "effect": "--no-skills disables skill discovery and loading"}
    raise ValueError(f"unknown host {host}")


def command_for(host: str, prompt: str, mode: str = "skill", skill_paths: list[str] | None = None) -> list[str]:
    """The host argv. `mode` is 'skill' (skills enabled), or 'none' (baseline). No model flag, no
    credential flag, no trust bypass, no permission override, and no HOME change."""
    if host == "codex":
        return ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                "-C", WORK, prompt]
    if host == "claude-code":
        argv = ["claude", "-p", "--output-format", "stream-json", "--no-session-persistence",
                "--add-dir", WORK]
        if mode == "none":
            argv.append("--disable-slash-commands")
        return argv + [prompt]
    if host == "pi":
        argv = ["pi", "-p", "--mode", "json", "--no-session", "--offline"]
        if mode == "none":
            # B-2. The baseline carries no skill. A nonempty skill path list is rejected, not passed.
            if skill_paths:
                raise ValueError("the Pi baseline rejects skill paths. Use skill mode to attach a skill")
            return argv + ["--no-skills", prompt]
        for path in skill_paths or []:
            argv += ["--skill", path]
        return argv + [prompt]
    raise ValueError(f"unknown host {host}")


def flags_missing_from_help(host: str, argv: list[str]) -> list[str]:
    """Each flag in the argv must appear in the retained installed help. Return the missing ones."""
    help_text = (HELP_DIR / HOST_HELP[host]).read_text(encoding="utf-8")
    return [token for token in argv[1:] if token.startswith("-") and token not in help_text]


def run_stub(run_root: Path, stub_args: list[str], timeout_seconds: int, probe: dict) -> dict:
    """Run the local stub script inside the boundary. One attempt only. Return the process record."""
    stub_src = Path(__file__).resolve().parent / "fixtures" / "stub" / "stub.sh"
    run_root.mkdir(parents=True, exist_ok=True)
    stub = run_root / "stub.sh"
    stub.write_bytes(stub_src.read_bytes())
    inside = ["/bin/sh", f"{WORK}/stub.sh", *stub_args]
    result = SB.run_in_boundary(inside, run_root, timeout_seconds, probe)
    if result["status"] != "ran":
        return {**result, "execution_status": "refused", "attempts": 0}
    out_dir = run_root / "proc"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stdout.txt").write_text(result["stdout"], encoding="utf-8")
    (out_dir / "stderr.txt").write_text(result["stderr"], encoding="utf-8")
    code = result["exit_code"]
    if code == 124:
        execution, stop = "timeout", f"stopped by timeout after {timeout_seconds} s (exit 124)"
    elif code == 0:
        execution, stop = "exited-0", ""
    else:
        execution, stop = "failed", f"exit {code}"
    record = {k: v for k, v in result.items() if k not in ("stdout", "stderr")}
    record.update({"execution_status": execution, "stop_reason": stop, "attempts": 1,
                   "automatic_retry": False, "stdout_path": "proc/stdout.txt",
                   "stderr_path": "proc/stderr.txt"})
    return record


def tick_count(ticks_file: Path) -> int:
    """Lines in the child tick file. A missing file counts as zero."""
    if not ticks_file.is_file():
        return 0
    return len(ticks_file.read_text(encoding="utf-8").splitlines())


def run_stub_observed(run_root: Path, stub_args: list[str], timeout_seconds: int, probe: dict,
                      sample_seconds: float = 0.2, observe_seconds: float = 1.5) -> dict:
    """Run the stub in a thread and sample the child tick file while it runs (B-3).

    After the stub returns, the record holds the live samples, the immediate post-return count, and
    the count after the declared observation interval. A change between the two fails the test. One
    attempt, no retry. The count is taken after the return, and no earlier count is claimed.
    """
    ticks_file = run_root / "proc" / "child-ticks.txt"
    holder: dict = {}
    samples: list[dict] = []
    started = time.monotonic()

    def target() -> None:
        holder["run"] = run_stub(run_root, stub_args, timeout_seconds, probe)

    worker = threading.Thread(target=target)
    worker.start()
    while worker.is_alive():
        samples.append({"t_seconds": round(time.monotonic() - started, 3), "ticks": tick_count(ticks_file)})
        time.sleep(sample_seconds)
    worker.join()
    run = holder["run"]
    immediate = tick_count(ticks_file)
    time.sleep(observe_seconds)
    later = tick_count(ticks_file)
    run.update({"live_samples": samples, "sample_interval_seconds": sample_seconds,
                "immediate_post_return_count": immediate, "later_count": later,
                "observation_interval_seconds": observe_seconds})
    return run


def parse_output(stdout: str) -> dict:
    """Keep each fact separate. Only what the output shows is recorded. The rest is unavailable."""
    lines = [line for line in stdout.splitlines() if line.strip()]
    json_lines = 0
    for line in lines:
        try:
            json.loads(line)
            json_lines += 1
        except json.JSONDecodeError:
            pass
    return {
        "trace_status": "raw-lines",
        "trace_line_count": len(lines),
        "trace_json_lines": json_lines,
        "reported_tokens": None,
        "token_status": "unavailable: no measured output schema",
        "host_discovery_status": "unavailable",
        "host_discovered_paths": None,
        "host_selection_status": "unavailable",
        "host_selected_paths": None,
    }
