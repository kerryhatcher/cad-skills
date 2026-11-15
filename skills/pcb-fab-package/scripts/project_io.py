#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Project lock, confined paths, atomic file write and package publication.

  uv run contracts/project_io.py hold    --project DIR --task ID [--seconds N]
  uv run contracts/project_io.py try     --project DIR --task ID
  uv run contracts/project_io.py status  --project DIR
  uv run contracts/project_io.py release --project DIR --token T

The lock protects cooperating processes on one local file system. It does not protect
against a hostile process, a network file system, a power loss, or a rollback of several files.
Code never removes an existing lock. After the user finds that the owner stopped,
the user removes the file `.cad-skills.lock`.

The caller holds the lock for the whole sequence: validate the staged package, then publish it.
`publish_dir` does not know the schema.

Exit status: 0 success, 1 refused (lock.held, lock.malformed, lock.token_mismatch, path.escape,
path.symlink), 2 incorrect arguments, 3 tool failure.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import secrets
import socket
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

LOCK_NAME = ".cad-skills.lock"
TEMP_PREFIX = ".cad-skills-tmp-"


class LockHeld(Exception):
    """The lock file exists. `owner` is the owner record."""

    def __init__(self, owner):
        self.owner = owner
        super().__init__("Another process holds the project lock.")


class LockMalformed(Exception):
    """The lock file exists but is not a valid lock record."""


class PathEscape(Exception):
    """A path resolves outside the project root."""


class SymlinkTarget(PathEscape):
    """The target of a write is a symbolic link."""


class PostReplaceError(OSError):
    """The new bytes are in place, but a step after `os.replace` failed."""

    replaced = True


class PostRenameError(OSError):
    """The new package is visible, but a step after `os.rename` failed."""

    renamed = True


# --------------------------------------------------------------------------- lock


def _start_ticks():
    try:
        with open("/proc/self/stat", "rb") as handle:
            return int(handle.read().rsplit(b")", 1)[1].split()[19])
    except (OSError, ValueError, IndexError):
        return None


def read_lock(project):
    """Return the lock record, or None if there is no lock. Raise LockMalformed for a bad file."""
    path = Path(project) / LOCK_NAME
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as err:
        raise LockMalformed(f"Cannot read the lock file: {err}")
    try:
        record = json.loads(text)
    except ValueError as err:
        raise LockMalformed(f"The lock file is not valid JSON: {err}")
    if not isinstance(record, dict) or not isinstance(record.get("token"), str):
        raise LockMalformed("The lock file has no token.")
    return record


def acquire_lock(project, task: str) -> dict:
    """Create the lock file with an exclusive create. Raise LockHeld or LockMalformed if it exists."""
    path = Path(project) / LOCK_NAME
    record = {
        "schema_version": "1.0", "pid": os.getpid(), "host": socket.gethostname(), "start_ticks": _start_ticks(),
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "task": task,
        "token": secrets.token_hex(16),
    }
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        raise LockHeld(read_lock(project))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def release_lock(project, token: str) -> bool:
    """Remove the lock if the token matches. Return False if it does not match or there is no lock."""
    record = read_lock(project)
    if record is None or record["token"] != token:
        return False
    (Path(project) / LOCK_NAME).unlink()
    return True


@contextlib.contextmanager
def project_lock(project, task: str):
    """Hold the project lock for a block. Release it when the block ends or fails."""
    record = acquire_lock(project, task)
    try:
        yield record
    finally:
        release_lock(project, record["token"])


# --------------------------------------------------------------------------- paths and writes


def confine(project, candidate, *, must_exist=False) -> Path:
    """Return the real path of `candidate` if it is under the project root. Raise PathEscape if not.

    A relative path starts at the root. A path that does not exist is resolved through
    the nearest part that exists, so a new leaf under an outside link is rejected.
    """
    root = Path(project).resolve()
    path = Path(candidate)
    if not path.is_absolute():
        path = root / path
    existing, tail = path, []
    while not os.path.lexists(existing) and existing != existing.parent:
        tail.insert(0, existing.name)
        existing = existing.parent
    real = existing.resolve().joinpath(*tail)
    real = Path(os.path.normpath(real))
    if real != root and root not in real.parents:
        raise PathEscape(f"The path {candidate} is outside the project root.")
    if must_exist and not os.path.lexists(real):
        raise FileNotFoundError(real)
    return real


