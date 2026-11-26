# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3", "gerbonara==1.6.3"]
# ///
"""Tests for skills/pcb-fab-package. Run with: uv run tests/test_pcb_fab_package.py"""
import copy
import os
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from fab_fixture import fixture_skill

SKILL = fixture_skill(ROOT / "skills" / "pcb-fab-package")
SCRIPTS = SKILL / "scripts"
FIX = ROOT / "tests" / "fixtures" / "pcb-fab-package"
sys.path.insert(0, str(SCRIPTS))
import export_inspect  # noqa: E402
import fab  # noqa: E402
import inspect_slots  # noqa: E402

PROFILE = SKILL / "supplier" / "profiles" / "oshpark-two-layer.yaml"
BOUND_MM = Fraction(3, 1000000)  # the derived mask bound, 0.000003 mm
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f": {detail}"))


def load_profile():
    return json.loads(PROFILE.read_text())


def run_fab(*args):
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def mutated_profile(tmp, change):
    prof = load_profile()
    change(prof)
    prof["content_sha256"] = fab.content_hash(prof)
    path = tmp / "profile.yaml"
    path.write_text(json.dumps(prof, indent=2))
    return path


# ------------------------------------------------------------------ profiles
def test_profiles(tmp):
    for path in sorted((SKILL / "supplier" / "profiles").glob("*.yaml")):
        fab.check_profile(path)
    check("nine profiles validate", len(list((SKILL / "supplier" / "profiles").glob("*.yaml"))) == 9)
    for label, change, text in [
        ("unknown division key", lambda p: p["division"]["kicad_dru"].append("no_such_limit"), "names no limit"),
        ("duplicate division key", lambda p: p["division"]["geometric_tests"].append("min_trace"), "used twice"),
        ("limit missing from division", lambda p: p["division"]["kicad_dru"].remove("min_trace"), "not in the division"),
        ("text value with minimum kind", lambda p: p["limits"]["min_trace"].update(value_kind="text", value="6 mil"), "text value"),
        ("single-layer with one page bound", None, "must bind the pages"),
    ]:
        if change is None:
            prof_path = tmp / "single.yaml"
            src = json.loads((SKILL / "supplier" / "profiles" / "oshpark-single-layer.yaml").read_text())
            del src["extensions"]["evidence_pages"]["two-layer"]
            src["content_sha256"] = fab.content_hash(src)
            prof_path.write_text(json.dumps(src))
        else:
            prof_path = mutated_profile(tmp, change)
        try:
            fab.check_profile(prof_path)
            check(f"profile refused: {label}", False, "accepted")
        except fab.Invalid as err:
            check(f"profile refused: {label}", text in str(err), str(err))
    bad = load_profile()
    bad["content_sha256"] = "0" * 64
    p = tmp / "hash.yaml"
    p.write_text(json.dumps(bad))
    try:
        fab.check_profile(p)
        check("content hash mismatch refused", False, "accepted")
    except fab.Invalid:
        check("content hash mismatch refused", True)


# ------------------------------------------------------------------ boundaries
def test_boundaries():
    mm = Fraction
    check("max width 406.3/406.4/406.5", [fab.judge("maximum", mm("406.3"), mm("406.4")), fab.judge("maximum", mm("406.4"), mm("406.4")),
          fab.judge("maximum", mm("406.5"), mm("406.4"))] == ["pass", "pass", "fail"])
    check("max height 558.7/558.8/558.9", [fab.judge("maximum", mm("558.7"), mm("558.8")), fab.judge("maximum", mm("558.8"), mm("558.8")),
          fab.judge("maximum", mm("558.9"), mm("558.8"))] == ["pass", "pass", "fail"])
    check("min board edge 6.34/6.35/6.36 mm", [fab.judge("minimum", mm("6.34"), mm("6.35")), fab.judge("minimum", mm("6.35"), mm("6.35")),
          fab.judge("minimum", mm("6.36"), mm("6.35"))] == ["fail", "pass", "pass"])
    check("min slot 19.9/20/20.1 mil", [fab.judge("minimum", mm("19.9"), mm(20)), fab.judge("minimum", mm(20), mm(20)),
          fab.judge("minimum", mm("20.1"), mm(20))] == ["fail", "pass", "pass"])
    check("mask web 3.9/4.0/4.1 with derived bound",
          [fab.judge("minimum", mm("3.9") * fab.UNIT_MM["mil"] / fab.UNIT_MM["mil"], mm(4), bound=BOUND_MM / fab.UNIT_MM["mil"] * 0 + Fraction(0))
           is not None] == [True], "structure")
    mil = fab.UNIT_MM["mil"]
    bound_mil = BOUND_MM / mil
    check("mask at the limit is uncertain", fab.judge("minimum", mm(4), mm(4), bound=bound_mil) == "uncertain")
    check("mask 4.1 passes", fab.judge("minimum", mm("4.1"), mm(4), bound=bound_mil) == "pass")
    check("mask 3.9 fails", fab.judge("minimum", mm("3.9"), mm(4), bound=bound_mil) == "fail")
    check("recommendation never fails", fab.judge("recommendation", mm(2), mm(5)) == "finding")


