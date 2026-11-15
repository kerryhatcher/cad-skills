# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for contracts/project_io.py: lock, confined paths, atomic write, package publication.

  uv run tests/test_project_io.py            # all tests
  uv run tests/test_project_io.py lock       # only tests with 'lock' in their name

The lock tests use real operating-system processes. The module protects cooperating
processes on one local file system. The tests do not claim more.
"""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "contracts/project_io.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pcb_support as P  # noqa: E402

V = P.V
_spec = importlib.util.spec_from_file_location("project_io", TOOL)
IO = importlib.util.module_from_spec(_spec)
sys.modules["project_io"] = IO
_spec.loader.exec_module(IO)


def tool(*args):
    r = subprocess.run(["uv", "run", "-q", str(TOOL), *map(str, args)], capture_output=True, text=True)
    return r


def start_holder(project, seconds=30):
    proc = subprocess.Popen(["uv", "run", "-q", str(TOOL), "hold", "--project", str(project), "--task", "holder",
                             "--seconds", str(seconds)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line = proc.stdout.readline()
    assert line, proc.stderr.read()
    return proc, json.loads(line)


def stop(proc):
    if proc.poll() is None:
        proc.kill()
    proc.wait()


def snapshot(root: Path):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file() and p.name != IO.LOCK_NAME}


def test_lock_two_processes(tmp: Path):
    (tmp / "data.txt").write_text("data\n")
    before = snapshot(tmp)
    holder, record = start_holder(tmp)
    try:
        assert (tmp / IO.LOCK_NAME).is_file() and record["task"] == "holder" and len(record["token"]) == 32
        second = tool("try", "--project", tmp, "--task", "second")
        assert second.returncode == 1, second.stdout + second.stderr
        refusal = json.loads(second.stdout)
        assert refusal["code"] == "lock.held" and refusal["owner"]["token"] == record["token"]
        assert snapshot(tmp) == before, "a refused writer changes no file"
        status = tool("status", "--project", tmp)
        assert status.returncode == 0 and json.loads(status.stdout)["token"] == record["token"]
    finally:
        stop(holder)


def test_lock_read_only_while_held(tmp: Path):
    project = P.build_project(tmp / "project")
    holder, _ = start_holder(project)
    try:
        code, rep = P.examine(project)
        assert code == 0 and rep["findings"] == [], "validation does not take the lock"
        r = subprocess.run(["uv", "run", "-q", str(ROOT / "contracts/validate.py"), "--project", str(project)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
    finally:
        stop(holder)


def test_lock_interrupted_owner(tmp: Path):
    holder, record = start_holder(tmp)
    holder.send_signal(signal.SIGKILL)
    holder.wait()
    assert (tmp / IO.LOCK_NAME).is_file(), "code does not remove the lock of a stopped owner"
    again = tool("try", "--project", tmp, "--task", "next")
    assert again.returncode == 1 and json.loads(again.stdout)["owner"]["pid"] == record["pid"]
    (tmp / IO.LOCK_NAME).unlink()  # the user removes the file after the user finds that the owner stopped
    ok = tool("try", "--project", tmp, "--task", "next")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    token = json.loads(ok.stdout)["token"]
    assert tool("release", "--project", tmp, "--token", token).returncode == 0
    assert not (tmp / IO.LOCK_NAME).exists()


def test_lock_wrong_token_and_malformed(tmp: Path):
    ok = tool("try", "--project", tmp, "--task", "t")
    token = json.loads(ok.stdout)["token"]
    wrong = tool("release", "--project", tmp, "--token", "WRONG")
    assert wrong.returncode == 1 and json.loads(wrong.stdout)["code"] == "lock.token_mismatch"
    assert (tmp / IO.LOCK_NAME).is_file()
    assert tool("release", "--project", tmp, "--token", token).returncode == 0
    for text in ("not json", "[]", '{"pid": 1}'):
        (tmp / IO.LOCK_NAME).write_text(text)
        r = tool("try", "--project", tmp, "--task", "t")
        assert r.returncode == 1 and json.loads(r.stdout)["code"] == "lock.malformed", text
        assert (tmp / IO.LOCK_NAME).read_text() == text, "code does not change a malformed lock"
        assert tool("status", "--project", tmp).returncode == 1
        (tmp / IO.LOCK_NAME).unlink()
    assert tool("status", "--project", tmp).stdout.strip() == "none"
    assert tool("try", "--project", tmp / "missing", "--task", "t").returncode == 2
    assert tool("bogus").returncode == 2


def test_lock_released_on_failure(tmp: Path):
    try:
        with IO.project_lock(tmp, "failing"):
            assert (tmp / IO.LOCK_NAME).is_file()
            raise RuntimeError("handled failure")
    except RuntimeError:
        pass
    assert not (tmp / IO.LOCK_NAME).exists()
    with IO.project_lock(tmp, "ok") as record:
        try:
            IO.acquire_lock(tmp, "second")
            raise AssertionError("a second acquire must fail")
        except IO.LockHeld as err:
            assert err.owner["token"] == record["token"]
    assert not (tmp / IO.LOCK_NAME).exists()
    assert IO.release_lock(tmp, "x") is False


def temp_files(directory: Path):
    return [p.name for p in directory.iterdir() if p.name.startswith(IO.TEMP_PREFIX)]


def test_atomic_write_success_and_failures(tmp: Path):
    IO.atomic_write(tmp, "sub/file.txt", b"first\n")
    assert (tmp / "sub/file.txt").read_bytes() == b"first\n"
    IO.atomic_write(tmp, "sub/file.txt", b"second\n")
    assert (tmp / "sub/file.txt").read_bytes() == b"second\n" and temp_files(tmp / "sub") == []
    assert sorted(p.name for p in (tmp / "sub").iterdir()) == ["file.txt"], "no extra file"

    def before():
        raise OSError("injected before the replacement")

    try:
        IO.atomic_write(tmp, "sub/file.txt", b"third\n", _before_replace=before)
        raise AssertionError("must fail")
    except OSError as err:
        assert not isinstance(err, IO.PostReplaceError)
    assert (tmp / "sub/file.txt").read_bytes() == b"second\n", "a failure before the replacement keeps the old bytes"
    assert temp_files(tmp / "sub") == []

    def after():
        raise OSError("injected directory synchronization failure")

    try:
        IO.atomic_write(tmp, "sub/file.txt", b"fourth\n", _after_replace=after)
        raise AssertionError("must fail")
    except IO.PostReplaceError as err:
        assert err.replaced is True
    assert (tmp / "sub/file.txt").read_bytes() == b"fourth\n", "the complete new bytes are in place"
    assert temp_files(tmp / "sub") == []


def test_atomic_write_symlink_and_confinement(tmp: Path):
    project, outside = tmp / "project", tmp / "outside"
    project.mkdir()
    outside.mkdir()
    (outside / "target.txt").write_text("outside\n")
    (project / "link.txt").symlink_to(outside / "target.txt")
    (project / "linkdir").symlink_to(outside, target_is_directory=True)
    try:
        IO.atomic_write(project, "link.txt", b"x")
        raise AssertionError("a symbolic link target must fail")
    except IO.SymlinkTarget:
        pass
    assert (outside / "target.txt").read_text() == "outside\n"
    for bad in ("../x", "/etc/x", str(outside / "new.txt"), "linkdir/new.txt", "linkdir/sub/new.txt", "a/../../x"):
        try:
            IO.confine(project, bad)
            raise AssertionError(f"accepted {bad}")
        except IO.PathEscape:
            pass
        try:
            IO.atomic_write(project, bad, b"x")
            raise AssertionError(f"wrote {bad}")
        except IO.PathEscape:
            pass
    assert not (outside / "new.txt").exists() and not (outside / "sub").exists()
    assert IO.confine(project, "nested/new/file.txt") == project.resolve() / "nested/new/file.txt"
    IO.atomic_write(project, "nested/new/file.txt", b"ok\n")
    assert (project / "nested/new/file.txt").read_bytes() == b"ok\n"
    r = tool("try", "--project", project, "--task", "t")
    assert r.returncode == 0


def make_staging(project: Path, name="staging"):
    staging = project / name
    P.write(staging / "manifest.json", {"x": 1})
    return staging


def test_publish_dir(tmp: Path):
    project = tmp / "project"
    project.mkdir()
    staging = make_staging(project)
    IO.publish_dir(project, staging, "out/release-1")
    assert (project / "out/release-1/manifest.json").is_file() and not staging.exists()
    other = make_staging(project, "staging2")
    for dest in ("out/release-1", "../escape", "/etc/escape", "staging2/inner"):
        try:
            IO.publish_dir(project, other, dest)
            raise AssertionError(f"published to {dest}")
        except (FileExistsError, IO.PathEscape, ValueError):
            pass
    assert other.is_dir() and (project / "out/release-1/manifest.json").is_file()
    outside = tmp / "outside"
    P.write(outside / "manifest.json", {"x": 1})
    try:
        IO.publish_dir(project, outside, "out/release-2")
        raise AssertionError("a staging directory outside the project must fail")
    except IO.PathEscape:
        pass
    (project / "linkdir").symlink_to(tmp, target_is_directory=True)
    try:
        IO.publish_dir(project, other, "linkdir/release-3")
        raise AssertionError("a destination under an outside link must fail")
    except IO.PathEscape:
        pass
    assert not (tmp / "release-3").exists()

    def before():
        raise OSError("injected before the rename")

    try:
        IO.publish_dir(project, other, "out/release-4", _before_rename=before)
        raise AssertionError("must fail")
    except OSError as err:
        assert not isinstance(err, IO.PostRenameError)
    assert other.is_dir() and not (project / "out/release-4").exists(), "no new package appears"

    def after():
        raise OSError("injected synchronization failure")

    try:
        IO.publish_dir(project, other, "out/release-5", _after_rename=after)
        raise AssertionError("must fail")
    except IO.PostRenameError as err:
        assert err.renamed is True
    assert (project / "out/release-5/manifest.json").is_file(), "the complete new package is visible"


def test_publish_refuses_existing_lexical_destination(tmp: Path):
    """The function refuses an existing destination link, even when its target does not exist."""
    project = tmp / "project"
    project.mkdir()
    staging = make_staging(project)
    (project / "dest").symlink_to(project / "referent", target_is_directory=True)
    try:
        IO.publish_dir(project, staging, "dest")
        raise AssertionError("a dangling destination link must be refused")
    except FileExistsError:
        pass
    assert staging.is_dir() and (staging / "manifest.json").is_file(), "the stage is unchanged"
    assert os.path.islink(project / "dest") and not (project / "referent").exists(), "the link is unchanged and nothing was made"
    (project / "outside-link").symlink_to(tmp / "nowhere", target_is_directory=True)
    try:
        IO.publish_dir(project, staging, "outside-link")
        raise AssertionError("a dangling link to an outside path must be refused")
    except (FileExistsError, IO.PathEscape):
        pass
    assert not (tmp / "nowhere").exists() and staging.is_dir()
    (project / "plain").mkdir()
    try:
        IO.publish_dir(project, staging, "plain")
        raise AssertionError("an existing directory must be refused")
    except FileExistsError:
        pass


def publish_package(project: Path, staging: Path, dest: str, task="publisher"):
    """The reference caller. It holds the lock for the whole validate-then-publish sequence."""
    with IO.project_lock(project, task):
        code, report = V.build_report([], P.SCHEMAS, project, staging)
        if code != 0:
            return code, report
        IO.publish_dir(project, staging, dest)
        return 0, report


def test_publish_order(tmp: Path):
    project = P.build_project(tmp / "project")
    staging = tmp / "project" / "out/staging"
    P.build_package(project, staging)
    code, report = publish_package(project, staging, "out/release-1")
    assert code == 0 and (project / "out/release-1/manifest.json").is_file() and not staging.exists()
    assert not (project / IO.LOCK_NAME).exists(), "the sequence releases the lock"
    bad = project / "out/staging2"
    P.build_package(project, bad)
    P.write(bad / "gerber/board.GTL", "changed\n")
    code, report = publish_package(project, bad, "out/release-2")
    assert code == 1 and bad.is_dir() and not (project / "out/release-2").exists(), "an invalid package is not published"
    assert not (project / IO.LOCK_NAME).exists()
    good = project / "out/staging3"
    P.build_package(project, good)
    try:
        publish_package(project, good, "out/release-1")
        raise AssertionError("an existing destination must fail")
    except FileExistsError:
        pass
    assert good.is_dir() and not (project / IO.LOCK_NAME).exists()
    holder, _ = start_holder(project)
    try:
        try:
            publish_package(project, good, "out/release-3")
            raise AssertionError("a held lock must stop the sequence")
        except IO.LockHeld:
            pass
        assert good.is_dir() and not (project / "out/release-3").exists()
    finally:
        stop(holder)


def git_ignored(repo: Path, *paths):
    result = {}
    for path in paths:
        r = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=repo)
        result[path] = r.returncode == 0
    return result


def test_ignore_rules(tmp: Path):
    ignored = ["a/.cad-skills.lock", ".cad-skills.lock", ".cad-skills-tmp-abc", "kicad/board.kicad_prl", "kicad/fp-info-cache",
               "kicad/board-backups/board.kicad_pcb", "kicad/_autosave-board.kicad_pcb", "kicad/board.kicad_pcb.lck"]
    kept = ["kicad/board.kicad_pcb", "kicad/board.kicad_sch", "kicad/board.kicad_pro", "components/x.kicad_mod",
            "components/part.yaml", "tests/fixtures/pcb/x.yaml", "mechanical/board-interface.json", "manufacturing/export.yaml"]
    got = git_ignored(ROOT, *ignored, *kept)
    assert all(got[p] for p in ignored), [p for p in ignored if not got[p]]
    assert not any(got[p] for p in kept), [p for p in kept if got[p]]
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    (tmp / ".gitignore").write_text("*.kicad_pcb\n")
    bad = git_ignored(tmp, "kicad/board.kicad_pcb", "kicad/board.kicad_sch")
    assert bad == {"kicad/board.kicad_pcb": True, "kicad/board.kicad_sch": False}, "the test finds an incorrect rule"


def main(argv):
    key = argv[0] if argv else ""
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and key in n]
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                fn(tmp)
                print(f"ok   {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
