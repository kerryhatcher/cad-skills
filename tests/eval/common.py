# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Shared helpers for the release harness: matrix loading, hashes and run counts.

The harness makes no provider call in this revision. See run_case.py.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

EVAL_DIR = Path(__file__).resolve().parent
MATRIX_PATH = EVAL_DIR / "matrix.yaml"
IGNORED_NAMES = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc"}


def load_matrix(path: Path = MATRIX_PATH) -> dict:
    """Read the fixed matrix. The file holds no secret and no provider setting."""
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(root: Path) -> dict[str, str]:
    """Map each relative file path under root to its SHA-256. Caches and bytecode are skipped."""
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in rel.parts) or path.suffix in IGNORED_SUFFIXES:
            continue
        files[rel.as_posix()] = sha256_file(path)
    return files


def aggregate_digest(files: dict[str, str]) -> str:
    """One SHA-256 for a whole tree, from its sorted path and file hash pairs."""
    lines = "\n".join(f"{name} {digest}" for name, digest in sorted(files.items()))
    return sha256_bytes(lines.encode("utf-8"))


def counts(matrix: dict) -> dict[str, int]:
    """Derive every count from the matrix. The tests compare these with the accepted numbers."""
    skills = len(matrix["skills"])
    hosts = len(matrix["hosts"])
    cases = len(matrix["routing"]["cases"])
    routing = skills * cases * hosts * matrix["routing"]["repeats"]
    artifact_skill = skills * hosts * matrix["artifact"]["runs_per_cell"]
    artifact_baseline = skills * hosts * matrix["artifact"]["runs_per_cell"]
    explicit = skills * hosts * matrix["explicit"]["repeats"]
    compaction = hosts * matrix["compaction"]["runs_per_host"]
    core = routing + artifact_skill + artifact_baseline
    paid_total = core + explicit + compaction
    install_copy = skills * hosts
    install_symlink = skills * sum(
        1 for host in matrix["hosts"] if "symlink" in host["install_modes"]
    )
    install_user = skills * sum(1 for host in matrix["hosts"] if "user" in host["install_modes"])
    return {
        "routing": routing,
        "artifact_skill": artifact_skill,
        "artifact_baseline": artifact_baseline,
        "core": core,
        "explicit": explicit,
        "compaction": compaction,
        "paid_total": paid_total,
        "install_copy": install_copy,
        "install_symlink": install_symlink,
        "install_user": install_user,
        "install_total": install_copy + install_symlink + install_user,
    }


def worst_case_tokens(matrix: dict) -> int:
    """Sum of the per-run ceilings for every scheduled run. Compare it with the batch ceiling."""
    value = counts(matrix)
    limits = matrix["limits"]
    short = limits["routing_and_explicit"]["reported_tokens"]
    long = limits["artifact_baseline_compaction"]["reported_tokens"]
    short_runs = value["routing"] + value["explicit"]
    long_runs = value["artifact_skill"] + value["artifact_baseline"] + value["compaction"]
    return short_runs * short + long_runs * long