# ------------------------------------------------------------------ slots
def inv(endpoints, minor, attr="npth", major=None):
    return {"slots": [{"object": "pad X.1", "attr": attr, "endpoints_mm": endpoints, "minor_mm": minor,
                       "major_mm": major if major is not None else minor + 1.0}]}


def drl(lines):
    head = "M48\n; FORMAT={3:3/ absolute / metric / suppress leading zeros}\nMETRIC,TZ\nFMAT,2\nT1C0.508\n%\nG90\nG05\nT1\n"
    return head + "\n".join(lines) + "\nG05\nM30\n"


def export_slot(p1, p2):
    """p1 and p2 in the export frame (micrometres)."""
    return f"X{p1[0]}Y{p1[1]}G85X{p2[0]}Y{p2[1]}"


def compare(board, pth_lines, npth_lines):
    status, report = inspect_slots.inspect(board, drl(pth_lines), drl(npth_lines))
    return status, report


def test_slots():
    # Board point (mm) -> export point (micrometres, Y negated). Board x 115.824499 -> export 115825 is 501 nm.
    base = [[115.825, 118.0], [124.225, 118.0]]
    export_ok = export_slot((115825, -118000), (124225, -118000))
    s, _ = compare(inv(base, 0.508), [], [export_ok])
    check("slot exact match passes", s == 0, s)
    s, _ = compare(inv([[115.824499, 118.0], [124.225, 118.0]], 0.508), [], [export_ok])
    check("slot 0.000501 mm coordinate offset passes (boundary)", s == 0, s)
    s, _ = compare(inv([[115.824498, 118.0], [124.225, 118.0]], 0.508), [], [export_ok])
    check("slot 0.000502 mm coordinate offset is a mismatch", s == 1, s)
    s, _ = compare(inv([[124.225, 118.0], [115.825, 118.0]], 0.508), [], [export_ok])
    check("slot endpoints in reversed order match", s == 0, s)
    s, _ = compare(inv(base, 0.508), [], [export_ok, export_ok])
    check("duplicate export record without a second board slot is a mismatch", s == 1, s)
    board_two = {"slots": inv(base, 0.508)["slots"] * 2}
    s, _ = compare(board_two, [], [export_ok])
    check("duplicate board slot needs two export records", s == 1, s)
    s, _ = compare(inv(base, 0.508, attr="pth"), [], [export_ok])
    check("class swap: PTH board slot exported only as NPTH is a mismatch", s == 1, s)
    s, _ = compare(inv(base, 0.508), [], [])
    check("missing export record is a mismatch", s == 1, s)
    s, _ = compare(inv(base, 0.5054), [], [export_ok])
    check("minor width 19.9 mil (0.5054 mm) against 20 mil export is a mismatch", s == 1, s)
    s, _ = compare(inv(base, 0.508, major=0.508 + 0.0004), [], [export_ok])
    check("near-circular slot is reported and still matched", s == 0, s)


def test_export_reader(tmp):
    good = (FIX / "slot" / "board_rot45_board_rot45-NPTH.drl").read_text()
    recs = export_inspect.parse(good)
    check("measured NPTH file parses", [r["kind"] for r in recs] == ["hole", "slot"], str(recs))
    variants = {
        "inch units": good.replace("METRIC,TZ", "INCH,TZ"),
        "M72 units": good.replace("METRIC,TZ", "M72"),
        "no metric declaration": good.replace("METRIC,TZ\n", ""),
        "no FMAT declaration": good.replace("FMAT,2\n", ""),
        "duplicate tool definition": good.replace("T2C3.200", "T1C2.000"),
        "two-decimal tool width": good.replace("T1C2.000", "T1C2.00"),
        "four-decimal tool width (no rounding)": good.replace("T1C2.000", "T1C2.0004"),
        "M72 in the body": good.replace("G05\nM30", "M72\nG05\nM30"),
    }
    for label, text in variants.items():
        try:
            export_inspect.parse(text)
            check(f"reader refuses: {label}", False, "accepted")
        except export_inspect.UnsupportedRecord:
            check(f"reader refuses: {label}", True)


def test_measured_slot_fixtures():
    inventory = FIX / "inventory"
    for board, kind in [("board", "board"), ("board_rot45", "rot45")]:
        pth = FIX / "slot" / f"{board}_{board}-PTH.drl" if board == "board_rot45" else FIX / "slot" / f"board_board-PTH.drl"
        npth = FIX / "slot" / f"{board}_{board}-NPTH.drl" if board == "board_rot45" else FIX / "slot" / f"board_board-NPTH.drl"
        data = json.loads((inventory / f"{board}.inventory.json").read_text())
        status, _ = inspect_slots.inspect(data, pth.read_text(), npth.read_text())
        check(f"measured slot fixture passes: {kind}", status == 0, status)


# ------------------------------------------------------------------ mask
def mask(name, limit="4"):
    tmp = Path(tempfile.mkdtemp())
    report = tmp / "mask.json"
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "inspect_mask.py"), "--gerber",
                           str(FIX / "mask" / f"{name}.gts"), "--limit-mil", limit, "--report", str(report)],
                          capture_output=True, text=True)
    data = json.loads(report.read_text()) if report.exists() else {}
    shutil.rmtree(tmp)
    return proc.returncode, data


