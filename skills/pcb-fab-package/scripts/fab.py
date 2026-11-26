#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""pcb-fab-package command line. Each command follows the exit table of `SKILL.md`.

Exit status: 0 success, 1 invalid record or failed check, 2 invalid arguments, unsupported construct,
missing prerequisite or a command this batch does not implement, 3 tool failure.

Commands in this batch:
  profile          validate a supplier profile record and its evidence bindings
  judge            judge one measured value against one limit (boundary rules of the profile)
  review-source    compare the stored supplier pages with the live pages and write REVIEW.json
  review-gate      verify a REVIEW.json against the profile and the live pages (package gate)
  drawing-facts    write the drawing facts from a board inventory and a profile
  drawing          write the one-page fabrication drawing sheet from the drawing facts
  inspect-slots   compare the board slots with the export drill files (see inspect_slots.py)
  inspect-mask    measure the mask webs of a Gerber (see inspect_mask.py, run through uv)
Not implemented in this batch (exit 2): design, supplier, package.
"""

import hashlib
import json
import os
import pathlib
import signal
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate as VAL  # noqa: E402  (the byte copy of contracts/validate.py)
import inspect_slots  # noqa: E402
import review  # noqa: E402
import project_io as PIO  # noqa: E402
import workflow  # noqa: E402

SKILL = HERE.parent
PAGES = SKILL / "supplier" / "pages"
PROFILE_PAGES = {
    "oshpark-single-layer": {"single-layer", "two-layer"},
    "oshpark-two-layer": {"two-layer"},
    "oshpark-two-layer-hhdc": {"two-layer-hhdc"},
    "oshpark-four-layer": {"four-layer"},
    "oshpark-six-layer": {"six-layer"},
    "jlcpcb-two-layer": {"jlcpcb-pcb-capabilities"},
    "jlcpcb-four-layer": {"jlcpcb-pcb-capabilities"},
    "pcbway-two-layer": {"pcbway-capabilities"},
    "pcbway-four-layer": {"pcbway-capabilities"},
}
# Only these profiles have the OSH Park facts that the workflow uses. Other profiles contain only values (decision Q2).
WORKFLOW_PROFILES = {"oshpark-single-layer", "oshpark-two-layer", "oshpark-two-layer-hhdc",
                     "oshpark-four-layer", "oshpark-six-layer"}
DIVISION_KEYS = ("kicad_dru", "project_settings", "geometric_tests", "manual_evidence")
EXIT_OK, EXIT_FAIL, EXIT_ARGS, EXIT_TOOL = 0, 1, 2, 3
UNIT_MM = {"mm": Fraction(1), "mil": Fraction(254, 10000), "in": Fraction(254, 10)}
LIVE_DIR = ("out", "fab", "source-review", "live")
PLACEHOLDER = "0" * 64


class Invalid(Exception):
    """An invalid record or observation. The caller exits 1."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_hash(record):
    body = {k: v for k, v in record.items() if k != "content_sha256"}
    return sha(canonical_bytes(body))


def judge(kind, measured, threshold, bound=Fraction(0)):
    """Boundary rules of the profile. `measured` and `threshold` are Fractions in one unit. `bound` is the
    error bound in the same unit. A value inside the bound of a threshold is `uncertain`.
    Maximum: pass at and below the threshold, fail above it. Minimum: fail below, pass at and above.
    Recommendation: never fail, reported as a finding."""
    measured, threshold = Fraction(measured), Fraction(threshold)
    if kind == "recommendation":
        return "finding"
    if kind == "maximum":
        if measured <= threshold - bound:
            return "pass"
        if measured > threshold + bound:
            return "fail"
        return "uncertain"
    if kind == "minimum":
        if measured >= threshold + bound:
            return "pass"
        if measured < threshold - bound:
            return "fail"
        return "uncertain"
    raise Invalid(f"no judgment for the limit kind {kind!r}")


def limit_in_mm(limit):
    return Fraction(str(limit["value"])) * UNIT_MM[limit["unit"]]


