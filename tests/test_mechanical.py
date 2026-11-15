# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery", "jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Contract and command-flow tests for the B11 mechanical fit (completion repair).

  uv run tests/test_mechanical.py              # all tests
  uv run tests/test_mechanical.py transform    # tests with 'transform' in their name

The command tests that need the local image refuse before any container starts, so they run
without podman. The end-to-end positive and negative runs are retained in
docs/reviews/mechanical/b11-e2e-evidence (historical until the repaired run is re-frozen).
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "pcb-design"
sys.path.insert(0, str(SKILL / "scripts"))
FIXTURE_DIR = SKILL / "templates" / "mech-fit-a"

import mechanical as M  # noqa: E402


def load_make_fixture():
    spec = importlib.util.spec_from_file_location("make_fixture", FIXTURE_DIR / "make_fixture.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generated(tmp: Path) -> Path:
    with contextlib.redirect_stdout(io.StringIO()):
        load_make_fixture().main(["--out", str(tmp)])
    return tmp


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = generated(Path(self.tmp.name))
        self.iface = read_json(self.root / "mechanical" / "board-interface.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_transform_missing_refuses(self):
        bad = copy.deepcopy(self.iface)
        del bad["extensions"]["transform"]
        with self.assertRaises(M.MechError) as ctx:
            M.load_transform(bad)
        self.assertEqual(ctx.exception.code, "transform.missing")
        self.assertEqual(ctx.exception.status, 2)

    def test_transform_extra_key_refuses(self):
        bad = copy.deepcopy(self.iface)
        bad["extensions"]["transform"]["target_origin_mm"] = {"x": 0, "y": 0}
        with self.assertRaises(M.MechError) as ctx:
            M.load_transform(bad)
        self.assertEqual(ctx.exception.code, "transform.keys")

    def test_transform_boolean_scale_refuses(self):
        bad = copy.deepcopy(self.iface)
        bad["extensions"]["transform"]["scale"] = True
        with self.assertRaises(M.MechError) as ctx:
            M.load_transform(bad)
        self.assertEqual(ctx.exception.code, "transform.type")

    def test_transform_scale_two_refuses(self):
        bad = copy.deepcopy(self.iface)
        bad["extensions"]["transform"]["scale"] = 2
        with self.assertRaises(M.MechError) as ctx:
            M.load_transform(bad)
        self.assertEqual(ctx.exception.code, "transform.scale")

    def test_transform_unsupported_axes_refuse(self):
        bad = copy.deepcopy(self.iface)
        bad["extensions"]["transform"]["source_axes"] = {"x": "right", "y": "up"}
        with self.assertRaises(M.MechError) as ctx:
            M.load_transform(bad)
        self.assertEqual(ctx.exception.code, "transform.axes")

    def test_outline_start_maps_to_expected_point(self):
        t = M.load_transform(self.iface)
        x, y = M.to_target((100, 100), t)
        self.assertAlmostEqual(x, -3.7, places=9)
        self.assertAlmostEqual(y, 18.2, places=9)

    def test_mirrored_transform_moves_holes(self):
        t = M.load_transform(self.iface)
        good = M.to_target((110.0, 130.0), t)
        mirrored = (t["origin"][0] - (110.0 - t["anchor"][0]), good[1])
        self.assertGreater(abs(mirrored[0] - good[0]), M.FIXED_TOLERANCE["geometry_mm"])


class FrameTests(unittest.TestCase):
    def test_asymmetric_vector_at_30_degrees(self):
        """local (2.0, 0.5) at 30 degrees gives (1.982, 0.567), target angle 15.96."""
        vec = M.target_vector((2.0, 0.5), 30.0)
        self.assertAlmostEqual(vec[0], 1.982, places=3)
        self.assertAlmostEqual(vec[1], 0.567, places=3)
        self.assertAlmostEqual(M.target_angle_deg(vec), 15.964, places=2)

    def test_axis_vector_at_30_degrees_is_bottom_connector(self):
        vec = M.target_vector((1.0, 0.0), 30.0)
        self.assertAlmostEqual(vec[0] * 4.0, 3.464, places=3)
        self.assertAlmostEqual(vec[1] * 4.0, 2.0, places=3)
        self.assertAlmostEqual(M.target_angle_deg(vec), 30.0, places=6)

    def test_board_vector_matches_measured_pad(self):
        bv = M.board_vector((2.0, 0.5), 30.0)
        self.assertAlmostEqual(bv[0], 1.982, places=3)
        self.assertAlmostEqual(bv[1], -0.567, places=3)


class StackupAndEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.src = read_json(FIXTURE_DIR / "fixture-source.json")

    def test_layer_sum_matches_total(self):
        surfaces = M.check_stackup(self.src)
        self.assertEqual(surfaces["core_mm"], 1.51)
        self.assertEqual(surfaces["bottom_surface_z"], -0.045)
        self.assertEqual(surfaces["top_surface_z"], 1.555)

    def test_layer_sum_mismatch_refuses(self):
        bad = copy.deepcopy(self.src)
        bad["stackup"]["thickness_mm"] = 1.556
        with self.assertRaises(M.MechError) as ctx:
            M.check_stackup(bad)
        self.assertEqual(ctx.exception.code, "C05s")

    def test_envelope_surface_must_match_stackup(self):
        surfaces = M.check_stackup(self.src)
        bad = copy.deepcopy(self.src)
        bad["finished_envelope"]["top_surface_z_mm"] = 1.51
        with self.assertRaises(M.MechError) as ctx:
            M.check_finished_envelope(bad, surfaces)
        self.assertEqual(ctx.exception.code, "envelope.surface")


class EvidenceAndOwnerTests(unittest.TestCase):
    def test_unconfirmed_is_never_pass(self):
        self.assertEqual(M.evidence_status({"evidence": "unconfirmed", "height_mm": 1, "limit_mm": 10}), "unconfirmed")

    def test_proxy_gives_envelope_only(self):
        self.assertEqual(M.evidence_status({"evidence": "proxy", "height_mm": 2.8, "limit_mm": 4.0}),
                         "conservative_envelope_only")

    def test_measured_over_limit_fails(self):
        self.assertEqual(M.evidence_status({"evidence": "measured", "height_mm": 5.0, "limit_mm": 4.0}), "fail")

    def test_non_numeric_height_uses_evidence_code(self):
        with self.assertRaises(M.MechError) as ctx:
            M.evidence_status({"evidence": "measured", "height_mm": "tall", "limit_mm": 4.0})
        self.assertEqual(ctx.exception.code, "evidence.height")

    def test_measured_source_null_refuses(self):
        with self.assertRaises(M.MechError) as ctx:
            M.check_evidence_source({"ref": "B1", "evidence": "measured", "source_sha256": None})
        self.assertEqual(ctx.exception.code, "evidence.source")

    def test_bottom_footprint_without_pad_frame_refuses(self):
        with self.assertRaises(M.MechError) as ctx:
            M.check_footprint_evidence({"ref": "X1", "side": "bottom"})
        self.assertEqual(ctx.exception.code, "pad_frame.missing")

    def test_library_unflipped_frame_refuses(self):
        with self.assertRaises(M.MechError) as ctx:
            M.check_footprint_evidence({"ref": "X1", "side": "bottom", "pad_frame": "library-unflipped"})
        self.assertEqual(ctx.exception.code, "pad_frame.unsupported")

    def test_connector_extra_field_refuses(self):
        item = {"id": "CN1", "side": "top", "x": 1, "y": 2, "rotation_deg": 0, "insertion_depth_mm": 4,
                "connector_width_mm": 9.0}
        with self.assertRaises(M.MechError) as ctx:
            M.check_connector_record(item)
        self.assertEqual(ctx.exception.code, "connector.field")

    def test_connector_body_length_is_required_and_separate(self):
        rec = {"ref": "CN1", "insertion_depth_mm": 4.0, "connector_envelope": {}, "insertion_vector_local": {}}
        with self.assertRaises(M.MechError) as ctx:
            M.check_connector_evidence(rec)
        self.assertEqual(ctx.exception.code, "connector.evidence")

    def test_owner_conflict_names_dimension(self):
        iface = {k: "mechanical" for k in M.OWNER_KEYS}
        src = dict(iface)
        src["holes"] = "electrical"
        self.assertEqual(M.owner_conflicts(iface, src), ["holes"])


class ExcludedHoleTests(unittest.TestCase):
    """R1 and P3: an excluded through hole needs position, positive diameter, plated flag and a reason."""

    GOOD = {"id": "V1", "x": 90.0, "y": 90.0, "diameter_mm": 0.3, "plated": True, "reason": "via drill"}

    def iface(self, entry):
        return {"extensions": {"excluded_through_holes": [entry]}}

    def test_valid_entry_passes(self):
        self.assertEqual(M.validate_excluded(self.iface(self.GOOD))[0]["id"], "V1")

    def test_missing_reason_refuses(self):
        bad = {k: v for k, v in self.GOOD.items() if k != "reason"}
        with self.assertRaises(M.MechError) as ctx:
            M.validate_excluded(self.iface(bad))
        self.assertEqual(ctx.exception.code, "excluded.fields")

    def test_blank_reason_refuses(self):
        with self.assertRaises(M.MechError) as ctx:
            M.validate_excluded(self.iface(dict(self.GOOD, reason="   ")))
        self.assertEqual(ctx.exception.code, "excluded.reason")

    def test_zero_diameter_refuses(self):
        with self.assertRaises(M.MechError) as ctx:
            M.validate_excluded(self.iface(dict(self.GOOD, diameter_mm=0)))
        self.assertEqual(ctx.exception.code, "excluded.diameter")

    def test_boolean_position_refuses(self):
        with self.assertRaises(M.MechError):
            M.validate_excluded(self.iface(dict(self.GOOD, x=True)))


class CommandFlowTests(unittest.TestCase):
    """The command flow refuses before any container starts. Each refusal names its cause."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = generated(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_capture_refuses_missing_input(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(M.MechError) as ctx:
                M.capture(Path(empty))
            self.assertEqual(ctx.exception.code, "input.missing")

    def test_missing_b1_refuses_by_reference(self):
        """R4: a source part without an evidence record refuses and names the reference."""
        path = self.root / "mechanical" / "component-evidence.json"
        data = read_json(path)
        data["components"] = [c for c in data["components"] if c["ref"] != "B1"]
        write_json(path, data)
        with self.assertRaises(M.MechError) as ctx:
            M.check_fixture(self.root)
        self.assertEqual(ctx.exception.code, "component.missing")
        self.assertIn("B1", ctx.exception.message)

    def test_missing_connector_body_length_refuses(self):
        path = self.root / "mechanical" / "component-evidence.json"
        data = read_json(path)
        for c in data["components"]:
            if c["ref"] == "CN1":
                del c["body_length_mm"]
        write_json(path, data)
        with self.assertRaises(M.MechError) as ctx:
            M.check_fixture(self.root)
        self.assertEqual(ctx.exception.code, "connector.evidence")

    def test_export_refuses_unpinned_image(self):
        with contextlib.redirect_stderr(io.StringIO()):
            status = M.main(["export", "--project", str(self.root), "--image", "localhost/does-not-exist:none"])
        self.assertEqual(status, 2)

    def test_fit_refuses_stale_input_after_export_record(self):
        """A record for another input set refuses before any calculation (exit 1)."""
        export_dir = self.root / "out" / "mechanical" / "export"
        export_dir.mkdir(parents=True)
        write_json(export_dir / "export.json", {"record": "mech-export/1", "version": "1", "inputs": {},
                                                "outputs": {}})
        with contextlib.redirect_stderr(io.StringIO()):
            status = M.main(["fit", "--project", str(self.root)])
        self.assertEqual(status, 1)

    def test_export_record_path_escape_refuses(self):
        """R7: a crafted output path outside the project is refused before any read."""
        outputs = {name: {"path": "/etc/hostname", "role": role, "sha256": "0" * 64, "size": 10}
                   for name, role in M.EXPORT_FILES.items()}
        with self.assertRaises(M.MechError) as ctx:
            M._export_record_check({"record": "mech-export/1", "version": "1", "outputs": outputs})
        self.assertEqual(ctx.exception.code, "export.path")

    def test_release_refuses_empty_report_with_passing_status(self):
        """R8: a report with no results is never released, whatever its status says."""
        report_path = self.root / "out" / "mechanical" / "report.json"
        report_path.parent.mkdir(parents=True)
        write_json(report_path, {"record": "mech-report/1", "version": "1", "results": [],
                                 "status": {"geometry_status": "pass", "fit_status": "pass", "missing": []}})
        with contextlib.redirect_stderr(io.StringIO()):
            status = M.main(["release", "--project", str(self.root)])
        self.assertEqual(status, 1)
        self.assertFalse((self.root / "out" / "release" / "mech-release.json").exists())

    def test_release_refuses_missing_report(self):
        with contextlib.redirect_stderr(io.StringIO()):
            status = M.main(["release", "--project", str(self.root)])
        self.assertEqual(status, 2)

    def test_release_roles_are_closed(self):
        self.assertEqual(set(M.ROLES), {"step_board", "dxf_outline", "drill_pth", "drill_npth", "step_fit", "report"})


class ReleaseOrderTests(unittest.TestCase):
    def test_first_mismatch_names_electrical_release_first(self):
        expected = {k: "same" for k in M.RELEASE_ORDER}
        actual = dict(expected, electrical_release_id="other", board_sha256="z")
        self.assertEqual(M.release_first_mismatch(expected, actual)["input"], "electrical_release_id")

    def test_first_mismatch_none_when_equal(self):
        expected = {k: "same" for k in M.RELEASE_ORDER}
        self.assertIsNone(M.release_first_mismatch(expected, dict(expected)))

    def test_first_stale_names_first_changed_input(self):
        base = {rel: {"sha256": "a" * 64, "size": 1} for rel in M.CAPTURED}
        cap = {rel: {"sha256": "a" * 64, "size": 1, "bytes": b""} for rel in M.CAPTURED}
        cap["mechanical/fixture-source.json"]["sha256"] = "b" * 64
        self.assertEqual(M.first_stale(base, cap)["input"], "mechanical/fixture-source.json")


class FixtureTests(unittest.TestCase):
    def test_generated_fixture_passes_contract_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = M.check_fixture(generated(Path(tmp)))
            self.assertEqual(summary["transform_anchor"], [103.7, 118.2])

    def test_fixture_board_yaml_has_no_owner_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = generated(Path(tmp))
            self.assertNotIn("dimension_owners", (root / "board.yaml").read_text(encoding="utf-8"))

    def test_fixture_holes_are_complete_and_plated_hole_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = generated(Path(tmp))
            holes = read_json(root / "mechanical" / "board-interface.json")["holes"]
            self.assertEqual(len(holes), 3)
            self.assertEqual(sum(1 for h in holes if h["plated"]), 1)

    def test_readiness_reports_commands_and_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = M.readiness(generated(Path(tmp)))
            self.assertEqual(state["state"], "ready_for_export")
            self.assertEqual(state["commands"], ["export", "fit", "release"])
            self.assertIn("cadquery", state["dependency"])


class PcbRouteTests(unittest.TestCase):
    """Decision 14: the thin `pcb.py mechanical` route dispatches check, readiness, export, fit and release."""

    def test_route_check_exits_zero_on_generated_fixture(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = generated(Path(tmp))
            proc = subprocess.run([sys.executable, str(SKILL / "scripts" / "pcb.py"), "mechanical", "check", str(root)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_route_lists_all_five_actions(self):
        import subprocess
        proc = subprocess.run([sys.executable, str(SKILL / "scripts" / "pcb.py"), "mechanical", "--help"],
                              capture_output=True, text=True)
        for action in ("check", "readiness", "export", "fit", "release"):
            self.assertIn(action, proc.stdout)


class ResidualCorrectionTests(unittest.TestCase):
    """Residual correction tests: connector agreement, export drift before publication,
    the explicit release mismatch order before the generic stale check, and the full output gate."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = generated(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def edit_iface(self, fn):
        path = self.root / "mechanical" / "board-interface.json"
        data = read_json(path)
        fn(data)
        write_json(path, data)

    def test_interface_side_mismatch_names_connector_and_field(self):
        """Pi N1: an interface side of bottom against a source side of top refuses by name."""
        self.edit_iface(lambda d: d["connector_frames"][0].update({"side": "bottom"}))
        with self.assertRaises(M.MechError) as ctx:
            M.check_fixture(self.root)
        self.assertEqual(ctx.exception.code, "connector.mismatch")
        self.assertIn("CN1", ctx.exception.message)
        self.assertIn("side", ctx.exception.message)

    def test_interface_depth_mismatch_names_connector_and_field(self):
        """Pi N1: an interface depth of 8.0 against a source depth of 4.0 refuses by name."""
        self.edit_iface(lambda d: d["connector_frames"][0].update({"insertion_depth_mm": 8.0}))
        with self.assertRaises(M.MechError) as ctx:
            M.check_fixture(self.root)
        self.assertEqual(ctx.exception.code, "connector.mismatch")
        self.assertIn("insertion_depth_mm", ctx.exception.message)

    def test_export_source_drift_refused_before_publication(self):
        """Residual correction 2: a board change during the export publishes nothing.
        The KiCad runs and the image check are stood in for, so the test needs no container."""
        import shutil
        settings = read_json(self.root / "export-settings.json")
        original_image = M._image_id
        original_run = M._run_kicad

        def fake_image(ref):
            return settings["image_id"]

        def fake_run(stage, image_id, args):
            # Write the outputs the real command would write, then change the live board (drift).
            (stage / "out" / "drill").mkdir(parents=True, exist_ok=True)
            if args[2] == "step":
                (stage / "out" / "board.step").write_bytes(b"STEP fake\n")
            elif args[2] == "dxf":
                (stage / "out" / "outline.dxf").write_bytes(b"DXF fake\n")
            else:
                (stage / "out" / "drill" / "board-PTH.drl").write_bytes(b"PTH fake\n")
                (stage / "out" / "drill" / "board-NPTH.drl").write_bytes(b"NPTH fake\n")
                board = self.root / "board.kicad_pcb"
                board.write_bytes(board.read_bytes() + b"\n")
            return 0, ""

        M._image_id = fake_image
        M._run_kicad = fake_run
        try:
            with self.assertRaises(M.MechError) as ctx:
                M.run_export(self.root, "localhost/cad-skills-pcb:b6")
        finally:
            M._image_id = original_image
            M._run_kicad = original_run
        self.assertEqual(ctx.exception.code, "stale.input")
        self.assertIn("board.kicad_pcb", ctx.exception.message)
        self.assertFalse((self.root / "out" / "mechanical" / "export" / "export.json").exists())
        self.assertFalse((self.root / "out" / "mechanical" / "export" / "board.step").exists())
        shutil.rmtree(self.root / "out" / "staging", ignore_errors=True)

    def make_passing_report(self):
        """A complete passing report with real output files, so the release gate can be exercised."""
        import mechanical_fit as MF
        cap = M.capture(self.root)
        src = read_json(self.root / "mechanical" / "fixture-source.json")
        results = [{"id": k[0], "ref": k[1], "status": "pass", "measured_error_mm": None,
                    "tolerance_mm": None, "reason": ""} for k in MF.required_keys(src)]
        status = MF.recompute_status(results, MF.required_keys(src))
        settings = read_json(self.root / "export-settings.json")
        expected = {"electrical_release_id": src["electrical_release_id"], "release_id": src["release_id"],
                    "board_sha256": cap["board.kicad_pcb"]["sha256"],
                    "interface_sha256": cap["mechanical/board-interface.json"]["sha256"],
                    "component_evidence_sha256": cap["mechanical/component-evidence.json"]["sha256"],
                    "fixture_source_sha256": cap["mechanical/fixture-source.json"]["sha256"],
                    "export_settings_sha256": cap["export-settings.json"]["sha256"],
                    "toolchain_image_id": settings["image_id"], "fixture_id": src["fixture_id"]}
        outputs = {}
        for name, role in M.EXPORT_FILES.items():
            rel = f"{M.EXPORT_DIR}/{name}"
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            data = f"fake {name}\n".encode("utf-8")
            path.write_bytes(data)
            outputs[name] = {"path": rel, "role": role, "sha256": M._sha(data), "size": len(data)}
        fit = self.root / M.FIT_ASSEMBLY
        fit.parent.mkdir(parents=True, exist_ok=True)
        fit.write_bytes(b"fit fake\n")
        report = {"record": M.REPORT_RECORD, "version": "1", "expected": expected,
                  "inputs": M.inputs_record(cap), "export_record_sha256": "0" * 64, "outputs": outputs,
                  "results": results, "status": status,
                  "fit_assembly": {"path": M.FIT_ASSEMBLY, "sha256": M._sha(b"fit fake\n"), "size": 9}}
        write_json(self.root / M.REPORT, report)
        return report

    def test_release_passes_for_complete_consistent_report(self):
        self.make_passing_report()
        record = M.run_release(self.root)
        self.assertEqual(record["release_id"], read_json(self.root / "mechanical" / "fixture-source.json")["release_id"])
        self.assertIsNone(record["first_mismatch"])

    def test_release_id_change_names_release_id_first(self):
        """Residual correction 4: the explicit mismatch order runs before the generic stale check."""
        self.make_passing_report()
        src = self.root / "mechanical" / "fixture-source.json"
        data = read_json(src)
        data["release_id"] = "b11-other"
        write_json(src, data)
        with self.assertRaises(M.MechError) as ctx:
            M.run_release(self.root)
        self.assertEqual(ctx.exception.code, "release.mismatch")
        self.assertIn("release_id", ctx.exception.message)
        self.assertIn("b11-other", ctx.exception.message)

    def test_board_change_names_board_sha256(self):
        self.make_passing_report()
        board = self.root / "board.kicad_pcb"
        board.write_bytes(board.read_bytes() + b"\n")
        with self.assertRaises(M.MechError) as ctx:
            M.run_release(self.root)
        self.assertEqual(ctx.exception.code, "release.mismatch")
        self.assertIn("board_sha256", ctx.exception.message)

    def test_fit_assembly_change_refuses_before_release(self):
        """Residual correction 3: the fit assembly is a bound output and is gated before release."""
        self.make_passing_report()
        (self.root / M.FIT_ASSEMBLY).write_bytes(b"changed\n")
        with self.assertRaises(M.MechError) as ctx:
            M.run_release(self.root)
        self.assertIn(ctx.exception.code, ("stale.fit_assembly", "export.altered"))
        self.assertFalse((self.root / M.RELEASE).exists())

    def test_report_output_change_refuses_before_release(self):
        self.make_passing_report()
        report = read_json(self.root / M.REPORT)
        path = self.root / report["outputs"]["board.step"]["path"]
        path.write_bytes(b"changed step\n")
        with self.assertRaises(M.MechError) as ctx:
            M.run_release(self.root)
        self.assertEqual(ctx.exception.code, "export.altered")
        self.assertFalse((self.root / M.RELEASE).exists())


class PcbForwardingTests(unittest.TestCase):
    """The thin dispatch takes the positional fixture path and forwards the optional image."""

    def test_export_forwards_image_selector(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = generated(Path(tmp))
            proc = subprocess.run([sys.executable, str(SKILL / "scripts" / "pcb.py"), "mechanical", "export",
                                   str(root), "--image", "localhost/does-not-exist:none"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("runtime.image_missing", proc.stderr)


if __name__ == "__main__":
    unittest.main()