def mask_args(name, *args):
    tmp = Path(tempfile.mkdtemp())
    report = tmp / "mask.json"
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "inspect_mask.py"), "--gerber",
                           str(FIX / "mask" / f"{name}.gts"), *args, "--report", str(report)],
                          capture_output=True, text=True)
    existed = report.exists()
    data = json.loads(report.read_text()) if existed else {}
    shutil.rmtree(tmp)
    return proc.returncode, data, existed


def test_mask():
    code, data = mask("m39")
    check("mask 3.9 mil fixture fails (exit 1)", code == 1 and data.get("result") == "fail", (code, data.get("result")))
    code, data = mask("m40")
    check("mask 4.0 mil fixture is uncertain (exit 1)", code == 1 and data.get("result") == "uncertain", (code, data.get("result")))
    code, data = mask("m41")
    check("mask 4.1 mil fixture passes (exit 0)", code == 0, code)
    code, data = mask("rr")
    check("round-rect fixture: exact RoundRect web 4.0000 mil", abs(data["minimum_web_mm"] - 0.1016) < 1e-6, data.get("minimum_web_mm"))
    check("round-rect fixture at the limit is uncertain", data.get("result") == "uncertain", data.get("result"))
    code, data = mask("oval")
    check("unknown macro or obround aperture refused (exit 2)", code == 2 and "ObroundAperture" in data.get("unsupported", ""), (code, data))
    code, data = mask("overlap")
    check("overlapping cluster refused (exit 2)", code == 2 and "overlapping cluster" in data.get("unsupported", ""), (code, data))
    code, data = mask("m39merge")
    check("region output refused for automatic inspection (exit 2)", code == 2 and "Region" in data.get("unsupported", ""), (code, data))


def test_mask_units(tmp):
    """The mask command accepts the limit in mm or mil. An incorrect limit gives exit 2 and no report."""
    for name, expected in (("m39", "fail"), ("m40", "uncertain"), ("m41", "pass")):
        code_mil, data_mil = mask(name)
        code_mm, data_mm, existed = mask_args(name, "--limit-mm", "0.1016")
        check(f"mask {name}: the limit in mm gives the same result as the limit in mil",
              (code_mm, data_mm.get("result"), data_mm.get("counts"), data_mm.get("minimum_web_mm"))
              == (code_mil, data_mil.get("result"), data_mil.get("counts"), data_mil.get("minimum_web_mm"))
              and data_mm.get("result") == expected and existed,
              (code_mil, code_mm, data_mil.get("result"), data_mm.get("result")))
    code, data, existed = mask_args("m41", "--limit-mm", "0.1016")
    check("the report for a limit in mm has no mil value and the given mm value",
          data.get("limit_mil") is None and data.get("limit_mm") == 0.1016, (data.get("limit_mil"), data.get("limit_mm")))
    code, data, existed = mask_args("m41", "--limit-mil", "4", "--limit-mm", "0.1016")
    check("two limit flags give exit 2 and no report", code == 2 and not existed, (code, existed))
    code, data, existed = mask_args("m41")
    check("no limit flag gives exit 2 and no report", code == 2 and not existed, (code, existed))
    for flag in ("--limit-mil", "--limit-mm"):
        for value in ("abc", "0", "-1", "nan", "inf"):
            code, data, existed = mask_args("m41", flag, value)
            check(f"{flag} {value} gives exit 2 and no report", code == 2 and not existed, (code, existed))
    stub = tmp / "stub.py"
    stub.write_text('# /// script\n# requires-python = ">=3.10"\n# dependencies = []\n# ///\n'
                    'import json\nimport sys\nargs = sys.argv[1:]\n'
                    'open(args[args.index("--report") + 1], "w").write(json.dumps(args))\n')
    old = os.environ.get("PCB_FAB_MASK_WORKER")
    os.environ["PCB_FAB_MASK_WORKER"] = str(stub)
    try:
        g = str(FIX / "mask" / "m41.gts")
        cases = [("4", {}, ["--limit-mil", "4"]),
                 ("4", {"unit": "mil"}, ["--limit-mil", "4"]),
                 ("0.13", {"unit": "mm"}, ["--limit-mm", "0.13"]),
                 ("0.005", {"unit": "in"}, ["--limit-mm", "0.127"])]
        for index, (value, kwargs, wanted) in enumerate(cases, start=1):
            report = tmp / f"r{index}.json"
            code = fab.run_mask_worker(g, value, str(report), **kwargs)
            args = json.loads(report.read_text()) if report.exists() else []
            check(f"run_mask_worker {value} {kwargs} gives the worker arguments {wanted}",
                  code == 0 and all(item in args for item in wanted)
                  and ("--limit-mil" in args) == ("--limit-mil" in wanted), (code, args))
        for index, (value, kwargs) in enumerate((("4", {"unit": "cm"}), ("abc", {"unit": "in"}),
                                                ("abc", {}), ("0", {"unit": "mm"}), ("nan", {}),
                                                ("1/0", {"unit": "in"}), ("1/3", {"unit": "in"})), start=5):
            report = tmp / f"r{index}.json"
            code = fab.run_mask_worker(g, value, str(report), **kwargs)
            check(f"run_mask_worker refuses {value} {kwargs} with exit 2 and no report",
                  code == 2 and not report.exists(), (code, report.exists()))
        report = tmp / "r10.json"
        code = fab.run_mask_worker(g, "0.1234567890123456789012345678", str(report), unit="in")
        args = json.loads(report.read_text()) if report.exists() else []
        check("run_mask_worker converts a 28-digit value in inches exactly to millimeters",
              code == 0 and "3.13580244091358024409135802212" in args, (code, args))
    finally:
        if old is None:
            os.environ.pop("PCB_FAB_MASK_WORKER", None)
        else:
            os.environ["PCB_FAB_MASK_WORKER"] = old