def _sync_directory(directory: Path):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(project, target, data: bytes, *, _before_replace=None, _after_replace=None) -> None:
    """Write `data` to `target` through a temporary file in the same directory.

    A failure before `os.replace` keeps the old bytes and removes the temporary file.
    A failure after `os.replace` raises PostReplaceError. The new bytes are then in place,
    and the function does not restore the old bytes. A crash can leave a temporary file.
    """
    root = Path(project).resolve()
    lexical = Path(target) if Path(target).is_absolute() else root / target
    if os.path.islink(lexical):
        raise SymlinkTarget(f"The target {target} is a symbolic link.")
    path = confine(project, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    confine(project, path.parent, must_exist=True)
    mode = (path.stat().st_mode & 0o777) if path.is_file() else 0o644
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=TEMP_PREFIX)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, mode)
        if _before_replace is not None:
            _before_replace()
        os.replace(temp_name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)
        raise
    try:
        if _after_replace is not None:
            _after_replace()
        _sync_directory(path.parent)
    except OSError as err:
        raise PostReplaceError(f"The new bytes of {target} are in place, but a later step failed: {err}") from err


def publish_dir(project, staging, dest, *, _before_rename=None, _after_rename=None) -> None:
    """Move a complete staging directory to a new name under the project root.

    Both paths are confined. An existing destination is refused. A failure before `os.rename`
    leaves no new package. A failure of the directory synchronization after `os.rename`
    raises PostRenameError, and the complete new package is visible.
    """
    root = Path(project).resolve()
    lexical = Path(dest) if Path(dest).is_absolute() else root / dest
    if os.path.lexists(lexical):  # This includes a dangling symbolic link.
        raise FileExistsError(lexical)
    source = confine(project, staging, must_exist=True)
    target = confine(project, dest)
    if not source.is_dir():
        raise NotADirectoryError(source)
    if os.path.lexists(target):
        raise FileExistsError(target)
    if source == target or target in source.parents or source in target.parents:
        raise ValueError("The staging and destination paths overlap.")
    target.parent.mkdir(parents=True, exist_ok=True)
    if _before_rename is not None:
        _before_rename()
    os.rename(source, target)
    try:
        if _after_rename is not None:
            _after_rename()
        _sync_directory(target.parent)
    except OSError as err:
        raise PostRenameError(f"The package {dest} is visible, but a later step failed: {err}") from err


# --------------------------------------------------------------------------- command line


class _ArgError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgError(message)


def _refuse(code, **extra):
    print(json.dumps({"code": code, **extra}))
    return 1


def main(argv=None) -> int:
    parser = _Parser(prog="project_io.py", description="Project lock helpers.")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("hold", "try"):
        one = sub.add_parser(name)
        one.add_argument("--project", required=True)
        one.add_argument("--task", required=True)
        if name == "hold":
            one.add_argument("--seconds", type=float, default=60.0)
    sub.add_parser("status").add_argument("--project", required=True)
    rel = sub.add_parser("release")
    rel.add_argument("--project", required=True)
    rel.add_argument("--token", required=True)
    try:
        args = parser.parse_args(argv)
    except _ArgError as err:
        print(f"project_io.py: error: {err}", file=sys.stderr)
        return 2
    project = Path(args.project)
    if not project.is_dir():
        print(f"project_io.py: error: {project} is not a directory", file=sys.stderr)
        return 2
    try:
        if args.command in ("hold", "try"):
            record = acquire_lock(project, args.task)
            print(json.dumps(record), flush=True)
            if args.command == "hold":
                try:
                    time.sleep(args.seconds)
                finally:
                    release_lock(project, record["token"])
            return 0
        if args.command == "status":
            record = read_lock(project)
            print(json.dumps(record) if record else "none")
            return 0
        if release_lock(project, args.token):
            return 0
        return _refuse("lock.token_mismatch")
    except LockHeld as err:
        return _refuse("lock.held", owner=err.owner)
    except LockMalformed as err:
        return _refuse("lock.malformed", message=str(err))
    except SymlinkTarget as err:
        return _refuse("path.symlink", message=str(err))
    except PathEscape as err:
        return _refuse("path.escape", message=str(err))
    except OSError as err:
        print(json.dumps({"code": "tool.failure", "message": str(err)}))
        return 3


if __name__ == "__main__":
    sys.exit(main())
