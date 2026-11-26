# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the one-line errors and relative --out paths of review-source in skills/pcb-fab-package (issues #11, #18).

Run with: uv run tests/test_pcb_fab_review_errors.py

The tests do not use the network, a container or a stored supplier page. They run the CLI
on a temporary fixture skill (tests/fab_fixture.py).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from fab_fixture import fixture_skill  # noqa: E402

SKILL = fixture_skill(ROOT / "skills" / "pcb-fab-package")
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fab  # noqa: E402
import review  # noqa: E402

PROFILE = SKILL / "supplier" / "profiles" / "pcbway-two-layer.yaml"
PAGE_ID = "pcbway-capabilities"
RELEASE = "r1"
REVIEWER = "fixture reviewer"
STATEMENT = "Project-authored fixture statement."
OUTSIDE_HINT = "Give a path in the project."
LINK_HINT = "Give an output path that is not a symbolic link."
OBS_HINT = "Correct the file and run the command again."


def expect(condition, message):
    """Raise AssertionError with the message when the condition is false."""
    if not condition:
        raise AssertionError(message)


def expect_one_line_error(stderr, code, want_code, label):
    """Check that a command failed with one error line: no traceback, the prefix and the exit code."""
    expect(code == want_code, f"{label}: exit {code}. Expected {want_code}. Error: {stderr}")
    expect("Traceback" not in stderr, f"{label}: the error has a traceback. Error: {stderr}")
    expect(len(stderr.strip().splitlines()) == 1, f"{label}: the error is not one line. Error: {stderr}")
    expect(stderr.startswith("fab: "), f"{label}: the error does not start with the prefix. Error: {stderr}")


def run_cli(*args, cwd=None):
    """Run fab.py through uv. Return the exit code, the stdout text and the stderr text."""
    done = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), *args],
                          capture_output=True, text=True, env=dict(os.environ), cwd=cwd, check=False)
    return done.returncode, done.stdout, done.stderr


def run_review(project, observations, out, cwd=None):
    """Run review-source for the fixture profile and the fixture release."""
    return run_cli("review-source", "--project", str(project), "--profile", str(PROFILE),
                   "--release", RELEASE, "--observations", str(observations),
                   "--reviewer", REVIEWER, "--out", str(out), cwd=cwd)


def new_project(td):
    """Make a project with the live copy of the stored page. Return the project root."""
    project = Path(td) / "project"
    live = project / "out" / "fab" / "source-review" / "live"
    live.mkdir(parents=True)
    stored = SKILL / "supplier" / "pages" / f"{PAGE_ID}.html"
    (live / f"{PAGE_ID}.html").write_bytes(stored.read_bytes())
    return project


def observation_body(project):
    """Return a valid observation file for the live copy in the project. It lists each fact of the profile."""
    record = fab.check_profile(PROFILE)
    stored = SKILL / "supplier" / "pages" / f"{PAGE_ID}.html"
    live_bytes = (project / "out" / "fab" / "source-review" / "live" / f"{PAGE_ID}.html").read_bytes()
    page_url = record["extensions"]["evidence_pages"][PAGE_ID]["source_url"]
    items = []
    for key, (value, unit, source_url) in sorted(review.fact_items(record).items()):
        items.append({"key": key, "observed_value": value, "observed_unit": unit,
                      "observed_condition": "Project-authored fixture reading.",
                      "source_url": source_url, "reviewer_reading": "Project-authored fixture reading."})
    return {
        "schema_id": "pcb-fab-package/source-observations", "schema_version": 1, "release_id": RELEASE,
        "profile_sha256": record["content_sha256"],
        "pages": [{"page_id": PAGE_ID, "source_url": page_url,
                   "stored_path": f"supplier/pages/{PAGE_ID}.html",
                   "stored_sha256": hashlib.sha256(stored.read_bytes()).hexdigest(),
                   "live_path": f"out/fab/source-review/live/{PAGE_ID}.html",
                   "live_sha256": hashlib.sha256(live_bytes).hexdigest(), "retrieved": "2026-11-26"}],
        "observations": items, "reviewer": REVIEWER, "statement": STATEMENT,
    }


def write_body(td, body, name="observations.json"):
    """Write an observation file outside the project. Return its path."""
    path = Path(td) / name
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return path


