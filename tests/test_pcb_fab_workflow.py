# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the design, supplier and package commands, and the strict source review.

Run with: uv run tests/test_pcb_fab_workflow.py. The KiCad runs use the accepted image through podman.
"""
import copy
import os
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "pcb-fab-package"
SCRIPTS = SKILL / "scripts"
PROFILE = SKILL / "supplier" / "profiles" / "oshpark-two-layer.yaml"
TEMPLATE = ROOT / "skills" / "pcb-design" / "templates" / "rc-bare-board"
sys.path.insert(0, str(SCRIPTS))
import fab  # noqa: E402
import review  # noqa: E402
import validate as VAL  # noqa: E402
import project_io  # noqa: E402
import workflow  # noqa: E402
from workflow import STAGE_MARK  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f": {detail}"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fresh_project(tmp, label):
    proj = tmp / label
    shutil.copytree(TEMPLATE, proj, ignore=shutil.ignore_patterns("out"))
    shutil.copy2(PROFILE, proj / "manufacturing" / "supplier.yaml")
    prof = json.loads(PROFILE.read_text())
    board = (proj / "board.yaml").read_text()
    board = board.replace("quantity: 5", "quantity: 6").replace("  id: example-two-layer", "  id: oshpark-two-layer")
    board = board.replace("  service: Example two-layer service", "  service: OSH Park two-layer service")
    board = board.replace("  profile_sha256: b37b37495cbab698f921e7b229585ea890cefd7298f3615cd15cec02bb00fb77",
                          f"  profile_sha256: {prof['content_sha256']}")
    (proj / "board.yaml").write_text(board)
    return proj


def observations(proj, profile, release="trial-1", mutate=None, live_extra=b""):
    page = next(iter(fab.PROFILE_PAGES[profile["id"]]))
    stored = review.PAGES / f"{page}.html"
    live = proj / "out" / "fab" / "source-review" / "live" / f"{page}.html"
    live.parent.mkdir(parents=True, exist_ok=True)
    live.write_bytes(stored.read_bytes() + live_extra)
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
    if mutate:
        mutate(rec)
    return json.dumps(rec, indent=2).encode()


def review_outcome(proj, profile, raw, release="trial-1"):
    try:
        rec = review.build_review(raw, profile, PROFILE.read_bytes(), release, proj)
        return "ok", rec
    except (review.ReviewError, VAL.RecordError) as err:
        return "refused", str(err)


def test_source_review(tmp):
    profile = json.loads(PROFILE.read_text())
    proj = fresh_project(tmp, "review")
    base = observations(proj, profile)
    status, rec = review_outcome(proj, profile, base)
    check("review of the complete, unchanged page is unchanged", status == "ok" and rec["decision"] == "unchanged", rec)
    status, rec = review_outcome(proj, profile, base.replace(b'"release_id": "trial-1"', b'"release_id": "trial-1", "release_id": "x"'))
    check("duplicate key is refused (strict JSON)", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r.update(extra=1)))
    check("unknown top-level key is refused", status == "refused" and "unknown keys" in rec, rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"][0].update(extra=1)))
    check("unknown observation field is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"].append(
        {"key": "no_such_fact", "observed_value": 1, "observed_unit": "mil", "observed_condition": "c",
         "source_url": profile["source_url"], "reviewer_reading": "r"})))
    check("unknown observation key is refused", status == "refused" and "unknown observation key" in rec, rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"][0].update(source_url="https://example.com/x")))
    check("observation with another source URL is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"][0].update(observed_condition="  ")))
    check("empty observed condition is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r.update(statement="bad\u0001")))
    check("control character in the statement is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["pages"][0].update(retrieved="2026-02-30")))
    check("impossible date is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["pages"][0].update(live_path="../escape.html")))
    check("path escape in the live page is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["pages"][0].update(stored_sha256="0" * 64)))
    check("wrong stored hash is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r.update(pages=[])))
    check("an incomplete page set is refused", status == "refused", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"].pop(0)))
    check("a missing observation gives material", status == "ok" and rec["decision"] == "material", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"][0].update(observed_value="7")))
    check("a value of the wrong number gives material", status == "ok" and rec["decision"] == "material", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: r["observations"][0].update(observed_value=6.0)))
    check("a number with the wrong type gives material", status == "ok" and rec["decision"] == "material", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, mutate=lambda r: [o.update(observed_unit="in") for o in r["observations"] if o["key"] == "min_trace"]))
    check("a unit mismatch gives material", status == "ok" and rec["decision"] == "material", rec)
    status, rec = review_outcome(proj, profile, observations(proj, profile, live_extra=b"<!-- changed -->"))
    check("a changed live page with equal facts gives harmless", status == "ok" and rec["decision"] == "harmless", rec)


def test_gate(tmp):
    profile = json.loads(PROFILE.read_text())
    proj = fresh_project(tmp, "gate")
    raw = observations(proj, profile)
    rec = review.build_review(raw, profile, PROFILE.read_bytes(), "trial-1", proj)
    body = (json.dumps(rec, indent=2, sort_keys=True) + "\n").encode()
    expect = sha(body)
    pbytes = PROFILE.read_bytes()
    check("gate passes an intact review", review.gate(proj, profile, pbytes, body, expect, "trial-1") == [])
    check("gate rejects a missing review (omission)", review.gate(proj, profile, pbytes, None, expect, "trial-1") != [])
    check("gate rejects changed review bytes", review.gate(proj, profile, pbytes, body + b" ", expect, "trial-1") != [])
    altered = copy.deepcopy(rec)
    altered["observations"][0]["observed_value"] = "7"
    alt = (json.dumps(altered, indent=2, sort_keys=True) + "\n").encode()
    check("gate rejects altered observations", review.gate(proj, profile, pbytes, alt, sha(alt), "trial-1") != [])
    check("gate rejects another release", review.gate(proj, profile, pbytes, body, expect, "trial-2") != [])
    other = copy.deepcopy(profile)
    other["content_sha256"] = "1" * 64
    check("gate rejects another profile", review.gate(proj, other, pbytes, body, expect, "trial-1") != [])
    check("gate rejects changed profile file bytes", review.gate(proj, profile, pbytes + b" ", body, expect, "trial-1") != [])
    live = proj / "out" / "fab" / "source-review" / "live" / "two-layer.html"
    live.write_bytes(live.read_bytes() + b"x")
    check("gate rejects a live page that differs from the reviewed hash", review.gate(proj, profile, pbytes, body, expect, "trial-1") != [])


def run_fab(*args):
    return subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), *args], capture_output=True, text=True)


def test_design_supplier_package(tmp):
    proj = fresh_project(tmp, "run")
    prof = str(PROFILE)
    p = run_fab("design", "--project", str(proj), "--profile", prof)
    check("design passes on the bare-board template (exit 0)", p.returncode == 0, p.stderr[-300:])
    design = proj / "out" / "fab" / "design"
    check("design writes the exports, inventory and drawing",
          all((design / name).exists() for name in ("export/board-F_Cu.gbr", "export/board-PTH.drl",
                                                    "inventory.json", "fabrication-drawing.pdf", "design-result.json")))
    s = run_fab("supplier", "--project", str(proj), "--profile", prof)
    check("supplier stops at the mandatory manual silk condition (exit 1)", s.returncode == 1, s.stdout[-200:])
    rows = {r["condition"]: r for r in json.loads((proj / "out" / "fab" / "supplier" / "supplier-result.json").read_text())["rows"]}
    check("supplier rows give pass for every KiCad rule", all(rows[k]["status"] == "pass" for k in ("min_trace", "min_space", "min_drill", "edge_keepout")))
    check("supplier silk row is pending", rows["silk_line_min_short_text"]["status"] == "pending")
    check("the supplier mask path writes both mask rows (regression for the returncode defect)", all(k in rows and rows[k]["status"] in ("pass", "fail", "uncertain") for k in ("mask_web_min_top", "mask_web_min_bottom")), sorted(rows))
    dru = (proj / "out" / "fab" / "supplier" / "supplier.kicad_dru").read_text()
    check("generated rule uses the exact trace minimum 0.1524 mm", "(min 0.1524mm)" in dru, dru)
    pkg = proj / "out" / "fab" / "packages" / "unqualified"
    review_path = proj / "out" / "fab" / "source-review" / "REVIEW.json"
    profile = json.loads(PROFILE.read_text())
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes((json.dumps(review.build_review(observations(proj, profile), profile, PROFILE.read_bytes(),
                                                            "trial-1", proj), indent=2, sort_keys=True) + "\n").encode())
    (review_path.parent / "observations.json").write_bytes(observations(proj, profile))
    review_sha = sha(review_path.read_bytes())
    q = run_fab("package", "--project", str(proj), "--profile", prof, "--release", "trial-1",
                "--review", str(review_path), "--review-sha256", review_sha, "--dest", str(pkg))
    check("package without manual silk evidence is unqualified (exit 1)", q.returncode == 1, q.stdout[-200:])
    manual_art = proj / "out" / "fab" / "manual" / "silk-check.txt"
    manual_art.parent.mkdir(parents=True, exist_ok=True)
    manual_art.write_text("Silk short-text check on the saved silk layer.\n")
    rec = {"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1, "condition": "silk_line_min_short_text",
           "result": "pass", "procedure": "Measured short silk strokes and text on the saved silk layer",
           "artifact_path": "out/fab/manual/silk-check.txt", "artifact_sha256": sha(manual_art.read_bytes()),
           "inputs": {"board_sha256": sha((proj / "kicad/board.kicad_pcb").read_bytes()),
                      "silk_gerber_sha256": sha((design / "export/board-F_Silkscreen.gbr").read_bytes())},
           "reviewer": "R. Reviewer", "statement": "Manual measurement on the saved layer."}
    manual = proj / "out" / "fab" / "manual-record.json"
    manual.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    s2 = run_fab("supplier", "--project", str(proj), "--profile", prof, "--manual", str(manual))
    check("supplier with current manual evidence passes (exit 0)", s2.returncode == 0, s2.stdout[-200:])
    stale = copy.deepcopy(rec)
    stale["inputs"]["board_sha256"] = "0" * 64
    manual.write_text(json.dumps(stale, indent=2, sort_keys=True) + "\n")
    s3 = run_fab("supplier", "--project", str(proj), "--profile", prof, "--manual", str(manual))
    check("stale manual evidence is refused (exit 1)", s3.returncode == 1, s3.stdout[-200:] + s3.stderr[-200:])
    manual.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    run_fab("supplier", "--project", str(proj), "--profile", prof, "--manual", str(manual))
    pkg2 = proj / "out" / "fab" / "packages" / "qualified"
    q2 = run_fab("package", "--project", str(proj), "--profile", prof, "--release", "trial-1",
                 "--review", str(review_path), "--review-sha256", review_sha, "--dest", str(pkg2))
    check("package with every condition passing is qualified (exit 0)", q2.returncode == 0, q2.stdout[-300:])
    manifest = json.loads((pkg2 / "manifest.json").read_text())
    check("qualified manifest has no reasons", manifest["status"] == "qualified" and manifest["reasons"] == [])
    gerber = pkg2 / "gerber" / "board-F_Cu.gbr"
    gerber.write_text(gerber.read_text() + "\n")
    _, report = VAL.build_report([str(pkg2 / "manifest.json")], SKILL / "contracts" / "schemas", proj, pkg2)
    check("the validator detects a changed output after qualification", bool(report["findings"]), report.get("findings"))
    review_path.write_bytes(review_path.read_bytes() + b" ")
    q3 = run_fab("package", "--project", str(proj), "--profile", prof, "--release", "trial-1",
                 "--review", str(review_path), "--review-sha256", review_sha,
                 "--dest", str(proj / "out" / "fab" / "packages" / "tampered"))
    check("a changed review record makes the package unqualified (exit 1)", q3.returncode == 1, q3.stdout[-200:])




def test_semantic_export_checks(tmp):
    import semantics as SM
    contract = {"layers": [{"kicad_layer": "F.Cu", "suffix": "-F_Cu.gbr"}, {"kicad_layer": "B.Cu", "suffix": "-B_Cu.gbr"}]}
    d = tmp / "semantic"
    d.mkdir()
    (d / "board-F_Cu.gbr").write_text("G04 #@! TF.FileFunction,Copper,L1,Top*\n")
    (d / "board-B_Cu.gbr").write_text("G04 #@! TF.FileFunction,Copper,L2,Bot*\n")
    check("functions of a correct copper pair pass", SM.function_problems(contract, d, ["F.Cu", "B.Cu"]) == [])
    (d / "board-B_Cu.gbr").write_text("G04 #@! TF.FileFunction,Copper,L2,Bot*\nG04 #@! TF.FileFunction,Copper,L2,Bot*\n")
    check("a duplicate declaration is a problem", any("3" in p or "declares its function" in p for p in SM.function_problems(contract, d, ["F.Cu", "B.Cu"])))
    (d / "board-B_Cu.gbr").write_text("G04 #@! TF.FileFunction,Copper,L1,Top*\n")
    check("swapped copper layers are a problem", bool(SM.function_problems(contract, d, ["F.Cu", "B.Cu"])))
    (d / "board-B_Cu.gbr").write_text("%TF.FileFunction,Copper,L2,Bot*%\n")
    check("active X2 attributes are a problem", any("X2" in p for p in SM.function_problems(contract, d, ["F.Cu", "B.Cu"])))
    inv = {"holes": [{"attr": "pth", "x": 1.0, "y": 2.0, "diameter": 0.3}], "copper_layers": ["F.Cu", "B.Cu"]}
    (d / "board-PTH.drl").write_text(drill_text(1000, -2000, 300))
    (d / "board-NPTH.drl").write_text("M48\nMETRIC,TZ\nFMAT,2\n%\nG90\nG05\nM30\n")
    check("the drill multiset matches the board", SM.drill_problems(inv, d) == [], SM.drill_problems(inv, d))
    (d / "board-PTH.drl").write_text(drill_text(1100, -2000, 300))
    check("a changed drill coordinate with an equal count is a problem", bool(SM.drill_problems(inv, d)))
    (d / "board-PTH.drl").write_text(drill_text(1000, -2000, 350))
    check("a changed drill diameter with an equal count is a problem", bool(SM.drill_problems(inv, d)))
    (d / "board-PTH.drl").write_text(drill_text(1000, -2000, 300).replace("M30\n", "M30\nX1000Y1000\n"))
    check("a drill file with a record after M30 is a problem", any("unsupported" in p for p in SM.drill_problems(inv, d)))


def drill_text(x=1000, y=-2000, w=300):
    """A minimal drill file in the measured form: one hole at (x, y) micrometres, tool width w micrometres."""
    return ("M48\nMETRIC,TZ\nFMAT,2\nT1C%d.%03d\n%%\nG90\nG05\nT1\nX%dY%d\nG05\nM30\n"
            % (w // 1000, w % 1000, x, y))


def test_negative_workflow(tmp):
    profile = json.loads(PROFILE.read_text())
    proj = fresh_project(tmp, "neg")
    (proj / "board.yaml").write_text((proj / "board.yaml").read_text().replace("quantity: 6", "quantity: 5"))
    src_dru = proj / "kicad" / "board.kicad_dru"
    src_dru.write_text('(version 1)\n(rule "source_keep" (constraint clearance (min 0.2mm)))\n')
    prof = str(PROFILE)
    dsg = run_fab("design", "--project", str(proj), "--profile", prof)
    check("design runs before the quantity test", dsg.returncode == 0, dsg.returncode)
    s = run_fab("supplier", "--project", str(proj), "--profile", prof)
    check("the supplier result stops on a quantity of 5 (exit 1 or 2, not a pass)", s.returncode in (1, 2), s.returncode)
    if s.returncode in (1, 2):
        pass
    gen = proj / "out" / "fab" / "supplier" / "supplier.kicad_dru"
    check("source rules are preserved before the generated rules", gen.is_file() and "source_keep" in gen.read_text(), "missing")
    lock = proj / "toolchain.lock.json"
    lock.write_text(lock.read_text().replace("sha256:b2731833711a", "sha256:0000000000aa"))
    d = run_fab("design", "--project", str(proj), "--profile", prof)
    check("a wrong image identity is refused (exit 2)", d.returncode == 2, d.stdout[-200:] + d.stderr[-200:])


def test_pipeline_rules(tmp):
    """Runtime identity, input snapshots with absence, staleness at package time, and the stage marker."""
    proj = fresh_project(tmp, "rules")
    prof = str(PROFILE)
    lock = json.loads((proj / "toolchain.lock.json").read_text())
    d = run_fab("design", "--project", str(proj), "--profile", prof)
    check("design passes on the rules project (exit 0)", d.returncode == 0, d.stderr[-200:])
    design_result = json.loads((proj / "out" / "fab" / "design" / "design-result.json").read_text())
    check("the design result records the measured image identity, not the tag",
          design_result["runtime"]["image_id"] == lock["container"]["digest"], design_result["runtime"])
    check("an absent optional source rule is recorded as absent",
          design_result["source_sha256"].get("kicad/board.kicad_dru") == "absent", design_result["source_sha256"].get("kicad/board.kicad_dru"))
    check("a present source file is recorded by its hash",
          len(design_result["source_sha256"].get("kicad/board.kicad_pcb", "")) == 64)
    unmarked = tmp / "unmarked"
    shutil.copytree(proj, unmarked)
    (unmarked / "out" / "fab" / "design" / "work" / ".pcb-fab-stage").unlink(missing_ok=True)
    d2 = run_fab("design", "--project", str(unmarked), "--profile", prof)
    check("an unmarked stage is refused, not removed (exit 2)", d2.returncode == 2, (d2.returncode, d2.stderr[-200:]))
    s = run_fab("supplier", "--project", str(proj), "--profile", prof)
    review_path = proj / "out" / "fab" / "source-review" / "REVIEW.json"
    profile = json.loads(PROFILE.read_text())
    if not review_path.is_file():
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_bytes((json.dumps(review.build_review(observations(proj, profile), profile, PROFILE.read_bytes(),
                                                                "trial-1", proj), indent=2, sort_keys=True) + "\n").encode())
        (review_path.parent / "observations.json").write_bytes(observations(proj, profile))
    art = proj / "out" / "fab" / "manual" / "silk-check.txt"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("silk check\n")
    manual = proj / "out" / "fab" / "manual-record.json"
    rec = {"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1, "condition": "silk_line_min_short_text",
           "result": "pass", "procedure": "Measured silk strokes on the saved layer",
           "artifact_path": "out/fab/manual/silk-check.txt", "artifact_sha256": sha(art.read_bytes()),
           "inputs": {"board_sha256": sha((proj / "kicad/board.kicad_pcb").read_bytes()),
                      "silk_gerber_sha256": sha((proj / "out/fab/design/export/board-F_Silkscreen.gbr").read_bytes())},
           "reviewer": "R. Reviewer", "statement": "Manual measurement."}
    manual.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    s2 = run_fab("supplier", "--project", str(proj), "--profile", prof, "--manual", str(manual))
    check("supplier with current manual evidence passes (exit 0)", s2.returncode == 0, s2.stdout[-200:])
    rsha = sha(review_path.read_bytes())
    q = run_fab("package", "--project", str(proj), "--profile", prof, "--release", "trial-1",
                "--review", str(review_path), "--review-sha256", rsha, "--dest", str(proj / "out" / "fab" / "packages" / "fresh"))
    check("package of current inputs is qualified (exit 0)", q.returncode == 0, q.stdout[-200:])
    (proj / "kicad" / "board.kicad_sch").write_bytes((proj / "kicad" / "board.kicad_sch").read_bytes() + b"\n")
    q2 = run_fab("package", "--project", str(proj), "--profile", prof, "--release", "trial-1",
                 "--review", str(review_path), "--review-sha256", rsha, "--dest", str(proj / "out" / "fab" / "packages" / "stale"))
    m = json.loads((proj / "out" / "fab" / "packages" / "stale" / "manifest.json").read_text()) if (proj / "out" / "fab" / "packages" / "stale" / "manifest.json").is_file() else {"status": "missing", "reasons": []}
    stale = any("stale" in r["text"] for r in m["reasons"])
    check("a source changed after the design run makes the package unqualified and stale (exit 1)", q2.returncode == 1 and stale and m["status"] == "draft", (q2.returncode, m["reasons"]))


def _first_track_marker(pcb_text):
    """The straight-track midpoint in nanometres of the first track segment (the marker of the measured exclusion)."""
    sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))
    import sexp  # test-only parser (the accepted B6 S-expression reader)

    def walk(node):
        if isinstance(node, list):
            if node and node[0] == "segment":
                return node
            for child in node:
                found = walk(child)
                if found is not None:
                    return found
        return None
    seg = walk(sexp.parse(pcb_text))
    start = [c for c in seg if c[0] == "start"][0]
    end = [c for c in seg if c[0] == "end"][0]
    uuid = [c for c in seg if c[0] == "uuid"][0][1]
    sx, sy, ex, ey = (round(float(v) * 1e6) for v in (start[1], start[2], end[1], end[2]))
    return (sx + ex) // 2, (sy + ey) // 2, uuid


def test_row_15a(tmp):
    """Row 15a: the ignore severity and the effective exclusion are separate cases. Each one leaves the supplier violation."""
    proj = fresh_project(tmp, "row15a")
    pcb = proj / "kicad" / "board.kicad_pcb"
    pcb.write_text(pcb.read_text().replace("(width 0.25)", "(width 0.1)"))
    mx, my, uuid = _first_track_marker(pcb.read_text())
    pro_path = proj / "kicad" / "board.kicad_pro"
    base_pro = json.loads(pro_path.read_text())
    prof = str(PROFILE)
    run_fab("design", "--project", str(proj), "--profile", prof)
    nil = "00000000-0000-0000-0000-000000000000"
    cases = {
        "ignore": {"rule_severities": {"track_width": "ignore"}},
        "exclusion": {"drc_exclusions": [[f"track_width|{mx}|{my}|{uuid}|{nil}", "row 15a effective exclusion"]]},
    }
    source_pcb = sha(pcb.read_bytes())
    for label, settings in cases.items():
        pro = copy.deepcopy(base_pro)
        ds = pro.setdefault("board", {}).setdefault("design_settings", {})
        ds.update({k: v for k, v in settings.items() if k != "rule_severities"})
        if "rule_severities" in settings:
            ds.setdefault("rule_severities", {}).update(settings["rule_severities"])
        pro_bytes = (json.dumps(pro, indent=2) + "\n").encode()
        pro_path.write_bytes(pro_bytes)
        run_fab("design", "--project", str(proj), "--profile", prof)
        design_drc = json.loads((proj / "out" / "fab" / "design" / "drc.json").read_text())
        target = [v for v in design_drc["violations"] if v["type"] == "track_width"
                  and any(i.get("uuid") == uuid for i in v.get("items", []))]
        if label == "ignore":
            check("15a ignore: the source design DRC bytes omit the target track_width finding",
                  not target, target)
        else:
            check("15a exclusion: the source design DRC bytes mark the target track_width finding excluded",
                  len(target) == 1 and target[0].get("excluded") is True, target)
        s = run_fab("supplier", "--project", str(proj), "--profile", prof)
        staged_drc = json.loads((proj / "out" / "fab" / "supplier" / "supplier-drc.json").read_text())
        staged_target = [v for v in staged_drc["violations"] if v["type"] == "track_width"
                         and any(i.get("uuid") == uuid for i in v.get("items", []))]
        check(f"15a {label}: the staged DRC bytes show the target track_width finding active",
              len(staged_target) == 1 and not staged_target[0].get("excluded"), staged_target)
        result = json.loads((proj / "out" / "fab" / "supplier" / "supplier-result.json").read_text())
        rows = {r["condition"]: r for r in result["rows"]}
        check(f"15a {label}: the thin tracks still fail the trace row (measured key track_width)",
              rows["min_trace"]["status"] == "fail" and rows["min_trace"]["violations"] > 0, rows.get("min_trace"))
        staged = json.loads((proj / "out" / "fab" / "supplier" / "supplier.kicad_pro").read_text())["board"]["design_settings"]
        check(f"15a {label}: the staged project clears any exclusion", "drc_exclusions" not in staged)
        check(f"15a {label}: the staged project sets the track_width severity to error",
              staged.get("rule_severities", {}).get("track_width") == "error", staged.get("rule_severities"))
        check(f"15a {label}: the source files keep their bytes", pro_path.read_bytes() == pro_bytes and sha(pcb.read_bytes()) == source_pcb)
        check(f"15a {label}: the supplier run is not clean (exit 1)", s.returncode == 1, s.returncode)


def test_snapshot_once(tmp):
    """W1: a source changed after the capture must not change the staged bytes or the recorded hash."""
    proj = tmp / "w1" / "project"
    for rel in workflow.SOURCE_FILES:
        (proj / rel).parent.mkdir(parents=True, exist_ok=True)
        (proj / rel).write_bytes(b"original bytes\n")
    board = proj / "kicad/board.kicad_pcb"
    stage = tmp / "w1" / "stage"
    original = workflow.captured

    def capture_then_change(project, extra=None):
        data = original(project, extra)
        board.write_bytes(b"changed after the capture\n")
        return data

    workflow.captured = capture_then_change
    try:
        recorded = workflow.stage_project(proj, stage)
    finally:
        workflow.captured = original
    staged = (stage / "kicad/board.kicad_pcb").read_bytes()
    check("W1: the staged bytes are the captured bytes", staged == b"original bytes\n", staged)
    check("W1: the recorded hash matches the staged bytes",
          recorded["kicad/board.kicad_pcb"] == sha(staged), recorded["kicad/board.kicad_pcb"])
    check("W1: the current source (changed) is not substituted for the snapshot",
          sha(board.read_bytes()) != recorded["kicad/board.kicad_pcb"])


def test_report_keys(tmp):
    """W2: a finding is counted under its KiCad report key, and the report keys get the error severity."""
    counts = {"drill_out_of_range": 2, "copper_edge_clearance": 1, "track_width": 0}
    check("W2: drill_out_of_range findings count for the minimum drill rule",
          workflow.violations_for(counts, "min_drill") == 2, workflow.violations_for(counts, "min_drill"))
    check("W2: copper_edge_clearance findings count for the edge keepout rule",
          workflow.violations_for(counts, "edge_keepout") == 1, workflow.violations_for(counts, "edge_keepout"))
    prof = json.loads(PROFILE.read_text())
    pro = json.loads(workflow.effective_pro(b'{"board": {"design_settings": {"drc_exclusions": [["x", "y"]]}}}', prof))
    sev = pro["board"]["design_settings"]["rule_severities"]
    check("W2: the KiCad report keys carry the error severity",
          sev.get("drill_out_of_range") == "error" and sev.get("copper_edge_clearance") == "error", sev)
    check("W2: the staged project clears the exclusion", "drc_exclusions" not in pro["board"]["design_settings"])


def test_binding_and_lock(tmp):
    """Four-part correction: bindings, lock, confined nested links, changed artifacts before publication."""
    base = fresh_project(tmp, "base")
    prof = str(PROFILE)
    profile = json.loads(PROFILE.read_text())
    run_fab("design", "--project", str(base), "--profile", prof)
    run_fab("supplier", "--project", str(base), "--profile", prof)
    review_path = base / "out" / "fab" / "source-review" / "REVIEW.json"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes((json.dumps(review.build_review(observations(base, profile), profile, PROFILE.read_bytes(),
                                                            "trial-1", base), indent=2, sort_keys=True) + "\n").encode())
    (review_path.parent / "observations.json").write_bytes(observations(base, profile))
    art = base / "out" / "fab" / "manual" / "silk-check.txt"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("silk check\n")
    manual = base / "out" / "fab" / "manual-record.json"
    manual.write_text(json.dumps({"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
                                  "condition": "silk_line_min_short_text", "result": "pass",
                                  "procedure": "Measured silk strokes", "artifact_path": "out/fab/manual/silk-check.txt",
                                  "artifact_sha256": sha(art.read_bytes()),
                                  "inputs": {"board_sha256": sha((base / "kicad/board.kicad_pcb").read_bytes()),
                                             "silk_gerber_sha256": sha((base / "out/fab/design/export/board-F_Silkscreen.gbr").read_bytes())},
                                  "reviewer": "R. Reviewer", "statement": "Manual."}, indent=2, sort_keys=True) + "\n")
    run_fab("supplier", "--project", str(base), "--profile", prof, "--manual", str(manual))
    rsha = sha(review_path.read_bytes())

    def variant(label, mutate):
        proj = tmp / label
        shutil.copytree(base, proj, symlinks=True)
        mutate(proj)
        dest = proj / "out" / "fab" / "packages" / label
        p = run_fab("package", "--project", str(proj), "--profile", prof, "--release", "trial-1",
                    "--review", str(proj / "out/fab/source-review/REVIEW.json"), "--review-sha256", rsha, "--dest", str(dest))
        reasons = json.loads((dest / "manifest.json").read_text())["reasons"] if (dest / "manifest.json").is_file() else []
        return p.returncode, [r["text"] for r in reasons]

    code, reasons = variant("clean", lambda p: None)
    check("binding: the unchanged project qualifies (exit 0)", code == 0, (code, reasons))
    code, reasons = variant("raw_report", lambda p: (p / "out/fab/design/export/board-F_Cu.gbr").write_text("changed\n"))
    check("binding: a changed raw export before packaging is refused (exit 1)",
          code == 1 and any("changed after its binding" in r for r in reasons), (code, reasons))
    code, reasons = variant("tamper", lambda p: (p / "out/fab/design/design-binding.json").write_text("{}\n"))
    check("binding: a tampered binding file is not bound by the result (exit 1)",
          code == 1 and any("does not bind" in r for r in reasons), (code, reasons))
    code, reasons = variant("artifact", lambda p: (p / "out/fab/manual/silk-check.txt").write_text("changed\n"))
    check("binding: a changed manual artifact is refused (exit 1)",
          code == 1 and any("manual artifact changed" in r for r in reasons), (code, reasons))
    locked = tmp / "locked"
    shutil.copytree(base, locked, symlinks=True)
    (locked / ".cad-skills.lock").write_text("not a lock record\n")
    d = run_fab("design", "--project", str(locked), "--profile", prof)
    check("lock: a held project lock stops the design (exit 2)", d.returncode == 2, (d.returncode, d.stderr[-200:]))
    linked = tmp / "linked"
    shutil.copytree(base, linked, symlinks=True)
    outside = tmp / "outside-target"
    outside.mkdir()
    shutil.rmtree(linked / "out" / "fab" / "design")
    os.symlink(outside, linked / "out" / "fab" / "design")
    d2 = run_fab("design", "--project", str(linked), "--profile", prof)
    check("confinement: a nested output link is refused (exit 2) and nothing is written outside",
          d2.returncode == 2 and not any(outside.iterdir()), (d2.returncode, d2.stderr[-200:], list(outside.iterdir())))


def test_product_keys(tmp):
    """Decision 4 product results: a sub-minimum drill and a copper item inside the edge limit, each named by its report key."""
    proj = fresh_project(tmp, "keys")
    pcb = proj / "kicad" / "board.kicad_pcb"
    text = pcb.read_text()
    via_old = "(at 127.5 106)\n\t\t(size 0.6)\n\t\t(drill 0.3)"
    check("keys: the fixture via is present", text.count(via_old) == 1)
    text = text.replace(via_old, "(at 127.5 106)\n\t\t(size 0.6)\n\t\t(drill 0.2)")
    edge_uuid = "6f1c2a7e-0d2b-4c3a-9e8f-1a2b3c4d5e6f"
    edge_track = (f'\t(segment\n\t\t(start 100.1 105)\n\t\t(end 100.1 110)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n'
                  f'\t\t(net "/GND")\n\t\t(uuid "{edge_uuid}")\n\t)\n')
    text = text.replace("\t(gr_rect\n", edge_track + "\t(gr_rect\n", 1)
    pcb.write_text(text)
    prof = str(PROFILE)
    run_fab("design", "--project", str(proj), "--profile", prof)
    s = run_fab("supplier", "--project", str(proj), "--profile", prof)
    drc = json.loads((proj / "out" / "fab" / "supplier" / "supplier-drc.json").read_text())
    by_type = {}
    for v in drc["violations"]:
        by_type.setdefault(v["type"], []).append(v)
    drill_items = by_type.get("drill_out_of_range", [])
    edge_items = by_type.get("copper_edge_clearance", [])
    check("keys: the sub-minimum drill is reported as drill_out_of_range on the fixture via",
          any(any(i.get("uuid") == "2ef3b910-7b1d-5ece-8898-a1004dc84af3" for i in v.get("items", [])) for v in drill_items), drill_items[:1])
    check("keys: the track inside the edge limit is reported as copper_edge_clearance on the fixture track",
          any(any(i.get("uuid") == edge_uuid for i in v.get("items", [])) for v in edge_items), edge_items[:1])
    rows = {r["condition"]: r for r in json.loads((proj / "out" / "fab" / "supplier" / "supplier-result.json").read_text())["rows"]}
    check("keys: the min_drill row fails through drill_out_of_range", rows["min_drill"]["status"] == "fail" and rows["min_drill"]["violations"] >= 1, rows.get("min_drill"))
    check("keys: the edge_keepout row fails through copper_edge_clearance", rows["edge_keepout"]["status"] == "fail" and rows["edge_keepout"]["violations"] >= 1, rows.get("edge_keepout"))
    check("keys: the supplier run is not clean (exit 1)", s.returncode == 1, s.returncode)


def test_captured_child_link(tmp):
    """C1: a link at the captured-profile child path causes no write outside the project."""
    proj = tmp / "c1" / "project"
    (proj / "out" / "fab" / "design").mkdir(parents=True)
    outside = tmp / "c1" / "outside"
    outside.mkdir(parents=True)
    os.symlink(outside, proj / "out" / "fab" / "design" / "captured")
    try:
        workflow.profile_from_bytes(proj, PROFILE.read_bytes(), proj / "out" / "fab" / "design" / "captured")
        check("C1: a link at the captured child path is refused", False, "accepted")
    except workflow.Stop as err:
        check("C1: a link at the captured child path is refused", err.code == 2, str(err))
    check("C1: no file is written outside the project", not any(outside.iterdir()), list(outside.iterdir()))


def test_manual_original(tmp):
    """C3: a byte-only change to the original manual record after measurement makes the package unqualified."""
    base = fresh_project(tmp, "c3")
    prof = str(PROFILE)
    profile = json.loads(PROFILE.read_text())
    run_fab("design", "--project", str(base), "--profile", prof)
    review_path = base / "out" / "fab" / "source-review" / "REVIEW.json"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes((json.dumps(review.build_review(observations(base, profile), profile, PROFILE.read_bytes(),
                                                            "trial-1", base), indent=2, sort_keys=True) + "\n").encode())
    (review_path.parent / "observations.json").write_bytes(observations(base, profile))
    art = base / "out" / "fab" / "manual" / "silk-check.txt"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("silk check\n")
    manual = base / "out" / "fab" / "manual-record.json"
    manual.write_text(json.dumps({"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
                                  "condition": "silk_line_min_short_text", "result": "pass",
                                  "procedure": "Measured silk strokes", "artifact_path": "out/fab/manual/silk-check.txt",
                                  "artifact_sha256": sha(art.read_bytes()),
                                  "inputs": {"board_sha256": sha((base / "kicad/board.kicad_pcb").read_bytes()),
                                             "silk_gerber_sha256": sha((base / "out/fab/design/export/board-F_Silkscreen.gbr").read_bytes())},
                                  "reviewer": "R. Reviewer", "statement": "Manual."}, indent=2, sort_keys=True) + "\n")
    run_fab("supplier", "--project", str(base), "--profile", prof, "--manual", str(manual))
    manual.write_bytes(manual.read_bytes() + b"\n")
    rsha = sha(review_path.read_bytes())
    dest = base / "out" / "fab" / "packages" / "c3"
    p = run_fab("package", "--project", str(base), "--profile", prof, "--release", "trial-1",
                "--review", str(review_path), "--review-sha256", rsha, "--dest", str(dest))
    reasons = [r["text"] for r in json.loads((dest / "manifest.json").read_text())["reasons"]] if (dest / "manifest.json").is_file() else []
    check("C3: a byte-only change to the original manual record makes the package unqualified (exit 1)",
          p.returncode == 1 and any("original manual record changed" in r for r in reasons), (p.returncode, reasons))


def prepared(tmp, label):
    """A project with a design, a supplier run with manual evidence, and a source review. Return (proj, review, sha)."""
    proj = fresh_project(tmp, label)
    prof = str(PROFILE)
    profile = json.loads(PROFILE.read_text())
    run_fab("design", "--project", str(proj), "--profile", prof)
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
    run_fab("supplier", "--project", str(proj), "--profile", prof, "--manual", str(manual))
    return proj, review_path, sha(review_path.read_bytes())


def package_in_process(proj, review_path, rsha, dest):
    """Run the package command in this process, so that a test can hook its steps. Return (exit, manifest)."""
    return workflow.package(proj, PROFILE, "trial-1", review_path, dest, proj / "out" / "fab" / "design",
                            proj / "out" / "fab" / "supplier", rsha)


def test_interrupted_binding(tmp):
    """C7: a run stops after the new binding write and before the new result write. The old result cannot pass."""
    proj, review_path, rsha = prepared(tmp, "c7")
    design = proj / "out" / "fab" / "design"
    old_result = (design / "design-result.json").read_bytes()
    old_binding = (design / "design-binding.json").read_bytes()
    board_yaml = proj / "board.yaml"
    board_yaml.write_bytes(board_yaml.read_bytes() + b"# a change before the interrupted run\n")
    original_write = workflow.write_result

    def interrupt(path, record):
        raise RuntimeError("interrupted after the binding write")

    workflow.write_result = interrupt
    interrupted = False
    try:
        workflow.design(proj, PROFILE, design)
    except RuntimeError:
        interrupted = True
    finally:
        workflow.write_result = original_write
    check("C7: the run stops after the new binding write", interrupted, interrupted)
    check("C7: the new binding is written", (design / "design-binding.json").read_bytes() != old_binding)
    check("C7: the old result is kept, because the new result is not written",
          (design / "design-result.json").read_bytes() == old_result)
    check("C7: the interrupted run releases the project lock", not (proj / ".cad-skills.lock").exists())
    dest = proj / "out" / "fab" / "packages" / "c7"
    code, reasons = 0, []
    try:
        code, manifest = package_in_process(proj, review_path, rsha, dest)
        reasons = [r["text"] for r in manifest["reasons"]]
    except workflow.Stop as err:
        code, reasons = err.code, [str(err)]
    check("C7: the old design result cannot pass against the new binding (not qualified)",
          code != 0 and any("does not bind the current design-binding.json" in r for r in reasons), (code, reasons))


def test_copy_change(tmp):
    """A controlled change to a source artifact between its capture and its copy makes the package a draft.

    The manifest keeps the hash of the bytes that were copied, not the measured hash."""
    proj, review_path, rsha = prepared(tmp, "copy")
    gerber = proj / "out" / "fab" / "design" / "export" / "board-F_Cu.gbr"
    injected = b"injected copper bytes, not measured\n"
    original_gate = review.gate

    def gate_then_inject(*args, **kwargs):
        result = original_gate(*args, **kwargs)  # runs before the copies
        gerber.write_bytes(injected)
        return result

    review.gate = gate_then_inject
    try:
        code, manifest = package_in_process(proj, review_path, rsha, proj / "out" / "fab" / "packages" / "copy")
    finally:
        review.gate = original_gate
    reasons = [r["text"] for r in manifest["reasons"]]
    entry = next(o for o in manifest["outputs"] if o["path"] == "gerber/board-F_Cu.gbr")
    check("copy: the changed copper Gerber is refused (exit 1, draft)",
          code == 1 and manifest["status"] == "draft", (code, manifest["status"]))
    check("copy: the reason names the changed copy", any("gerber/board-F_Cu.gbr changed after its measurement" in r for r in reasons), reasons)
    check("copy: the manifest hash is the hash of the bytes that were copied", entry["sha256"] == sha(injected), entry["sha256"])


def test_final_gate(tmp):
    """A change after the manifest is prepared fails the final freshness gate before publication."""
    proj, review_path, rsha = prepared(tmp, "final-gate")
    gerber = proj / "out" / "fab" / "design" / "export" / "board-F_Cu.gbr"
    original_build = workflow.VAL.build_report
    changed = {"done": False}

    def build_then_change(*args, **kwargs):
        result = original_build(*args, **kwargs)  # the manifest is prepared by now
        if not changed["done"]:
            changed["done"] = True
            gerber.write_bytes(b"changed after the manifest\n")
        return result

    workflow.VAL.build_report = build_then_change
    try:
        code, manifest = package_in_process(proj, review_path, rsha, proj / "out" / "fab" / "packages" / "gate")
    finally:
        workflow.VAL.build_report = original_build
    gate = [r["text"] for r in manifest["reasons"] if r["code"] == "pkg.final_gate"]
    check("final gate: a change after the manifest is prepared is refused (exit 1, draft)",
          code == 1 and manifest["status"] == "draft", (code, manifest["status"]))
    check("final gate: the reason is the final freshness gate", any("changed before publication" in r for r in gate), gate)


def test_captured_settings(tmp):
    """The settings are read once. A live change after the capture does not enter the supplier calculation."""
    proj = fresh_project(tmp, "settings")
    run_fab("design", "--project", str(proj), "--profile", str(PROFILE))
    live_pro = proj / "kicad" / "board.kicad_pro"
    captured_pro = b'{"board": {"design_settings": {"rule_severities": {"clearance": "warning"}}}}\n'
    live_pro.write_bytes(captured_pro)
    original = workflow.captured
    state = {"changed": False}

    def capture_then_change(project, extra=None):
        data = original(project, extra)
        if not state["changed"]:
            state["changed"] = True
            live_pro.write_bytes(b'{"changed": "after the capture"}\n')
        return data

    workflow.captured = capture_then_change
    stopped = None
    try:
        workflow.supplier(proj, PROFILE, proj / "out" / "fab" / "supplier", proj / "out" / "fab" / "design")
    except workflow.Stop as err:
        stopped = err
    finally:
        workflow.captured = original
    profile = fab.check_profile(PROFILE)
    staged = (proj / "out" / "fab" / "supplier" / "work" / "kicad" / "board.kicad_pro").read_bytes()
    check("settings: the staged settings are the captured settings, not the live file",
          staged == workflow.effective_pro(captured_pro, profile).encode(), staged[:120])
    check("settings: the run refuses the changed live file (exit 1)",
          stopped is not None and stopped.code == workflow.EXIT_FAIL, stopped)


def test_review_lock(tmp):
    """C4: a held project lock refuses review-source and leaves the existing records unchanged."""
    proj = fresh_project(tmp, "review-lock")
    profile = json.loads(PROFILE.read_text())
    observations_file = tmp / "review-lock-observations.json"
    observations_file.write_bytes(observations(proj, profile))
    review_out = proj / "out" / "fab" / "source-review" / "REVIEW.json"
    review_out.parent.mkdir(parents=True, exist_ok=True)
    previous = review_out.parent / "observations.json"
    previous.write_bytes(b"the previous observations\n")
    args = ["review-source", "--project", str(proj), "--profile", str(PROFILE), "--release", "trial-1",
            "--observations", str(observations_file), "--reviewer", "R. Reviewer", "--out", str(review_out)]
    held = project_io.acquire_lock(proj, "test-holder")
    try:
        p = run_fab(*args)
    finally:
        project_io.release_lock(proj, held["token"])
    check("review lock: a held project lock refuses review-source (exit 2)", p.returncode == 2, (p.returncode, p.stderr[-200:]))
    check("review lock: no review record is written", not review_out.exists())
    check("review lock: the existing observation file is unchanged", previous.read_bytes() == b"the previous observations\n")
    ok = run_fab(*args)
    check("review lock: without a holder, review-source writes the record (exit 0)", ok.returncode == 0 and review_out.is_file(), ok.stderr[-200:])
    check("review lock: the lock is released after review-source", not (proj / ".cad-skills.lock").exists())


def main():
    tmp = Path(tempfile.mkdtemp(prefix="fab-workflow-"))
    try:
        test_source_review(tmp)
        test_gate(tmp)
        test_semantic_export_checks(tmp)
        test_design_supplier_package(tmp)
        test_negative_workflow(tmp)
        test_pipeline_rules(tmp / "rules") if (tmp / "rules").mkdir() is None else None
        test_row_15a(tmp / "r15a") if (tmp / "r15a").mkdir() is None else None
        test_snapshot_once(tmp)
        test_product_keys(tmp / "keys") if (tmp / "keys").mkdir() is None else None
        test_captured_child_link(tmp)
        test_manual_original(tmp / "c3m") if (tmp / "c3m").mkdir() is None else None
        test_report_keys(tmp)
        test_binding_and_lock(tmp / "bind") if (tmp / "bind").mkdir() is None else None
        test_interrupted_binding(tmp)
        test_copy_change(tmp)
        test_final_gate(tmp)
        test_captured_settings(tmp)
        test_review_lock(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\n{passed}/{len(RESULTS)} passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