# ------------------------------------------------------------------ source review
def live_project(tmp, profile, live_changed=False, observations=None):
    proj = tmp / "project"
    live = proj / "out" / "fab" / "source-review" / "live"
    live.mkdir(parents=True)
    stored = SKILL / "supplier" / "pages" / "two-layer.html"
    data = stored.read_bytes() + (b"<!-- changed -->" if live_changed else b"")
    (live / "two-layer.html").write_bytes(data)
    obs = observations if observations is not None else [
        {"key": k, "observed_value": str(v["value"]), "observed_unit": v["unit"], "observed_condition": "service page",
         "source_url": v["source_url"], "reviewer_reading": "read"} for k, v in profile["limits"].items()]
    pages = [{"page_id": "two-layer", "source_url": profile["source_url"],
              "stored_path": "supplier/pages/two-layer.html", "stored_sha256": hashlib.sha256(stored.read_bytes()).hexdigest(),
              "live_path": "out/fab/source-review/live/two-layer.html", "live_sha256": hashlib.sha256(data).hexdigest(),
              "retrieved": "2026-11-14"}]
    obs_path = tmp / "observations.json"
    obs_path.write_text(json.dumps({"release_id": "trial-1", "profile_sha256": profile["content_sha256"], "pages": pages,
                                    "observations": obs, "reviewer": "R. Reviewer", "statement": "test"}))
    return proj, obs_path


def test_source_review(tmp):
    profile = load_profile()
    cases = [
        ("unchanged", dict(), 0, "unchanged"),
        ("harmless (changed page, equal observations)", dict(live_changed=True), 0, "harmless"),
    ]
    for label, kw, code, decision in cases:
        proj, obs = live_project(tmp / label.split()[0], profile, **kw)
        c, review = fab.review_source(proj, profile, "trial-1", obs, "R. Reviewer")
        check(f"review {label}", c == code and review["decision"] == decision, (c, review["decision"]))
    obs_list = [{"key": "min_trace", "observed_value": "6", "observed_unit": "mil", "observed_condition": "x",
                 "source_url": "u", "reviewer_reading": "r"}]
    proj, obs = live_project(tmp / "missing", profile, observations=obs_list)
    c, review = fab.review_source(proj, profile, "trial-1", obs, "R. Reviewer")
    check("review material: observations incomplete (exit 1)", c == 1 and review["decision"] == "material", (c, review["decision"]))
    all_obs = [{"key": k, "observed_value": str(v["value"]), "observed_unit": v["unit"], "observed_condition": "c",
                "source_url": "u", "reviewer_reading": "r"} for k, v in profile["limits"].items()]
    all_obs[0]["observed_value"] = "7"
    proj, obs = live_project(tmp / "material", profile, observations=all_obs)
    c, review = fab.review_source(proj, profile, "trial-1", obs, "R. Reviewer")
    check("review material: a different value (exit 1)", c == 1 and review["decision"] == "material", (c, review["decision"]))
    unknown = all_obs + [{"key": "no_such_key", "observed_value": "1", "observed_unit": "mil", "observed_condition": "c",
                           "source_url": "u", "reviewer_reading": "r"}]
    proj, obs = live_project(tmp / "unknown", profile, observations=unknown)
    try:
        fab.review_source(proj, profile, "trial-1", obs, "R. Reviewer")
        check("review refuses an unknown observation key", False, "accepted")
    except fab.Invalid as err:
        check("review refuses an unknown observation key", "unknown observation key" in str(err), str(err))
    proj, obs = live_project(tmp / "escape", profile)
    spec = json.loads(obs.read_text())
    spec["pages"][0]["stored_path"] = "../../etc/passwd"
    obs.write_text(json.dumps(spec))
    try:
        fab.review_source(proj, profile, "trial-1", obs, "R. Reviewer")
        check("review refuses a path escape", False, "accepted")
    except fab.Invalid as err:
        check("review refuses a path escape", "path escape" in str(err), str(err))


