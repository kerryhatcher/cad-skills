# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Test the standalone KiCad rule files of the pcb-fab-package skill.

The files are made by scripts/make_rules.py. Each test that changes a file uses a copy of the
skill in a temporary directory, outside the repository. The tests need no container and no
supplier pages.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "pcb-fab-package"
RULES_REL = "skills/pcb-fab-package/supplier/rules"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(ROOT / "tests" / "eval"))

import fab  # noqa: E402
import packaging as P  # noqa: E402
import validate as VAL  # noqa: E402
import workflow  # noqa: E402

RULE_LINE = re.compile(r'^\(rule "supplier_([a-z_]+)" \(constraint ([a-z_]+) \(min ([0-9.]+)mm\)\)\)$')
MIL_MM = Fraction(254, 10000)
UNIT_MM = {"mm": Fraction(1), "mil": MIL_MM, "in": Fraction(254, 10)}


def expect(condition, message):
    """Raise AssertionError with the message when the condition is false."""
    if not condition:
        raise AssertionError(message)


def profile_files(skill: Path) -> list[Path]:
    return sorted((skill / "supplier" / "profiles").glob("*.yaml"))


def profile_ids(skill: Path = SKILL) -> list[str]:
    return sorted(VAL.load_record(path)["id"] for path in profile_files(skill))


def rules_dir(skill: Path) -> Path:
    return skill / "supplier" / "rules"


def rule_bytes(skill: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(rules_dir(skill).iterdir())}


def skill_copy(tmp: Path) -> Path:
    """Copy the skill scripts, contracts, profiles and rule files. Omit the supplier pages."""
    skill = tmp / "pcb-fab-package"
    shutil.copytree(SKILL / "scripts", skill / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SKILL / "contracts", skill / "contracts")
    shutil.copytree(SKILL / "supplier" / "profiles", skill / "supplier" / "profiles")
    shutil.copytree(rules_dir(SKILL), rules_dir(skill))
    return skill


