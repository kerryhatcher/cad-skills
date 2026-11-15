# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Package checks for skills: names, references, schema copies, snippet routing.

  uv run tests/test_skill_packages.py            # all tests
  uv run tests/test_skill_packages.py copy       # only tests with 'copy' in their name

Limits of these checks:
  * The reference scan finds links and path references in Markdown. It does not prove portability.
  * The copy-run test runs a fixture skill from an unrelated directory with a cleaned environment.
    It shows that the fixture needs no repository path. It does not stop a process from reading
    the repository. It is NOT a sandbox. The final gate (B12) runs real isolated tool tasks.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_snippets as SN  # noqa: E402

EXTENSIONS = (".md", ".py", ".json", ".yaml", ".yml", ".txt", ".pdf")
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE_SPAN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")


def finding(code, file, message):
    return {"code": code, "file": str(file), "message": message}


def strip_fences(text: str) -> str:
    """Remove fenced code blocks. A fenced block is an example, so the scanner skips it."""
    kept, fence = [], None
    for line in text.splitlines():
        marker = line.strip()[:3]
        if fence is None and marker in ("```", "~~~"):
            fence = marker
        elif fence is not None and line.strip().startswith(fence):
            fence = None
        elif fence is None:
            kept.append(line)
    return "\n".join(kept)


def references(text: str):
    """Yield the local file references of a Markdown text (without fenced blocks)."""
    body = strip_fences(text)
    targets = [m.group(1) for m in LINK.finditer(body)]
    for m in CODE_SPAN.finditer(body):
        token = m.group(1)
        if re.search(r"\s", token) or re.search(r"[<>*{}$|=]", token):
            continue
        if token.startswith(("./", "../")) or ("/" in token and token.lower().endswith(EXTENSIONS)):
            targets.append(token)
    for target in targets:
        if target.startswith(("http://", "https://", "mailto:", "//", "#")):
            continue
        target = target.split("#", 1)[0].split("?", 1)[0]
        if target:
            yield target


def check_skill(skill_dir: Path) -> list[dict]:
    """Return the findings for one skill directory."""
    out, skill_dir = [], Path(skill_dir)
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
    meta, valid = {}, True
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if match:
        try:
            loaded = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            loaded = False  # The YAML text is not valid.
        if isinstance(loaded, dict):
            meta = loaded
        elif loaded is not None or not match.group(1).strip() == "":
            out.append(finding("skill.frontmatter_invalid", skill_md, "The frontmatter is not a YAML mapping."))
            valid = False
    name, description = meta.get("name"), meta.get("description")
    if valid and (not isinstance(name, str) or not name.strip() or name != skill_dir.name):
        out.append(finding("skill.name_mismatch", skill_md, f"The name {name!r} differs from the directory name {skill_dir.name!r}."))
    if valid and (not isinstance(description, str) or not description.strip()):
        out.append(finding("skill.description_empty", skill_md, "The description is blank."))
    if len(text.splitlines()) >= 500:
        out.append(finding("skill.too_long", skill_md, "SKILL.md has 500 lines or more."))
    base = skill_dir.resolve()
    for md in sorted(skill_dir.rglob("*.md")):
        for target in references(md.read_text(encoding="utf-8")):
            if target.startswith(("/", "~/")):
                out.append(finding("skill.absolute_path", md, f"The reference {target} is an absolute path."))
                continue
            resolved = (md.parent / target).resolve()
            if resolved != base and base not in resolved.parents:
                out.append(finding("skill.reference_escape", md, f"The reference {target} leaves the skill directory."))
            elif not resolved.exists():
                out.append(finding("skill.reference_missing", md, f"The reference {target} does not exist."))
    return out


def copy_set(contracts_dir: Path) -> list[str]:
    """The files of a schema copy, relative to a contracts folder."""
    registry = json.loads((contracts_dir / "schemas/registry.json").read_text())
    names = {"README.md", "schemas/registry.json"}
    for entry in registry["records"].values():
        names.update(f"schemas/{file}" for file in entry["schemas"].values())
    return sorted(names)


