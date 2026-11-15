# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3", "jsonschema==4.26.0"]
# ///
"""Focused tests for the pcb-design skill. They run the real tools in the runtime image.

  uv run tests/test_pcb_design.py           # all tests
  uv run tests/test_pcb_design.py waiver    # only tests with 'waiver' in their name

The tests need podman and the image localhost/cad-skills-pcb:b6 (skills/pcb-design/runtime/BUILD.md).
They copy the template and fixtures into a temporary directory. They never write to the repository.
"""

from __future__ import annotations

import filecmp
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/pcb-design"
TEMPLATE = SKILL / "templates/rc-bare-board"
FIX = ROOT / "tests/fixtures/pcb-design"
PCB = ["uv", "run", str(SKILL / "scripts/pcb.py")]
COPIES = ["validate.py", "project_io.py", "identity.py", "sexp.py"]


def run_pcb(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(PCB + list(args) + ["--project", str(project)], capture_output=True, text=True, cwd=SKILL)


def fresh_project(tmp: Path, name: str = "p") -> Path:
    project = tmp / name
    shutil.copytree(TEMPLATE, project)
    return project


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_of(project: Path, op: str) -> dict:
    return json.loads((project / "out/reports" / f"{op}.result.json").read_text())


def test_contract_copies_match_their_sources_byte_for_byte() -> None:
    assert filecmp.cmp(ROOT / "contracts/README.md", SKILL / "contracts/README.md", shallow=False)
    for source in sorted((ROOT / "contracts/schemas").iterdir()):
        assert filecmp.cmp(source, SKILL / "contracts/schemas" / source.name, shallow=False), source.name


def test_gui_preflight_refuses_an_unmeasured_image_id() -> None:
    pcb = load_pcb_module()
    real = set(pcb.GUI_IMAGE_IDS)
    pcb.GUI_IMAGE_IDS.clear()
    try:
        try:
            pcb.gui_preflight("localhost/cad-skills-pcb:b6")
            raise AssertionError("an unmeasured image must be refused")
        except pcb.Refusal as err:
            assert err.code == "update.adapter_unavailable" and "image" in str(err)
    finally:
        pcb.GUI_IMAGE_IDS.update(real)


def test_copies_are_unchanged() -> None:
    for name in COPIES:
        source = ROOT / ("examples/pcb-trial/scripts" if name in ("identity.py", "sexp.py") else "contracts") / name
        assert filecmp.cmp(source, SKILL / "scripts" / name, shallow=False), f"{name} differs from its source"
    schemas = sorted(p.name for p in (ROOT / "contracts/schemas").iterdir())
    assert schemas == sorted(p.name for p in (SKILL / "contracts/schemas").iterdir())


def test_template_records_validate() -> None:
    proc = subprocess.run(["uv", "run", "--no-project", "--no-config", str(SKILL / "scripts/validate.py"),
                           "--schemas", str(SKILL / "contracts/schemas"), "--project", str(TEMPLATE)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_env_matches_lock() -> None:
    proc = subprocess.run(PCB + ["env", "--project", str(TEMPLATE), "--json"], capture_output=True, text=True, cwd=SKILL)
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["lock_matches_image"] is True
    assert report["tools"]["kicad-cli"]["version"] == "10.0.5"


def test_clean_template_passes_all_checks() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        for op in ("erc", "drc", "sim"):
            proc = run_pcb(project, op)
            assert proc.returncode == 0, f"{op}: {proc.stdout}{proc.stderr}"
        proc = run_pcb(project, "export")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "failed 0" in proc.stdout
        assert run_pcb(project, "check").returncode == 0


def test_stale_result_after_schematic_edit() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        assert run_pcb(project, "erc").returncode == 0
        sch = project / "kicad/board.kicad_sch"
        sch.write_text(sch.read_text().replace('"10k"', '"22k"', 1))
        proc = run_pcb(project, "check", "--for", "erc")
        assert proc.returncode == 1 and "report.stale" in proc.stderr


def test_sim_assertion_fails_outside_tolerance() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        path = project / "simulations/assertions.json"
        data = json.loads(path.read_text())
        data[0]["expected"] = 2.5
        path.write_text(json.dumps(data))
        proc = run_pcb(project, "sim")
        assert proc.returncode == 1 and "fail" in proc.stdout


def test_sim_malformed_duplicate_pair_is_exit_1() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        path = project / "simulations/assertions.json"
        data = json.loads(path.read_text())
        path.write_text(json.dumps(data + data))
        assert run_pcb(project, "sim").returncode == 1


def test_waiver_unwaived_then_waived_then_stale() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        shutil.copyfile(FIX / "defective.kicad_sch", project / "kicad/board.kicad_sch")
        proc = run_pcb(project, "erc")
        assert proc.returncode == 1, proc.stdout
        unwaived = result_of(project, "erc")["unwaived"]
        assert len(unwaived) == 3 and all(f["reason"] == "unwaived" for f in unwaived)
        pcb_sha = sha(project / "kicad/board.kicad_pcb")
        sch_sha = sha(project / "kicad/board.kicad_sch")
        waivers = [{"id": f"W{i}", "kind": "erc", "rule": f["rule"], "objects": f["objects"], "reason": "Test.",
                    "reviewer": "Test reviewer", "revision": "A", "board_sha256": pcb_sha, "schematic_sha256": sch_sha}
                   for i, f in enumerate(unwaived, 1)]
        (project / "manufacturing/waivers.yaml").write_text(
            yaml.safe_dump({"schema_id": "cad-skills/waivers", "schema_version": "1.0", "waivers": waivers}, sort_keys=False))
        proc = run_pcb(project, "erc")
        assert proc.returncode == 0 and result_of(project, "erc")["status"] == "pass_with_waivers"
        for w in waivers:
            w["revision"] = "B"
        (project / "manufacturing/waivers.yaml").write_text(
            yaml.safe_dump({"schema_id": "cad-skills/waivers", "schema_version": "1.0", "waivers": waivers}, sort_keys=False))
        proc = run_pcb(project, "erc")
        assert proc.returncode == 1
        assert all(f["reason"] == "waiver.stale" for f in result_of(project, "erc")["unwaived"])


def test_waiver_superset_does_not_apply() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        shutil.copyfile(FIX / "defective.kicad_sch", project / "kicad/board.kicad_sch")
        assert run_pcb(project, "erc").returncode == 1
        first = result_of(project, "erc")["unwaived"][0]
        waiver = {"id": "W1", "kind": "erc", "rule": first["rule"],
                  "objects": first["objects"] + ["00000000-0000-0000-0000-000000000001"],
                  "reason": "Test.", "reviewer": "Test reviewer", "revision": "A",
                  "board_sha256": sha(project / "kicad/board.kicad_pcb"),
                  "schematic_sha256": sha(project / "kicad/board.kicad_sch")}
        (project / "manufacturing/waivers.yaml").write_text(
            yaml.safe_dump({"schema_id": "cad-skills/waivers", "schema_version": "1.0", "waivers": [waiver]}, sort_keys=False))
        assert run_pcb(project, "erc").returncode == 1
        result = result_of(project, "erc")
        assert result["status"] == "fail" and not result["waived"]
        assert any(f["rule"] == "waiver.unused" for f in result["unwaived"])


def test_refill_matches_accepted_board_and_rebinds_interface() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        shutil.copyfile(FIX / "unfilled.kicad_pcb", project / "kicad/board.kicad_pcb")
        iface_path = project / "mechanical/board-interface.json"
        iface = json.loads(iface_path.read_text())
        iface["board_sha256"] = sha(project / "kicad/board.kicad_pcb")
        iface_path.write_text(json.dumps(iface, indent=2))
        assert run_pcb(project, "drc", "--refill-zones").returncode == 0
        accepted = ROOT / "examples/pcb-trial/results/final_r2/trial.kicad_pcb"
        assert filecmp.cmp(project / "kicad/board.kicad_pcb", accepted, shallow=False)
        assert any(p.name.endswith(".kicad_pcb") for p in (project / "out/history/boards").iterdir())
        proc = run_pcb(project, "interface", "--apply", "--expect", str(project / "out/reports/refill.expect.json"))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert json.loads(iface_path.read_text())["board_sha256"] == sha(project / "kicad/board.kicad_pcb")
        # An interface edit that the rebinding did not see (a height limit) makes the automatic result stale.
        iface = json.loads(iface_path.read_text())
        iface["height_limits"]["top_mm"] = iface["height_limits"]["top_mm"] + 1
        iface_path.write_text(json.dumps(iface, indent=2))
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and interface_finding(proc.stderr), proc.stderr


def test_review_with_string_examined_is_not_a_review() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        review = project / "mechanical/interface-review.json"
        record = json.loads(review.read_text())
        record["examined"] = "/outline"
        review.write_text(json.dumps(record, indent=2))
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and interface_finding(proc.stderr), proc.stderr


def test_interface_refuses_without_recorded_expectation() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        iface_path = project / "mechanical/board-interface.json"
        iface = json.loads(iface_path.read_text())
        iface["board_sha256"] = "0" * 64
        iface_path.write_text(json.dumps(iface, indent=2))
        expect = project / "expect.json"
        expect.write_text('{"differences": []}')
        proc = run_pcb(project, "interface", "--apply", "--expect", str(expect))
        assert proc.returncode == 1 and "interface.prior_missing" in proc.stderr


def test_binding_result_mismatch_after_interruption() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        assert run_pcb(project, "erc").returncode == 0
        old_result = (project / "out/reports/erc.result.json").read_bytes()
        sch = project / "kicad/board.kicad_sch"
        sch.write_text(sch.read_text().replace('"10k"', '"22k"', 1))
        assert run_pcb(project, "erc").returncode == 0
        (project / "out/reports/erc.result.json").write_bytes(old_result)
        proc = run_pcb(project, "check", "--for", "erc")
        assert proc.returncode == 1 and "binding_mismatch" in proc.stderr


def test_export_refuses_unsupported_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        for op in ("erc", "drc", "sim"):
            assert run_pcb(project, op).returncode == 0
        path = project / "manufacturing/export.yaml"
        data = yaml.safe_load(path.read_text())
        data["x2"] = True
        path.write_text(json.dumps(data))
        # The export contract is part of every input closure, so the checks run again first.
        for op in ("erc", "drc", "sim"):
            assert run_pcb(project, op).returncode == 0
        proc = run_pcb(project, "export")
        assert proc.returncode == 2 and "export.unsupported_setting" in proc.stderr


def test_export_destination_exists_is_exit_2() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        for op in ("erc", "drc", "sim"):
            assert run_pcb(project, op).returncode == 0
        (project / "exists").mkdir()
        proc = run_pcb(project, "export", "--dest", "exists")
        assert proc.returncode == 2 and "export.destination_exists" in proc.stderr


def test_settings_mismatch_and_apply() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        board = project / "kicad/board.kicad_pcb"
        board.write_text(board.read_text().replace("(drillshape 0)", "(drillshape 1)"))
        assert run_pcb(project, "settings").returncode == 1
        assert run_pcb(project, "settings", "--apply").returncode == 0
        assert run_pcb(project, "settings").returncode == 0


def test_manual_update_and_gui_refusal() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        assert run_pcb(project, "update", "--adapter", "gui").returncode == 2
        proc = run_pcb(project, "update", "--adapter", "manual")
        assert proc.returncode == 2 and "update.manual_required" in proc.stderr
        assert (project / "out/handoff/manual.json").is_file()


def stage_r2_edit(project: Path) -> None:
    """Change R2 in the schematic only, as an agent does before a GUI update."""
    sch = project / "kicad/board.kicad_sch"
    text = sch.read_text()
    i = text.index('(property "Reference" "R2"')
    j = text.index('"Value" "10k"', i)
    sch.write_text(text[:j] + '"Value" "20k"' + text[j + len('"Value" "10k"'):])


def r2_expectation(project: Path, after: str = "20k") -> str:
    path = project / "expect/r2-value.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"differences": [{"op": "changed", "class": "footprint", "ident": "R2",
                                                 "field": "value", "before": "10k", "after": after}]}))
    return "expect/r2-value.json"


