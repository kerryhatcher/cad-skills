# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Acceptance tests for r8 rows 31, 41, 44 and 45 of the B7/B8 package.

Run with: uv run tests/test_pcb_fab_acceptance.py. The KiCad runs use the accepted local image through podman.
The tests create their own projects under a temporary directory. They do not change the accepted fixtures.
"""
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from fab_fixture import fixture_skill

SKILL = fixture_skill(ROOT / "skills" / "pcb-fab-package")
SCRIPTS = SKILL / "scripts"
PROFILE = SKILL / "supplier" / "profiles" / "oshpark-two-layer.yaml"
TEMPLATE = ROOT / "skills" / "pcb-design" / "templates" / "rc-bare-board"
SLOT_BOARD = ROOT / "tests" / "fixtures" / "pcb-design" / "slot.kicad_pcb"
sys.path.insert(0, str(SCRIPTS))
import fab  # noqa: E402
import review  # noqa: E402
import workflow  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f": {detail}"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fresh_project(tmp, label):
    """A copy of the bare-board template with the two-layer profile, as the workflow tests build it."""
    proj = tmp / label
    shutil.copytree(TEMPLATE, proj, ignore=shutil.ignore_patterns("out"))
    shutil.copy2(PROFILE, proj / "manufacturing" / "supplier.yaml")
    prof = json.loads(PROFILE.read_text())
    board = (proj / "board.yaml").read_text()
    board = board.replace("quantity: 5", "quantity: 6").replace("  id: example-two-layer", "  id: oshpark-two-layer")
    board = board.replace("  service: Example two-layer service", "  service: OSH Park two-layer service")
    board = board.replace("  profile_sha256: b37b37495cbab698f921e7b229585ea890cefd7298f3615cd15cec02bb00fb77",
                          f"  profile_sha256: {prof['content_sha256']}")
    board += "\nextensions:\n  fabrication:\n    via_process: standard_through\n"
    (proj / "board.yaml").write_text(board)
    return proj


def run_fab(*args):
    return subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), *args], capture_output=True, text=True)


def observations(proj, profile, release="trial-1"):
    page = next(iter(fab.PROFILE_PAGES[profile["id"]]))
    stored = review.PAGES / f"{page}.html"
    live = proj / "out" / "fab" / "source-review" / "live" / f"{page}.html"
    live.parent.mkdir(parents=True, exist_ok=True)
    live.write_bytes(stored.read_bytes())
    pages = [{"page_id": page, "source_url": profile["extensions"]["evidence_pages"][page]["source_url"],
              "stored_path": f"supplier/pages/{page}.html", "stored_sha256": sha(stored.read_bytes()),
              "live_path": f"out/fab/source-review/live/{page}.html", "live_sha256": sha(live.read_bytes()),
              "retrieved": "2026-11-14"}]
    obs = [{"key": k, "observed_value": v, "observed_unit": u, "observed_condition": "service page statement",
            "source_url": s, "reviewer_reading": "read from the stored page"}
           for k, (v, u, s) in review.fact_items(profile).items()]
    rec = {"schema_id": review.OBS_SCHEMA, "schema_version": 1, "release_id": release,
           "profile_sha256": profile["content_sha256"], "pages": pages, "observations": obs,
           "reviewer": "R. Reviewer", "statement": "Read from the stored supplier page."}
    return json.dumps(rec, indent=2).encode()


def prepared(tmp, label):
    """A project with a design, a supplier run with manual silk evidence, and a source review. Return (proj, review, sha)."""
    proj = fresh_project(tmp, label)
    profile = json.loads(PROFILE.read_text())
    run_fab("design", "--project", str(proj), "--profile", str(PROFILE))
    review_path = proj / "out" / "fab" / "source-review" / "REVIEW.json"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes((json.dumps(review.build_review(observations(proj, profile), profile, PROFILE.read_bytes(),
                                                            "trial-1", proj), indent=2, sort_keys=True) + "\n").encode())
    (review_path.parent / "observations.json").write_bytes(observations(proj, profile))
    art = proj / "out" / "fab" / "manual" / "silk-check.txt"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("silk check\n")
    manual = proj / "out" / "fab" / "manual-record.json"
    manual.write_text(json.dumps({"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
                                  "condition": "silk_line_min_short_text", "result": "pass",
                                  "procedure": "Measured silk strokes", "artifact_path": "out/fab/manual/silk-check.txt",
                                  "artifact_sha256": sha(art.read_bytes()),
                                  "inputs": {"board_sha256": sha((proj / "kicad/board.kicad_pcb").read_bytes()),
                                             "silk_gerber_sha256": sha((proj / "out/fab/design/export/board-F_Silkscreen.gbr").read_bytes())},
                                  "reviewer": "R. Reviewer", "statement": "Manual."}, indent=2, sort_keys=True) + "\n")
    run_fab("supplier", "--project", str(proj), "--profile", str(PROFILE), "--manual", str(manual))
    return proj, review_path, sha(review_path.read_bytes())


_DESIGN = {}


def design_once(tmp):
    """One design run, shared by the tests that read its outputs. Return the project."""
    if "proj" not in _DESIGN:
        proj = fresh_project(tmp, "design-shared")
        code = run_fab("design", "--project", str(proj), "--profile", str(PROFILE)).returncode
        _DESIGN["proj"] = proj
        _DESIGN["code"] = code
    return _DESIGN["proj"], _DESIGN["code"]


def test_row41_worker(tmp):
    """Row 41: the B6 worker refuses an oval or slot drill with exit 2, and the B7 derivative reports supported slots."""
    stage = tmp / "row41"
    (stage / "kicad").mkdir(parents=True)
    shutil.copy2(SLOT_BOARD, stage / "kicad" / "board.kicad_pcb")
    rc_b6, out_b6, _ = workflow.podman(stage, ["/usr/bin/python3", "/worker/board_inventory.py",
                                               "/work/kicad/board.kicad_pcb"], worker=SCRIPTS)
    check("41a: the B6 worker refuses the slot drill with exit 2 and names the object",
          rc_b6 == 2 and "slot or oval drill" in out_b6, (rc_b6, out_b6[-300:]))
    rc_d, out_d, _ = workflow.podman(stage, ["/usr/bin/python3", "/worker/board_inventory_slots.py",
                                             "/work/kicad/board.kicad_pcb"], worker=SCRIPTS)
    inv = json.loads(out_d) if rc_d == 0 else {}
    check("41b: the B7 derivative reports the slot with endpoints, minor and major dimensions",
          rc_d == 0 and len(inv.get("slots", [])) >= 1 and all(
              {"endpoints_mm", "minor_mm", "major_mm"} <= set(s) for s in inv["slots"]), (rc_d, out_d[-300:]))


def test_row44_drawing(tmp):
    """Row 44: a substituted drawing PDF or changed facts are refused before any package is published."""
    proj, code = design_once(tmp)
    check("44 setup: the design run passes (exit 0)", code == 0, code)
    if code != 0:
        return
    design = proj / "out" / "fab" / "design"
    profile = json.loads(PROFILE.read_text())
    reader = workflow.Reader()
    board = (proj / "kicad" / "board.kicad_pcb").read_bytes()
    supplier = (proj / "manufacturing" / "supplier.yaml").read_bytes()
    check("44a: the genuine drawing matches its captured facts",
          workflow.drawing_problem(design, reader, board, profile, supplier) is None,
          workflow.drawing_problem(design, reader, board, profile, supplier))
    check("44b: the stored drawing equals a rebuild from its stored facts",
          fab.drawing_pdf(json.loads((design / "drawing-facts.json").read_text())) == (design / "fabrication-drawing.pdf").read_bytes())
    sub = tmp / "row44-sub"
    shutil.copytree(design, sub)
    (sub / "fabrication-drawing.pdf").write_bytes(b"%PDF-1.4\n% substituted layer PDF\n%%EOF\n")
    problem = workflow.drawing_problem(sub, reader, board, profile, supplier)
    check("44c: a substituted PDF is refused with the drawing reason",
          problem == "the fabrication drawing is not the drawing made from its captured facts", problem)
    sub2 = tmp / "row44-facts"
    shutil.copytree(design, sub2)
    facts = json.loads((sub2 / "drawing-facts.json").read_text())
    facts["overall_width_mm"] = facts["overall_width_mm"] + 1
    (sub2 / "drawing-facts.json").write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
    problem2 = workflow.drawing_problem(sub2, reader, board, profile, supplier)
    check("44d: changed facts are refused with the facts reason",
          problem2 == "the drawing facts differ from the captured board inventory and profile", problem2)
    # Package path: a substituted PDF is refused before publication, with exit 1 and no destination.
    proj2, review_path, rsha = prepared(tmp, "row44-package")
    design2 = proj2 / "out" / "fab" / "design"
    (design2 / "fabrication-drawing.pdf").write_bytes(b"%PDF-1.4\n% substituted layer PDF\n%%EOF\n")
    dest = proj2 / "out" / "fab" / "packages" / "row44"
    try:
        workflow.package(proj2, PROFILE, "trial-1", review_path, dest, design2, proj2 / "out" / "fab" / "supplier", rsha)
        refused, code_pkg, text = False, None, ""
    except workflow.Stop as err:
        refused, code_pkg, text = True, err.code, str(err)
    check("44e: the package refuses the substituted PDF with exit 1 before publication",
          refused and code_pkg == 1 and "not the drawing made from its captured facts" in text and not dest.exists(),
          (refused, code_pkg, text))


def test_row45_facts(tmp):
    """Row 45: the drawing facts equal the captured inventory. The facts come from pcbnew, not a regex parser."""
    proj, code = design_once(tmp)
    if code != 0:
        check("45 setup: the design run passes (exit 0)", False, code)
        return
    design = proj / "out" / "fab" / "design"
    facts = json.loads((design / "drawing-facts.json").read_text())
    inv = json.loads((design / "inventory.json").read_text())
    holes = inv.get("holes", []) + inv.get("slots", [])
    diameters = sorted({h.get("diameter", h.get("minor_mm")) for h in holes})
    check("45a: the hole count in the facts equals the inventory holes and slots",
          facts["holes"]["count"] == len(holes), (facts["holes"]["count"], len(holes)))
    check("45b: the hole diameters in the facts equal the inventory diameters",
          facts["holes"]["diameters_mm"] == diameters, (facts["holes"]["diameters_mm"], diameters))
    check("45c: the facts bind the captured board hash",
          facts["board_sha256"] == sha((proj / "kicad" / "board.kicad_pcb").read_bytes()))
    source = open(fab.__file__, encoding="utf-8").read()
    body = source[source.index("def drawing_facts"):source.index("def _pdf_escape")]
    check("45d: drawing_facts reads no regex object parser", re.search(r"\bre\.", body) is None)


def test_row31_no_maximum(tmp):
    """Row 31: the supplier profile holds no drill maximum. The generated rules hold minimums only."""
    profile = json.loads(PROFILE.read_text())
    maxima = [k for k, v in profile["limits"].items() if v.get("kind") == "maximum" and "drill" in k]
    check("31a: the profile holds no maximum drill limit", maxima == [], maxima)
    rules = workflow.supplier_rules_text(profile)
    check("31b: the generated rules use minimum constraints only", "(min " in rules and "(max " not in rules, rules)
    check("31c: the process note above 250 mil is a note, not a limit",
          "250" in profile["extensions"].get("notes.max_drill", "") and "not a limit" in profile["extensions"]["notes.max_drill"])


def test_row32_quantity(tmp):
    """Row 32: order quantities 1, 2, 3 and 4 through the supplier path. 1, 2 and 4 fail; 3 passes."""
    expected = {1: "fail", 2: "fail", 3: "pass", 4: "fail"}
    for quantity, want in expected.items():
        proj = fresh_project(tmp, f"row32-{quantity}")
        board = (proj / "board.yaml").read_text()
        board = re.sub(r"quantity: \d+", f"quantity: {quantity}", board, count=1)
        (proj / "board.yaml").write_text(board)
        run_fab("design", "--project", str(proj), "--profile", str(PROFILE))
        run_fab("supplier", "--project", str(proj), "--profile", str(PROFILE))
        result = proj / "out" / "fab" / "supplier" / "supplier-result.json"
        rows = {r["condition"]: r for r in json.loads(result.read_text())["rows"]} if result.exists() else {}
        got = rows.get("service.order_multiple", {}).get("status")
        check(f"32: quantity {quantity} gives {want} on service.order_multiple", got == want, got)


HOLE_FIXTURES = ROOT / "tests" / "fixtures" / "pcb-fab-package" / "hole-clearance"
FOUR_LAYER = SKILL / "supplier" / "profiles" / "oshpark-four-layer.yaml"


def hole_findings(tmp, fixture):
    """Run the supplier rule DRC without refill on one fixture. Return the hole_clearance findings and the report."""
    stage = tmp / fixture.stem
    stage.mkdir(parents=True)
    shutil.copy2(HOLE_FIXTURES / fixture, stage / "board.kicad_pcb")
    prof = json.loads(FOUR_LAYER.read_text())
    (stage / "board.kicad_pro").write_text(workflow.effective_pro(b"", prof))
    (stage / "board.kicad_dru").write_text(workflow.supplier_rules_text(prof))
    rc, _, err = workflow.podman(stage, ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json",
                                         "-o", "/work/drc.json", "/work/board.kicad_pcb"])
    report = json.loads((stage / "drc.json").read_text())
    hits = [v for v in report["violations"] if v["type"] == "hole_clearance"]
    actual = sorted({float(re.search(r"actual ([0-9.]+) mm", v["description"]).group(1)) for v in hits})
    return rc, hits, actual


def test_row23_24_hole_clearance(tmp):
    """Rows 23 and 24: a different-net copper object on an internal layer at the exact hole distance.

    The measured actual values are compared with the designed gaps. The fixtures are owned and described in README.md."""
    rc, hits, actual = hole_findings(tmp, Path("r24-unconnected-9.9mil.kicad_pcb"))
    check("24a: 9.9 mil unconnected copper fails the hole clearance (exit findings present, actual 0.2515 mm)",
          rc == 0 and len(hits) > 0 and actual == [0.2515], (rc, actual))
    rc, hits, actual = hole_findings(tmp, Path("r24-unconnected-10mil.kicad_pcb"))
    check("24b: 10 mil unconnected copper passes (no hole clearance finding)", rc == 0 and hits == [], actual)
    rc, hits, actual = hole_findings(tmp, Path("r24-unconnected-10.1mil.kicad_pcb"))
    check("24c: 10.1 mil unconnected copper passes (no hole clearance finding)", rc == 0 and hits == [], actual)
    rc, hits, actual = hole_findings(tmp, Path("r23-same-net-0mil.kicad_pcb"))
    check("23a: same-net copper at 0 mil is not a hole clearance finding (connected case)", rc == 0 and hits == [], actual)
    rc, hits, actual = hole_findings(tmp, Path("probe-unconnected-0.2mm.kicad_pcb"))
    check("24d: a deliberately large violation at 0.2 mm is reported with actual 0.2000 mm",
          rc == 0 and actual == [0.2], (rc, actual))
    rc, hits, actual = hole_findings(tmp, Path("r23-zone-internal-plane.kicad_pcb"))
    text = (tmp / "r23-zone-internal-plane" / "board.kicad_pcb").read_text()
    radius = None
    for block in text.split("(filled_polygon")[1:]:
        if '(layer "In1.Cu")' in block.split("(pts")[0]:
            pts = [(float(x), float(y)) for x, y in re.findall(r"\(xy ([-0-9.]+) ([-0-9.]+)\)", block.split("(pts")[1])]
            radius = min(math.hypot(x - 10, y - 10) for x, y in pts)
    polys = radius is not None
    check("23b: the In1.Cu zone cutout around the hole is measured at 0.40799 mm, a gap of 0.25799 mm (pass)",
          rc == 0 and hits == [] and polys and abs(radius - 0.40799) < 1e-4, (actual, radius))


def test_internal_track_boundaries_root(tmp):
    """Rows 23 and 24 use an internal track and a connected internal plane."""
    for mil, expected in (("9.9", [0.2515]), ("10", []), ("10.1", [])):
        fixture = Path(f"r24-internal-track-{mil}mil.kicad_pcb")
        rc, hits, actual = hole_findings(tmp, fixture)
        identified = all(any(item.get("uuid") == "5a1c0000-0000-4000-8000-00000000c0de"
                             and "In1.Cu" in item.get("description", "")
                             for item in hit["items"]) for hit in hits)
        check(f"24 internal track: {mil} mil gives {expected}",
              rc == 0 and actual == expected and identified, (rc, actual, hits))
    fixture = Path("r23-connected-plane-root.kicad_pcb")
    rc, hits, actual = hole_findings(tmp, fixture)
    stage = tmp / fixture.stem
    script = (
        "import pcbnew,json; b=pcbnew.LoadBoard('/work/board.kicad_pcb'); "
        "p=next(p for f in b.GetFootprints() for p in f.Pads()); z=next(iter(b.Zones())); "
        "print(json.dumps({'pad_net':p.GetNetname(),'zone_net':z.GetNetname(),"
        "'contains_center':z.GetFilledPolysList(pcbnew.In1_Cu).Contains(p.GetPosition()),"
        "'connection':int(z.GetPadConnection())}))")
    measured_code, output, _ = workflow.podman(stage, ["python3", "-c", script])
    measured = json.loads(output) if measured_code == 0 else {}
    check("23 connected plane: the same-net filled copper reaches the hole with no clearance finding",
          rc == 0 and not hits and measured == {"pad_net": "N1", "zone_net": "N1",
                                               "contains_center": True, "connection": 2}, measured)


def via_pair_check(tmp, fixture):
    """Report the hole_clearance findings for one via fixture, with the layer and UUID of each copper item.

    The independent gap is the via centre distance minus the hole radius minus the via copper radius, read from the file."""
    rc, hits, actual = hole_findings(tmp, Path(fixture))
    text = (HOLE_FIXTURES / fixture).read_text()
    via_x = float(re.search(r"\(via (?:blind )?\(at ([-0-9.]+) ", text).group(1))
    via_size = float(re.search(r"\(via (?:blind )?\(at [-0-9.]+ [-0-9.]+\)\s+\(size ([-0-9.]+)\)", text).group(1))
    gap = (via_x - 10.0) - 0.15 - via_size / 2
    items = [(i.get("description", ""), i.get("uuid")) for v in hits for i in v["items"]]
    layers = sorted({re.search(r"on ([^\]]+)$", d).group(1) for d, _ in items if " on " in d and "Via" in d or "Blind" in d})
    return rc, hits, actual, gap, items, layers


def test_internal_copper_negative(tmp):
    """The internal-only copper negative (a blind via In1.Cu to In2.Cu) and its outer-layer control.

    Both are measured at the same gap. The internal finding is reported with the layer and UUID of the offending copper."""
    rc, hits, actual, gap, items, layers = via_pair_check(tmp, "internal-blind-via-0.2mm.kicad_pcb")
    uuid_ok = any(u == "5a1c0000-0000-4000-8000-00000000e0de" for _, u in items)
    check("N1: internal-only copper (In1.Cu to In2.Cu) at 0.2 mm is reported by hole_clearance",
          rc == 0 and hits and actual == [0.2] and abs(gap - 0.2) < 1e-6 and uuid_ok and any("In1.Cu - In2.Cu" in d for d, _ in items),
          (rc, actual, gap, items[:2]))
    rc, hits, actual, gap, items, layers = via_pair_check(tmp, "control-outer-via-0.2mm.kicad_pcb")
    check("N2: the outer-layer control at the same gap (F.Cu to B.Cu) is reported with the same actual value",
          rc == 0 and hits and actual == [0.2] and abs(gap - 0.2) < 1e-6 and any("F.Cu - B.Cu" in d for d, _ in items),
          (rc, actual, gap, items[:2]))


def test_row22_package_omissions(tmp):
    """Row 22: a package whose schematic or drawing output is absent is refused with exit 1 and not published.

    The schematic case is refused by the final gate. The drawing case is refused by the drawing check. Neither
    case may end in a traceback. The original projects are not changed."""
    for label, rel in (("schematic", "out/fab/design/export/schematic.pdf"), ("drawing", "out/fab/design/fabrication-drawing.pdf")):
        proj, review_path, rsha = prepared(tmp, f"row22-{label}")
        (proj / rel).unlink()
        dest = proj / "out" / "fab" / "packages" / f"omit-{label}"
        try:
            workflow.package(proj, PROFILE, "trial-1", review_path, dest, proj / "out" / "fab" / "design",
                             proj / "out" / "fab" / "supplier", rsha)
            code = 0
        except workflow.Stop as err:
            code = err.code
        check(f"22: a package without the {label} output exits 1 and publishes nothing",
              code == 1 and not dest.exists(), code)


def test_row36_stored_page_drift(tmp):
    """Row 36: a stored supplier page that differs from its bound hash is refused by the source review."""
    copy = tmp / "row36-skill"
    shutil.copytree(SKILL, copy, ignore=shutil.ignore_patterns("__pycache__"))
    page = copy / "supplier" / "pages" / "two-layer.html"
    page.write_bytes(page.read_bytes() + b"\n<!-- drift -->\n")
    proj = fresh_project(tmp, "row36")
    obs = tmp / "row36-observations.json"
    obs.write_bytes(observations(proj, json.loads(PROFILE.read_text())))
    r = subprocess.run(["uv", "run", "--quiet", str(copy / "scripts" / "fab.py"), "review-source",
                        "--project", str(proj), "--profile", str(copy / "supplier" / "profiles" / "oshpark-two-layer.yaml"),
                        "--release", "trial-1", "--observations", str(obs), "--reviewer", "R. Reviewer",
                        "--out", str(tmp / "row36-review.json")], capture_output=True, text=True)
    check("36: a changed stored page is refused by review-source with exit 1",
          r.returncode == 1 and "differs from its bound hash" in r.stdout + r.stderr, (r.returncode, r.stdout[-200:]))


def test_row26_silk_boundary_judgement():
    """Row 26: the short-text silk minimum is judged at 2.9, 3 and 3.1 mil. This is the judgement only.

    The automatic silk measurement is not claimed. The manual evidence route records the reviewer's result."""
    expected = {"2.9": "fail", "3": "pass", "3.1": "pass"}
    results = {v: fab.judge("minimum", v, "3") for v in expected}
    check("26: the silk minimum judgement is fail at 2.9, pass at 3 and pass at 3.1 mil",
          results == expected, results)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="fab-acceptance-"))
    try:
        test_row31_no_maximum(tmp)
        test_row32_quantity(tmp)
        test_row23_24_hole_clearance(tmp)
        test_internal_copper_negative(tmp)
        test_internal_track_boundaries_root(tmp)
        test_row22_package_omissions(tmp)
        test_row36_stored_page_drift(tmp)
        test_row26_silk_boundary_judgement()
        test_row41_worker(tmp / "r41") if (tmp / "r41").mkdir() is None else None
        test_row44_drawing(tmp)
        test_row45_facts(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\n{passed}/{len(RESULTS)} passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