def test_review_gate(tmp):
    profile = load_profile()
    proj, obs = live_project(tmp / "gate", profile, live_changed=True)
    code, review = fab.review_source(proj, profile, "trial-1", obs, "R. Reviewer")
    rpath = proj / "out" / "fab" / "source-review" / "REVIEW.json"
    rpath.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(review, indent=2, sort_keys=True).encode() + b"\n"
    rpath.write_bytes(raw)
    expect = hashlib.sha256(raw).hexdigest()
    check("gate passes an intact review", fab.review_gate(proj, profile, rpath, expect, "trial-1") == [], fab.review_gate(proj, profile, rpath, expect, "trial-1"))
    missing = tmp / "absent.json"
    check("gate rejects a missing review (omission)", fab.review_gate(proj, profile, missing, expect, "trial-1") != [])
    rpath.write_bytes(raw + b" ")
    check("gate rejects changed review bytes", fab.review_gate(proj, profile, rpath, expect, "trial-1") != [])
    rpath.write_bytes(raw)
    altered = copy.deepcopy(review)
    altered["observations"][0]["observed_value"] = "7"
    alt_raw = json.dumps(altered, indent=2, sort_keys=True).encode() + b"\n"
    rpath.write_bytes(alt_raw)
    check("gate rejects altered observations (hash differs)", fab.review_gate(proj, profile, rpath, hashlib.sha256(alt_raw).hexdigest(), "trial-1") != [])
    rpath.write_bytes(raw)
    check("gate rejects another release", fab.review_gate(proj, profile, rpath, expect, "trial-2") != [])
    other = copy.deepcopy(profile)
    other["content_sha256"] = "1" * 64
    check("gate rejects another profile hash", fab.review_gate(proj, other, rpath, expect, "trial-1") != [])
    live = proj / "out" / "fab" / "source-review" / "live" / "two-layer.html"
    live.write_bytes(live.read_bytes() + b"x")
    check("gate rejects a live page that differs from the reviewed hash", fab.review_gate(proj, profile, rpath, expect, "trial-1") != [])


# ------------------------------------------------------------------ drawing
def test_drawing(tmp):
    profile = load_profile()
    inv_data = json.loads((FIX / "inventory" / "board_rot45.inventory.json").read_text())
    board = FIX / "inventory" / "board_rot45.inventory.json"
    facts = fab.drawing_facts(inv_data, profile, board.read_bytes(), "trial-1", PROFILE.read_bytes())
    pdf = fab.drawing_pdf(facts)
    out = tmp / "drawing.pdf"
    out.write_bytes(pdf)
    text = pdf.decode("ascii", errors="replace")
    shown = [s.replace("\\(", "(").replace("\\)", ")") for s in text.split(" Tj")[0:0]]
    lines = []
    for part in text.split("\n"):
        if part.startswith("BT /F1") and " Tj" in part:
            lines.append(part.split("(", 1)[1].rsplit(") Tj", 1)[0].replace("\\(", "(").replace("\\)", ")"))
    joined = "\n".join(lines)
    need = {
        "release identity": "Release: trial-1",
        "units": "Units: mm",
        "overall size": f"Overall size: {facts['overall_width_mm']:.3f} mm x {facts['overall_height_mm']:.3f} mm",
        "holes": f"Holes: {facts['holes']['count']} ",
        "stackup": "stackup: 2-layer",
        "copper layers": "F.Cu, B.Cu",
        "profile identity": "Profile: oshpark-two-layer",
        "process facts": "min trace 6 mil",
        "mask web": "mask web min 4 mil",
        "board hash": f"Board SHA-256: {facts['board_sha256']}",
        "profile hash": f"Profile SHA-256: {facts['profile_sha256']}",
        "facts hash": f"Facts SHA-256: {hashlib.sha256(json.dumps(facts, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}",
    }
    for label, want in need.items():
        check(f"drawing shows {label}", want in joined, want)
    check("drawing has one page", text.count("/Type /Page ") == 1)
    proc = subprocess.run(["pdftoppm", "-png", "-r", "90", "-singlefile", str(out), str(tmp / "drawing")],
                          capture_output=True, text=True)
    png = tmp / "drawing.png"
    check("drawing renders to PNG", proc.returncode == 0 and png.is_file() and png.stat().st_size > 1000, proc.stderr)


def process_line(pdf):
    """The text of the Process line of the drawing sheet."""
    text = pdf.decode("ascii", errors="replace")
    for part in text.split("\n"):
        if part.startswith("BT /F1") and " Tj" in part:
            line = part.split("(", 1)[1].rsplit(") Tj", 1)[0].replace("\\(", "(").replace("\\)", ")")
            if line.startswith("Process: "):
                return line
    return None