def test_gui_update_requires_expectation() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        proc = run_pcb(project, "update", "--adapter", "gui")
        assert proc.returncode == 2 and "update.expectation_missing" in proc.stderr


def test_gui_update_identity_mismatch_publishes_nothing() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        before = sha(project / "kicad/board.kicad_pcb")
        stage_r2_edit(project)
        expect = r2_expectation(project, after="22k")
        proc = run_pcb(project, "update", "--adapter", "gui", "--expect", expect)
        assert proc.returncode == 1 and "update.identity_mismatch" in proc.stderr, proc.stdout + proc.stderr
        assert sha(project / "kicad/board.kicad_pcb") == before
        assert not (project / "out/reports/update.result.json").exists()


def test_gui_update_integration_then_rebind_and_ready() -> None:
    """The real KiCad GUI in Xvfb updates R2 from the schematic. The identity reader and the parity check decide."""
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        stage_r2_edit(project)
        expect = r2_expectation(project)
        proc = run_pcb(project, "update", "--adapter", "gui", "--expect", expect)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        result = json.loads((project / "out/reports/update.result.json").read_text())
        assert result["status"] == "pass" and result["state"] == "ready", result
        assert '"Value" "20k"' in (project / "kicad/board.kicad_pcb").read_text()
        assert run_pcb(project, "interface", "--apply", "--expect", str(project / "out/reports/update.expect.json")).returncode == 0
        for op in ("erc", "drc", "sim"):
            assert run_pcb(project, op).returncode == 0, op
        assert run_pcb(project, "export").returncode == 0
        assert run_pcb(project, "check", "--for", "ready").returncode == 0


