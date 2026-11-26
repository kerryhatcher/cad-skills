# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///

"""Source review of the supplier pages. Strict records, bound to the release, the profile and every input hash.

Uses the accepted B1 routines of `validate.py`: `parse_record` (strict JSON: no duplicate keys, finite numbers)
and `canonical_hash` (SHA-256 of the canonical JSON without `content_sha256`).

Observation record (`pcb-fab-package/source-observations`, version 1): exact top-level keys
`schema_id`, `schema_version`, `release_id`, `profile_sha256`, `pages`, `observations`, `reviewer`, `statement`.
Each page entry has exact keys `page_id`, `source_url`, `stored_path`, `stored_sha256`, `live_path`,
`live_sha256`, `retrieved`. Each observation has exact keys `key`, `observed_value`, `observed_unit`,
`observed_condition`, `source_url`, `reviewer_reading`.

Review record (`pcb-fab-package/source-review`, version 1) is written by `write_review` and checked by `gate`.
"""
import datetime
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate as VAL  # noqa: E402

SKILL = pathlib.Path(__file__).resolve().parents[1]
PAGES = SKILL / "supplier" / "pages"
OBS_SCHEMA = "pcb-fab-package/source-observations"
REVIEW_SCHEMA = "pcb-fab-package/source-review"
OBS_KEYS = {"schema_id", "schema_version", "release_id", "profile_sha256", "pages", "observations", "reviewer", "statement"}
PAGE_KEYS = {"page_id", "source_url", "stored_path", "stored_sha256", "live_path", "live_sha256", "retrieved"}
OBS_ITEM_KEYS = {"key", "observed_value", "observed_unit", "observed_condition", "source_url", "reviewer_reading"}
LIVE_PREFIX = ("out", "fab", "source-review", "live")
PAGE_SETS = {
    "oshpark-single-layer": {"single-layer", "two-layer"},
    "oshpark-two-layer": {"two-layer"},
    "oshpark-two-layer-hhdc": {"two-layer-hhdc"},
    "oshpark-four-layer": {"four-layer"},
    "oshpark-six-layer": {"six-layer"},
    "jlcpcb-two-layer": {"jlcpcb-pcb-capabilities"},
    "jlcpcb-four-layer": {"jlcpcb-pcb-capabilities"},
}
DECISIONS = ("unchanged", "harmless", "material")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReviewError(Exception):
    """An invalid observation or review record. The caller exits 1 and writes nothing."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _text(value, where, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()) or CONTROL.search(value):
        raise ReviewError(f"{where} must be a non-empty text without control characters")
    return value


def _exact_keys(obj, keys, where):
    if not isinstance(obj, dict):
        raise ReviewError(f"{where} must be a mapping")
    extra = set(obj) - keys
    missing = keys - set(obj)
    if extra:
        raise ReviewError(f"{where} has unknown keys {sorted(extra)}")
    if missing:
        raise ReviewError(f"{where} is missing keys {sorted(missing)}")


def _date(value, where):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ReviewError(f"{where} must be a date YYYY-MM-DD")
    try:
        datetime.date.fromisoformat(value)
    except ValueError as err:
        raise ReviewError(f"{where}: {err}")
    return value


def _relative(value, where):
    """A confined relative path: no absolute path, no `..`, no empty part."""
    if not isinstance(value, str) or not value:
        raise ReviewError(f"{where} must be a path text")
    p = pathlib.PurePosixPath(value)
    if p.is_absolute() or any(part in ("", "..", ".") for part in p.parts):
        raise ReviewError(f"{where} escapes its root: {value!r}")
    return p


def fact_items(profile):
    """Every material fact of the profile: each limit, and each service or process or note extension.
    Return {key: (value, unit, source_url)}."""
    facts = {}
    for key, limit in profile["limits"].items():
        facts[key] = (limit["value"], limit.get("unit", ""), limit["source_url"])
    for key, val in profile["extensions"].items():
        if key == "evidence_pages":
            continue
        if isinstance(val, dict) and "value" in val:
            facts[key] = (val["value"], val.get("unit", ""), val.get("source_url", profile["source_url"]))
        else:
            facts[key] = (val, "", profile["source_url"])
    return facts


def profile_page_urls(profile):
    return {page: entry["source_url"] for page, entry in profile["extensions"]["evidence_pages"].items()}


def value_matches(observed, expected):
    """Strict equality by JSON type: a string is not a number, and a boolean is not a number."""
    if isinstance(expected, bool) or isinstance(observed, bool):
        return isinstance(expected, bool) and isinstance(observed, bool) and observed == expected
    if isinstance(expected, (int, float)):
        return isinstance(observed, (int, float)) and not isinstance(observed, bool) and observed == expected
    if isinstance(expected, str):
        return isinstance(observed, str) and observed == expected
    if isinstance(expected, list):
        return isinstance(observed, list) and observed == expected
    return observed == expected


def parse_observations(raw, profile, release, project_dir):
    """Return (pages, observations, record) after the strict checks. Raise ReviewError for any defect."""
    record = VAL.parse_record(raw, ".json", "observations")
    _exact_keys(record, OBS_KEYS, "observation record")
    if record["schema_id"] != OBS_SCHEMA or record["schema_version"] != 1 or type(record["schema_version"]) is not int:
        raise ReviewError("the observation schema_id or schema_version is wrong")
    if record["release_id"] != release:
        raise ReviewError("the observation file names another release")
    if record["profile_sha256"] != profile["content_sha256"] or not HEX64.match(record["profile_sha256"]):
        raise ReviewError("the observation file names another profile hash")
    _text(record["reviewer"], "reviewer")
    _text(record["statement"], "statement")
    required = PAGE_SETS[profile["id"]]
    urls = profile_page_urls(profile)
    if not isinstance(record["pages"], list):
        raise ReviewError("pages must be a list")
    pages, seen = [], set()
    for i, entry in enumerate(record["pages"]):
        where = f"pages[{i}]"
        _exact_keys(entry, PAGE_KEYS, where)
        page = _text(entry["page_id"], f"{where}.page_id")
        if page in seen:
            raise ReviewError(f"page {page!r} is listed twice")
        seen.add(page)
        if page not in required:
            raise ReviewError(f"page {page!r} is not a page of profile {profile['id']}")
        if entry["source_url"] != urls[page]:
            raise ReviewError(f"page {page!r} has another source_url")
        if _relative(entry["stored_path"], f"{where}.stored_path") != pathlib.PurePosixPath(f"supplier/pages/{page}.html"):
            raise ReviewError(f"page {page!r} names another stored path")
        stored = PAGES / f"{page}.html"
        if not isinstance(entry["stored_sha256"], str) or not HEX64.match(entry["stored_sha256"]):
            raise ReviewError(f"{where}.stored_sha256 must be a SHA-256 text")
        if sha(stored.read_bytes()) != entry["stored_sha256"]:
            raise ReviewError(f"stored_sha256 differs from the stored bytes of {page!r}")
        lp = _relative(entry["live_path"], f"{where}.live_path")
        if lp.parts[:len(LIVE_PREFIX)] != LIVE_PREFIX:
            raise ReviewError("the live path is outside out/fab/source-review/live/")
        live = project_dir.joinpath(*lp.parts)
        if any(p.is_symlink() for p in [project_dir.joinpath(*lp.parts[:i]) for i in range(1, len(lp.parts) + 1)]):
            raise ReviewError("a symbolic link is in the live path")
        if not live.is_file():
            raise ReviewError(f"the live page {page!r} is missing")
        if not isinstance(entry["live_sha256"], str) or not HEX64.match(entry["live_sha256"]):
            raise ReviewError(f"{where}.live_sha256 must be a SHA-256 text")
        if sha(live.read_bytes()) != entry["live_sha256"]:
            raise ReviewError(f"live_sha256 differs from the live bytes of {page!r}")
        _date(entry["retrieved"], f"{where}.retrieved")
        pages.append({"page_id": page, "stored_sha256": entry["stored_sha256"], "live_sha256": entry["live_sha256"],
                      "bytes_equal": stored.read_bytes() == live.read_bytes(), "retrieved": entry["retrieved"],
                      "source_url": entry["source_url"]})
    if seen != required:
        raise ReviewError(f"the observation file must list the pages {sorted(required)}")
    facts = fact_items(profile)
    if not isinstance(record["observations"], list):
        raise ReviewError("observations must be a list")
    obs_seen, obs = set(), []
    for i, item in enumerate(record["observations"]):
        where = f"observations[{i}]"
        _exact_keys(item, OBS_ITEM_KEYS, where)
        key = _text(item["key"], f"{where}.key")
        if key in obs_seen:
            raise ReviewError(f"observation {key!r} is listed twice")
        obs_seen.add(key)
        if key not in facts:
            raise ReviewError(f"unknown observation key {key!r}")
        if not isinstance(item["observed_unit"], str) or CONTROL.search(item["observed_unit"]):
            raise ReviewError(f"{where}.observed_unit must be text")
        _text(item["observed_condition"], f"{where}.observed_condition")
        _text(item["reviewer_reading"], f"{where}.reviewer_reading")
        if item["source_url"] not in set(urls.values()):
            raise ReviewError(f"observation {key!r} names a source_url that is not a page of the profile")
        if item["source_url"] != facts[key][2]:
            raise ReviewError(f"observation {key!r} names another source_url than its fact")
        obs.append(item)
    return pages, obs, record


def compare(obs, profile):
    """Return the list of facts that differ or are missing. An empty list means every fact matches."""
    facts = fact_items(profile)
    found = {item["key"]: item for item in obs}
    problems = [f"missing observation {k!r}" for k in facts if k not in found]
    for key, item in found.items():
        value, unit, _ = facts[key]
        if not value_matches(item["observed_value"], value):
            problems.append(f"{key!r} differs: observed {item['observed_value']!r}, profile {value!r}")
        if item["observed_unit"] != unit:
            problems.append(f"{key!r} unit differs: observed {item['observed_unit']!r}, profile {unit!r}")
    return problems


def decide(pages, problems):
    if problems:
        return "material"
    return "harmless" if any(not p["bytes_equal"] for p in pages) else "unchanged"


def canonical_list_hash(items):
    return sha(json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))


def build_review(raw_obs, profile, profile_file_bytes, release, project_dir):
    """Return the review record. The caller writes it. Raise ReviewError for an invalid observation file."""
    pages, obs, record = parse_observations(raw_obs, profile, release, project_dir)
    problems = compare(obs, profile)
    review = {
        "schema_id": REVIEW_SCHEMA, "schema_version": 1, "release_id": release,
        "profile_sha256": profile["content_sha256"], "profile_file_sha256": sha(profile_file_bytes),
        "observations_file_sha256": sha(raw_obs), "observations": obs,
        "observations_sha256": canonical_list_hash(obs), "pages": pages,
        "problems": problems, "decision": decide(pages, problems),
        "reviewer": record["reviewer"], "statement": record["statement"],
    }
    review["content_sha256"] = VAL.canonical_hash(review)
    return review


def gate(project_dir, profile, profile_file_bytes, review_bytes, expected_sha, release):
    """Verify a review record. Return a list of problems. Empty means the gate passes."""
    problems = []
    if review_bytes is None:
        return ["the source review record is missing"]
    if sha(review_bytes) != expected_sha:
        problems.append("the review bytes differ from the package hash")
    try:
        review = VAL.parse_record(review_bytes, ".json", "REVIEW.json")
    except VAL.RecordError as err:
        return problems + [f"the review record is invalid: {err}"]
    if not isinstance(review, dict) or set(review) != {"schema_id", "schema_version", "release_id", "profile_sha256",
                                                        "profile_file_sha256", "observations_file_sha256",
                                                        "observations", "observations_sha256", "pages", "problems",
                                                        "decision", "reviewer", "statement", "content_sha256"}:
        return problems + ["the review record has the wrong keys"]
    if review["schema_id"] != REVIEW_SCHEMA or review["schema_version"] != 1:
        problems.append("the review schema is wrong")
    if review["release_id"] != release:
        problems.append("the release differs from the package release")
    if review["profile_sha256"] != profile["content_sha256"]:
        problems.append("the profile hash differs")
    if review["profile_file_sha256"] != sha(profile_file_bytes):
        problems.append("the profile file bytes differ")
    if VAL.canonical_hash(review) != review["content_sha256"]:
        problems.append("the review content hash differs")
    if canonical_list_hash(review["observations"]) != review["observations_sha256"]:
        problems.append("the observations differ from the recorded observation hash")
    recomputed = compare(review["observations"], profile)
    if recomputed != review["problems"]:
        problems.append("the recorded comparison differs from the observations")
    expected_pages = PAGE_SETS[profile["id"]]
    if {p["page_id"] for p in review["pages"]} != expected_pages or len(review["pages"]) != len(expected_pages):
        problems.append("the reviewed pages are not the complete page set")
    for page in review["pages"]:
        stored = PAGES / f"{page['page_id']}.html"
        if page["page_id"] not in expected_pages:
            continue
        if sha(stored.read_bytes()) != page["stored_sha256"]:
            problems.append(f"stored page {page['page_id']!r} differs from the reviewed hash")
        live = project_dir / "out" / "fab" / "source-review" / "live" / f"{page['page_id']}.html"
        if not live.is_file() or sha(live.read_bytes()) != page["live_sha256"]:
            problems.append(f"live page {page['page_id']!r} differs from the reviewed hash")
        if page["bytes_equal"] != (stored.read_bytes() == (live.read_bytes() if live.is_file() else b"")):
            problems.append(f"the byte comparison of {page['page_id']!r} differs")
    if decide(review["pages"], recomputed) != review["decision"]:
        problems.append("the recorded decision differs from the recomputed decision")
    if review["decision"] not in ("unchanged", "harmless"):
        problems.append(f"the decision is {review['decision']}")
    return problems