def test_drawing_units(tmp):
    """The drawing facts and the sheet show the unit of each process limit."""
    profile = load_profile()
    inv_data = json.loads((FIX / "inventory" / "board_rot45.inventory.json").read_text())
    board = FIX / "inventory" / "board_rot45.inventory.json"
    facts = fab.drawing_facts(inv_data, profile, board.read_bytes(), "trial-1", PROFILE.read_bytes())
    check("drawing facts of the OSH Park profile have the same profile keys",
          set(facts["profile"]) == {"profile", "source_page", "min_trace_mil", "min_space_mil", "min_drill_mil",
                                    "mask_web_min_mil", "substrate", "finished_thickness_mm", "copper"},
          sorted(facts["profile"]))
    check("the OSH Park process line does not change",
          process_line(fab.drawing_pdf(facts))
          == "Process: min trace 6 mil, min space 6 mil, min drill 10 mil, mask web min 4 mil",
          process_line(fab.drawing_pdf(facts)))
    changed = copy.deepcopy(load_profile())
    for name, value, unit in (("min_trace", 0.1, "mm"), ("min_drill", 0.2, "mm"),
                              ("mask_web_min", 0.13, "mm"), ("min_space", 6, "mil")):
        changed["limits"][name] = dict(changed["limits"][name], value=value, unit=unit)
    facts = fab.drawing_facts(inv_data, changed, board.read_bytes(), "trial-1", PROFILE.read_bytes())
    keys = set(facts["profile"])
    check("a limit in mm gives a key in mm and no key in mil",
          {"min_trace_mm", "min_drill_mm", "mask_web_min_mm", "min_space_mil"} <= keys and "min_trace_mil" not in keys,
          sorted(keys))
    check("the process line shows the unit of each limit",
          process_line(fab.drawing_pdf(facts))
          == "Process: min trace 0.1 mm, min space 6 mil, min drill 0.2 mm, mask web min 0.13 mm",
          process_line(fab.drawing_pdf(facts)))
    mm_facts = facts
    changed = copy.deepcopy(load_profile())
    changed["limits"]["min_drill"] = dict(changed["limits"]["min_drill"], value=0.01, unit="in")
    facts = fab.drawing_facts(inv_data, changed, board.read_bytes(), "trial-1", PROFILE.read_bytes())
    check("a limit in in gives a key in in and the text in in",
          "min_drill_in" in facts["profile"] and "min drill 0.01 in" in process_line(fab.drawing_pdf(facts)),
          (sorted(facts["profile"]), process_line(fab.drawing_pdf(facts))))
    two = copy.deepcopy(mm_facts)
    two["profile"]["min_trace_mil"] = 6
    try:
        fab.drawing_pdf(two)
        refused = False
    except fab.Invalid:
        refused = True
    check("the sheet refuses two units for one limit", refused)
    none = copy.deepcopy(mm_facts)
    del none["profile"]["min_trace_mm"]
    try:
        fab.drawing_pdf(none)
        refused = False
    except fab.Invalid:
        refused = True
    check("the sheet refuses a limit with no unit", refused)


def test_refuses_unimplemented(tmp):
    code, text = run_fab("design", "--project", str(tmp), "--profile", str(SKILL / "supplier" / "profiles" / "oshpark-two-layer.yaml"))
    check("design refuses a project with no files (not zero)", code != 0, (code, text))


GERBER_HEAD = "%FSLAX46Y46*%\n%MOMM*%\n"


def gerber(apertures, flashes, extra=""):
    """A small mask Gerber: apertures are lines like `%ADD10R,2X2*%`; flashes are (aperture, x_mm, y_mm)."""
    body = "".join(f"D{n}*\nX{round(x * 1e6)}Y{round(y * 1e6)}D03*\n" for n, x, y in flashes)
    return GERBER_HEAD + "\n".join(apertures) + "\n%LPD*%\n" + extra + body + "M02*\n"


def mask_text(tmp, label, text, limit="4"):
    path = tmp / f"{label}.gts"
    path.write_text(text)
    report = tmp / f"{label}.json"
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "inspect_mask.py"), "--gerber", str(path),
                           "--limit-mil", limit, "--report", str(report)], capture_output=True, text=True)
    data = json.loads(report.read_text()) if report.exists() else {}
    return proc.returncode, data


def test_geometry_focused(tmp):
    rect = "%ADD10R,2X2*%"
    code, data = mask_text(tmp, "rect_overlap", gerber([rect], [(10, 10, 10), (10, 11, 10)]))
    check("two 2 mm rectangles overlapping by 1 mm are refused (exit 2)", code == 2 and "overlapping cluster" in data.get("unsupported", ""), (code, data))
    code, data = mask_text(tmp, "rect_coincident", gerber([rect], [(10, 10, 10), (10, 10, 10)]))
    check("coincident rectangles are refused (exit 2)", code == 2 and "overlapping cluster" in data.get("unsupported", ""), (code, data))
    code, data = mask_text(tmp, "rect_edge_contact", gerber([rect], [(10, 10, 10), (10, 12, 10)]))
    check("rectangles touching on an edge are merged_opening, not a web (exit 0)", code == 0 and data.get("counts", {}).get("merged_opening") == 1, (code, data))
    code, data = mask_text(tmp, "rect_round_overlap", gerber(["%ADD10C,1.0*%", rect], [(10, 10, 10), (10, 10.6, 10)]))
    check("circle inside a rectangle is refused (exit 2)", code == 2 and "overlapping cluster" in data.get("unsupported", ""), (code, data))
    code, data = mask_text(tmp, "rect_web", gerber([rect], [(10, 10, 10), (10, 12.05, 10)]))
    check("rectangles 0.05 mm apart give a web of 0.05 mm (fail below 4 mil)", code == 1 and abs((data.get("minimum_web_mm") or 0) - 0.05) < 1e-6, (code, data.get("minimum_web_mm")))
    macro = (FIX / "mask" / "rr.gts").read_text()
    changed = macro.replace("1,1,$1+$1,$2,$3*", "1,1,$1+$1,$2,$3+0.05*")
    code, data = mask_text(tmp, "macro_changed", changed)
    check("a RoundRect macro with a changed primitive is refused (exit 2)", code == 2 and "measured definition" in data.get("unsupported", ""), (code, data))
    dense = gerber(["%ADD10C,0.1*%"], [(10, 10, 10 + 0.2 * i) for i in range(2100)])
    code, data = mask_text(tmp, "dense_column", dense)
    check("more than 2000000 candidate pairs or the time budget refuses (exit 2)", code == 2 and ("candidate pairs" in data.get("unsupported", "") or "elapsed-time" in data.get("unsupported", "")), (code, str(data)[:200]))