def load_pcb_module():
    """Import the controller module from the skill (its dependencies come from the test environment)."""
    import importlib.util
    scripts = str(SKILL / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("pcb_controller", SKILL / "scripts/pcb.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_prerequisites_are_per_operation(monkeypatch=None) -> None:
    """A missing ngspice blocks only the simulation. ERC does not need it (section 4 and section 5)."""
    pcb = load_pcb_module()
    real_which = pcb.shutil.which
    # Only ngspice is missing here. The other tools are simulated as present.
    pcb.shutil.which = lambda name: None if name == "ngspice" else ("/bin/true" if name == "kicad-cli" else real_which(name))
    try:
        pcb.native_check("erc")  # must not raise
        try:
            pcb.native_check("sim")
            raise AssertionError("sim must need ngspice")
        except pcb.Refusal as err:
            assert err.code == "runtime.native_unavailable" and "ngspice" in str(err)
    finally:
        pcb.shutil.which = real_which


def test_staged_bytes_bind_the_closure() -> None:
    """The closure holds the hashes of the bytes written to staging. A later live edit is then detectable."""
    pcb = load_pcb_module()
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        stage, closure = pcb.stage_snapshot(project, "erc")
        staged = stage / "kicad/board.kicad_sch"
        assert sha(staged) == closure["kicad/board.kicad_sch"]
        sch = project / "kicad/board.kicad_sch"
        sch.write_text(sch.read_text().replace('"10k"', '"22k"', 1))
        assert sha(staged) == closure["kicad/board.kicad_sch"], "staging must not follow the live edit"
        assert pcb.current_closure(project, "erc") != closure, "the live edit must be detected before publication"


def test_runtime_refusals_on_host() -> None:
    """--runtime native needs the tools on this host (none here), and it conflicts with a container lock."""
    assert run_pcb(TEMPLATE, "env", "--runtime", "native").returncode == 2
    assert run_pcb(TEMPLATE, "erc", "--runtime", "native").returncode == 2


def test_native_route_inside_runtime_image() -> None:
    """The native controller branch runs inside the existing runtime image with a native lock.

    The host has no KiCad, so the controller runs inside the image. The validator dependencies come from a read-only
    directory that uv installs offline. This tests the branch. It does not test a native host installation.
    """
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        root = Path(tmp)
        project = fresh_project(root)
        lock = json.loads((project / "toolchain.lock.json").read_text())
        lock["execution"] = "native"
        lock.pop("container", None)
        (project / "toolchain.lock.json").write_text(json.dumps(lock, indent=2))
        deps = root / "pydeps"
        subprocess.run(["uv", "pip", "install", "--offline", "--python", "3.13", "--target", str(deps),
                        "jsonschema==4.26.0", "pyyaml==6.0.3"], check=True, capture_output=True)

        def inside(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(["podman", "run", "--rm", "--pull=never", "--network", "none",
                                   "--security-opt", "label=disable", "-v", f"{project}:/proj",
                                   "-v", f"{SKILL}:/skill:ro", "-v", f"{deps}:/pydeps:ro", "-e", "PYTHONPATH=/pydeps",
                                   "-w", "/proj", "localhost/cad-skills-pcb:b6", "/usr/bin/python3",
                                   "/skill/scripts/pcb.py", *args, "--project", "/proj"],
                                  capture_output=True, text=True)

        for op in ("erc", "drc", "sim"):
            proc = inside(op)
            assert proc.returncode == 0, f"{op}: {proc.stdout}{proc.stderr}"
        lock["tools"]["kicad"]["version"] = "10.0.4"
        (project / "toolchain.lock.json").write_text(json.dumps(lock, indent=2))
        proc = inside("erc")
        assert proc.returncode == 2 and "runtime.version_mismatch" in proc.stderr, proc.stderr
        lock["tools"]["kicad"]["version"] = "10.0.5"
        (project / "toolchain.lock.json").write_text(json.dumps(lock, indent=2))
        assert inside("export").returncode == 0
        assert inside("check").returncode == 0
        result = json.loads((project / "out/reports/erc.binding.json").read_text())
        assert result["runtime"]["execution"] == "native"


def gui_namespace(project: Path, expect: str = "expect/r2-value.json"):
    import argparse
    return argparse.Namespace(project=str(project), adapter="gui", expect=expect, relink="off", replace="off",
                              delete="off", image=None, runtime="auto")


def run_gui_with_summary(summary_text: str, options: dict | None = None, kicad_exit: dict | None = None) -> int:
    """Run cmd_update_gui with a crafted driver summary. The preflight is bypassed on purpose: this tests the
    summary validation, not the image."""
    import io
    import contextlib
    pcb = load_pcb_module()
    real_run = pcb.subprocess.run
    real_pre = pcb.gui_preflight
    real_image = pcb.container_image
    real_tools = pcb.measure_tools

    class Done:
        returncode = 0
        stdout = summary_text
        stderr = ""

    def fake_run(argv, *a, **kw):
        if "gui_update.py" in " ".join(argv):
            return Done()
        return real_run(argv, *a, **kw)

    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        stage_r2_edit(project)
        expect = r2_expectation(project)
        pcb.subprocess.run = fake_run
        pcb.gui_preflight = lambda image: None
        pcb.container_image = lambda *a, **kw: "localhost/cad-skills-pcb:b6"
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                try:
                    return pcb.cmd_update_gui(gui_namespace(project, expect), project)
                except pcb.Refusal as err:
                    return {"update.summary_malformed": 3, "update.kicad_exit": 3, "update.option_mismatch": 3,
                            "update.gui_failed": 3}.get(err.code, err.status)
        finally:
            pcb.subprocess.run = real_run
            pcb.gui_preflight = real_pre
            pcb.container_image = real_image


def good_summary(**changes) -> str:
    summary = {"kicad_exit": {"state": "exited", "code": 0},
               "options_measured": {"relink": {"after": False}, "replace": {"after": False}, "delete": {"after": False}}}
    summary.update(changes)
    return json.dumps(summary)


def test_gui_summary_absent_or_malformed_is_refused() -> None:
    assert run_gui_with_summary("") == 3
    assert run_gui_with_summary("not json") == 3
    assert run_gui_with_summary(json.dumps({"kicad_exit": {"state": "exited", "code": 0}})) == 3


def test_gui_forced_stop_and_nonzero_exit_are_refused() -> None:
    forced = good_summary(kicad_exit={"state": "stopped by the script after 15 s", "code": -15})
    assert run_gui_with_summary(forced) == 3
    nonzero = good_summary(kicad_exit={"state": "exited", "code": 1})
    assert run_gui_with_summary(nonzero) == 3


def test_gui_option_mismatch_is_refused() -> None:
    wrong = good_summary(options_measured={"relink": {"after": False}, "replace": {"after": True},
                                           "delete": {"after": False}})
    assert run_gui_with_summary(wrong) == 3


def test_slot_drill_is_refused_by_the_worker_with_a_named_object() -> None:
    proc = subprocess.run(["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
                           "-v", f"{SKILL}/scripts:/worker:ro", "-v", f"{FIX}:/work:ro", "-w", "/work",
                           "localhost/cad-skills-pcb:b6", "uv", "run", "--no-project", "--no-config", "--offline",
                           "--python", "/usr/bin/python3", "python", "/worker/board_inventory.py", "/work/slot.kicad_pcb"],
                          capture_output=True, text=True)
    assert proc.returncode == 2, proc.stderr
    record = json.loads(proc.stdout)
    assert record["unsupported"] and "slot or oval drill" in record["unsupported"][0]["reason"]


def test_check_export_detects_missing_and_changed_files() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        for op in ("erc", "drc", "sim"):
            assert run_pcb(project, op).returncode == 0
        assert run_pcb(project, "export").returncode == 0
        assert run_pcb(project, "check", "--for", "export").returncode == 0
        published = json.loads((project / "out/reports/export.result.json").read_text())["published"]
        gerber = project / published / "board-F_Cu.gbr"
        saved = gerber.read_bytes()
        gerber.unlink()
        proc = run_pcb(project, "check", "--for", "export")
        assert proc.returncode == 1 and "export.file_missing" in proc.stderr, proc.stderr
        gerber.write_bytes(saved + b"\n")
        proc = run_pcb(project, "check", "--for", "export")
        assert proc.returncode == 1 and "export.file_changed" in proc.stderr, proc.stderr


def test_external_library_is_refused_and_nested_library_is_in_the_closure() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        table = project / "kicad/fp-lib-table"
        original = table.read_text()
        table.write_text(original.rstrip().rstrip(")") + '\t(lib (name "Outside")(type "KiCad")(uri "/home/someone/lib.pretty")(options "")(descr ""))\n)\n')
        proc = run_pcb(project, "erc")
        assert proc.returncode == 2 and "pcb.external_library" in proc.stderr, proc.stderr
        table.write_text(original.rstrip().rstrip(")") + '\t(lib (name "Local")(type "KiCad")(uri "${KIPRJMOD}/local/nested/x.pretty")(options "")(descr ""))\n)\n')
        nested = project / "kicad/local/nested/x.pretty"
        nested.mkdir(parents=True)
        (nested / "part.kicad_mod").write_text("(footprint \"part\")\n")
        assert run_pcb(project, "erc").returncode == 0
        (nested / "part.kicad_mod").write_text("(footprint \"part\" (descr changed))\n")
        proc = run_pcb(project, "check", "--for", "erc")
        assert proc.returncode == 1 and "report.stale" in proc.stderr, proc.stderr


def test_export_declares_inner_and_bottom_copper_for_four_and_six_layers() -> None:
    """Real KiCad boards with inner copper (Pi F1). The FileFunction of each copper file follows the stackup."""
    import re
    for count in (4, 6):
        with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
            project = fresh_project(Path(tmp))
            shutil.copyfile(FIX / f"stack{count}.kicad_pcb", project / "kicad/board.kicad_pcb")
            contract = yaml.safe_load((project / "manufacturing/export.yaml").read_text())
            inner = [f"In{k}.Cu" for k in range(1, count - 1)]
            layers = [l for l in contract["layers"] if l["role"] != "copper_bottom"]
            layers += [{"role": "copper_inner", "kicad_layer": n, "suffix": "-" + n.replace(".", "_") + ".gbr"} for n in inner]
            layers += [{"role": "copper_bottom", "kicad_layer": "B.Cu", "suffix": "-B_Cu.gbr"}]
            contract["layers"] = layers
            (project / "manufacturing/export.yaml").write_text(json.dumps(contract))
            for op in ("erc", "drc", "sim"):
                assert run_pcb(project, op).returncode == 0, (count, op)
            proc = run_pcb(project, "export")
            assert proc.returncode == 0, proc.stdout + proc.stderr
            folder = project / json.loads((project / "out/reports/export.result.json").read_text())["published"]
            first_inner = (folder / "board-In1_Cu.gbr").read_text()
            assert re.search(r"TF\.FileFunction,Copper,L2,Inr\*", first_inner), "inner layer 1 must be L2 Inr"
            bottom = (folder / "board-B_Cu.gbr").read_text()
            assert re.search(rf"TF\.FileFunction,Copper,L{count},Bot\*", bottom), f"bottom must be L{count} Bot"


def interface_finding(stderr: str) -> bool:
    """True when the output names an interface readiness code (not the file name board-interface.json)."""
    return re.search(r"interface\.(review|geometry|evidence|expectation|prior)_", stderr) is not None


def change_interface(project: Path, **changes) -> None:
    path = project / "mechanical/board-interface.json"
    data = json.loads(path.read_text())
    for key, value in changes.items():
        data[key] = value
    path.write_text(json.dumps(data, indent=2))


def record_review_cli(project: Path, *examined: str) -> subprocess.CompletedProcess:
    args = ["interface", "--record-review", "--reviewer", "Test reviewer"]
    for pointer in examined:
        args += ["--examined", pointer]
    return run_pcb(project, *args)


def test_manual_review_without_prior_needs_all_top_level_keys() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        (project / "mechanical/interface-review.json").unlink()
        change_interface(project, thickness_mm=1.7)
        proc = record_review_cli(project, "/thickness_mm")
        assert proc.returncode == 1 and "interface.review_invalid" in proc.stderr, proc.stderr


def test_manual_review_must_cover_changed_pointers_of_the_preserved_prior() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        change_interface(project, thickness_mm=1.7, height_limits={"top_mm": 11, "bottom_mm": 2})
        proc = record_review_cli(project, "/thickness_mm")
        assert proc.returncode == 1 and "/height_limits/top_mm" in proc.stderr, proc.stderr


def test_manual_review_with_full_coverage_passes_and_names_the_prior() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        change_interface(project, height_limits={"top_mm": 11, "bottom_mm": 2})
        assert record_review_cli(project, "/height_limits/top_mm").returncode == 0
        record = json.loads((project / "mechanical/interface-review.json").read_text())
        assert record["prior_interface_sha256"] == sha_text(TEMPLATE / "mechanical/board-interface.json"), record
        assert (project / "out/history/interfaces" / f"{record['prior_interface_sha256']}.json").is_file()
        proc = run_pcb(project, "check", "--for", "ready")
        assert not interface_finding(proc.stderr), proc.stderr


def sha_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_review_with_missing_or_altered_prior_interface_fails_readiness() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        change_interface(project, height_limits={"top_mm": 11, "bottom_mm": 2})
        assert record_review_cli(project, "/height_limits/top_mm").returncode == 0
        prior = json.loads((project / "mechanical/interface-review.json").read_text())["prior_interface_sha256"]
        # The record of the review names the interface it reviewed. Alter that preserved prior: readiness must fail.
        history = project / "out/history/interfaces" / f"{prior}.json"
        history.write_text(history.read_text() + " ")
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and interface_finding(proc.stderr), proc.stderr


def test_automatic_evidence_checks_board_and_expectation_bytes() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        shutil.copyfile(FIX / "unfilled.kicad_pcb", project / "kicad/board.kicad_pcb")
        iface_path = project / "mechanical/board-interface.json"
        iface = json.loads(iface_path.read_text())
        iface["board_sha256"] = sha(project / "kicad/board.kicad_pcb")
        iface_path.write_text(json.dumps(iface, indent=2))
        assert run_pcb(project, "drc", "--refill-zones").returncode == 0
        assert run_pcb(project, "interface", "--apply", "--expect", str(project / "out/reports/refill.expect.json")).returncode == 0
        assert not interface_finding(run_pcb(project, "check", "--for", "ready").stderr)
        prior = next((project / "out/history/boards").glob("*.kicad_pcb"))
        saved = prior.read_bytes()
        prior.write_bytes(saved + b"\n")
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and interface_finding(proc.stderr), proc.stderr
        prior.write_bytes(saved)
        expect = project / "out/reports/refill.expect.json"
        expect.write_text(expect.read_text() + " ")
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and interface_finding(proc.stderr), proc.stderr


def test_residual_staging_directory_is_a_finding_and_an_empty_parent_is_not() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        staging = project / "out/staging"
        (staging / "erc-leftover").mkdir(parents=True)
        proc = run_pcb(project, "check", "--for", "erc")
        assert proc.returncode == 1 and "staging.residual" in proc.stderr, proc.stderr
        shutil.rmtree(staging / "erc-leftover")
        proc = run_pcb(project, "check", "--for", "erc")
        assert "staging" not in proc.stderr, proc.stderr


def test_malformed_assertions_exit_1_without_traceback() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        path = project / "simulations/assertions.json"
        good = path.read_text()
        cases = {
            "duplicate": '[{"circuit":"rc.cir","measurement":"vtau","expected":2.086,"tolerance":0.02086,'
                         '"tolerance":0.5}]',
            "newline": good.replace('"vtau"', '"vtau\\n"'),
            "excessive": good.replace("2.086", "1" + "0" * 400),
        }
        for name, text in cases.items():
            path.write_text(text)
            proc = run_pcb(project, "sim")
            assert proc.returncode == 1 and "assertion.malformed" in proc.stderr, (name, proc.stderr)
            assert "Traceback" not in proc.stderr, name


def test_malformed_interface_evidence_is_not_ready() -> None:
    with tempfile.TemporaryDirectory(prefix="pcb-design-") as tmp:
        project = fresh_project(Path(tmp))
        review = project / "mechanical/interface-review.json"
        text = review.read_text()
        review.write_text(text.replace('"reviewer": "template-author"', '"reviewer": "a", "reviewer": "b"'))
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and "Traceback" not in proc.stderr, proc.stderr
        assert interface_finding(proc.stderr)
        record = json.loads(text)
        record["prior_interface_sha256"] = "ABC"
        review.write_text(json.dumps(record))
        proc = run_pcb(project, "check", "--for", "ready")
        assert proc.returncode == 1 and interface_finding(proc.stderr) and "Traceback" not in proc.stderr, proc.stderr


def test_native_probes_are_per_operation_and_never_traceback() -> None:
    """erc does not probe ngspice. sim does not probe kicad-cli. A missing tool is exit 2, not a traceback."""
    import subprocess as sp
    pcb = load_pcb_module()
    lock = json.loads((TEMPLATE / "toolchain.lock.json").read_text())
    calls: list[str] = []
    real_run = pcb.subprocess.run

    def fake_run(argv, *args, **kwargs):
        calls.append(argv[0])
        if argv[0] == "sh":  # the ngspice probe; ngspice is absent in this case
            raise FileNotFoundError("sh")
        if argv[0] == "kicad-cli":
            return sp.CompletedProcess(argv, 0, "10.0.5\n", "")
        return sp.CompletedProcess(argv, 0, "10.0.5-probe\n", "")

    pcb.subprocess.run = fake_run
    try:
        pcb.native_versions_ok(lock, "erc")
        assert "sh" not in calls and "kicad-cli" in calls, calls
        calls.clear()
        try:
            pcb.native_versions_ok(lock, "sim")
            raise AssertionError("sim without ngspice must be refused")
        except pcb.Refusal as err:
            assert err.code == "runtime.native_unavailable" and err.status == 2, (err.code, err.status)
        assert "kicad-cli" not in calls, calls
        calls.clear()
        measured = pcb.measure_tools(None, tools=("ngspice",))
        assert measured["ngspice"]["exit"] == 127 and measured["ngspice"]["version"] is None, measured
    finally:
        pcb.subprocess.run = real_run


def test_gitignore_exception_is_template_history_only() -> None:
    """The template interface history is tracked. Other out/ files stay ignored (two-level exception check)."""
    required = next((SKILL / "templates/rc-bare-board/out/history/interfaces").glob("*.json"))
    rel = required.relative_to(ROOT).as_posix()
    unrelated = [
        "skills/pcb-design/templates/rc-bare-board/out/history/interfaces/notes.txt",
        "skills/pcb-design/templates/rc-bare-board/out/history/interfaces/sub/y.json",
        "skills/pcb-design/templates/rc-bare-board/out/history/boards/x.kicad_pcb",
        "skills/pcb-design/templates/rc-bare-board/out/reports/a.json",
        "out/history/interfaces/h.json",
        "examples/pcb-trial/out/history/interfaces/h.json",
    ]

    def ignored(path: str) -> int:
        return subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", path], capture_output=True).returncode

    assert ignored(rel) == 1, f"{rel} must not be ignored"
    for path in unrelated:
        assert ignored(path) == 0, f"{path} must stay ignored"


TESTS = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]


def main(argv: list[str]) -> int:
    pattern = argv[0] if argv else ""
    failed = 0
    for fn in TESTS:
        if pattern and pattern not in fn.__name__:
            continue
        try:
            fn()
            print(f"pass {fn.__name__}")
        except AssertionError as err:
            failed += 1
            print(f"FAIL {fn.__name__}: {err}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
