# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Filesystem and network boundary for local stub subprocesses. Local only. No provider, no network.

Route: bubblewrap (`bwrap`). Its host requirement is `bwrap` on PATH (bubblewrap 0.13.1 measured on
this host). The subprocess sees the system directories read-only, the run root as its only writable
directory, and a temporary HOME inside the run root. The repository and the real HOME are not
mounted. `--unshare-all` gives the subprocess its own network namespace.

The temporary HOME serves credential-free local stub tests only. It is not a route for an
authenticated host, and no real HOME is mounted or exposed (release record, 2026-11-15).

Refused routes:
- `unshare` alone gives a user namespace. It does not hide any file. It is refused (I-3), not passed.

A route is established only when the measured probe passes:
- control: the sentinel is readable outside the boundary.
- boundary: the sentinel is not readable inside, and the run root is.

When the probe fails, the operation is refused before the subprocess starts. No silent fallback.
Every record keeps the full argv, its flags, its SHA-256, and the probe's stderr text and hash.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SENTINEL = REPO / "README.md"  # a tracked repository file. The subprocess must not read it.
SYSTEM_DIRS = ["/usr", "/lib", "/lib64", "/bin"]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_argv(argv: list[str]) -> str:
    return sha256_text("\x00".join(argv))


def flags_of(argv: list[str]) -> list[str]:
    """The option tokens of an argv. Values and prompts are not flags."""
    return [token for token in argv if token.startswith("-")]


def _bwrap_args(run_root: Path) -> list[str]:
    args = []
    for path in SYSTEM_DIRS:
        if Path(path).exists():
            args += ["--ro-bind", path, path]
    args += ["--proc", "/proc", "--dev", "/dev", "--unshare-all", "--die-with-parent",
             "--bind", str(run_root), "/work", "--chdir", "/work"]
    return args


def _version(binary: str, flag: str = "--version") -> str:
    try:
        out = subprocess.run([binary, flag], capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "unavailable"


def probe_bwrap(run_root: Path) -> dict:
    """Measure the bwrap boundary with the repository sentinel. Return one record. Never raise."""
    binary = shutil.which("bwrap")
    record = {"route": "bwrap", "host_version": _version("bwrap") if binary else "unavailable",
              "sentinel": SENTINEL.relative_to(REPO).as_posix(), "boundary_established": False}
    if binary is None:
        record["reason"] = "bwrap is not installed. The route is unavailable and refused"
        return record
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "probe-ok.txt").write_text("run root readable\n", encoding="utf-8")
    script = (f"cat /work/probe-ok.txt; "
              f"if cat {SENTINEL} >/dev/null 2>/work/probe-err.txt; then echo SENTINEL_READ; "
              f"else echo SENTINEL_HIDDEN; fi")
    argv = [binary, *_bwrap_args(run_root), "--", "/bin/sh", "-c", script]
    started = time.monotonic()
    done = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    elapsed = time.monotonic() - started
    probe_err_path = run_root / "probe-err.txt"
    probe_stderr = probe_err_path.read_text(encoding="utf-8") if probe_err_path.exists() else ""
    control = SENTINEL.is_file() and os.access(SENTINEL, os.R_OK)  # control: readable outside
    inside_hidden = "SENTINEL_HIDDEN" in done.stdout
    run_root_readable = "run root readable" in done.stdout
    record.update({
        "argv": argv,
        "flags": flags_of(argv),
        "argv_sha256": sha256_argv(argv),
        "command": " ".join(argv),
        "exit_code": done.returncode,
        "stdout_sha256": sha256_text(done.stdout),
        "stderr_sha256": sha256_text(done.stderr),
        "probe_stderr": probe_stderr,
        "probe_stderr_sha256": sha256_text(probe_stderr),
        "elapsed_seconds": round(elapsed, 3),
        "control_sentinel_readable_outside": control,
        "sentinel_hidden_inside": inside_hidden,
        "run_root_readable_inside": run_root_readable,
    })
    record["boundary_established"] = bool(control and inside_hidden and run_root_readable
                                          and done.returncode == 0)
    record["reason"] = ("" if record["boundary_established"]
                        else "probe failed. The boundary is not established and the route is refused")
    return record


def refuse_unshare() -> dict:
    """I-3. `unshare` gives a user namespace only. It hides no file. Refused, not passed."""
    binary = shutil.which("unshare")
    return {"route": "unshare", "host_version": _version("unshare") if binary else "unavailable",
            "boundary_established": False,
            "reason": "unshare provides a user namespace only. No file boundary is measured. Refused (I-3)"}


def run_in_boundary(argv_inside: list[str], run_root: Path, timeout_seconds: int, probe: dict) -> dict:
    """Run argv inside the bwrap boundary with the timeout utility. Refuse if the probe failed.

    argv_inside names paths as they appear inside the boundary (for example /work/stub.sh).
    The environment is cleared. HOME is a directory inside the run root. No credential is passed.
    """
    if not probe.get("boundary_established"):
        return {"status": "refused", "reason": probe.get("reason", "boundary not established"),
                "started": False}
    binary = shutil.which("bwrap")
    timeout_bin = shutil.which("timeout") or "/usr/bin/timeout"
    (run_root / "home").mkdir(parents=True, exist_ok=True)
    argv = [binary, *_bwrap_args(run_root), "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/work/home",
            "--", timeout_bin, "--kill-after=2", str(timeout_seconds), *argv_inside]
    started = time.monotonic()
    done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds + 30)
    elapsed = time.monotonic() - started
    return {"status": "ran", "started": True, "argv": argv, "flags": flags_of(argv),
            "argv_sha256": sha256_argv(argv), "command": " ".join(argv),
            "inside_argv": argv_inside, "exit_code": done.returncode,
            "stdout": done.stdout, "stderr": done.stderr,
            "stdout_sha256": sha256_text(done.stdout), "stderr_sha256": sha256_text(done.stderr),
            "elapsed_seconds": round(elapsed, 3), "timeout_seconds": timeout_seconds}