def check_profile(path):
    """Validate a profile. Return the record. Raise Invalid for any defect that the profile rules name."""
    record = VAL.load_record(path)
    if record.get("content_sha256") != content_hash(record):
        raise Invalid("content_sha256 does not match the canonical record content")
    pid = record["id"]
    limits = record["limits"]
    seen = {}
    for name in DIVISION_KEYS:
        for key in record["division"].get(name, []):
            if key in seen:
                raise Invalid(f"division key {key!r} is used twice ({seen[key]} and {name})")
            seen[key] = name
    for key in seen:
        if key not in limits:
            raise Invalid(f"division key {key!r} names no limit")
    for key, limit in limits.items():
        if key not in seen:
            raise Invalid(f"limit {key!r} is not in the division")
        if limit["value_kind"] == "text":
            if limit["kind"] in ("minimum", "maximum"):
                raise Invalid(f"limit {key!r} is a {limit['kind']} with a text value")
            if "unit" in limit and limit["unit"]:
                raise Invalid(f"text limit {key!r} must not have a unit")
        elif limit["unit"] not in UNIT_MM:
            raise Invalid(f"limit {key!r} has an unsupported unit {limit['unit']!r}")
    ext = record["extensions"]
    if not isinstance(ext["service.layers"]["value"], int) or isinstance(ext["service.layers"]["value"], bool):
        raise Invalid("service.layers must be an integer")
    order = ext.get("service.order_multiple")
    if isinstance(order, dict) and order.get("kind") == "not_stated":
        # The marked form states that the page gives no order multiple. It must not carry a value.
        if "value" in order:
            raise Invalid("service.order_multiple is not_stated, so it must not have a value")
        if pid in WORKFLOW_PROFILES:
            raise Invalid("service.order_multiple must be an integer for a profile that the workflow uses")
    elif not isinstance(order, dict) or not isinstance(order.get("value"), int):
        raise Invalid("service.order_multiple must be an integer")
    bound_pages = ext["evidence_pages"]
    required = PROFILE_PAGES.get(pid)
    if required is None:
        raise Invalid(f"unknown profile id {pid!r}")
    if set(bound_pages) != required:
        raise Invalid(f"the profile must bind the pages {sorted(required)}, found {sorted(bound_pages)}")
    for page, entry in bound_pages.items():
        data = (PAGES / f"{page}.html").read_bytes()
        if sha(data) != entry["sha256"]:
            raise Invalid(f"stored page {page} differs from its bound hash")
    if record["evidence_sha256"] != bound_pages[sorted(required)[0]]["sha256"]:
        if record["evidence_sha256"] not in {e["sha256"] for e in bound_pages.values()}:
            raise Invalid("evidence_sha256 is not a bound page hash")
    return record


def refuse_data_only(profile_path, command):
    """Stop a command that reads the OSH Park facts when the profile contains only values (decision Q2).

    Read only the profile id. Read no page, no project and no lock. A profile id that is not
    in WORKFLOW_PROFILES is refused, so a new profile gets the same stop by default."""
    pid = VAL.load_record(profile_path)["id"]
    if pid not in WORKFLOW_PROFILES:
        raise workflow.Stop(workflow.EXIT_UNSUPPORTED,
                            f"the profile {pid} contains only values. The command {command} does not run for it. "
                            "Use profile, judge or review-source. "
                            f"See references/{pid.split('-')[0]}-kicad-setup.md.")


def _confined(root, rel):
    """Return the resolved path under `root`, or raise Invalid for an absolute path, `..`, or a link."""
    p = pathlib.PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts or not rel:
        raise Invalid(f"path escape: {rel!r}")
    full = root.joinpath(*p.parts)
    for part in [root, *[root.joinpath(*p.parts[:i]) for i in range(1, len(p.parts) + 1)]]:
        if part.is_symlink():
            raise Invalid(f"symbolic link in path: {rel!r}")
    return full