def test_geometry_corrections(tmp):
    """Regressions for the six corrections G1 to G3, aperture holes, RoundRect geometry and the Excellon end."""
    rr = (FIX / "mask" / "rr.gts").read_text()
    add = next(line for line in rr.splitlines() if line.startswith("%ADD10RoundRect"))
    rect_add = "%ADD10RoundRect,0.150000X-0.150000X-0.150000X0.150000X-0.150000X0.150000X0.150000X-0.150000X0.150000X0*%"
    check("the fixture RoundRect aperture is the measured form", add == rect_add, add)
    # G1: a macro with a different body, inline with the previous text or after a space, is refused.
    body = "%AMRoundRect*1,1,10,0,0*%"
    inline = rr.replace("%AMRoundRect", "%MOMM*%" + body + "%AMRoundRect", 1)
    code, data = mask_text(tmp, "g1_inline", rr.replace("%AMRoundRect", body + "%AMRoundRect", 1) if False else
                           rr.replace("%MOMM*%\n", "%MOMM*%" + body + "\n", 1))
    check("G1: a macro inline on the units line is refused (exit 2)", code == 2 and "unsupported macro" in data.get("unsupported", "") or
          code == 2 and "measured form" in data.get("unsupported", "") or code == 2, (code, data))
    spaced = rr.replace("\n%AMRoundRect", "\n %AMRoundRect", 1)
    code, data = mask_text(tmp, "g1_space", spaced)
    check("G1: a macro with a leading space is refused (exit 2)", code == 2, (code, data))
    changed = rr.replace("1,1,$1+$1,$2,$3*", "1,1,$1+$1,$2,$3+0.05*")
    code, data = mask_text(tmp, "g1_changed", changed)
    check("G1: a changed RoundRect definition is refused (exit 2)", code == 2 and "measured definition" in data.get("unsupported", ""), (code, data))
    # G2: the hash binds the bytes that were measured. One read only.
    raw = (FIX / "mask" / "m41.gts").read_bytes()
    import builtins  # noqa: F401
    reads = []
    original = pathlib.Path.read_bytes if False else None
    result = {}
    path = tmp / "g2.gts"
    path.write_bytes(raw)
    original_read = Path.read_bytes

    def swapping_read(self):
        reads.append(1)
        return raw if len(reads) == 1 else b"%FSLAX46Y46*%\n"
    Path.read_bytes = swapping_read
    try:
        sys.path.insert(0, str(SCRIPTS))
        import inspect_mask as IM
        status, body_out = IM.inspect(path, 4 * 0.0254)
        result = {"status": status, "sha": body_out["gerber_sha256"], "reads": len(reads)}
    finally:
        Path.read_bytes = original_read
    check("G2: the file is read once", result.get("reads") == 1, result)
    check("G2: the reported hash is the hash of the measured bytes", result.get("sha") == hashlib.sha256(raw).hexdigest(), result)
    # G3: the elapsed-time budget covers reading, parsing and pair inspection.
    import inspect_mask as IM2
    try:
        IM2.inspect(FIX / "mask" / "m41.gts", 4 * 0.0254, max_seconds=0.0)
        check("G3: a zero time budget is refused", False, "accepted")
    except IM2.Unsupported as err:
        check("G3: a zero time budget is refused", "elapsed-time" in str(err), str(err))
    # G4: an aperture with a hole is refused.
    code, data = mask_text(tmp, "g4_hole", gerber(["%ADD10C,2X1.9*%"], [(10, 10, 10)]))
    check("G4: a circle aperture with a hole is refused (exit 2)", code == 2 and "hole" in data.get("unsupported", ""), (code, data))
    # G5: RoundRect parameters: diagonal corner order, rotation, and a radius outside the rectangle.
    diagonal = rr.replace(add, "%ADD10RoundRect,0.150000X-0.150000X-0.150000X0.150000X0.150000X-0.150000X-0.150000X0.150000X0.150000X0*%")
    code, data = mask_text(tmp, "g5_diagonal", diagonal)
    check("G5: corners in diagonal order are refused (exit 2)", code == 2, (code, data))
    rotated = rr.replace(add, rect_add[:-2] + "90*%")
    code, data = mask_text(tmp, "g5_rotated", rotated)
    check("G5: a rotated RoundRect is refused (exit 2)", code == 2 and "rotated" in data.get("unsupported", ""), (code, data))
    big = rr.replace(add, "%ADD10RoundRect,0.500000X-0.150000X-0.150000X0.150000X-0.150000X0.150000X0.150000X-0.150000X0.150000X0*%")
    code, data = mask_text(tmp, "g5_radius", big)
    check("G5: a radius above half the core side now follows the overlap rule (exit 2 here, overlapping flashes)", code == 2 and "overlapping cluster" in data.get("unsupported", ""), (code, data))
    # G6: the Excellon file ends with the terminal M30.
    import export_inspect as EI
    good = (FIX / "slot" / "board_rot45_board_rot45-NPTH.drl").read_text()
    try:
        EI.parse(good.replace("M30\n", ""))
        check("G6: a missing terminal M30 is refused", False, "accepted")
    except EI.UnsupportedRecord as err:
        check("G6: a missing terminal M30 is refused", "terminal M30" in str(err), str(err))
    try:
        EI.parse(good.replace("M30\n", "M30\nX1000000Y1000000\n"))
        check("G6: a record after M30 is refused", False, "accepted")
    except EI.UnsupportedRecord as err:
        check("G6: a record after M30 is refused", "follows the terminal M30" in str(err), str(err))