def check_copies(skill_dir: Path, contracts_dir: Path) -> list[dict]:
    """Compare the `contracts/` folder of a skill with the repository contracts."""
    copy_dir = Path(skill_dir) / "contracts"
    if not copy_dir.is_dir():
        return []
    out, wanted = [], copy_set(contracts_dir)
    for rel in wanted:
        mine, theirs = copy_dir / rel, contracts_dir / rel
        if not mine.is_file():
            out.append(finding("skill.copy_missing", copy_dir / rel, "A file of the copy set is absent."))
        elif mine.read_bytes() != theirs.read_bytes():
            out.append(finding("skill.copy_changed", mine, "The copy differs from the file in contracts/."))
    for path in sorted(p for p in (copy_dir / "schemas").rglob("*") if p.is_file()) if (copy_dir / "schemas").is_dir() else []:
        if str(path.relative_to(copy_dir)) not in wanted:
            out.append(finding("skill.copy_extra", path, "The registry does not name this file."))
    return out


# --------------------------------------------------------------------------- fixtures


def make_skill(root: Path, name="demo", body="", extra=None) -> Path:
    skill = root / name
    (skill / "references").mkdir(parents=True)
    (skill / "scripts").mkdir()
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: A fixture skill.\n---\n\n# {name}\n\n{body}\n")
    (skill / "references/a.md").write_text("# Reference A\n")
    (skill / "scripts/run.py").write_text("print('ok')\n")
    for rel, content in (extra or {}).items():
        path = skill / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return skill


def codes(found):
    return sorted(f["code"] for f in found)


def test_existing_skills(tmp: Path):
    names = sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
    assert names, "no skill directories"
    for name in names:
        found = check_skill(ROOT / "skills" / name)
        assert found == [], (name, found)


def test_new_missing_reference_in_a_legacy_file(tmp: Path):
    """The existing cadquery skill has no finding. A new missing reference in recipes.md is still found."""
    copy = tmp / "cadquery"
    shutil.copytree(ROOT / "skills/cadquery", copy)
    assert check_skill(copy) == []
    recipes = copy / "references/recipes.md"
    recipes.write_text(recipes.read_text() + "\nSee [new](references/new-missing.md).\n")
    found = check_skill(copy)
    assert codes(found) == ["skill.reference_missing"] and found[0]["file"].endswith("recipes.md"), found
    troubleshooting = copy / "references/troubleshooting.md"
    troubleshooting.write_text(troubleshooting.read_text() + "\nAlso `scripts/inspect_model.py`.\n")
    assert codes(check_skill(copy)) == ["skill.reference_missing", "skill.reference_missing"], "two defects stay two findings"


def test_skill_metadata(tmp: Path):
    assert check_skill(make_skill(tmp)) == []
    bad = make_skill(tmp, "wrong")
    (bad / "SKILL.md").write_text("---\nname: other\ndescription: A fixture skill.\n---\n")
    assert codes(check_skill(bad)) == ["skill.name_mismatch"]
    empty = make_skill(tmp, "empty")
    (empty / "SKILL.md").write_text("---\nname: empty\ndescription: ' '\n---\n")
    assert codes(check_skill(empty)) == ["skill.description_empty"]
    nameless = make_skill(tmp, "nameless")
    (nameless / "SKILL.md").write_text("---\ndescription: x\n---\n")
    assert "skill.name_mismatch" in codes(check_skill(nameless))
    long = make_skill(tmp, "long")
    (long / "SKILL.md").write_text("---\nname: long\ndescription: x\n---\n" + "line\n" * 500)
    assert codes(check_skill(long)) == ["skill.too_long"]


def test_frontmatter_shapes(tmp: Path):
    """A frontmatter that is not a mapping gives one finding. The checker does not crash."""
    for label, front in (("list", "- name: demo\n  description: x"), ("scalar", "just text"), ("integer", "42"),
                         ("invalid", "name: [unclosed"), ("string-list", "[a, b]")):
        skill = make_skill(tmp, f"front-{label}")
        (skill / "SKILL.md").write_text(f"---\n{front}\n---\n\n# text\n")
        assert codes(check_skill(skill)) == ["skill.frontmatter_invalid"], label
    empty = make_skill(tmp, "front-empty")
    (empty / "SKILL.md").write_text("---\n\n---\n")
    assert "skill.name_mismatch" in codes(check_skill(empty)), "an empty frontmatter has no name"