def test_out_outside_project_exits_2():
    """An --out path outside the project gives one line and exit 2. It writes nothing."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        obs = write_body(td, observation_body(project))
        outside = Path(td) / "outside"
        code, _, err = run_review(project, obs, outside / "REVIEW.json")
        expect_one_line_error(err, code, 2, "outside the project")
        expect("outside the project root" in err, f"The confinement message is missing. Error: {err}")
        expect(OUTSIDE_HINT in err, f"The hint is missing. Error: {err}")
        expect(not outside.exists(), "The directory outside the project was made.")
        expect(not any(project.rglob("REVIEW.json")), "A REVIEW.json was written in the project.")
        expect(not any(project.rglob("observations.json")), "An observations.json was written in the project.")


def test_out_outside_project_that_exists_exits_2():
    """An existing --out path outside the project gives the confinement error, not the destination error."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        obs = write_body(td, observation_body(project))
        outside = Path(td) / "outside"
        outside.mkdir()
        old = outside / "REVIEW.json"
        old.write_bytes(b"old\n")
        code, _, err = run_review(project, obs, old)
        expect_one_line_error(err, code, 2, "outside the project, existing")
        expect("outside the project root" in err, f"The confinement message is missing. Error: {err}")
        expect(OUTSIDE_HINT in err, f"The hint is missing. Error: {err}")
        expect(old.read_bytes() == b"old\n", "The file outside the project changed.")


def test_out_link_out_of_project_exits_2():
    """An --out path through a link to a directory outside the project gives exit 2. The target stays empty."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        obs = write_body(td, observation_body(project))
        elsewhere = Path(td) / "elsewhere"
        elsewhere.mkdir()
        link = project / "out" / "fab" / "review-link"
        link.symlink_to(elsewhere, target_is_directory=True)
        code, _, err = run_review(project, obs, link / "REVIEW.json")
        expect_one_line_error(err, code, 2, "link out of the project")
        expect("outside the project root" in err, f"The confinement message is missing. Error: {err}")
        expect(OUTSIDE_HINT in err, f"The hint is missing. Error: {err}")
        expect(list(elsewhere.iterdir()) == [], "A file was written through the link.")


def test_out_symlink_target_exits_2():
    """An --out path that is a symbolic link gives exit 2. The link and its target stay unchanged."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        obs = write_body(td, observation_body(project))
        review_dir = project / "out" / "fab" / "review"
        review_dir.mkdir(parents=True)
        target = review_dir / "target.json"
        link = review_dir / "REVIEW.json"
        link.symlink_to(target)
        code, _, err = run_review(project, obs, link)
        expect_one_line_error(err, code, 2, "symbolic link target")
        expect("symbolic link" in err, f"The symbolic link message is missing. Error: {err}")
        expect(LINK_HINT in err, f"The hint is missing. Error: {err}")
        expect(not target.exists(), "The target of the link was written.")
        expect(os.readlink(link) == str(target), "The link changed.")


def test_invalid_observations_exits_1():
    """An observation file without the statement gives one line and exit 1. It writes nothing."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        body = observation_body(project)
        del body["statement"]
        obs = write_body(td, body)
        out = project / "out" / "fab" / "review" / "REVIEW.json"
        code, _, err = run_review(project, obs, out)
        expect_one_line_error(err, code, 1, "invalid observations")
        expect("is missing keys" in err and "statement" in err, f"The missing key is not named. Error: {err}")
        expect("invalid observation file" in err, f"The error does not name the file. Error: {err}")
        expect(OBS_HINT in err, f"The hint is missing. Error: {err}")
        expect(not out.exists(), "REVIEW.json was written for an invalid observation file.")


def test_unknown_observation_key_exits_1():
    """An observation with a key that the profile does not have gives one line and exit 1."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        body = observation_body(project)
        body["observations"].append({
            "key": "service.turn_time", "observed_value": 1, "observed_unit": "",
            "observed_condition": "Project-authored fixture reading.",
            "source_url": fab.check_profile(PROFILE)["source_url"],
            "reviewer_reading": "Project-authored fixture reading."})
        obs = write_body(td, body)
        out = project / "out" / "fab" / "review" / "REVIEW.json"
        code, _, err = run_review(project, obs, out)
        expect_one_line_error(err, code, 1, "unknown observation key")
        expect("unknown observation key" in err, f"The key message is missing. Error: {err}")
        expect(OBS_HINT in err, f"The hint is missing. Error: {err}")
        expect(not out.exists(), "REVIEW.json was written for an unknown observation key.")