def review_source(project, profile, release, observations_path, reviewer):
    """Return (exit, review dict). Write nothing here; the caller writes the record."""
    obs = json.loads(pathlib.Path(observations_path).read_text())
    if obs.get("release_id") != release:
        raise Invalid("the observation file names another release")
    if obs.get("profile_sha256") != profile["content_sha256"]:
        raise Invalid("the observation file names another profile hash")
    if obs.get("reviewer") != reviewer:
        raise Invalid("the reviewer differs from the observation file")
    pages_out = []
    seen_pages = set()
    for entry in obs.get("pages", []):
        page = entry["page_id"]
        if page in seen_pages:
            raise Invalid(f"page {page} is listed twice")
        seen_pages.add(page)
        if page not in PROFILE_PAGES[profile["id"]]:
            raise Invalid(f"page {page} is not a page of this profile")
        stored = _confined(SKILL, entry["stored_path"])
        if not stored.is_file() or stored != PAGES / f"{page}.html":
            raise Invalid(f"stored path does not name the stored page {page}")
        stored_bytes = stored.read_bytes()
        if sha(stored_bytes) != entry["stored_sha256"]:
            raise Invalid(f"stored_sha256 differs from the bytes of {page}")
        live = _confined(project, entry["live_path"])
        if live.parts[-len(LIVE_DIR) - 1:-1] != LIVE_DIR:
            raise Invalid("the live path is outside out/fab/source-review/live/")
        if not live.is_file():
            raise Invalid(f"live page missing: {entry['live_path']}")
        live_bytes = live.read_bytes()
        if sha(live_bytes) != entry["live_sha256"]:
            raise Invalid(f"live_sha256 differs from the live bytes of {page}")
        pages_out.append({"page_id": page, "stored_sha256": sha(stored_bytes), "live_sha256": sha(live_bytes),
                          "bytes_equal": stored_bytes == live_bytes, "retrieved": entry["retrieved"]})
    if seen_pages != PROFILE_PAGES[profile["id"]]:
        raise Invalid(f"the observation file must list every page {sorted(PROFILE_PAGES[profile['id']])}")
    limits = profile["limits"]
    seen = set()
    matches = True
    for item in obs.get("observations", []):
        key = item["key"]
        if key in seen:
            raise Invalid(f"observation {key!r} is listed twice")
        seen.add(key)
        if key not in limits:
            raise Invalid(f"unknown observation key {key!r}")
        lim = limits[key]
        if str(item["observed_value"]) != str(lim["value"]) or item["observed_unit"] != lim.get("unit", ""):
            matches = False
    if seen != set(limits):
        matches = False  # a missing observation is a material difference
    obs_hash = sha(canonical_bytes(obs.get("observations", [])))
    changed = any(not p["bytes_equal"] for p in pages_out)
    if not matches:
        decision = "material"
    elif changed:
        decision = "harmless"
    else:
        decision = "unchanged"
    review = {"schema_id": "cad-skills/source-review", "schema_version": "1.0", "release_id": release,
              "profile_sha256": profile["content_sha256"], "pages": pages_out, "observations": obs.get("observations", []),
              "observations_sha256": obs_hash, "decision": decision, "reviewer": reviewer,
              "statement": obs.get("statement", "")}
    return (EXIT_OK if decision != "material" else EXIT_FAIL), review


def review_gate(project, profile, review_path, expected_sha, release):
    """Re-check a REVIEW.json. Return a list of problems. An empty list means the gate passes."""
    raw = pathlib.Path(review_path).read_bytes() if pathlib.Path(review_path).is_file() else None
    if raw is None:
        return ["the source review record is missing"]
    problems = []
    if sha(raw) != expected_sha:
        problems.append("the source review bytes differ from the package hash")
    review = json.loads(raw)
    if review.get("profile_sha256") != profile["content_sha256"]:
        problems.append("the profile hash differs")
    if sha(canonical_bytes(review.get("observations", []))) != review.get("observations_sha256"):
        problems.append("the observations differ from the recorded observation hash")
    limits = profile["limits"]
    observed = {item["key"]: item for item in review.get("observations", [])}
    if set(observed) != set(limits):
        problems.append("the observations do not cover every limit")
    for key, item in observed.items():
        lim = limits.get(key)
        if lim is None or str(item["observed_value"]) != str(lim["value"]) or item["observed_unit"] != lim.get("unit", ""):
            problems.append(f"observation {key!r} differs from the profile")
    for page in review.get("pages", []):
        stored = PAGES / f"{page['page_id']}.html"
        if page["page_id"] not in PROFILE_PAGES.get(profile["id"], set()):
            problems.append(f"page {page['page_id']} is not a page of the profile")
            continue
        if sha(stored.read_bytes()) != page["stored_sha256"]:
            problems.append(f"stored page {page['page_id']} differs from the reviewed hash")
        live_entries = [p for p in review.get("pages", []) if p["page_id"] == page["page_id"]]
        live_path = project / "out" / "fab" / "source-review" / "live" / f"{page['page_id']}.html"
        if not live_path.is_file() or sha(live_path.read_bytes()) != page["live_sha256"]:
            problems.append(f"live page {page['page_id']} differs from the reviewed hash")
        if len(live_entries) != 1:
            problems.append(f"page {page['page_id']} is listed more than once")
    if review.get("decision") not in ("unchanged", "harmless"):
        problems.append(f"the decision is {review.get('decision')}")
    if review.get("release_id") is None:
        problems.append("the release is missing")
    if review.get("release_id") != release:
        problems.append("the release differs from the package release")
    return problems