def test_reference_scanner(tmp: Path):
    inside = make_skill(tmp, "inside", "See [A](references/a.md) and `scripts/run.py`.")
    assert check_skill(inside) == []
    (inside / "references/b.md").write_text("Back to [the skill](../SKILL.md) and `../scripts/run.py`.\n")
    assert check_skill(inside) == [], "a ../ reference that stays in the skill is valid"
    fragment = make_skill(tmp, "fragment", "See [A](references/a.md#part) and [top](#top).")
    assert check_skill(fragment) == []
    external = make_skill(tmp, "external", "See [W](https://example.com/a.pdf), [M](mailto:a@example.com), [P](//example.com/x.pdf).")
    assert check_skill(external) == []
    fenced = make_skill(tmp, "fenced", "```bash\nuv run /app/x.py\ncat `../../outside.md`\n```\n")
    assert check_skill(fenced) == [], "a fenced block is an example"
    spans = make_skill(tmp, "spans", "Run `uv run scripts/pcb.py env` with Python `3.10`, file `part.py`, and `<skill-dir>/scripts/x.py`.")
    assert check_skill(spans) == [], "a command, a number, a bare file name and a placeholder are not references"
    missing = make_skill(tmp, "missing", "See [A](references/none.md).")
    assert codes(check_skill(missing)) == ["skill.reference_missing"]
    (tmp / "outside.md").write_text("outside\n")
    escape = make_skill(tmp, "escape", "See [O](../outside.md) and `../outside.md`.")
    assert codes(check_skill(escape)) == ["skill.reference_escape", "skill.reference_escape"]
    absolute = make_skill(tmp, "absolute", "See `/etc/passwd.txt` and [H](~/notes.md).")
    assert codes(check_skill(absolute)) == ["skill.absolute_path", "skill.absolute_path"]
    link = make_skill(tmp, "linked", "See `references/escape/x.md`.")
    (tmp / "elsewhere").mkdir()
    (tmp / "elsewhere/x.md").write_text("x\n")
    (link / "references/escape").symlink_to(tmp / "elsewhere", target_is_directory=True)
    assert codes(check_skill(link)) == ["skill.reference_escape"], "a link to an outside directory leaves the skill"


def test_copy_checks(tmp: Path):
    skill = make_skill(tmp, "copies")
    assert check_copies(skill, CONTRACTS) == [], "a skill with no contracts folder is not a failure in this batch"
    shutil.copytree(CONTRACTS / "schemas", skill / "contracts/schemas")
    shutil.copy(CONTRACTS / "README.md", skill / "contracts/README.md")
    assert check_copies(skill, CONTRACTS) == []
    (skill / "contracts/schemas/board.schema.json").write_bytes((CONTRACTS / "schemas/board.schema.json").read_bytes() + b" ")
    assert codes(check_copies(skill, CONTRACTS)) == ["skill.copy_changed"]
    shutil.copy(CONTRACTS / "schemas/board.schema.json", skill / "contracts/schemas/board.schema.json")
    (skill / "contracts/schemas/part.schema.json").unlink()
    assert codes(check_copies(skill, CONTRACTS)) == ["skill.copy_missing"]
    shutil.copy(CONTRACTS / "schemas/part.schema.json", skill / "contracts/schemas/part.schema.json")
    (skill / "contracts/schemas/extra.schema.json").write_text("{}\n")
    assert codes(check_copies(skill, CONTRACTS)) == ["skill.copy_extra"]
    (skill / "contracts/schemas/extra.schema.json").unlink()
    (skill / "contracts/README.md").unlink()
    assert codes(check_copies(skill, CONTRACTS)) == ["skill.copy_missing"]
    names = copy_set(CONTRACTS)
    assert "README.md" in names and "schemas/registry.json" in names and "schemas/manifest.schema.json" in names


