# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery", "jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Geometry tests for the B11 mechanical fit (completion repair).

  uv run tests/test_mechanical_fit.py          # all tests
  uv run tests/test_mechanical_fit.py real     # the retained real-export tests

Parser and comparison tests use synthetic bytes. The real-export tests read the retained
KiCad 10.0.5 export bytes in tests/fixtures/mech-fit-a/real-export.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))

import mechanical as M  # noqa: E402
import mechanical_fit as F  # noqa: E402

HOLES = [
    {"id": "H1", "x": 6.3, "y": -11.8, "diameter_mm": 3.2, "plated": False},
    {"id": "H2", "x": 48.8, "y": 14.7, "diameter_mm": 2.5, "plated": False},
    {"id": "H3", "x": 14.3, "y": 12.2, "diameter_mm": 3.0, "plated": True},
]
OUTLINE = [(-3.7, 18.2), (56.3, 18.2), (56.3, -17.8), (2.3, -17.8), (-3.7, -11.8)]
FIX = ROOT / "tests" / "fixtures" / "mech-fit-a"


def step_cylinders(holes=HOLES, radius_scale=1.0):
    out = []
    for h in holes:
        for z in (0.0, 1.51):
            out.append({"x": h["x"], "y": h["y"], "z": z, "radius_mm": h["diameter_mm"] / 2 * radius_scale})
    return out


def dxf_bytes(lines, circles) -> bytes:
    out = ["0", "SECTION", "2", "HEADER", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for (x1, y1), (x2, y2) in lines:
        out += ["0", "LINE", "8", "Edge.Cuts", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)]
    for x, y, r in circles:
        out += ["0", "CIRCLE", "8", "Edge.Cuts", "10", str(x), "20", str(y), "40", str(r)]
    out += ["0", "ENDSEC", "0", "EOF"]
    return ("\n".join(out) + "\n").encode("utf-8")


def outline_lines(points):
    closed = points + [points[0]]
    return list(zip(closed, closed[1:]))


def hole_circles(holes=HOLES):
    return [(h["x"], h["y"], h["diameter_mm"] / 2) for h in holes]


def excellon_bytes(holes, plated_flag) -> bytes:
    """One file for one plating class, in the KiCad layout. `holes` must all be of that class."""
    table = {}
    body = ["M48", "METRIC,TZ"]
    tools = []
    for h in holes:
        key = h["diameter_mm"]
        if key not in table:
            table[key] = str(len(table) + 1)
            kind = "Plated,PTH,ComponentDrill" if plated_flag else "NonPlated,NPTH,ComponentDrill"
            body += [f"; #@! TA.AperFunction,{kind}", f"T{table[key]}C{key:.3f}"]
            tools.append(key)
    body += ["%", "G90", "G05"]
    for h in holes:
        body += [f"T{table[h['diameter_mm']]}", f"X{h['x']:.3f}Y{h['y']:.3f}"]
    body.append("M30")
    return ("\n".join(body) + "\n").encode("utf-8")


def split_plating(holes):
    pth = [h for h in holes if h["plated"]]
    npth = [h for h in holes if not h["plated"]]
    return excellon_bytes(pth, True), excellon_bytes(npth, False)