# The process limits on the drawing sheet: the limit name and the label. The facts key has the unit of the limit.
DRAWING_LIMITS = (("min_trace", "min trace"), ("min_space", "min space"), ("min_drill", "min drill"),
                  ("mask_web_min", "mask web min"))
DRAWING_UNITS = ("mil", "mm", "in")


def _limit_text(p, name, label):
    """The sheet text of one process limit. The facts must give the limit in exactly one unit."""
    found = [(unit, p[f"{name}_{unit}"]) for unit in DRAWING_UNITS if f"{name}_{unit}" in p]
    if len(found) != 1:
        raise Invalid(f"the drawing facts must give one unit for {name}")
    unit, value = found[0]
    return f"{label} {value} {unit}"


def drawing_facts(inventory, profile, board_bytes, release, profile_bytes):
    """Build the facts that the drawing sheet shows. The inventory comes from board_inventory_slots.py."""
    outline = inventory["outline"]
    holes = inventory.get("holes", []) + inventory.get("slots", [])
    diameters = sorted({h.get("diameter", h.get("minor_mm")) for h in holes})
    layers = inventory["copper_layers"]
    shown = {"profile": profile["id"], "source_page": "stored supplier page"}
    for name, _ in DRAWING_LIMITS:
        limit = profile["limits"][name]
        shown[f"{name}_{limit['unit']}"] = limit["value"]
    shown.update({"substrate": profile["extensions"]["service.substrate"],
                  "finished_thickness_mm": profile["extensions"]["service.finished_thickness_display_mm"],
                  "copper": profile["extensions"]["service.copper"]})
    return {"release_id": release, "unit": "mm",
            "board_sha256": sha(board_bytes), "profile_sha256": profile["content_sha256"],
            "profile_file_sha256": sha(profile_bytes),
            "overall_width_mm": outline["width"], "overall_height_mm": outline["height"],
            "holes": {"count": len(holes), "diameters_mm": diameters},
            "copper_layers": layers, "stackup": f"{len(layers)}-layer",
            "profile": shown}