def isolated_run(skill_copy: Path, script: str, work: Path, canary: Path, *args):
    """Run a script of a copied skill from an unrelated directory with a cleaned environment."""
    home = work / "home"
    cwd = work / "unrelated"
    home.mkdir(exist_ok=True)
    cwd.mkdir(exist_ok=True)
    before = (SN.source_digest(skill_copy), SN.source_digest(canary))
    result = subprocess.run([sys.executable, "-I", str(skill_copy / script), *args], cwd=cwd, capture_output=True, text=True,
                            env={"PATH": "/usr/bin:/bin", "HOME": str(home)}, timeout=60)
    (work / "unrelated-report.md").write_text("an unrelated edit during the run\n")  # outside the compared bytes
    after = (SN.source_digest(skill_copy), SN.source_digest(canary))
    return result, before[0] != after[0], before[1] != after[1]


def test_copy_run_isolation(tmp: Path):
    print("  note: the copy-run test shows that the fixture needs no repository path. It is not a sandbox.")
    skill = make_skill(tmp, "runner", extra={
        "scripts/ok.py": "from pathlib import Path\nprint(Path(__file__).resolve().parents[1].joinpath('references/a.md').read_text().strip())\n",
        "scripts/mutate.py": "from pathlib import Path\nPath(__file__).write_text(Path(__file__).read_text() + '# changed\\n')\n",
        "scripts/leak.py": "import sys\nfrom pathlib import Path\nPath(sys.argv[1], 'leak.txt').write_text('leak')\n",
    })
    work = tmp / "work"
    work.mkdir()
    copy = work / "runner"
    shutil.copytree(skill, copy)
    canary = work / "canary"
    canary.mkdir()
    (canary / "keep.txt").write_text("keep\n")
    result, source_changed, canary_changed = isolated_run(copy, "scripts/ok.py", work, canary)
    assert result.returncode == 0 and "Reference A" in result.stdout and not source_changed and not canary_changed, result.stderr
    assert str(ROOT) not in result.stdout + result.stderr, "the fixture needs no repository path"
    result, source_changed, canary_changed = isolated_run(copy, "scripts/mutate.py", work, canary)
    assert result.returncode == 0 and source_changed and not canary_changed, "the test finds a changed copied source"
    shutil.rmtree(copy)
    shutil.copytree(skill, copy)
    result, source_changed, canary_changed = isolated_run(copy, "scripts/leak.py", work, canary, str(canary))
    assert result.returncode == 0 and canary_changed and not source_changed, "the test finds a write to the canary directory"
    assert (work / "unrelated-report.md").is_file(), "an unrelated edit did not change the comparison"


WORKER = textwrap.dedent("""
    import json, os, signal, sys, time
    request = json.load(sys.stdin)
    code = request["code"]
    if "EXIT7" in code or "SIGNAL" in code:
        print(json.dumps({"status": "ok", "stdout": "", "stderr": ""}), flush=True)
        if "EXIT7" in code:
            sys.exit(7)
        os.kill(os.getpid(), signal.SIGKILL)
    if "SLEEP" in code:
        time.sleep(30)
    if "BADJSON" in code:
        print("not json")
        sys.exit(0)
    try:
        exec(compile(code, request["label"], "exec"), {})
        print(json.dumps({"status": "ok", "stdout": "", "stderr": ""}))
    except Exception as err:
        print(json.dumps({"status": "error", "stdout": "", "stderr": repr(err)}))
""")


def routing_fixture(tmp: Path, blocks: dict[str, str]):
    skills = tmp / "skills"
    for name, body in blocks.items():
        make_skill(skills, name, body)
    worker = tmp / "worker.py"
    worker.write_text(WORKER)
    table = {"envs": {"inproc": {"command": None}, "worker": {"command": [sys.executable, str(worker)]},
                      "gone": {"command": None, "available": False}},
             "skills": {}}
    return skills, table


def fence(code, first=""):
    return f"```python\n{first}{code}\n```"