class DxfTests(unittest.TestCase):
    def test_dxf_outline_order_does_not_matter(self):
        dxf = F.parse_dxf(dxf_bytes(list(reversed(outline_lines(OUTLINE))), hole_circles()))
        self.assertEqual(F.c01_outline(OUTLINE, dxf)["status"], "pass")

    def test_dxf_mirrored_outline_fails(self):
        mirrored = [(-x, y) for x, y in OUTLINE]
        dxf = F.parse_dxf(dxf_bytes(outline_lines(mirrored), hole_circles()))
        self.assertEqual(F.c01_outline(OUTLINE, dxf)["status"], "fail")

    def test_dxf_arc_entity_is_refused_by_name(self):
        """A slot in the DXF shows as an arc. The entity is refused by name."""
        text = dxf_bytes([], []).decode("utf-8").replace("0\nENDSEC\n0\nEOF", "0\nARC\n8\nEdge.Cuts\n0\nENDSEC\n0\nEOF")
        with self.assertRaises(F.UnsupportedDrill) as ctx:
            F.parse_dxf(text.encode("utf-8"))
        self.assertIn("ARC", str(ctx.exception))

    def test_dxf_circles_match_holes(self):
        dxf = F.parse_dxf(dxf_bytes([], hole_circles()))
        self.assertEqual(F.c02d_dxf_holes(HOLES, dxf)["status"], "pass")
        self.assertEqual(F.c03_diameters(HOLES, dxf, step_cylinders())["status"], "pass")

    def test_dxf_duplicate_circle_fails_count(self):
        dxf = F.parse_dxf(dxf_bytes([], hole_circles() + [hole_circles()[0]]))
        self.assertEqual(F.c02d_dxf_holes(HOLES, dxf)["status"], "fail")

    def test_dxf_wrong_diameter_fails_c03(self):
        bad = [(x, y, r + 0.05) for x, y, r in hole_circles()]
        dxf = F.parse_dxf(dxf_bytes([], bad))
        self.assertEqual(F.c03_diameters(HOLES, dxf, step_cylinders())["status"], "fail")

    def test_c03_step_radius_mismatch_fails(self):
        dxf = F.parse_dxf(dxf_bytes([], hole_circles()))
        self.assertEqual(F.c03_diameters(HOLES, dxf, step_cylinders(radius_scale=1.02))["status"], "fail")


class ExcellonTests(unittest.TestCase):
    def test_plated_flags_read_from_aperture_comments(self):
        pth, npth = split_plating(HOLES)
        p = F.parse_excellon(pth, expect_plated=True)
        n = F.parse_excellon(npth, expect_plated=False)
        self.assertEqual(len(F.excellon_holes(p)), 1)
        self.assertEqual(len(F.excellon_holes(n)), 2)

    def test_c04_passes_for_separate_files(self):
        pth, npth = split_plating(HOLES)
        result = F.c04_plated(HOLES, F.parse_excellon(pth, expect_plated=True),
                              F.parse_excellon(npth, expect_plated=False))
        self.assertEqual(result["status"], "pass")

    def test_c04_fails_when_plated_flag_changes(self):
        changed = [dict(h) for h in HOLES]
        changed[0]["plated"] = True
        pth, npth = split_plating(HOLES)
        result = F.c04_plated(changed, F.parse_excellon(pth, expect_plated=True),
                              F.parse_excellon(npth, expect_plated=False))
        self.assertEqual(result["status"], "fail")

    def test_slot_record_is_refused_by_name(self):
        """Measured form of an oval NPTH slot: G85 with two coordinate pairs. Refused, object named."""
        text = excellon_bytes(HOLES[:2], False).decode("utf-8").replace(
            "M30", "X20.300Y-6.800G85X22.300Y-6.800\nM30")
        with self.assertRaises(F.UnsupportedDrill) as ctx:
            F.parse_excellon(text.encode("utf-8"), expect_plated=False)
        self.assertIn("slot", str(ctx.exception))

    def test_unknown_record_is_refused(self):
        text = excellon_bytes(HOLES[:2], False).decode("utf-8").replace("M30", "G81 Z-1\nM30")
        with self.assertRaises(F.UnsupportedDrill):
            F.parse_excellon(text.encode("utf-8"), expect_plated=False)

    def test_plating_mismatch_within_file_is_refused(self):
        with self.assertRaises(F.UnsupportedDrill):
            F.parse_excellon(excellon_bytes(HOLES[:1], False), expect_plated=True)


class HoleSetTests(unittest.TestCase):
    def test_closed_set_passes_for_complete_set(self):
        centres = [(h["x"], h["y"]) for h in HOLES]
        self.assertEqual(F.closed_set("STEP", centres, centres)["status"], "pass")

    def test_closed_set_fails_for_extra_hole(self):
        centres = [(h["x"], h["y"]) for h in HOLES]
        result = F.closed_set("DXF", centres + [(90.0, 90.0)], centres)
        self.assertEqual(result["status"], "fail")
        self.assertIn("DXF", result["reason"])

    def test_closed_set_fails_for_missing_hole(self):
        centres = [(h["x"], h["y"]) for h in HOLES]
        self.assertEqual(F.closed_set("PTH", centres[:2], centres)["status"], "fail")