def _pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def drawing_pdf(facts):
    """Return the bytes of a one-page sheet with the facts. Stdlib only."""
    raw = canonical_bytes(facts)
    p = facts["profile"]
    lines = [
        ("FABRICATION DRAWING", 14),
        (f"Release: {facts['release_id']}", 11),
        (f"Units: {facts['unit']}", 11),
        (f"Overall size: {facts['overall_width_mm']:.3f} mm x {facts['overall_height_mm']:.3f} mm", 11),
        (f"Holes: {facts['holes']['count']} (diameters mm: {', '.join(str(d) for d in facts['holes']['diameters_mm'])})", 11),
        (f"Copper layers: {', '.join(facts['copper_layers'])}; stackup: {facts['stackup']}", 11),
        (f"Profile: {p['profile']} (source: {p['source_page']})", 11),
        ("Process: " + ", ".join(_limit_text(p, name, label) for name, label in DRAWING_LIMITS), 11),
        (f"Substrate: {p['substrate']}; finished thickness {p['finished_thickness_mm']} mm; copper {p['copper']}", 11),
        (f"Board SHA-256: {facts['board_sha256']}", 9),
        (f"Profile SHA-256: {facts['profile_sha256']}", 9),
        (f"Facts SHA-256: {sha(raw)}", 9),
    ]
    scale = 4.0
    x0, y0 = 50.0, 420.0
    content = [f"0.5 w {x0:.2f} {y0:.2f} {facts['overall_width_mm'] * scale:.2f} {facts['overall_height_mm'] * scale:.2f} re S"]
    top = 780.0
    for text, size in lines:
        content.append(f"BT /F1 {size} Tf 50 {top:.2f} Td ({_pdf_escape(text)}) Tj ET")
        top -= size + 8
    content.append(f"BT /F1 9 Tf {x0:.2f} {y0 - 14:.2f} Td (Outline drawn to scale: {scale:.0f} pt per mm) Tj ET")
    stream = "\n".join(content).encode("ascii")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def mm_text(value):
    """The exact decimal text of a millimeter value, without trailing zeros.

    The value must be a terminating decimal. Otherwise the function raises ValueError.
    """
    value = Fraction(value)
    num, den = value.numerator, value.denominator
    twos = fives = 0
    while den % 2 == 0:
        den //= 2
        twos += 1
    while den % 5 == 0:
        den //= 5
        fives += 1
    if den != 1:
        raise ValueError(f"the value {value} is not a terminating decimal")
    digits = max(twos, fives)
    whole, frac = divmod(num, value.denominator)
    if frac == 0:
        return str(whole)
    scaled = frac * 10 ** digits // value.denominator
    return f"{whole}.{str(scaled).rjust(digits, '0').rstrip('0')}"


MASK_TIMEOUT_SECONDS = 2.0
MASK_LIMIT_FLAGS = {"mil": "--limit-mil", "mm": "--limit-mm"}  # the worker flag for each unit of the limit


def run_mask_worker(gerber, limit, report, unit="mil"):
    """Run the mask worker once through uv, with a caller timeout of MASK_TIMEOUT_SECONDS.

    The helper budget inside the worker checks elapsed time only at its checkpoints. The caller timeout stops
    the whole process group after the time limit. A timeout returns exit 2 and writes no report. The report
    path must be fresh, so an old result is never used. Process start and stop overhead is not removed.
    The unit is the unit of the profile limit: mm, mil or in. A value in inches goes to the worker in millimeters.
    """
    rep = pathlib.Path(report)
    if rep.exists() or rep.is_symlink():
        return _fail(EXIT_ARGS, "the report path exists; give a fresh report path")
    try:
        decimal_value = Decimal(str(limit))
    except (ValueError, TypeError, ArithmeticError):
        return _fail(EXIT_ARGS, f"the mask limit {limit!r} is not a number")
    if not decimal_value.is_finite() or decimal_value <= 0:
        return _fail(EXIT_ARGS, "the mask limit must be a finite number greater than 0")
    try:
        number = Fraction(decimal_value)
        if unit == "in":
            limit, unit = mm_text(number * UNIT_MM["in"]), "mm"
    except ValueError:
        return _fail(EXIT_ARGS, f"the mask limit {limit!r} is not a terminating decimal")
    if unit not in MASK_LIMIT_FLAGS:
        return _fail(EXIT_ARGS, f"the mask limit unit {unit!r} is not supported. Use mm, mil or in.")
    worker = os.environ.get("PCB_FAB_MASK_WORKER") or str(HERE / "inspect_mask.py")
    cmd = ["uv", "run", "--quiet", worker, "--gerber", gerber, MASK_LIMIT_FLAGS[unit], limit, "--report", report]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=MASK_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        if rep.exists():
            rep.unlink()
        return _fail(EXIT_ARGS, f"resource limit: the mask worker exceeded the {MASK_TIMEOUT_SECONDS}-second caller timeout")
    if proc.returncode in (0, 1, 2) and not rep.is_file():
        return _fail(EXIT_TOOL, "the mask worker wrote no report")
    if proc.returncode in (0, 1, 2):
        print(out.strip())
    else:
        sys.stderr.write(out + err)
    return proc.returncode