def test_valid_review_still_exits_0():
    """A valid observation file gives exit 0, the review record, and a copy of the observation bytes."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        obs = write_body(td, observation_body(project))
        out = project / "out" / "fab" / "review" / "REVIEW.json"
        code, text, err = run_review(project, obs, out)
        expect(code == 0, f"A valid review gave exit {code}. Expected 0. Error: {err}")
        written = json.loads(out.read_text(encoding="utf-8"))
        expect(written["decision"] == "unchanged", f"The decision is {written['decision']}. Expected unchanged.")
        expect((out.parent / "observations.json").read_bytes() == obs.read_bytes(),
               "observations.json does not have the bytes of the observation file.")


def test_existing_out_in_project_exits_2():
    """An existing --out path in the project still gives the destination error and exit 2. It keeps the old bytes."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        obs = write_body(td, observation_body(project))
        out = project / "out" / "fab" / "review" / "REVIEW.json"
        out.parent.mkdir(parents=True)
        out.write_bytes(b"old\n")
        code, _, err = run_review(project, obs, out)
        expect_one_line_error(err, code, 2, "existing destination")
        expect("the destination exists" in err, f"The destination message is missing. Error: {err}")
        expect(out.read_bytes() == b"old\n", "The existing destination changed.")


def test_relative_out_from_outside_cwd():
    """A relative --out from a caller directory outside the project writes into the project and refuses a second run."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        caller = Path(td) / "caller"
        caller.mkdir()
        obs = write_body(td, observation_body(project))
        rel_out = Path("out/fab/review/REVIEW.json")
        code, text, err = run_review(project, obs, rel_out, cwd=caller)
        expect(code == 0, f"A relative --out gave exit {code}. Expected 0. Error: {err}")
        expect(err == "", f"Stderr is not empty. Error: {err}")
        out_in_project = project / "out" / "fab" / "review" / "REVIEW.json"
        expect(out_in_project.is_file(), "REVIEW.json is missing in the project.")
        expect((out_in_project.parent / "observations.json").read_bytes() == obs.read_bytes(),
               "observations.json does not have the bytes of the observation file.")
        payload = json.loads(text)
        expect(payload["decision"] == "unchanged", f"The decision is {payload['decision']}. Expected unchanged.")
        expect(payload["review_sha256"] == hashlib.sha256(out_in_project.read_bytes()).hexdigest(),
               "review_sha256 differs from the written REVIEW.json bytes.")
        expect(list(caller.iterdir()) == [], "The command wrote items in the caller directory.")
        first_bytes = out_in_project.read_bytes()
        code2, _, err2 = run_review(project, obs, rel_out, cwd=caller)
        expect_one_line_error(err2, code2, 2, "relative existing destination")
        expect("the destination exists" in err2, f"The destination message is missing. Error: {err2}")
        expect(out_in_project.read_bytes() == first_bytes, "The existing destination changed.")
        expect(list(caller.iterdir()) == [], "The command wrote items in the caller directory on the second run.")


def test_relative_out_symlink_from_outside_cwd():
    """A relative --out that names a symbolic link in the project gives exit 2 from an outside directory."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        caller = Path(td) / "caller"
        caller.mkdir()
        obs = write_body(td, observation_body(project))
        review_dir = project / "out" / "fab" / "review"
        review_dir.mkdir(parents=True)
        target = review_dir / "target.json"
        link = review_dir / "REVIEW.json"
        link.symlink_to(target)
        code, _, err = run_review(project, obs, Path("out/fab/review/REVIEW.json"), cwd=caller)
        expect_one_line_error(err, code, 2, "relative symbolic link target")
        expect("symbolic link" in err, f"The symbolic link message is missing. Error: {err}")
        expect(LINK_HINT in err, f"The hint is missing. Error: {err}")
        expect(not target.exists(), "The target of the link was written.")
        expect(os.readlink(link) == str(target), "The link changed.")
        expect(list(caller.iterdir()) == [], "The command wrote items in the caller directory.")


def test_relative_out_escape_from_outside_cwd():
    """A relative --out that goes outside the project gives exit 2 from an outside directory."""
    with tempfile.TemporaryDirectory() as td:
        project = new_project(td)
        caller = Path(td) / "caller"
        caller.mkdir()
        obs = write_body(td, observation_body(project))
        code, _, err = run_review(project, obs, Path("../outside/REVIEW.json"), cwd=caller)
        expect_one_line_error(err, code, 2, "relative outside project")
        expect("outside the project root" in err, f"The confinement message is missing. Error: {err}")
        expect(OUTSIDE_HINT in err, f"The hint is missing. Error: {err}")
        expect(not (Path(td) / "outside").exists(), "The directory outside the project was made.")
        expect(list(caller.iterdir()) == [], "The command wrote items in the caller directory.")


TESTS = [value for name, value in list(globals().items()) if name.startswith("test_") and callable(value)]


def main():
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except Exception as err:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {type(err).__name__}: {err}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