class CavityTests(unittest.TestCase):
    def test_outward_cavity_offsets_outline_including_chamfer(self):
        cavity = F.outward_cavity(OUTLINE, 0.5)
        xs = [p[0] for p in cavity]
        self.assertAlmostEqual(max(xs), 56.8, places=6)
        self.assertAlmostEqual(min(xs), -4.2, places=3)

    def test_board_edge_point_is_inside_outward_cavity(self):
        """A point on the board edge lies in the outward cavity. No exemption is needed."""
        cavity = F.outward_cavity(OUTLINE, 0.5)
        self.assertTrue(F.inside_or_on((56.3, 5.0), cavity))

    def test_point_beyond_clearance_is_outside(self):
        cavity = F.outward_cavity(OUTLINE, 0.5)
        self.assertFalse(F.inside_or_on((57.3, 5.0), cavity))

    def test_c09_part_inside_cavity_passes_and_outside_fails(self):
        cavity = F.outward_cavity(OUTLINE, 0.5)
        self.assertEqual(F.c09_cavity("B1", (10.0, 0.0, 0.0, 18.0, 4.0, 2.0), cavity)["status"], "pass")
        self.assertEqual(F.c09_cavity("U9", (57.3, 5.0, 0.0, 59.3, 7.0, 2.0), cavity)["status"], "fail")

    def test_non_convex_outline_refuses(self):
        with self.assertRaises(ValueError):
            F.outward_cavity([(0, 0), (10, 0), (5, 2), (10, 10), (0, 10)], 0.5)


class StepComparisonTests(unittest.TestCase):
    def test_c02_matches_cylinder_centres_once_per_hole(self):
        self.assertEqual(F.c02_step_holes(HOLES, step_cylinders())["status"], "pass")

    def test_c02_fails_for_mirrored_centre(self):
        mirrored = [{"x": -h["x"], "y": h["y"], "z": 0.0, "radius_mm": 1.0} for h in HOLES]
        self.assertEqual(F.c02_step_holes(HOLES, mirrored)["status"], "fail")

    def test_c05_substrate_span_matches_core(self):
        solid = {"valid": True, "bbox": (0.0, 0.0, 0.0, 60.0, 36.0, 1.51), "volume": 1.0}
        self.assertEqual(F.c05_substrate(solid, 1.51)["status"], "pass")

    def test_c05_text_span_is_not_used(self):
        solid = {"valid": True, "bbox": (0.0, 0.0, -0.046, 60.0, 36.0, 1.51), "volume": 1.0}
        self.assertEqual(F.c05_substrate(solid, 1.51)["status"], "fail")

    def test_substrate_selection_refuses_two_solids(self):
        step = {"solids": [
            {"valid": True, "bbox": (0.0, 0.0, 0.0, 60.0, 36.0, 1.51), "volume": 1.0},
            {"valid": True, "bbox": (1.0, 1.0, 0.0, 2.0, 2.0, 1.0), "volume": 0.1}]}
        with self.assertRaises(ValueError):
            F.substrate_solid(step, (0.0, 0.0, 60.0, 36.0))

    def test_c12_origin_equal_to_anchor(self):
        self.assertEqual(F.c12_origin((103.7, 118.2), (103.7, 118.2))["status"], "pass")
        self.assertEqual(F.c12_origin((103.0, 118.2), (103.7, 118.2))["status"], "fail")