def test_snippet_routing(tmp: Path):
    skills, table = routing_fixture(tmp, {"a": fence("x = 1"), "b": fence("raise ValueError('boom')")})
    table["skills"] = {"a": "inproc", "b": "inproc"}
    log = []
    result = SN.run_suite(skills, table, out=log.append)
    assert [f["code"] for f in result["failures"]] == ["snippet.block_failed"] and result["counts"] == {"inproc": 2}
    # unrouted skill and a missing environment
    table["skills"] = {"a": "inproc", "b": "nowhere"}
    assert sorted(f["code"] for f in SN.run_suite(skills, table, out=log.append)["failures"]) == ["snippet.env_missing"]
    table["skills"] = {"a": "inproc"}
    codes_found = sorted(f["code"] for f in SN.run_suite(skills, table, out=log.append)["failures"])
    assert codes_found == ["snippet.unrouted"], codes_found
    # notest marks
    skills, table = routing_fixture(tmp / "n", {"a": fence("x = 1", "# notest\n"), "b": fence("x = 1", "# notest: needs a file\n")})
    table["skills"] = {"a": "inproc", "b": "inproc"}
    result = SN.run_suite(skills, table, out=log.append)
    assert [f["code"] for f in result["failures"]] == ["snippet.notest_reason"]
    assert [s["reason"] for s in result["skipped"]] == ["needs a file"] and result["counts"] == {}
    # worker environment: pass, failing block, timeout, invalid output
    skills, table = routing_fixture(tmp / "w", {"good": fence("x = 1"), "bad": fence("raise KeyError('k')"),
                                                "slow": fence("# SLEEP\nx = 1"), "junk": fence("# BADJSON\nx = 1"),
                                                "exit7": fence("# EXIT7\nx = 1"), "signal": fence("# SIGNAL\nx = 1")})
    table["skills"] = {name: "worker" for name in ("good", "bad", "slow", "junk", "exit7", "signal")}
    result = SN.run_suite(skills, table, timeout=2, out=log.append)
    assert sorted((f["label"].split("/")[1], f["code"]) for f in result["failures"]) == [
        ("bad", "snippet.block_failed"), ("exit7", "snippet.worker_failed"), ("junk", "snippet.worker_output"),
        ("signal", "snippet.worker_failed"), ("slow", "snippet.timeout")], result["failures"]
    messages = {f["label"].split("/")[1]: f["message"] for f in result["failures"]}
    assert "code 7" in messages["exit7"] and "Signal 9" in messages["signal"], messages
    assert result["counts"] == {"worker": 6}, "the report counts the blocks of the temporary worker, not PCB execution"
    # an unavailable environment is a failure, not a skip
    skills, table = routing_fixture(tmp / "u", {"pcbskill": fence("x = 1")})
    table["skills"] = {"pcbskill": "gone"}
    result = SN.run_suite(skills, table, out=log.append)
    assert [f["code"] for f in result["failures"]] == ["snippet.env_unavailable"]
    dry = SN.run_suite(skills, table, dry_run=True, out=log.append)
    assert [f["code"] for f in dry["failures"]] == ["snippet.env_unavailable"], "the dry run reports an unavailable environment"
    # a block that changes its own skill source, and a block that edits an unrelated file
    skills, table = routing_fixture(tmp / "s", {"edit": "", "other": ""})
    target = skills / "edit/references/a.md"
    unrelated = tmp / "s" / "unrelated.txt"
    (skills / "edit/references/blocks.md").write_text(fence(f"open({str(target)!r}, 'a').write('x')"))
    (skills / "other/references/blocks.md").write_text(fence(f"open({str(unrelated)!r}, 'w').write('x')"))
    table["skills"] = {"edit": "inproc", "other": "inproc"}
    result = SN.run_suite(skills, table, out=log.append)
    assert [(f["code"], f["label"]) for f in result["failures"]] == [("snippet.source_changed", "edit")], result["failures"]
    assert unrelated.is_file(), "an unrelated edit does not fail the run"
    # the real routing table
    real = SN.load_table()
    assert set(real["skills"]) == {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    assert real["envs"]["pcb"].get("available") is False and set(real["skills"].values()) <= set(real["envs"])


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