def run(skill: Path, *args: str) -> tuple[int, str, str]:
    """Run the generator of the skill through uv, offline. Return the exit code, stdout and stderr."""
    done = subprocess.run(
        ["uv", "run", "--offline", "--quiet", str(skill / "scripts" / "make_rules.py"), *args],
        cwd=skill, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout, done.stderr


def edit_profile(skill: Path, pid: str, mutate, rehash: bool = True) -> None:
    """Change one profile of a copy. Update content_sha256 unless rehash is false."""
    path = skill / "supplier" / "profiles" / f"{pid}.yaml"
    record = VAL.load_record(path)
    mutate(record)
    if rehash:
        record["content_sha256"] = fab.content_hash(record)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def test_each_profile_has_one_rules_file(tmp: Path):
    """The rules directory holds one `.kicad_dru` file for each profile id, and no other file."""
    names = sorted(path.name for path in rules_dir(SKILL).iterdir())
    expected = sorted(f"{pid}.kicad_dru" for pid in profile_ids())
    expect(names == expected, f"The rule files are {names}. Expected {expected}.")


def test_rules_file_equals_workflow_text(tmp: Path):
    """Each rule file has the same bytes as the text that the workflow makes for its profile."""
    for path in profile_files(SKILL):
        record = VAL.load_record(path)
        data = (rules_dir(SKILL) / f"{record['id']}.kicad_dru").read_bytes()
        expected = workflow.supplier_rules_text(record).encode("utf-8")
        expect(data == expected, f"{record['id']}: the rule file is different from the workflow text.")


def test_rules_values_match_profile_limits(tmp: Path):
    """Read each rule file again. Its values and constraints match the profile limits."""
    for path in profile_files(SKILL):
        record = VAL.load_record(path)
        pid = record["id"]
        text = (rules_dir(SKILL) / f"{pid}.kicad_dru").read_text(encoding="utf-8")
        expect(text.startswith("(version 1)\n"), f"{pid}: the first line is not (version 1).")
        expect(text.endswith("\n") and not text.endswith("\n\n"), f"{pid}: the file does not end with one newline.")
        expect("(max " not in text, f"{pid}: the file has a maximum rule.")
        found = {}
        for line in text.splitlines()[1:]:
            match = RULE_LINE.fullmatch(line)
            expect(match is not None, f"{pid}: the rule line {line!r} has an unexpected form.")
            key, constraint, value = match.group(1), match.group(2), match.group(3)
            expect(key not in found, f"{pid}: the rule {key} appears twice.")
            expect(key in workflow.RULE_CONSTRAINT, f"{pid}: the rule {key} has no constraint.")
            expect(constraint == workflow.RULE_CONSTRAINT[key], f"{pid}: the constraint of {key} is {constraint}.")
            limit = record["limits"][key]
            factor = UNIT_MM[limit["unit"]]
            expect(Fraction(value) == Fraction(str(limit["value"])) * factor,
                   f"{pid}: the value of {key} is {value} mm. The profile value is {limit['value']} {limit['unit']}.")
            found[key] = value
        expect(set(found) == set(record["division"]["kicad_dru"]),
               f"{pid}: the rules {sorted(found)} are different from the division.")


def test_check_passes_on_the_repository(tmp: Path):
    """The check passes on the committed files and changes no file."""
    before = rule_bytes(SKILL)
    code, _, err = run(SKILL, "--check")
    expect(code == 0, f"--check gave exit {code}: {err}")
    expect(rule_bytes(SKILL) == before, "--check changed a rule file.")


def test_check_works_without_supplier_pages(tmp: Path):
    """The check passes in a copy that has no supplier pages."""
    skill = skill_copy(tmp)
    expect(not (skill / "supplier" / "pages").exists(), "The copy has supplier pages.")
    code, _, err = run(skill, "--check")
    expect(code == 0, f"--check gave exit {code} without supplier pages: {err}")


def test_check_finds_a_changed_file(tmp: Path):
    """The check gives exit 1 and names a rule file with changed bytes. It keeps the changed bytes."""
    skill = skill_copy(tmp)
    path = rules_dir(skill) / "oshpark-two-layer.kicad_dru"
    changed = path.read_bytes().replace(b"0.1524mm", b"0.1525mm", 1)
    path.write_bytes(changed)
    code, _, err = run(skill, "--check")
    expect(code == 1, f"--check gave exit {code} for a changed file.")
    expect("oshpark-two-layer.kicad_dru" in err, f"The message does not name the file: {err}")
    expect(path.read_bytes() == changed, "--check changed the file.")


def test_check_finds_a_missing_file(tmp: Path):
    """The check gives exit 1 and names a rule file that is missing. It creates no file."""
    skill = skill_copy(tmp)
    path = rules_dir(skill) / "oshpark-two-layer.kicad_dru"
    path.unlink()
    code, _, err = run(skill, "--check")
    expect(code == 1, f"--check gave exit {code} for a missing file.")
    expect("oshpark-two-layer.kicad_dru" in err, f"The message does not name the file: {err}")
    expect(not path.exists(), "--check created the missing file.")


def test_extra_file_is_reported_and_kept(tmp: Path):
    """An extra rule file that no profile makes gives exit 1 in both modes. The generator keeps it."""
    skill = skill_copy(tmp)
    extra = rules_dir(skill) / "oshpark-old.kicad_dru"
    extra.write_bytes(b"(version 1)\n")
    code, _, err = run(skill, "--check")
    expect(code == 1, f"--check gave exit {code} for an extra file.")
    expect("oshpark-old.kicad_dru" in err, f"The message does not name the extra file: {err}")
    code, _, err = run(skill)
    expect(code == 1, f"The write mode gave exit {code} for an extra file.")
    expect(extra.exists(), "The write mode removed the extra file.")


def test_write_mode_restores_the_files(tmp: Path):
    """The write mode makes the missing files. A second run changes no file."""
    skill = skill_copy(tmp)
    expected = rule_bytes(SKILL)
    shutil.rmtree(rules_dir(skill))
    code, _, err = run(skill)
    expect(code == 0, f"The write mode gave exit {code}: {err}")
    expect(rule_bytes(skill) == expected, "The written bytes are different from the repository files.")
    stamps = {path.name: path.stat().st_mtime_ns for path in rules_dir(skill).iterdir()}
    code, _, err = run(skill)
    expect(code == 0, f"The second run gave exit {code}: {err}")
    expect({path.name: path.stat().st_mtime_ns for path in rules_dir(skill).iterdir()} == stamps,
           "The second run rewrote a file that had the same bytes.")


def test_profile_change_changes_the_file(tmp: Path):
    """A changed profile limit gives exit 1 in check mode. The write mode makes the new value."""
    skill = skill_copy(tmp)
    edit_profile(skill, "oshpark-two-layer", lambda r: r["limits"]["min_trace"].update(value=7))
    code, _, err = run(skill, "--check")
    expect(code == 1, f"--check gave exit {code} after a profile change.")
    code, _, err = run(skill)
    expect(code == 0, f"The write mode gave exit {code}: {err}")
    text = (rules_dir(skill) / "oshpark-two-layer.kicad_dru").read_text(encoding="utf-8")
    expect("(min 0.1778mm)" in text, "The written file does not hold the new trace width.")


def test_invalid_profile_is_refused(tmp: Path):
    """Each defect gives exit 2 in both modes and writes nothing. The message names the defect."""
    cases = [
        ("content hash", lambda r: r["limits"]["min_trace"].update(value=7), False, "content_sha256"),
        ("id is different from the file name", lambda r: r.update(id="oshpark-other"), True, "file name"),
        ("key without a constraint",
         lambda r: (r["limits"].update(min_unknown=dict(r["limits"]["min_trace"])),
                    r["division"]["kicad_dru"].append("min_unknown")), True, "min_unknown"),
        ("unit cm", lambda r: r["limits"]["min_trace"].update(unit="cm"), True, "min_trace"),
        ("maximum kind", lambda r: r["limits"]["min_trace"].update(kind="maximum"), True, "min_trace"),
    ]
    for index, (label, mutate, rehash, needle) in enumerate(cases):
        skill = skill_copy(tmp / f"case{index}")
        edit_profile(skill, "oshpark-two-layer", mutate, rehash=rehash)
        before = rule_bytes(skill)
        for args in (("--check",), ()):
            code, _, err = run(skill, *args)
            expect(code == 2, f"{label}: exit {code} with {args}. Expected 2.")
            expect(needle in err, f"{label}: the message does not name {needle!r}: {err}")
            expect(rule_bytes(skill) == before, f"{label}: the generator changed a rule file.")


def test_in_unit_is_accepted_and_exact(tmp: Path):
    """A kicad_dru limit in inches writes the exact millimeter rule."""
    skill = skill_copy(tmp)
    edit_profile(skill, "oshpark-two-layer", lambda r: r["limits"]["min_trace"].update(value=0.006, unit="in"))
    code, _, err = run(skill)
    expect(code == 0, f"The write mode with unit in gave exit {code}: {err}")
    text = (rules_dir(skill) / "oshpark-two-layer.kicad_dru").read_text(encoding="utf-8")
    expect('(rule "supplier_min_trace" (constraint track_width (min 0.1524mm)))' in text,
           f"The written file does not hold the exact trace width:\n{text}")


def test_schema_violation_is_refused(tmp: Path):
    """A profile that breaks the supplier profile schema gives exit 2 and writes nothing."""
    skill = skill_copy(tmp)
    edit_profile(skill, "oshpark-two-layer", lambda r: r.update(units="in"))
    before = rule_bytes(skill)
    code, _, err = run(skill)
    expect(code == 2, f"A schema violation gave exit {code}. Expected 2.")
    expect("units" in err, f"The message does not name the schema field: {err}")
    expect(rule_bytes(skill) == before, "The generator changed a rule file after a schema violation.")


def test_wrong_schema_id_is_refused(tmp: Path):
    """A record of another schema gives exit 2. The generator does not give a traceback."""
    skill = skill_copy(tmp)
    record = {"schema_id": "cad-skills/evidence", "schema_version": "1.0",
              "check_id": "example-check", "status": "fail", "method": "tool"}
    path = skill / "supplier" / "profiles" / "oshpark-two-layer.yaml"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    code, _, err = run(skill, "--check")
    expect(code == 2, f"A different schema id gave exit {code}. Expected 2.")
    expect("supplier-profile" in err, f"The message does not name the schema: {err}")


def test_directory_in_rules_is_refused(tmp: Path):
    """A directory with the rule suffix in the rules directory gives exit 2, not exit 3."""
    skill = skill_copy(tmp)
    extra = rules_dir(skill) / "extra.kicad_dru"
    extra.mkdir()
    code, _, err = run(skill, "--check")
    expect(code == 2, f"A directory in the rules directory gave exit {code}. Expected 2.")
    expect("extra.kicad_dru" in err, f"The message does not name the directory: {err}")


def test_symbolic_link_is_refused(tmp: Path):
    """A link at a rule file gives exit 2. The file that the link names stays unchanged."""
    skill = skill_copy(tmp / "file-link")
    outside = tmp / "outside.kicad_dru"
    outside.write_bytes(b"outside\n")
    path = rules_dir(skill) / "oshpark-two-layer.kicad_dru"
    path.unlink()
    os.symlink(outside, path)
    code, _, err = run(skill, "--check")
    expect(code == 2, f"--check gave exit {code} for a link at a rule file. Expected 2.")
    code, _, err = run(skill)
    expect(code == 2, f"The write mode gave exit {code} for a link at a rule file. Expected 2.")
    expect(outside.read_bytes() == b"outside\n", "The generator changed the file that the link names.")


def test_symbolic_link_directory_is_refused(tmp: Path):
    """A link for the rules directory to a directory outside the skill gives exit 2. The outside directory stays empty."""
    skill = skill_copy(tmp / "dir-link")
    outside = tmp / "outside-dir"
    outside.mkdir()
    shutil.rmtree(rules_dir(skill))
    os.symlink(outside, rules_dir(skill))
    code, _, err = run(skill)
    expect(code == 2, f"The write mode gave exit {code} for a linked directory. Expected 2.")
    expect(list(outside.iterdir()) == [], "The generator wrote into the directory outside the skill.")


def test_out_outside_the_skill_is_refused(tmp: Path):
    """An output directory outside the skill gives exit 2. The generator creates no directory there."""
    skill = skill_copy(tmp)
    target = tmp / "elsewhere"
    code, _, err = run(skill, "--out", str(target))
    expect(code == 2, f"--out outside the skill gave exit {code}. Expected 2.")
    expect(not target.exists(), "The generator created the directory outside the skill.")


def test_script_uses_only_its_own_skill(tmp: Path):
    """The generator imports only the standard library and modules of its own scripts directory."""
    text = (SKILL / "scripts" / "make_rules.py").read_text(encoding="utf-8")
    expect("skills/" not in text.replace("cad-skills/", ""),
           "The generator names a path of another skill.")
    expect("parents[" not in text, "The generator climbs the directory tree.")
    allowed = set(sys.stdlib_module_names) | {path.stem for path in (SKILL / "scripts").glob("*.py")}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            expect(node.level == 0, "The generator uses a relative import.")
            names = [node.module or ""]
        else:
            continue
        for name in names:
            expect(name.split(".")[0] in allowed, f"The generator imports {name!r}, which is not local.")


def test_workflow_does_not_read_the_rules_files(tmp: Path):
    """The workflow, the gate and the review code do not read the rule files (D1, amendment E)."""
    for name in ("workflow.py", "fab.py", "review.py"):
        text = (SKILL / "scripts" / name).read_text(encoding="utf-8")
        expect('"rules"' not in text, f"{name} has a rules path part.")
        expect("supplier/rules" not in text, f"{name} names the rule directory.")


def test_rules_files_are_tracked_and_not_ignored(tmp: Path):
    """Git tracks exactly the rule files, and no ignore rule matches them."""
    paths = [f"{RULES_REL}/{pid}.kicad_dru" for pid in profile_ids()]
    listed = subprocess.run(["git", "ls-files", "--", RULES_REL], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.split()
    expect(sorted(listed) == sorted(paths), f"Git tracks {sorted(listed)}. Expected {sorted(paths)}.")
    for path in paths:
        done = subprocess.run(["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT, check=False)
        expect(done.returncode == 1, f"An ignore rule matches {path}.")


def test_distribution_allows_the_rules_files(tmp: Path):
    """The distribution allowlist admits the rule files and no other file under supplier/rules."""
    dist = P.merged_distribution(ROOT, P.load_yaml(ROOT / "tests" / "eval" / "distribution.yaml"))
    paths = [f"{RULES_REL}/{pid}.kicad_dru" for pid in profile_ids()]
    found = P.check_distribution(paths, dist, root=ROOT)
    expect(found == [], f"The distribution check refuses the rule files: {found}")
    coverage = P.check_coverage(ROOT, dist, {entry["path"] for entry in dist["sources"]})
    expect(not any("supplier/rules/" in item.get("file", "") for item in coverage),
           f"The coverage check names a rule file: {coverage}")
    other = P.check_distribution([f"{RULES_REL}/x.txt"], dist, root=ROOT)
    expect(any(item["code"] == "D-6" for item in other), "The allowlist admits a file that is not a rule file.")


def test_skill_md_names_the_consumer(tmp: Path):
    """SKILL.md names the rule directory, the generator and the consumer of the files."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for needle in ("supplier/rules/", "make_rules.py", "The workflow does not read these files."):
        expect(needle in text, f"SKILL.md does not contain {needle!r}.")


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