class StatusTests(unittest.TestCase):
    KEYS = [("C01", None), ("C08", "B1"), ("C10", None)]

    def test_empty_results_never_pass(self):
        status = F.recompute_status([], self.KEYS)
        self.assertEqual(status["geometry_status"], "fail")
        self.assertTrue(status["missing"])

    def test_missing_reference_is_named(self):
        """R4: a missing B1 result fails by reference, even when every other result passes."""
        status = F.recompute_status([{"id": "C01", "ref": None, "status": "pass", "measured_error_mm": 0.0,
                                      "tolerance_mm": 0.01}], self.KEYS)
        self.assertIn("C08:B1", status["missing"])
        self.assertEqual(status["fit_status"], "fail")

    def test_duplicate_key_refuses(self):
        r = {"id": "C01", "ref": None, "status": "pass", "measured_error_mm": 0.0, "tolerance_mm": 0.01}
        status = F.recompute_status([r, dict(r)], [("C01", None)])
        self.assertTrue(status["duplicates"])

    def test_pass_above_tolerance_is_inconsistent(self):
        r = {"id": "C01", "ref": None, "status": "pass", "measured_error_mm": 0.5, "tolerance_mm": 0.01}
        status = F.recompute_status([r], [("C01", None)])
        self.assertTrue(status["inconsistent"])
        self.assertEqual(status["geometry_status"], "fail")

    def test_unconfirmed_fit_keeps_geometry_pass(self):
        results = [{"id": "C01", "ref": None, "status": "pass", "measured_error_mm": 0.0, "tolerance_mm": 0.01},
                   {"id": "C08", "ref": "B1", "status": "pass", "measured_error_mm": -1.0, "tolerance_mm": 0.01},
                   {"id": "C10", "ref": None, "status": "unconfirmed", "measured_error_mm": None, "tolerance_mm": None}]
        status = F.recompute_status(results, self.KEYS)
        self.assertEqual(status["geometry_status"], "pass")
        self.assertEqual(status["fit_status"], "unconfirmed")


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads((ROOT / "skills" / "pcb-design" / "templates" / "mech-fit-a"
                                    / "export-settings.json").read_text(encoding="utf-8"))

    def test_recorded_switch_set_passes(self):
        self.assertEqual(F.settings_switches_ok(self.settings), [])

    def test_separate_plating_switch_is_required(self):
        bad = json.loads(json.dumps(self.settings))
        bad["drill"]["switches"] = [s for s in bad["drill"]["switches"] if s != "--excellon-separate-th"]
        self.assertTrue(any("separate" in p for p in F.settings_switches_ok(bad)))

    def test_soldermask_in_step_refused(self):
        bad = json.loads(json.dumps(self.settings))
        bad["step_board"]["switches"].append("--include-soldermask")
        self.assertTrue(any("soldermask" in p for p in F.settings_switches_ok(bad)))