def _args(argv, names):
    values = {}
    for name in names:
        if name not in argv or argv.index(name) + 1 >= len(argv):
            raise SystemExit(_fail(EXIT_ARGS, f"give {name}"))
        values[name] = argv[argv.index(name) + 1]
    return values


def _fail(code, message):
    print(f"fab: {message}", file=sys.stderr)
    return code


def write_standalone(out, data):
    """Write one standalone output through the atomic helper.

    The drawing commands have no project argument. The output root is therefore the parent directory of `out`.
    No project confinement is claimed. A link at `out`, even a dangling one, is refused before any write."""
    out = pathlib.Path(out).absolute()
    if os.path.islink(out) or os.path.islink(out.parent):
        raise workflow.Stop(workflow.EXIT_UNSUPPORTED, f"the output {out} or its directory is a symbolic link; nothing is written")
    PIO.atomic_write(out.parent, out, data)


def _review_source(a, project):
    """Write the source review and its observation file. Run under the project lock. Return the exit status."""
    profile_path = pathlib.Path(a["--profile"])
    profile = check_profile(profile_path)
    raw_out = pathlib.Path(a["--out"])
    # Make sure that the path is in the project first. Thus an outside path never gets the destination message.
    out = PIO.confine(project, raw_out)
    # Refuse a symbolic link before the existing-file test. PIO.confine resolves links.
    lexical_out = raw_out if raw_out.is_absolute() else project.resolve() / raw_out
    if os.path.islink(lexical_out) or os.path.islink(out):
        raise PIO.SymlinkTarget(f"The target {raw_out} is a symbolic link.")
    if out.exists():
        return _fail(EXIT_ARGS, "the destination exists")
    raw_obs = pathlib.Path(a["--observations"]).read_bytes()
    review_record = review.build_review(raw_obs, profile, profile_path.read_bytes(), a["--release"], project)
    if review_record["reviewer"] != a["--reviewer"]:
        return _fail(EXIT_FAIL, "the reviewer differs from the observation file")
    out.parent.mkdir(parents=True, exist_ok=True)
    PIO.atomic_write(project, out, (json.dumps(review_record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    PIO.atomic_write(project, out.parent / "observations.json", raw_obs)
    print(json.dumps({"decision": review_record["decision"], "problems": review_record["problems"],
                      "review_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))
    return EXIT_FAIL if review_record["decision"] == "material" else EXIT_OK


def main(argv):
    if not argv:
        return _fail(EXIT_ARGS, "give a command: profile, judge, review-source, review-gate, drawing-facts, drawing, inspect-slots, inspect-mask")
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "profile":
            a = _args(rest, ["--profile"])
            check_profile(a["--profile"])
            print("profile valid")
            return EXIT_OK
        if cmd == "judge":
            a = _args(rest, ["--kind", "--measured", "--threshold", "--unit"])
            r = judge(a["--kind"], Fraction(a["--measured"]) * UNIT_MM[a["--unit"]],
                      Fraction(a["--threshold"]) * UNIT_MM[a["--unit"]])
            print(r)
            return EXIT_FAIL if r == "fail" else EXIT_OK
        if cmd == "review-source":
            a = _args(rest, ["--project", "--profile", "--release", "--observations", "--reviewer", "--out"])
            project = pathlib.Path(a["--project"])
            # The lock covers the reads and the atomic writes. Another command cannot replace the records during the run.
            with PIO.project_lock(project, "review-source"):
                return _review_source(a, project)
        if cmd == "review-gate":
            a = _args(rest, ["--project", "--profile", "--review", "--expect-sha256", "--release"])
            profile_path = pathlib.Path(a["--profile"])
            refuse_data_only(profile_path, cmd)
            profile = check_profile(profile_path)
            rpath = pathlib.Path(a["--review"])
            problems = review.gate(pathlib.Path(a["--project"]), profile, profile_path.read_bytes(),
                                   rpath.read_bytes() if rpath.is_file() else None, a["--expect-sha256"], a["--release"])
            for p in problems:
                print(f"review-gate: {p}")
            return EXIT_FAIL if problems else EXIT_OK
        if cmd == "drawing-facts":
            a = _args(rest, ["--inventory", "--profile", "--board", "--release", "--out"])
            profile_path = pathlib.Path(a["--profile"])
            refuse_data_only(profile_path, cmd)
            profile = check_profile(profile_path)
            inventory = json.loads(pathlib.Path(a["--inventory"]).read_text())
            facts = drawing_facts(inventory, profile, pathlib.Path(a["--board"]).read_bytes(), a["--release"],
                                  profile_path.read_bytes())
            write_standalone(a["--out"], (json.dumps(facts, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            return EXIT_OK
        if cmd == "drawing":
            a = _args(rest, ["--facts", "--out"])
            facts = json.loads(pathlib.Path(a["--facts"]).read_text())
            write_standalone(a["--out"], drawing_pdf(facts))
            return EXIT_OK
        if cmd == "inspect-slots":
            return inspect_slots.main(rest)
        if cmd == "inspect-mask":
            a = _args(rest, ["--gerber", "--limit-mil", "--report"])
            return run_mask_worker(a["--gerber"], a["--limit-mil"], a["--report"])
        if cmd == "design":
            a = _args(rest, ["--project", "--profile"])
            refuse_data_only(pathlib.Path(a["--profile"]), cmd)
            project = pathlib.Path(a["--project"])
            out = pathlib.Path(rest[rest.index("--out") + 1]) if "--out" in rest else project / "out" / "fab" / "design"
            code, _ = workflow.design(project, pathlib.Path(a["--profile"]), out)
            return code
        if cmd == "supplier":
            a = _args(rest, ["--project", "--profile"])
            refuse_data_only(pathlib.Path(a["--profile"]), cmd)
            project = pathlib.Path(a["--project"])
            design_dir = pathlib.Path(rest[rest.index("--design-dir") + 1]) if "--design-dir" in rest else project / "out" / "fab" / "design"
            out = pathlib.Path(rest[rest.index("--out") + 1]) if "--out" in rest else project / "out" / "fab" / "supplier"
            manual = pathlib.Path(rest[rest.index("--manual") + 1]) if "--manual" in rest else None
            code, _ = workflow.supplier(project, pathlib.Path(a["--profile"]), out, design_dir, manual)
            return code
        if cmd == "package":
            a = _args(rest, ["--project", "--profile", "--release", "--review", "--review-sha256", "--dest"])
            refuse_data_only(pathlib.Path(a["--profile"]), cmd)
            project = pathlib.Path(a["--project"])
            design_dir = project / "out" / "fab" / "design"
            supplier_dir = project / "out" / "fab" / "supplier"
            code, _ = workflow.package(project, pathlib.Path(a["--profile"]), a["--release"], pathlib.Path(a["--review"]),
                                       pathlib.Path(a["--dest"]), design_dir, supplier_dir, a["--review-sha256"])
            return code
        return _fail(EXIT_ARGS, f"unknown command {cmd!r}")
    except Invalid as err:
        return _fail(EXIT_FAIL, f"invalid: {err}")
    except (PIO.LockHeld, PIO.LockMalformed) as err:
        return _fail(EXIT_ARGS, f"the project is locked: {err}")
    except workflow.Stop as err:
        return _fail(err.code, str(err))
    # PIO.SymlinkTarget subclasses PIO.PathEscape. Thus it must come first.
    # These clauses apply to each command. PIO.atomic_write raises them in other commands too.
    except PIO.SymlinkTarget as err:
        return _fail(EXIT_ARGS, f"{err} Give an output path that is not a symbolic link.")
    except PIO.PathEscape as err:
        return _fail(EXIT_ARGS, f"{err} Give a path in the project.")
    except review.ReviewError as err:
        return _fail(EXIT_FAIL, f"invalid observation file: {err}. Correct the file and run the command again.")
    except VAL.RecordError as err:
        return _fail(EXIT_FAIL, f"invalid record: {err}")
    except (OSError, ValueError, KeyError) as err:
        return _fail(EXIT_FAIL, f"invalid input: {err}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
