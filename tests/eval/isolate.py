# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Install one skill into a fresh root for one host. Local only. No provider call.

Install modes:

- project: copy into the host's project-scoped skill path under the root.
- user: copy into the host's user-scoped path under `<root>/home`. The real home is never used.
- symlink: copy the skill to `<root>/frozen`, then link the host's project path to that copy.
  Only Codex and Pi are tested with symbolic links.

Discovery paths are the documented paths of each host. Claude Code paths are not measured yet.
The first discovery run measures them. Until then the paths are proposals.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import yaml

from common import aggregate_digest, tree_digest

DISCOVERY = {
    "codex": {"project": [".agents/skills"], "user": [".agents/skills"]},
    "pi": {
        "project": [".pi/skills", ".agents/skills"],
        "user": [".pi/agent/skills", ".agents/skills"],
    },
    "claude-code": {"project": [".claude/skills"], "user": [".claude/skills"]},
}
SYMLINK_HOSTS = {"codex", "pi"}
MAX_NAME = 64
MAX_DESCRIPTION = 1024


class IsolationError(Exception):
    """Base class. A message names the problem and the action to take."""


class MissingSkillFile(IsolationError):
    pass


class DuplicateSkillName(IsolationError):
    pass


class OutsideRoot(IsolationError):
    pass


def _inside(root: Path, target: Path) -> bool:
    """True when target lies under root. Symbolic links are not followed for this check."""
    base = os.path.normpath(os.path.abspath(root))
    path = os.path.normpath(os.path.abspath(target))
    return path == base or path.startswith(base + os.sep)


def new_root(root: Path) -> Path:
    """Create an empty root. Refuse a root that already holds files."""
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise IsolationError(f"root is not empty: {root}. Use a new directory for each run.")
    root.mkdir(parents=True, exist_ok=True)
    return root


def scan_installed(root: Path, host: str) -> list[tuple[str, Path]]:
    """Filesystem inventory: list every skill directory under the assumed host paths of root.

    This is not host discovery. No host is called. Host discovery and measured selection are
    separate facts, and they stay unavailable until a host reports them.
    """
    found: list[tuple[str, Path]] = []
    for scope in ("project", "user"):
        base = Path(root) / "home" if scope == "user" else Path(root)
        for rel in DISCOVERY[host][scope]:
            directory = base / rel
            if not directory.is_dir():
                continue
            for child in sorted(directory.iterdir()):
                if child.is_dir() and (child / "SKILL.md").is_file():
                    found.append((child.name, child))
    return found


def check_duplicates(found: list[tuple[str, Path]]) -> None:
    """Stop when two skill directories share one name. A host keeps only the first one."""
    seen: dict[str, Path] = {}
    for name, path in found:
        if name in seen:
            raise DuplicateSkillName(
                f"skill name '{name}' appears twice: {seen[name]} and {path}. "
                "Remove one copy before the run."
            )
        seen[name] = path


def diagnose_skill_md(skill_dir: Path) -> list[str]:
    """Return the problems that a host would report for SKILL.md. An empty list means no problem."""
    path = Path(skill_dir) / "SKILL.md"
    if not path.is_file():
        return ["SKILL.md is missing"]
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ["frontmatter is missing"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ["frontmatter is not closed"]
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as error:
        return [f"frontmatter is malformed: {error.__class__.__name__}"]
    if not isinstance(data, dict):
        return ["frontmatter is not a mapping"]
    problems: list[str] = []
    name = data.get("name")
    description = data.get("description")
    if not name:
        problems.append("name is missing")
    elif str(name) != skill_dir.name:
        problems.append("name differs from the directory name")
    elif len(str(name)) > MAX_NAME:
        problems.append("name is longer than 64 characters")
    if not description or not str(description).strip():
        problems.append("description is missing or empty")
    elif len(str(description)) > MAX_DESCRIPTION:
        problems.append("description is longer than 1024 characters")
    return problems


def install_set(sources: list[Path], root: Path, host: str, mode: str) -> list[dict]:
    """Install several skills into one root. A routing run installs all three public skills.

    The host then chooses among them. The records list every discovered path that the host sees.
    """
    records = [install(source, root, host, mode) for source in sources]
    names = sorted(record["installed_path"].rsplit("/", 1)[-1] for record in records)
    found = sorted(name for name, _ in scan_installed(root, host))
    if found != names:
        raise IsolationError(f"host paths discover {found}, not the installed set {names}")
    return records


def install(source: Path, root: Path, host: str, mode: str) -> dict:
    """Install one skill and return its record. Raise IsolationError on any problem."""
    source = Path(source)
    root = Path(root)
    if host not in DISCOVERY:
        raise IsolationError(f"unknown host '{host}'")
    if mode not in ("project", "user", "symlink"):
        raise IsolationError(f"unknown install mode '{mode}'")
    if mode == "symlink" and host not in SYMLINK_HOSTS:
        raise IsolationError(f"symbolic links are not tested for {host}. Use project or user mode.")
    if not (source / "SKILL.md").is_file():
        raise MissingSkillFile(f"{source} has no SKILL.md. Check the skill path.")
    name = source.name
    check_duplicates(scan_installed(root, host))

    scope = "user" if mode == "user" else "project"
    base = root / "home" if scope == "user" else root
    target = base / DISCOVERY[host][scope][0] / name
    if not _inside(root, target):
        raise OutsideRoot(f"{target} is outside the run root {root}. Nothing was written.")
    if target.exists() or target.is_symlink():
        raise IsolationError(f"{target} already exists. Use a new root for each run.")
    target.parent.mkdir(parents=True, exist_ok=True)

    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    if mode == "symlink":
        frozen = root / "frozen" / name
        shutil.copytree(source, frozen, ignore=ignore)
        os.symlink(frozen, target)
        real = Path(os.path.realpath(target))
    else:
        shutil.copytree(source, target, ignore=ignore)
        real = target

    source_files = tree_digest(source)
    installed_files = tree_digest(real)
    if source_files != installed_files:
        raise IsolationError(f"installed copy of {name} differs from the source. Stop the run.")

    found = scan_installed(root, host)
    check_duplicates(found)
    selected = [path for skill, path in found if skill == name]
    if len(selected) != 1 or os.path.normpath(selected[0]) != os.path.normpath(target):
        raise IsolationError(f"host paths do not select {target}. Record the discovery problem.")

    return {
        "host": host,
        "install_mode": mode,
        "scope": scope,
        "installed_path": target.relative_to(root).as_posix(),
        "home_root": (root / "home").relative_to(root).as_posix() if scope == "user" else None,
        "filesystem_selected_path": selected[0].relative_to(root).as_posix(),
        "scanned_paths": [p.relative_to(root).as_posix() for _, p in found],
        "skill_sha256": aggregate_digest(source_files),
        "file_count": len(source_files),
        "diagnostics": diagnose_skill_md(target),
    }