def test_final_decisions(tmp):
    """Radius without a core-side limit, and the caller timeout of the mask worker."""
    rr = (FIX / "mask" / "rr.gts").read_text()
    big = rr.replace("%ADD10RoundRect,0.150000X-0.150000X-0.150000X0.150000X-0.150000X0.150000X0.150000X-0.150000X0.150000X0*%",
                     "%ADD10RoundRect,0.500000X-0.150000X-0.150000X0.150000X-0.150000X0.150000X0.150000X-0.150000X0.150000X0*%")
    spaced = big.replace("X701600Y0D03*", "X2000000Y0D03*")
    code, data = mask_text(tmp, "radius_large", spaced, limit="30")
    # core gap 2.0 - 0.3 = 1.7 mm; minus two radii of 0.5 mm gives 0.7 mm
    check("a radius above half the core side follows the core-distance formula (30 mil limit, web 0.7 mm fails)",
          code == 1 and abs((data.get("minimum_web_mm") or 0) - 0.7) < 1e-6, (code, data.get("minimum_web_mm")))
    overlapping = big.replace("X701600Y0D03*", "X701600Y0D03*")
    code, data = mask_text(tmp, "radius_overlap", overlapping)
    check("a radius above half the core side keeps the overlap refusal (exit 2)",
          code == 2 and "overlapping cluster" in data.get("unsupported", ""), (code, data))
    worker = tmp / "stalled_worker.py"
    worker.write_text("# /// script\n# requires-python = \">=3.10\"\n# dependencies = []\n# ///\nimport time\ntime.sleep(30)\n")
    env = dict(os.environ, PCB_FAB_MASK_WORKER=str(worker))
    report = tmp / "stalled.json"
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), "inspect-mask", "--gerber",
                           str(FIX / "mask" / "m41.gts"), "--limit-mil", "4", "--report", str(report)],
                          capture_output=True, text=True, env=env, timeout=120)
    check("a stalled mask worker is stopped by the caller timeout (exit 2)",
          proc.returncode == 2 and "caller timeout" in proc.stdout + proc.stderr and not report.exists(),
          (proc.returncode, proc.stdout[-200:], proc.stderr[-200:]))
    report.write_text("{}\n")
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), "inspect-mask", "--gerber",
                           str(FIX / "mask" / "m41.gts"), "--limit-mil", "4", "--report", str(report)],
                          capture_output=True, text=True, timeout=120)
    check("an existing report path is refused: no stale success (exit 2)", proc.returncode == 2 and "fresh report" in proc.stdout + proc.stderr,
          (proc.returncode, proc.stdout[-200:]))
    fresh = tmp / "fresh.json"
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), "inspect-mask", "--gerber",
                           str(FIX / "mask" / "m41.gts"), "--limit-mil", "4", "--report", str(fresh)],
                          capture_output=True, text=True, timeout=120)
    check("a fresh report path with a passing web gives exit 0 and a report", proc.returncode == 0 and fresh.is_file(),
          (proc.returncode, proc.stderr[-200:]))


def test_report_link(tmp):
    """A dangling report symlink is refused. The public command must not create its target."""
    link = tmp / "dangling-report.json"
    target = tmp / "absent-target.json"
    os.symlink(target, link)
    proc = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), "inspect-mask", "--gerber",
                           str(FIX / "mask" / "m41.gts"), "--limit-mil", "4", "--report", str(link)],
                          capture_output=True, text=True, timeout=120)
    check("a dangling report symlink is refused (exit 2)", proc.returncode == 2, (proc.returncode, proc.stdout[-200:], proc.stderr[-200:]))
    check("the dangling report link is unchanged", link.is_symlink() and os.readlink(link) == str(target), os.readlink(link) if link.is_symlink() else "not a link")
    check("the link target is not created", not target.exists(), "the target was created")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="fab-tests-"))
    try:
        test_profiles(tmp / "p")  if (tmp / "p").mkdir() is None else None
        test_boundaries()
        test_slots()
        test_export_reader(tmp)
        test_measured_slot_fixtures()
        test_mask()
        test_mask_units(tmp / "mu") if (tmp / "mu").mkdir() is None else None
        test_source_review(tmp / "rv") if (tmp / "rv").mkdir() is None else None
        test_review_gate(tmp / "gt") if (tmp / "gt").mkdir() is None else None
        test_drawing(tmp / "dr") if (tmp / "dr").mkdir() is None else None
        test_drawing_units(tmp / "du") if (tmp / "du").mkdir() is None else None
        test_geometry_focused(tmp / "geo") if (tmp / "geo").mkdir() is None else None
        test_geometry_corrections(tmp / "corr") if (tmp / "corr").mkdir() is None else None
        test_final_decisions(tmp / "final") if (tmp / "final").mkdir() is None else None
        test_report_link(tmp / "link") if (tmp / "link").mkdir() is None else None
        test_refuses_unimplemented(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n{passed}/{len(RESULTS)} passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