class ProxyAssemblyTests(unittest.TestCase):
    def setUp(self):
        import cadquery as cq
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        board = cq.Workplane("XY").box(60, 36, 1.51, centered=False).translate((-3.7, -17.8, 0))
        cq.exporters.export(board, str(self.dir / "board.step"))

    def tearDown(self):
        self.tmp.cleanup()

    def assemble(self, proxies):
        out = self.dir / "fit.step"
        F.build_fit_assembly(self.dir / "board.step", proxies, out)
        return F.read_step(out)

    def test_c06_mating_face_position_and_rotation(self):
        import math as m
        theta, body = 30.0, 4.0
        u = (m.cos(m.radians(theta)), m.sin(m.radians(theta)))
        frame_xy = (20.0, 6.0)
        centre = (frame_xy[0] - u[0] * body / 2, frame_xy[1] - u[1] * body / 2)
        step = self.assemble([{"ref": "CN2", "centre_xy": centre, "size": (body, 9.0, 3.0), "z0": 0.0,
                               "rotation_deg": theta}])
        box = step["solids"][1]["bbox"]
        frame = {"id": "CN2", "x": frame_xy[0], "y": frame_xy[1], "rotation_deg": theta}
        self.assertEqual(F.c06_connector("CN2", frame, theta, step["planes"], box)["status"], "pass")
        moved = dict(frame, x=frame_xy[0] + 0.05)
        self.assertEqual(F.c06_connector("CN2", moved, theta, step["planes"], box)["status"], "fail")

    def test_c06_wrong_rotation_fails(self):
        import math as m
        theta, body = 30.0, 4.0
        u = (m.cos(m.radians(theta)), m.sin(m.radians(theta)))
        frame_xy = (20.0, 6.0)
        centre = (frame_xy[0] - u[0] * body / 2, frame_xy[1] - u[1] * body / 2)
        step = self.assemble([{"ref": "CN2", "centre_xy": centre, "size": (body, 9.0, 3.0), "z0": 0.0,
                               "rotation_deg": theta}])
        box = step["solids"][1]["bbox"]
        frame = {"id": "CN2", "x": frame_xy[0], "y": frame_xy[1], "rotation_deg": 0.0}
        self.assertEqual(F.c06_connector("CN2", frame, theta, step["planes"], box)["status"], "fail")

    def test_c07_other_solid_in_insertion_box_fails_and_is_named(self):
        box = F.make_box((4.0, 9.0, 3.0), (60.0, 6.0), 0.0, 0.0)
        blocker = F.make_box((2.0, 2.0, 2.0), (62.0, 6.0), 0.0, 0.0)
        far = F.make_box((2.0, 2.0, 2.0), (90.0, 30.0), 0.0, 0.0)
        result = F.c07_insertion("CN1", box, [("U7", blocker), ("U8", far)])
        self.assertEqual(result["status"], "fail")
        self.assertIn("U7", result["reason"])
        self.assertNotIn("U8", result["reason"])

    def test_c07_touching_only_passes(self):
        box = F.make_box((4.0, 9.0, 3.0), (60.0, 6.0), 0.0, 0.0)
        touching = F.make_box((2.0, 9.0, 3.0), (63.0, 6.0), 0.0, 0.0)
        self.assertEqual(F.c07_insertion("CN1", box, [("U9", touching)])["status"], "pass")

    def test_c08_bottom_limit_measured_from_mounting_surface(self):
        bottom_surface = -0.045
        ok = F.c08_vertical("B1", "bottom", (0, 0, bottom_surface - 2.8, 1, 1, bottom_surface), 1.555,
                            bottom_surface, 10.0, 4.0)
        bad = F.c08_vertical("B1", "bottom", (0, 0, bottom_surface - 5.0, 1, 1, bottom_surface), 1.555,
                             bottom_surface, 10.0, 4.0)
        self.assertEqual(ok["status"], "pass")
        self.assertEqual(bad["status"], "fail")


class RealExportTests(unittest.TestCase):
    """Retained bytes from the local-image KiCad 10.0.5 export of the fixture."""

    def setUp(self):
        self.src = json.loads((FIX / "fixture-source.json").read_text(encoding="utf-8"))
        self.iface = json.loads((FIX / "board-interface.json").read_text(encoding="utf-8"))

    def expected(self):
        t = M.load_transform(self.iface)
        outline = [M.to_target((x, y), t) for x, y in self.src["outline_kicad_mm"]]
        holes = []
        for h in self.src["holes"]:
            x, y = M.to_target((h["x"], h["y"]), t)
            holes.append({"id": h["id"], "x": x, "y": y, "diameter_mm": h["diameter_mm"], "plated": h["plated"]})
        return outline, holes

    def test_real_separate_drill_files_match_expected_plating(self):
        _, holes = self.expected()
        pth = F.parse_excellon((FIX / "real-export" / "board-PTH.drl").read_bytes(), expect_plated=True)
        npth = F.parse_excellon((FIX / "real-export" / "board-NPTH.drl").read_bytes(), expect_plated=False)
        self.assertEqual(F.c04_plated(holes, pth, npth)["status"], "pass")

    def test_real_dxf_outline_and_holes(self):
        dxf = F.parse_dxf((FIX / "real-export" / "outline.dxf").read_bytes())
        outline, holes = self.expected()
        self.assertEqual(F.c01_outline(outline, dxf)["status"], "pass")
        self.assertEqual(F.c02d_dxf_holes(holes, dxf)["status"], "pass")

    def test_real_step_substrate_and_cylinders(self):
        step = F.read_step(FIX / "real-export" / "board.step")
        outline, holes = self.expected()
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        solid = F.substrate_solid(step, (min(xs), min(ys), max(xs), max(ys)))
        self.assertEqual(F.c05_substrate(solid, self.src["stackup"]["core_mm"])["status"], "pass")
        self.assertEqual(F.c02_step_holes(holes, step["cylinders"])["status"], "pass")


if __name__ == "__main__":
    unittest.main()
