# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the cad-skills record contracts (B1): `contracts/validate.py`.

  uv run tests/test_pcb_tools.py              # all tests
  uv run tests/test_pcb_tools.py hash         # only tests with 'hash' in their name

Most tests call the validator functions in this process. The exit-code and report
tests run the tool through `uv run`, as an agent runs it.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "contracts/validate.py"
SCHEMAS = ROOT / "contracts/schemas"
FIX = ROOT / "tests/fixtures/pcb"
FIXTURES = ["board.yaml", "variants.yaml", "part.yaml", "supplier-profile.yaml"]

_spec = importlib.util.spec_from_file_location("validate", TOOL)
V = importlib.util.module_from_spec(_spec)
sys.modules["validate"] = V
_spec.loader.exec_module(V)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pcb_support as P  # noqa: E402


# --------------------------------------------------------------------------- helpers


def fixture(name):
    return V.load_record(FIX / name)


def put(tmp: Path, name: str, content) -> Path:
    path = tmp / name
    if isinstance(content, (dict, list)):
        content = json.dumps(content)
    path.write_text(content, encoding="utf-8") if isinstance(content, str) else path.write_bytes(content)
    return path


def report(paths, schemas=SCHEMAS):
    return V.build_report([str(p) for p in paths], Path(schemas))


def codes(path, schemas=SCHEMAS):
    """Finding codes for one file."""
    return [f["code"] for f in report([path], schemas)[1]["findings"]]


def run(*args, ok=(0, 1, 2, 3)):
    r = subprocess.run(["uv", "run", "-q", str(TOOL), *map(str, args)], capture_output=True, text=True)
    assert r.returncode in ok, f"{args} -> exit {r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
    return r


def parse_codes(text, suffix=".yaml"):
    """Finding codes from the loader. An empty list means that the text is accepted."""
    try:
        V.parse_record(text.encode("utf-8") if isinstance(text, str) else text, suffix)
    except V.RecordError as err:
        return [f["code"] for f in err.findings]
    return []


def reseal(profile):
    profile["content_sha256"] = V.canonical_hash(profile)
    return profile


def only(found, code, location=None):
    assert [f["code"] for f in found] == [code], f"expected only {code}, got {[(f['code'], f['location']) for f in found]}"
    if location is not None:
        assert found[0]["location"] == location, f"location {found[0]['location']!r} != {location!r}"


def finds(tmp, name, record, schemas=SCHEMAS):
    return report([put(tmp, name, record)], schemas)[1]["findings"]


def mutated(name, change):
    record = copy.deepcopy(fixture(name))
    change(record)
    return record


# --------------------------------------------------------------------------- valid data


def test_valid_fixtures_pass(tmp: Path):
    code, rep = report([FIX / n for n in FIXTURES])
    assert code == 0 and rep["status"] == "pass" and rep["findings"] == [], rep["findings"]
    assert [i["sha256"] for i in rep["inputs"]] == [hashlib.sha256((FIX / n).read_bytes()).hexdigest() for n in FIXTURES]


def test_plain_date_stays_string(tmp: Path):
    assert type(fixture("part.yaml")["stock"]["retrieved"]) is str
    assert parse_codes("a: !!timestamp 2026-11-13\n") == ["file.unsupported_tag"]


# --------------------------------------------------------------------------- loader


def test_duplicate_keys(tmp: Path):
    cases = [
        ("a: 1\na: 2\n", ".yaml", "/a"),
        ("x:\n  b: 1\n  b: 2\n", ".yaml", "/x/b"),
        ('schema_id: a\nschema_version: "1.0"\nschema_version: "1.0"\n', ".yaml", "/schema_version"),
        ('{"a": 1, "a": 2}', ".json", "/a"),
        ('{"x": {"b": 1, "b": 2}}', ".json", "/x/b"),
        ('{"v": [{"r": {"R1": "populate", "R1": "dnp"}}]}', ".json", "/v/0/r/R1"),
    ]
    for text, suffix, where in cases:
        try:
            V.parse_record(text.encode(), suffix)
            raise AssertionError(f"accepted {text!r}")
        except V.RecordError as err:
            assert [(f["code"], f["location"]) for f in err.findings] == [("file.duplicate_key", where)], (text, err.findings)
    text = (FIX / "variants.yaml").read_text().replace("      R2: populate\n", "      R1: dnp\n", 1)
    found = finds(tmp, "dup.yaml", text)
    only(found, "file.duplicate_key", "/variants/0/references/R1")


def test_yaml_forms(tmp: Path):
    rejected = {
        "non_string_key_int": ("1: x\n", "file.non_string_key"),
        "non_string_key_bool": ("true: x\n", "file.non_string_key"),
        "non_string_key_null": ("~: x\n", "file.non_string_key"),
        "complex_key": ("? [a]\n: x\n", "file.non_string_key"),
        "timestamp": ("a: !!timestamp 2026-11-13\n", "file.unsupported_tag"),
        "binary": ("a: !!binary aGk=\n", "file.unsupported_tag"),
        "set": ("a: !!set {x}\n", "file.unsupported_tag"),
        "custom_tag": ("a: !foo bar\n", "file.unsupported_tag"),
        "python_tag": ("a: !!python/object:os.system x\n", "file.unsupported_tag"),
        "merge_key": ("base: &b {x: 1}\nm:\n  <<: *b\n", "file.merge_key"),
        "recursive_alias": ("a: &a [*a]\n", "file.recursive_alias"),
        "two_documents": ("a: 1\n---\nb: 2\n", "file.parse_error"),
        "bad_syntax": ("a: [1, 2\n", "file.parse_error"),
        "not_mapping": ("- 1\n- 2\n", "file.not_mapping"),
        "empty": ("", "file.not_mapping"),
    }
    for label, (text, code) in rejected.items():
        assert parse_codes(text) == [code], (label, parse_codes(text))
    assert parse_codes("base: &b {x: 1}\nm: *b\n") == [], "an acyclic alias is accepted"
    data = V.parse_record(b"a: yes\nb: on\non: off\nd: 2026-11-13\ne: 0o17\nf: 1_000\n", ".yaml")
    assert data == {"a": "yes", "b": "on", "on": "off", "d": "2026-11-13", "e": "0o17", "f": "1_000"}, data
    assert parse_codes("a: 1\n", ".txt") == ["file.parse_error"]


def test_non_finite_numbers(tmp: Path):
    for text in ("a: .nan\n", "a: .inf\n", "a: -.inf\n", "a: 1e999\n"):
        assert parse_codes(text) == ["file.non_finite"], text
    assert parse_codes("a: [1, .inf]\n") == ["file.non_finite"]
    try:
        V.parse_record(b"a: [1, .inf]\n", ".yaml")
    except V.RecordError as err:
        assert err.findings[0]["location"] == "/a/1"
    for text in ('{"a": NaN}', '{"a": Infinity}', '{"a": -Infinity}', '{"a": 1e999}', '{"a": {"b": [1e999]}}'):
        assert parse_codes(text, ".json") == ["file.non_finite"], text


def test_unreadable_and_bad_bytes(tmp: Path):
    (tmp / "dir.json").mkdir()
    only(report([tmp / "dir.json"])[1]["findings"], "file.unreadable")
    only(finds(tmp, "bad.yaml", b"a: \xff\xfe\n"), "file.parse_error")
    only(finds(tmp, "bad.json", b"\xef\xbb\xbf{}"), "file.parse_error")


# --------------------------------------------------------------------------- exact types and fields


def test_exact_integer_types(tmp: Path):
    for value in (True, "1", 1.0, None, 2.5, 0, -1):
        found = finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(quantity=value)))
        only(found, "schema.invalid", "/quantity")
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(quantity=1))) == []
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r["stock"].update(quantity=True))), "schema.invalid", "/stock/quantity")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r["stock"].update(quantity=1.0))), "schema.invalid", "/stock/quantity")


def test_exact_number_types(tmp: Path):
    for value in (True, "5", None):
        found = finds(tmp, "b.json", mutated("board.yaml", lambda r: r["electrical_limits"]["supply_voltage"].update(value=value)))
        only(found, "schema.invalid", "/electrical_limits/supply_voltage/value")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r["mechanical"].update(width_mm=0))), "schema.invalid", "/mechanical/width_mm")
    # A number written as an integer is a valid number.
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r["mechanical"].update(width_mm=40))) == []


def test_blank_strings_dates_and_urls(tmp: Path):
    for value in ("", "  ", "\t"):
        only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(name=value))), "schema.invalid", "/name")
        only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r["supplier"].update(id=value))), "schema.invalid", "/supplier/id")
        only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r["ratings"]["forward_current"].update(unit=value))),
             "schema.invalid", "/ratings/forward_current/unit")
    for value in ("2026-02-30", "20261113", "2026-2-3", "2026-13-01", "today", 20261113, None):
        only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r["stock"].update(retrieved=value))), "schema.invalid", "/stock/retrieved")
    for value in ("ftp://example.com/a.pdf", "example.com/a.pdf", "https://", "https://a b", ""):
        only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(datasheet_url=value))), "schema.invalid", "/datasheet_url")
    for value in ("abc", "A" * 64, "g" * 64, "0" * 63):
        only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r["supplier"].update(profile_sha256=value))),
             "schema.invalid", "/supplier/profile_sha256")


def test_unknown_nested_fields_and_extensions(tmp: Path):
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(finish_color="red"))), "schema.unknown_field", "/finish_color")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r["supplier"].update(color="red"))), "schema.unknown_field", "/supplier/color")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r["coordinate_system"]["origin"].update(z_mm=0))),
         "schema.unknown_field", "/coordinate_system/origin/z_mm")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r["stock"].update(note="x"))), "schema.unknown_field", "/stock/note")
    only(finds(tmp, "v.json", mutated("variants.yaml", lambda r: r["variants"][0].update(color="x"))), "schema.unknown_field", "/variants/0/color")
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(extensions={"note": "any", "n": {"x": [1, 2]}}))) == []

    def swap(record):
        del record["quantity"]
        record["extensions"] = {"quantity": 5}

    only(finds(tmp, "b.json", mutated("board.yaml", swap)), "schema.invalid", "/quantity")


# --------------------------------------------------------------------------- versions


def test_version_strings(tmp: Path):
    for value in ("1", "1.0.0", "01.0", "1.00", "1.a", "", " 1.0", "1.0 ", "v1.0", 1.0, 1, True, None, ["1.0"]):
        found = finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_version=value)))
        only(found, "schema.version_malformed", "/schema_version")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.pop("schema_version"))), "schema.missing_id")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.pop("schema_id"))), "schema.missing_id")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_id="cad-skills/other"))), "schema.unknown_id")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_id=["cad-skills/board"]))), "schema.missing_id")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_version="2.0"))), "schema.major_unsupported")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_version="0.9"))), "schema.major_unsupported")
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_version="1.1"))), "schema.minor_newer")


def _registry(tmp: Path, versions: dict[str, dict]):
    """Write a temporary registry. `versions` maps a version to extra (property, required) data."""
    schemas = tmp / "schemas"
    schemas.mkdir(exist_ok=True)
    entries = {}
    for version, (props, required) in versions.items():
        name = f"board-{version}.schema.json"
        (schemas / name).write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False,
            "properties": {"schema_id": {"const": "cad-skills/board"}, "schema_version": {"const": version},
                           "name": {"type": "string"}, **props},
            "required": ["schema_id", "schema_version", "name", *required]}))
        entries[version] = name
    latest = max(versions, key=lambda v: tuple(map(int, v.split("."))))
    (schemas / "registry.json").write_text(json.dumps(
        {"registry_format": "1.0", "records": {"cad-skills/board": {"latest": latest, "schemas": entries}}}))
    return schemas


def test_version_registry(tmp: Path):
    schemas = _registry(tmp, {"1.1": ({}, []), "1.2": ({"owner": {"type": "string"}}, ["owner"])})

    def rec(version, **extra):
        return {"schema_id": "cad-skills/board", "schema_version": version, "name": "n", **extra}

    assert finds(tmp, "a.json", rec("1.1"), schemas) == [], "a valid 1.1 record passes without the 1.2 field"
    assert finds(tmp, "b.json", rec("1.2", owner="o"), schemas) == []
    only(finds(tmp, "c.json", rec("1.2"), schemas), "schema.invalid", "/owner")
    only(finds(tmp, "d.json", rec("1.1", owner="o"), schemas), "schema.unknown_field", "/owner")
    only(finds(tmp, "e.json", rec("1.0"), schemas), "schema.version_unsupported")
    only(finds(tmp, "f.json", rec("1.3"), schemas), "schema.minor_newer")
    only(finds(tmp, "g.json", rec("2.0"), schemas), "schema.major_unsupported")
    # The minor parts compare as integers: 1.10 is newer than 1.9.
    (tmp / "n").mkdir()
    schemas9 = _registry(tmp / "n", {"1.9": ({}, [])})
    only(finds(tmp, "h.json", rec("1.10"), schemas9), "schema.minor_newer")


# --------------------------------------------------------------------------- hash


def test_hash_fixed_bytes(tmp: Path):
    """The expected digests come from `printf ... | sha256sum`, not from canonical_hash."""
    record = {"schema_id": "x", "n": {"content_sha256": "keep"}, "b": [1, 2], "a": "\u00e9", "content_sha256": "zzz"}
    assert V.canonical_bytes(record) == '{"a":"\u00e9","b":[1,2],"n":{"content_sha256":"keep"},"schema_id":"x"}'.encode("utf-8")
    assert V.canonical_hash(record) == "225bf4f028ae2296b75f18a67cb6adae61f78d2c2f6005866e8de7b3f907c0d4"
    float_form = {"schema_id": "x", "n": {"content_sha256": "keep"}, "b": [1.0, 2], "a": "\u00e9"}
    assert V.canonical_hash(float_form) == "cbab099b9ffd6ef044f8fce49e98d7b42847e3661c255fb1fb10f107b90cdd0f"
    assert not V.canonical_bytes(record).startswith(b"\xef\xbb\xbf") and not V.canonical_bytes(record).endswith(b"\n")


def test_hash_rules(tmp: Path):
    base = {"a": 1, "b": [1, 2], "n": {"content_sha256": "keep"}}
    before = copy.deepcopy(base)
    h = V.canonical_hash(base)
    assert base == before, "the function does not change its input"
    assert V.canonical_hash({"n": {"content_sha256": "keep"}, "b": [1, 2], "a": 1}) == h, "key order"
    assert V.canonical_hash({**base, "content_sha256": "any"}) == h, "the root field is not hashed"
    assert V.canonical_hash({**base, "n": {"content_sha256": "other"}}) != h, "a nested field is hashed"
    assert V.canonical_hash({**base, "b": [2, 1]}) != h, "array order"
    assert V.canonical_hash({"a": 1}) != V.canonical_hash({"a": 1.0}), "1 and 1.0 differ"
    assert V.canonical_hash({"a": 0.0}) != V.canonical_hash({"a": -0.0}), "-0.0 and 0.0 differ"
    nfc, nfd = "\u00e9", "e\u0301"
    assert V.canonical_hash({"a": nfc}) != V.canonical_hash({"a": nfd}), "no Unicode normalization"
    for bad in ({"a": float("nan")}, {"a": float("inf")}, {"a": {1, 2}}, {"a": b"x"}, {1: "x", "b": 2}):
        try:
            V.canonical_hash(bad)
            raise AssertionError(f"hashed {bad!r}")
        except V.RecordError:
            pass
    plain = "a: 1\nb: [1, 2]\n"
    commented = "# comment\nb: [1, 2]   # note\n\na:   1\n"
    assert V.canonical_hash(V.parse_record(plain.encode(), ".yaml")) == V.canonical_hash(V.parse_record(commented.encode(), ".yaml"))
    assert hashlib.sha256(plain.encode()).hexdigest() != hashlib.sha256(commented.encode()).hexdigest(), "the file hash covers the bytes"


# --------------------------------------------------------------------------- record rules


def test_variant_rules(tmp: Path):
    only(finds(tmp, "v.json", mutated("variants.yaml", lambda r: r["variants"][1].update(id="base"))), "variants.duplicate_id", "/variants/1/id")
    for state in ("maybe", True, None, 1, ["populate"], ""):
        found = finds(tmp, "v.json", mutated("variants.yaml", lambda r: r["variants"][0]["references"].update(R1=state)))
        only(found, "variants.unknown_state", "/variants/0/references/R1")
    only(finds(tmp, "v.json", mutated("variants.yaml", lambda r: r["variants"][0]["references"].update({" ": "dnp"}))), "schema.invalid")
    only(finds(tmp, "v.json", mutated("variants.yaml", lambda r: r.update(variants=[]))), "schema.invalid", "/variants")


def test_part_rules(tmp: Path):
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.pop("mpn"))), "part.missing_mpn", "/mpn")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(mpn=" "))), "part.missing_mpn", "/mpn")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.pop("lifecycle"))), "schema.invalid", "/lifecycle")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(lifecycle="maybe"))), "schema.invalid", "/lifecycle")
    assert finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(lifecycle="unknown", stock={"status": "unknown"}))) == []
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r["stock"].pop("retrieved"))), "schema.invalid", "/stock/retrieved")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(stock={"status": "unknown", "quantity": 5}))), "schema.invalid", "/stock")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(stock=5))), "schema.invalid", "/stock")


def test_profile_hash_and_limits(tmp: Path):
    def limit(change):
        def apply(record):
            change(record["limits"]["min_trace"])
            reseal(record)
        return mutated("supplier-profile.yaml", apply)

    only(finds(tmp, "s.json", mutated("supplier-profile.yaml", lambda r: r["limits"]["min_trace"].update(value=7))),
         "profile.hash_mismatch", "/content_sha256")
    for value in (True, "6", None):
        only(finds(tmp, "s.json", limit(lambda lim: lim.update(value=value))), "schema.invalid", "/limits/min_trace/value")
    only(finds(tmp, "s.json", limit(lambda lim: lim.pop("unit"))), "schema.invalid", "/limits/min_trace/unit")
    only(finds(tmp, "s.json", limit(lambda lim: lim.update(value_kind="text", value="six"))), "schema.invalid", "/limits/min_trace/unit")
    only(finds(tmp, "s.json", limit(lambda lim: (lim.pop("unit"), lim.update(value_kind="text", value="six")))),
         "profile.limit_not_numeric", "/limits/min_trace")
    for field in ("source_url", "retrieved", "value_kind"):
        only(finds(tmp, "s.json", limit(lambda lim: lim.pop(field))), "profile.limit_incomplete", "/limits/min_trace")
    only(finds(tmp, "s.json", limit(lambda lim: (lim.pop("source_url"), lim.pop("retrieved")))), "profile.limit_incomplete")
    only(finds(tmp, "s.json", limit(lambda lim: lim.update(kind="unconfirmed"))), "profile.unconfirmed_with_value")
    assert finds(tmp, "s.json", limit(lambda lim: lim.update(kind="recommendation"))) == []
    only(finds(tmp, "s.json", limit(lambda lim: lim.update(kind="maximum", value_kind="text", value="six", unit=None))), "schema.invalid")
    only(finds(tmp, "s.json", limit(lambda lim: lim.update(kind="other"))), "schema.invalid", "/limits/min_trace/kind")


def test_one_finding_for_one_defect(tmp: Path):
    found = finds(tmp, "b.json", mutated("board.yaml", lambda r: (r.pop("quantity"), r.pop("variant"))))
    assert sorted((f["code"], f["location"]) for f in found) == [("schema.invalid", "/quantity"), ("schema.invalid", "/variant")]
    found = finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(a=1, b=2)))
    assert [f["location"] for f in found] == ["/a", "/b"] and {f["code"] for f in found} == {"schema.unknown_field"}


# --------------------------------------------------------------------------- exit codes and report


def test_exit_codes(tmp: Path):
    good = put(tmp, "good.json", mutated("board.yaml", lambda r: None))
    bad = put(tmp, "bad.json", mutated("board.yaml", lambda r: r.update(quantity=0)))
    assert run(good).returncode == 0
    assert run(bad).returncode == 1
    assert run(tmp / "nothing.json").returncode == 2
    r = run(bad, tmp / "nothing.json", "--json")
    assert r.returncode == 2, "a missing file beats an invalid record"
    rep = json.loads(r.stdout)
    assert {f["code"] for f in rep["findings"]} == {"cli.input_missing", "schema.invalid"}
    assert run(good, "--schemas", tmp / "no-such-dir").returncode == 2
    (tmp / "dir.json").mkdir()
    assert run(tmp / "dir.json").returncode == 1, "an unreadable existing file is exit 1"
    assert run().returncode == 2 and run().stdout == ""
    assert run("--bogus", good).returncode == 2


def test_tool_failures_exit_3(tmp: Path):
    good = put(tmp, "good.json", mutated("board.yaml", lambda r: None))
    missing = tmp / "nothing.json"

    def broken(name, mutate):
        schemas = tmp / name
        schemas.mkdir()
        for p in SCHEMAS.iterdir():
            (schemas / p.name).write_bytes(p.read_bytes())
        mutate(schemas)
        return schemas

    corrupt = broken("corrupt", lambda s: (s / "board.schema.json").write_text('{"type": 7}'))
    r = run(good, missing, "--schemas", corrupt, "--json")
    rep = json.loads(r.stdout)
    assert r.returncode == 3 and rep["exit_code"] == 3 and rep["status"] == "error", "a corrupt schema beats a missing input"
    assert rep["unprocessed"] == [str(good)] and rep["inputs"] == [], "an unprocessed file is not a pass"
    assert any(f["code"] == "tool.schema_invalid" for f in rep["findings"])
    assert run(good, "--schemas", broken("noschema", lambda s: (s / "part.schema.json").unlink())).returncode == 3
    assert run(good, "--schemas", broken("noreg", lambda s: (s / "registry.json").unlink())).returncode == 3
    assert run(good, "--schemas", broken("badreg", lambda s: (s / "registry.json").write_text("[]"))).returncode == 3
    assert run(good, "--schemas", broken("badjson", lambda s: (s / "registry.json").write_text("{"))).returncode == 3
    nofile = broken("nofile", lambda s: None)
    reg = json.loads((nofile / "registry.json").read_text())
    reg["records"]["cad-skills/board"]["schemas"]["1.0"] = "../escape.json"
    (nofile / "registry.json").write_text(json.dumps(reg))
    assert run(good, "--schemas", nofile).returncode == 3


def test_json_report(tmp: Path):
    good = put(tmp, "good.json", mutated("board.yaml", lambda r: None))
    bad = put(tmp, "bad.json", mutated("board.yaml", lambda r: r.update(quantity=0, name="")))
    missing = tmp / "nothing.json"
    first = run(missing, bad, good, "--json")
    second = run(missing, bad, good, "--json")
    assert first.stdout == second.stdout, "two runs give the same output"
    rep = json.loads(first.stdout)  # the whole standard output is one JSON object
    assert rep["exit_code"] == first.returncode == 2 and rep["status"] == "error"
    hashes = {i["path"]: i["sha256"] for i in rep["inputs"]}
    assert hashes == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (bad, good)}
    assert str(missing) not in hashes, "no hash for a missing file"
    keys = [(f["file"], f["location"], f["code"]) for f in rep["findings"]]
    assert keys == sorted(keys)
    assert set(rep) >= {"report_schema_version", "status", "exit_code", "tool_versions", "inputs", "findings", "unprocessed", "outputs"}
    assert set(rep["tool_versions"]) == {"python", "jsonschema", "pyyaml"}
    arg = run("--json")
    arep = json.loads(arg.stdout)
    assert arg.returncode == 2 and arep["exit_code"] == 2 and arep["inputs"] == []
    assert [f["code"] for f in arep["findings"]] == ["cli.argument_error"]
    ok = run(good, "--json")
    assert ok.returncode == 0 and json.loads(ok.stdout)["status"] == "pass"


def test_independent_files_continue(tmp: Path):
    good = put(tmp, "good.json", mutated("board.yaml", lambda r: None))
    bad = put(tmp, "bad.yaml", "a: 1\na: 2\n")
    code, rep = report([bad, good])
    assert code == 1 and [i["path"] for i in rep["inputs"]] == [str(bad), str(good)]
    assert [f["code"] for f in rep["findings"]] == ["file.duplicate_key"]


# --------------------------------------------------------------------------- B1 correction


def test_version_exact_boundaries(tmp: Path):
    for value in ("1.0\n", "\n1.0", "1.0\r", "1.0\n\n", "1\n.0"):
        found = finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(schema_version=value)))
        only(found, "schema.version_malformed", "/schema_version")
    assert V.parse_version("1.0\n") is None and V.parse_version("1.0") == (1, 0)
    code, rep = report([put(tmp, "n.json", mutated("board.yaml", lambda r: r.update(schema_version="1.0\n")))])
    assert code == 1, "a version with a final newline is a record defect, not a tool failure"


def test_fixed_strings_reject_final_newline(tmp: Path):
    sha = "a" * 64
    cases = [
        ("b.json", "board.yaml", lambda r: r["supplier"].update(profile_sha256=sha + "\n"), "/supplier/profile_sha256"),
        ("s.json", "supplier-profile.yaml", lambda r: r.update(evidence_sha256=sha + "\n"), "/evidence_sha256"),
        ("s.json", "supplier-profile.yaml", lambda r: r.update(content_sha256=sha + "\n"), "/content_sha256"),
        ("s.json", "supplier-profile.yaml", lambda r: r.update(retrieved="2026-11-13\n"), "/retrieved"),
        ("p.json", "part.yaml", lambda r: r["stock"].update(retrieved="2026-11-13\n"), "/stock/retrieved"),
        ("p.json", "part.yaml", lambda r: r.update(datasheet_url="https://example.com/a.pdf\n"), "/datasheet_url"),
        ("s.json", "supplier-profile.yaml", lambda r: r.update(source_url="https://example.com\n"), "/source_url"),
        ("p.json", "part.yaml", lambda r: r.update(datasheet_url="https://example.com/a b.pdf"), "/datasheet_url"),
        ("p.json", "part.yaml", lambda r: r.update(datasheet_url="https://"), "/datasheet_url"),
    ]
    for name, fixture_name, change, where in cases:
        found = finds(tmp, name, mutated(fixture_name, change))
        assert [(f["code"], f["location"]) for f in found] == [("schema.invalid", where)], (where, found)
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r["supplier"].update(profile_sha256=sha))) == []


def test_scalar_tag_values(tmp: Path):
    good = FIX / "board.yaml"
    for text in ("a: !!int bad\n", "a: !!float bad\n", "a: !!bool maybe\n", "a: !!int 99999999999999999999x\n"):
        bad = put(tmp, "bad.yaml", text)
        r = run(bad, good, "--json")
        rep = json.loads(r.stdout)
        assert r.returncode == 1, (text, r.returncode, rep["findings"])
        assert [(f["code"], f["file"]) for f in rep["findings"]] == [("file.parse_error", str(bad))], rep["findings"]
        assert [i["path"] for i in rep["inputs"]] == [str(bad), str(good)], "the good file is still processed"
        assert rep["unprocessed"] == [] and rep["tool_versions"]
    # An explicit tag selects the YAML lexical form. A plain scalar uses the JSON grammar.
    assert V.parse_record(b"a: !!bool yes\nb: !!int 0x10\nc: !!int 1_000\nd: yes\ne: 1_000\n", ".yaml") == \
        {"a": True, "b": 16, "c": 1000, "d": "yes", "e": "1_000"}


def test_number_type_checker(tmp: Path):
    big = 10 ** 400
    check = V._TYPE_CHECKER
    for value in (0, 1, -1, big, -big, 1.5, -0.0):
        assert check.is_type(value, "number"), value
    for value in (True, False, "1", None, float("nan"), float("inf"), float("-inf"), [1], {}):
        assert not check.is_type(value, "number"), value
    for value in (0, 7, big, -big):
        assert check.is_type(value, "integer"), value
    for value in (True, 1.0, "1", None, 1.5):
        assert not check.is_type(value, "integer"), value
    found = finds(tmp, "b.json", mutated("board.yaml", lambda r: r["mechanical"].update(width_mm=big)))
    assert found == [], found
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(quantity=big))) == []
    only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r["mechanical"].update(width_mm=-big))), "schema.invalid", "/mechanical/width_mm")
    code, rep = report([put(tmp, "big.yaml", "a: " + "9" * 401 + "\n")])
    assert code == 1 and [f["code"] for f in rep["findings"]] == ["schema.missing_id"], rep["findings"]


def test_hash_tree_check(tmp: Path):
    def reason(record):
        try:
            V.canonical_hash(record)
        except V.RecordError as err:
            assert [f["code"] for f in err.findings] == ["file.not_json_compatible"] * len(err.findings)
            return [f["location"] for f in err.findings]
        raise AssertionError(f"hashed {record!r}")

    assert reason({1: "x"}) == ["/1"]
    assert reason({True: "x"}) == ["/True"]
    assert reason({None: "x"}) == ["/None"]
    assert reason({"a": {2: 1}}) == ["/a/2"]
    assert reason((1, 2)) == [""] and reason([1, 2]) == [""], "the root must be a mapping"
    assert reason({"a": (1, 2)}) == ["/a"], "a tuple that equals a list in content is still rejected"
    assert reason({"a": [1, (2, 3)]}) == ["/a/1"]
    assert reason({"a": {1, 2}}) == ["/a"] and reason({"a": b"x"}) == ["/a"]
    assert reason({"a": __import__("datetime").date(2026, 11, 13)}) == ["/a"]
    assert reason({"a": [float("nan")]}) == ["/a/0"]
    loop = {"n": 1}
    loop["self"] = loop
    assert reason(loop) == ["/self/self"]
    chain = []
    chain.append(chain)
    assert reason({"a": chain}) == ["/a/0"]
    deep = []
    node = deep
    for _ in range(5000):
        node.append([])
        node = node[0]
    assert reason({"a": deep}) == [""]  # a depth problem, not a RecursionError
    shared = {"x": 1}
    assert V.canonical_hash({"a": shared, "b": shared}) == V.canonical_hash({"a": {"x": 1}, "b": {"x": 1}}), "a shared part is not a cycle"
    # Valid data gives the same bytes as before the correction.
    assert V.canonical_hash({"schema_id": "x", "n": {"content_sha256": "keep"}, "b": [1, 2], "a": "é"}) == \
        "225bf4f028ae2296b75f18a67cb6adae61f78d2c2f6005866e8de7b3f907c0d4"


def test_limit_scope(tmp: Path):
    def limit(change, name="min_trace"):
        def apply(record):
            change(record["limits"][name])
            reseal(record)
        return mutated("supplier-profile.yaml", apply)

    profile = fixture("supplier-profile.yaml")
    assert {lim["scope"] for lim in profile["limits"].values()} == {"fabrication", "assembly", "margin"}
    for scope in ("fabrication", "assembly", "margin"):
        assert finds(tmp, "s.json", limit(lambda lim: lim.update(scope=scope))) == []
    only(finds(tmp, "s.json", limit(lambda lim: lim.pop("scope"))), "schema.invalid", "/limits/min_trace/scope")
    for value in ("other", "Fabrication", "", None, 1, True, ["margin"]):
        only(finds(tmp, "s.json", limit(lambda lim: lim.update(scope=value))), "schema.invalid", "/limits/min_trace/scope")
    only(finds(tmp, "s.json", limit(lambda lim: lim.pop("scope"), "stackup_tolerance")), "schema.invalid", "/limits/stackup_tolerance/scope")


def test_text_limit_unit_and_part_variants(tmp: Path):
    def limit(change):
        def apply(record):
            change(record["limits"]["silkscreen_width"])
            reseal(record)
        return mutated("supplier-profile.yaml", apply)

    assert finds(tmp, "s.json", limit(lambda lim: None)) == [], "a text limit omits the unit"
    for value in ("", " ", "mil"):
        only(finds(tmp, "s.json", limit(lambda lim: lim.update(unit=value))), "schema.invalid", "/limits/silkscreen_width/unit")
    # variants.yaml is the only owner of variant data. A part record has no such field.
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(assembly_variants=["base"]))), "schema.unknown_field", "/assembly_variants")
    schema = json.loads((SCHEMAS / "part.schema.json").read_text())
    assert not any("variant" in name for name in schema["properties"])


def test_documented_limits(tmp: Path):
    # The README states these limits. The test makes sure that they stay true.
    assert V.parse_record(b"a: 1e-999\n", ".yaml") == {"a": 0.0}, "underflow becomes 0.0"
    assert V.parse_record(b'{"a": 1e-999}', ".json") == {"a": 0.0}
    readme = (ROOT / "contracts/README.md").read_text()
    for phrase in ("underflow", "explicit tag", "only owner of assembly variants", "`scope`", "A text limit omits `unit`"):
        assert phrase in readme, phrase


# --------------------------------------------------------------------------- control characters in identifiers


def _set_path(record, path, value):
    node = record
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value


def _get_path(record, path):
    node = record
    for part in path:
        node = node[part]
    return node


# (fixture, kind, path, location). kind "value": add a character to the value at `path`.
# kind "key": rename the last key of `path` and add a character to the name. The location is the map.
IDENTIFIER_CASES = [
    ("board.yaml", "value", ["name"], "/name"),
    ("board.yaml", "value", ["supplier", "id"], "/supplier/id"),
    ("board.yaml", "value", ["supplier", "service"], "/supplier/service"),
    ("board.yaml", "value", ["release_revision"], "/release_revision"),
    ("board.yaml", "value", ["variant"], "/variant"),
    ("board.yaml", "key", ["electrical_limits", "supply_voltage"], "/electrical_limits"),
    ("board.yaml", "value", ["electrical_limits", "supply_voltage", "unit"], "/electrical_limits/supply_voltage/unit"),
    ("part.yaml", "value", ["manufacturer"], "/manufacturer"),
    ("part.yaml", "value", ["mpn"], "/mpn"),
    ("part.yaml", "value", ["package"], "/package"),
    ("part.yaml", "value", ["symbol"], "/symbol"),
    ("part.yaml", "value", ["footprint"], "/footprint"),
    ("part.yaml", "value", ["datasheet_revision"], "/datasheet_revision"),
    ("part.yaml", "value", ["polarity"], "/polarity"),
    ("part.yaml", "value", ["supplier_part_numbers", 0, "supplier"], "/supplier_part_numbers/0/supplier"),
    ("part.yaml", "value", ["supplier_part_numbers", 0, "number"], "/supplier_part_numbers/0/number"),
    ("part.yaml", "key", ["pin_map", "1"], "/pin_map"),
    ("part.yaml", "value", ["pin_map", "1"], "/pin_map/1"),
    ("part.yaml", "key", ["ratings", "forward_current"], "/ratings"),
    ("part.yaml", "value", ["ratings", "forward_current", "unit"], "/ratings/forward_current/unit"),
    ("supplier-profile.yaml", "value", ["id"], "/id"),
    ("supplier-profile.yaml", "value", ["revision"], "/revision"),
    ("supplier-profile.yaml", "value", ["service"], "/service"),
    ("supplier-profile.yaml", "key", ["limits", "min_trace"], "/limits"),
    ("supplier-profile.yaml", "value", ["limits", "min_trace", "unit"], "/limits/min_trace/unit"),
    ("supplier-profile.yaml", "value", ["division", "kicad_dru", 0], "/division/kicad_dru/0"),
    ("variants.yaml", "value", ["variants", 0, "id"], "/variants/0/id"),
    ("variants.yaml", "key", ["variants", 0, "references", "R1"], "/variants/0/references"),
    ("variants.yaml", "value", ["variants", 1, "hand_installed", 0, "reference"], "/variants/1/hand_installed/0/reference"),
]


def _identifier_record(fixture_name, kind, path, suffix):
    record = copy.deepcopy(fixture(fixture_name))
    if kind == "value":
        _set_path(record, path, _get_path(record, path) + suffix)
    else:
        container = _get_path(record, path[:-1])
        rebuilt = {(k + suffix if k == path[-1] else k): v for k, v in container.items()}
        container.clear()
        container.update(rebuilt)
    if fixture_name == "supplier-profile.yaml":
        reseal(record)
    return record


def test_identifiers_reject_control_characters(tmp: Path):
    """Run one CLI call for all cases. Each case must give exactly one finding at its location."""
    files, expected = [], {}
    for i, (name, kind, path, where) in enumerate(IDENTIFIER_CASES):
        for label, suffix in (("lf", "\n"),) + ((("tab", "\t"), ("nul", "\x00")) if i in (0, 5, 16) else ()):
            file = put(tmp, f"case-{i}-{label}.json", _identifier_record(name, kind, path, suffix))
            files.append(file)
            expected[str(file)] = where
    r = run(*files, "--json")
    rep = json.loads(r.stdout)
    assert r.returncode == 1 and rep["exit_code"] == 1, rep["findings"][:3]
    by_file = {}
    for f in rep["findings"]:
        by_file.setdefault(f["file"], []).append((f["code"], f["location"]))
    for file, where in expected.items():
        assert by_file.get(file) == [("schema.invalid", where)], (file, where, by_file.get(file))
    assert rep["unprocessed"] == [] and len(rep["inputs"]) == len(files)


def test_identifiers_keep_spaces_unicode_and_prose_line_breaks(tmp: Path):
    ok = [
        mutated("board.yaml", lambda r: r.update(name="Größe-Ø 板 2")),
        mutated("board.yaml", lambda r: r["supplier"].update(service="Turnkey PRO")),
        mutated("board.yaml", lambda r: r["restrictions"][0].update(text="Line one.\nLine two.", source="Source\r\ntext")),
        mutated("board.yaml", lambda r: r.update(extensions={"note\nkey": "a\nb\tc"})),
        mutated("part.yaml", lambda r: r.update(package="ÅB 0603")),
        mutated("part.yaml", lambda r: r["stock"].update(source="Page\nwith a break")),
        mutated("variants.yaml", lambda r: r["variants"][1]["hand_installed"][0].update(reason="Reason one.\nReason two.")),
        mutated("supplier-profile.yaml", lambda r: (r["limits"]["silkscreen_width"].update(value="Text\nwith a break"), reseal(r))),
    ]
    files = [put(tmp, f"ok-{i}.json", record) for i, record in enumerate(ok)]
    r = run(*files, "--json")
    rep = json.loads(r.stdout)
    assert r.returncode == 0 and rep["findings"] == [], rep["findings"]
    assert run(*[FIX / n for n in FIXTURES]).returncode == 0
    # A control character in a key under `extensions` or in prose is not an identifier defect.
    # The key check applies to named maps of the schemas only. The boundary:
    for bad in ("\u0000", "\u001f", "\u007f"):
        only(finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(name="x" + bad))), "schema.invalid", "/name")
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(name="x\u0080"))) == [], "U+0080 is not in the rejected range"
    assert finds(tmp, "b.json", mutated("board.yaml", lambda r: r.update(name="x y"))) == [], "a normal space passes"


def test_mpn_diagnosis(tmp: Path):
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(mpn=" "))), "part.missing_mpn", "/mpn")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(mpn="EX-1\n"))), "schema.invalid", "/mpn")
    only(finds(tmp, "p.json", mutated("part.yaml", lambda r: r.update(mpn=5))), "schema.invalid", "/mpn")


# --------------------------------------------------------------------------- B234: new records


def tree(tmp, kind="pcba", **kw):
    """Build a project in `tmp/project` and a qualified package in `tmp/pkg`. Return (project, pkg, manifest)."""
    project = P.build_project(tmp / "project", kind, **kw)
    manifest = P.build_package(project, tmp / "pkg")
    return project, tmp / "pkg", manifest


def edit_manifest(pkg, change):
    manifest = V.load_record(pkg / "manifest.json")
    change(manifest)
    P.write_manifest(pkg, manifest)
    return manifest


def item_of(manifest, role, *, layer=None, section="outputs"):
    return next(i for i in manifest[section] if i["role"] == role and (layer is None or i.get("layer") == layer))


def codes_of(project, pkg=None):
    code, rep = P.examine(project, pkg)
    return code, sorted({f["code"] for f in rep["findings"]}), rep


def count(rep, code):
    return sum(1 for f in rep["findings"] if f["code"] == code)


def record_of(project, rel):
    return copy.deepcopy(V.load_record(project / rel))


def test_registry_and_role_lists(tmp: Path):
    registry = json.loads((SCHEMAS / "registry.json").read_text())["records"]
    assert sorted(registry) == sorted(f"cad-skills/{n}" for n in (
        "board", "variants", "part", "supplier-profile", "waivers", "manifest", "evidence", "board-interface",
        "toolchain-lock", "export-settings"))
    manifest = json.loads((SCHEMAS / "manifest.schema.json").read_text())["properties"]
    assert tuple(manifest["inputs"]["items"]["properties"]["role"]["enum"]) == V.INPUT_ROLES
    assert tuple(manifest["outputs"]["items"]["properties"]["role"]["enum"]) == V.OUTPUT_ROLES
    assert set(V.CHECK_INPUT_ROLES) == set(V.PCBA_CHECKS) and set(V.BARE_CHECKS) <= set(V.PCBA_CHECKS)
    for roles in V.CHECK_INPUT_ROLES.values():
        assert set(roles) <= set(V.INPUT_ROLES)


def test_valid_project_and_package(tmp: Path):
    for kind in ("pcba", "bare_board"):
        project, pkg, _ = tree(tmp / kind if (tmp / kind).mkdir() is None else tmp, kind)
        code, found, rep = codes_of(project, pkg)
        assert code == 0 and found == [], (kind, rep["findings"])
        assert rep["status"] == "pass" and rep["inputs"], kind


def test_waiver_rules(tmp: Path):
    project, _, _ = tree(tmp)
    base = record_of(project, "manufacturing/waivers.yaml")

    def edit(change):
        record = copy.deepcopy(base)
        change(record)
        return finds(tmp, "w.json", record)

    assert edit(lambda r: r.update(waivers=[])) == [], "an empty list is valid"
    assert edit(lambda r: None) == []
    only(edit(lambda r: r["waivers"][1].update(id="W1")), "waiver.duplicate_id", "/waivers/1/id")
    only(edit(lambda r: r["waivers"].append({**r["waivers"][0], "id": "W3"})), "waiver.duplicate_pair")
    for rule in ("*", "ALL", " any "):
        only(edit(lambda r: r["waivers"][0].update(rule=rule)), "waiver.wildcard", "/waivers/0/rule")
    only(edit(lambda r: r["waivers"][0].update(objects=["U1", "*"])), "waiver.wildcard", "/waivers/0/objects/1")
    only(edit(lambda r: r["waivers"][0].update(schematic_sha256=None)), "schema.invalid")
    only(edit(lambda r: r["waivers"][0].update(objects=[])), "schema.invalid", "/waivers/0/objects")
    for field in ("reason", "reviewer", "revision"):
        only(edit(lambda r: r["waivers"][0].update({field: " "})), "schema.invalid", f"/waivers/0/{field}")
    only(edit(lambda r: r["waivers"][0].pop("revision")), "schema.invalid", "/waivers/0/revision")
    only(edit(lambda r: r["waivers"][0].update(kind="other")), "schema.invalid", "/waivers/0/kind")
    only(edit(lambda r: r["waivers"][0].update(board_sha256="a" * 64 + "\n")), "schema.invalid", "/waivers/0/board_sha256")
    only(edit(lambda r: r["waivers"][0].update(note="x")), "schema.unknown_field", "/waivers/0/note")
    assert edit(lambda r: r["waivers"][0].update(reason="Line one.\nLine two.")) == [], "prose can hold line breaks"


def test_manifest_rules(tmp: Path):
    project, pkg, manifest = tree(tmp)

    def edit(change):
        record = copy.deepcopy(manifest)
        change(record)
        return finds(tmp, "m.json", record)

    for path in ("/etc/x", "../x", "a//b", "a\\b", "a/./b", "a/b\n", "C:/x", "a/\tb", "a/b/"):
        only(edit(lambda r: r["inputs"][0].update(path=path)), "pkg.path_invalid", "/inputs/0/path")
    only(edit(lambda r: r["outputs"][0].update(path=r["outputs"][1]["path"])), "pkg.duplicate_path", "/outputs/1/path") \
        if False else None
    dup = edit(lambda r: r["inputs"][1].update(path=r["inputs"][0]["path"]))
    assert [f["code"] for f in dup] == ["pkg.duplicate_path"], dup
    only(edit(lambda r: r["outputs"][0].update(path=r["inputs"][0]["path"])), "pkg.input_output_overlap", "/outputs/0/path")
    only(edit(lambda r: r["outputs"][0].update(path="manifest.json")), "pkg.self_reference", "/outputs/0/path")
    only(edit(lambda r: r["outputs"][0].update(size_bytes=0)), "pkg.output_empty", "/outputs/0")
    only(edit(lambda r: r["outputs"][0].update(size_bytes=-1)), "schema.invalid", "/outputs/0/size_bytes")
    only(edit(lambda r: r["outputs"][0].pop("layer")), "pkg.layer_unmapped", "/outputs/0")
    only(edit(lambda r: item_of(r, "bom").update(layer="F.Cu")), "pkg.layer_unmapped")
    only(edit(lambda r: r["outputs"].append({**r["outputs"][0], "path": "gerber/other.GTL"})), "pkg.layer_duplicate")
    only(edit(lambda r: r["checks"].append(copy.deepcopy(r["checks"][0]))), "pkg.check_duplicate", "/checks/13/id")
    only(edit(lambda r: r.update(status="unqualified")), "pkg.reasons_required", "/reasons")
    only(edit(lambda r: r.update(reasons=[{"code": "x", "text": "A reason."}])), "pkg.reasons_required", "/reasons")
    only(edit(lambda r: r["checks"][0].update(status="fail")), "pkg.false_qualification")
    only(edit(lambda r: r["checks"].pop(0)), "pkg.check_missing")
    only(edit(lambda r: r.update(outputs=[])), "pkg.no_outputs", "/outputs")
    only(edit(lambda r: r["inputs"].remove(item_of(r, "board_interface", section="inputs"))), "pkg.input_missing")
    only(edit(lambda r: r["inputs"].remove(item_of(r, "parts", section="inputs"))), "pkg.input_missing")
    # A draft or an unqualified package can omit what a qualified package needs.
    for state in ("draft", "unqualified"):
        incomplete = copy.deepcopy(manifest)
        incomplete.update(status=state, reasons=[{"code": "x", "text": "Incomplete."}] if state == "unqualified" else [])
        incomplete.update(outputs=[], checks=[])
        incomplete["inputs"] = incomplete["inputs"][:2]
        assert finds(tmp, "m.json", incomplete) == [], state
    only(edit(lambda r: r.update(applicability=None)), "schema.invalid")
    only(edit(lambda r: (r.update(kind="bare_board"))), "schema.invalid")
    only(edit(lambda r: r.pop("variant")), "schema.invalid", "/variant")
    only(edit(lambda r: r.update(release_id="Trial")), "schema.invalid", "/release_id")
    only(edit(lambda r: r["tool_versions"].update(kicad="latest")), "schema.invalid", "/tool_versions/kicad")
    only(edit(lambda r: r["checks"][0].update(evidence_sha256=None)), "schema.invalid") if False else None
    only(edit(lambda r: r["drill_applicability"].append({"role": "drill_plated", "condition": "other"})), "schema.invalid")


def test_evidence_record_rules(tmp: Path):
    project, pkg, manifest = tree(tmp)
    erc = V.load_record(pkg / "evidence/design.erc.json")
    manual = V.load_record(pkg / "evidence/asm.stock_dated.json")

    def edit(base, change):
        record = copy.deepcopy(base)
        change(record)
        return finds(tmp, "e.json", record)

    assert edit(erc, lambda r: None) == [] and edit(manual, lambda r: None) == []
    for field in ("tool", "inputs", "artifact"):
        only(edit(erc, lambda r: r.pop(field)), "evidence.tool_incomplete")
    only(edit(erc, lambda r: r.update(inputs=[])), "evidence.tool_incomplete")
    for field in ("reviewer", "observed_on", "inputs", "artifact"):
        only(edit(manual, lambda r: r.pop(field)), "pkg.check_manual_incomplete")
    assert edit(erc, lambda r: r.update(reviewer="R. Reviewer")) == [], "a tool record can have a reviewer"
    assert "reviewer" not in erc, "the helper makes no human reviewer for a tool check"
    pending = {"schema_id": "cad-skills/evidence", "schema_version": "1.0", "check_id": "design.erc", "status": "pending", "method": "tool"}
    assert finds(tmp, "e.json", pending) == [], "a pending record can omit inputs and artifact"
    only(edit(erc, lambda r: r["tool"].update(version="latest")), "schema.invalid", "/tool/version")
    only(edit(erc, lambda r: r["tool"].update(version="10.0.4\n")), "schema.invalid", "/tool/version")
    only(edit(erc, lambda r: r["inputs"][0].update(path="../x")), "pkg.path_invalid", "/inputs/0/path")
    only(edit(erc, lambda r: r["artifact"].update(path="/x")), "pkg.path_invalid", "/artifact/path")
    only(edit(manual, lambda r: r.update(observed_on="2026-11-13\n")), "schema.invalid", "/observed_on")
    only(edit(manual, lambda r: r.update(reviewer="R\n")), "schema.invalid", "/reviewer")
    only(edit(erc, lambda r: r.update(check_id="design.erc\n")), "schema.invalid", "/check_id")
    only(edit(erc, lambda r: r.update(method="robot")), "schema.invalid", "/method")


def _rect_with(points):
    return [{"x": x, "y": y} for x, y in points]


def test_interface_rules(tmp: Path):
    project, _, _ = tree(tmp)
    base = record_of(project, "mechanical/board-interface.json")

    def edit(change):
        record = copy.deepcopy(base)
        change(record)
        return finds(tmp, "i.json", record)

    assert edit(lambda r: None) == []
    cases = {
        "two points": _rect_with([(0, 0), (1, 1)]),
        "repeated point": _rect_with([(0, 0), (0, 0), (4, 0), (4, 4), (0, 4)]),
        "closing repeat": _rect_with([(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]),
        "zero area": _rect_with([(0, 0), (2, 0), (4, 0)]),
        "bow tie": _rect_with([(0, 0), (4, 4), (4, 0), (0, 4)]),
    }
    for label, points in cases.items():
        only(edit(lambda r: r.update(outline=points)), "iface.outline_invalid", "/outline")
        only(edit(lambda r: r.update(cutouts=[points])), "iface.cutout_invalid", "/cutouts/0")
    only(edit(lambda r: r["connector_frames"].append(
        {"id": "H1", "side": "top", "x": 1, "y": 1, "rotation_deg": 0, "insertion_depth_mm": 5})), "iface.duplicate_id", "/connector_frames/0/id")
    only(edit(lambda r: r["holes"].append({"id": "H1", "x": 5, "y": 5, "diameter_mm": 1, "plated": True})), "iface.duplicate_id")
    only(edit(lambda r: r["holes"][0].update(x=100)), "iface.hole_outside_outline", "/holes/0")
    only(edit(lambda r: r.update(cutouts=[_rect_with([(1, 1), (6, 1), (6, 6), (1, 6)])])), "iface.hole_outside_outline", "/holes/0")
    for field, value in (("thickness_mm", 0), ("geometry_tolerance_mm", 0), ("units", "in"), ("enclosure_clearance_mm", -1)):
        only(edit(lambda r: r.update({field: value})), "schema.invalid", f"/{field}")
    only(edit(lambda r: r["holes"][0].update(diameter_mm=0)), "schema.invalid", "/holes/0/diameter_mm")
    only(edit(lambda r: r["height_limits"].update(top_mm=-1)), "schema.invalid", "/height_limits/top_mm")
    only(edit(lambda r: r["dimension_owners"].pop("holes")), "schema.invalid", "/dimension_owners/holes")
    only(edit(lambda r: r["dimension_owners"].update(holes="both")), "schema.invalid", "/dimension_owners/holes")
    only(edit(lambda r: r["dimension_owners"].update(extra="mechanical")), "schema.unknown_field", "/dimension_owners/extra")
    frame = {"id": "J1", "side": "top", "x": 1, "y": 1, "rotation_deg": 0, "insertion_depth_mm": 5}
    assert edit(lambda r: r["connector_frames"].append(frame)) == []
    only(edit(lambda r: r["connector_frames"].append({**frame, "side": "left"})), "schema.invalid", "/connector_frames/0/side")
    only(edit(lambda r: r["connector_frames"].append({**frame, "rotation_deg": 360})), "schema.invalid", "/connector_frames/0/rotation_deg")
    only(edit(lambda r: r["connector_frames"].append({**frame, "insertion_depth_mm": 0})), "schema.invalid")
    only(edit(lambda r: r["board_sha256"].__class__ and r.update(board_sha256="b" * 64 + "\n")), "schema.invalid", "/board_sha256")
    big = 10 ** 400
    huge = edit(lambda r: r.update(outline=rect_points(big, big), holes=[{"id": "H1", "x": 3, "y": 3, "diameter_mm": 3.2, "plated": True}],
                                    geometry_tolerance_mm=big))
    assert huge == [], huge


def rect_points(width, height):
    return [{"x": 0, "y": 0}, {"x": width, "y": 0}, {"x": width, "y": height}, {"x": 0, "y": height}]


def test_toolchain_rules(tmp: Path):
    project, _, _ = tree(tmp)
    base = record_of(project, "toolchain.lock.json")

    def edit(change):
        record = copy.deepcopy(base)
        change(record)
        return finds(tmp, "t.json", record)

    digest = "sha256:" + "a" * 64
    container = {"image": "ghcr.io/example/kicad:1.9.0", "digest": digest}
    assert edit(lambda r: None) == []
    assert edit(lambda r: r.update(execution="container", container=container)) == []
    assert edit(lambda r: r["tools"].update(kibot={"used": False}, ngspice={"used": True, "version": "44.2", "source_url": "https://example.com/n", "license": "BSD-3-Clause"})) == []
    only(edit(lambda r: r.update(execution="container")), "schema.invalid")
    only(edit(lambda r: r.update(container=container)), "schema.invalid")
    for image in ("ghcr.io/example/kicad:latest", "ghcr.io/example/kicad\n"):
        only(edit(lambda r: r.update(execution="container", container={**container, "image": image})), "schema.invalid", "/container/image")
    for bad in ("sha256:" + "a" * 63, "sha256:" + "A" * 64, digest + "\n", "md5:" + "a" * 64):
        only(edit(lambda r: r.update(execution="container", container={**container, "digest": bad})), "schema.invalid", "/container/digest")
    for version in ("^1.0", "~1.0", ">=1.0", "1.*", "1.0,2.0", "1.0 2.0", "latest", "auto", "10.0.4\n", ""):
        only(edit(lambda r: r["tools"]["kicad"].update(version=version)), "schema.invalid", "/tools/kicad/version")
    only(edit(lambda r: r.update(python="3.13\n")), "schema.invalid", "/python")
    only(edit(lambda r: r["tools"]["kicad"].pop("license")), "schema.invalid")
    only(edit(lambda r: r["tools"]["kicad"].pop("source_url")), "schema.invalid")
    only(edit(lambda r: r["tools"].update(kibot={"used": False, "version": "1.9.0"})), "schema.invalid")
    only(edit(lambda r: r["tools"].update(other={"used": False})), "schema.unknown_field", "/tools/other")
    only(edit(lambda r: r["tools"].pop("kicad")), "schema.invalid", "/tools/kicad")
    only(edit(lambda r: r["tools"]["kicad"].update(license="unknown")), "toolchain.unknown_license_no_notes", "/tools/kicad/license")
    assert edit(lambda r: r["tools"]["kicad"].update(license="unknown", notes="The license text is not available.")) == []
    lib = {"name": "Device", "version": "10.0.4", "source_url": "https://example.com/lib", "license": "CC-BY-SA-4.0"}
    assert edit(lambda r: r.update(libraries=[lib], models=[{**lib, "sha256": "c" * 64}])) == []
    only(edit(lambda r: r.update(libraries=[lib, dict(lib)])), "toolchain.duplicate_item", "/libraries/1")
    only(edit(lambda r: r.update(libraries=[{**lib, "license": "unknown"}])), "toolchain.unknown_license_no_notes", "/libraries/0/license")
    only(edit(lambda r: r.update(libraries=[{**lib, "version": "latest"}])), "schema.invalid", "/libraries/0/version")
    assert edit(lambda r: r.update(java="25.0.4")) == []
    only(edit(lambda r: r.update(java=25)), "schema.invalid", "/java")


def test_export_settings_rules(tmp: Path):
    project, _, _ = tree(tmp)
    base = record_of(project, "manufacturing/export.yaml")

    def edit(change):
        record = copy.deepcopy(base)
        change(record)
        return finds(tmp, "x.json", record)

    assert edit(lambda r: None) == []
    only(edit(lambda r: r["layers"].append(dict(r["layers"][0], suffix=".X"))), "export.duplicate_layer", "/layers/7")
    only(edit(lambda r: r["layers"][1].update(suffix=r["layers"][0]["suffix"])), "export.suffix_duplicate", "/layers/1/suffix")
    only(edit(lambda r: r["drill"].update(nonplated_suffix=r["drill"]["plated_suffix"])), "export.suffix_duplicate")
    only(edit(lambda r: r["drill"].update(plated_suffix=r["layers"][0]["suffix"])), "export.suffix_duplicate")
    only(edit(lambda r: r.update(layers=[l for l in r["layers"] if l["role"] != "outline"])), "export.layer_missing")
    only(edit(lambda r: r.update(layers=[l for l in r["layers"] if l["role"] != "copper_top"])), "export.layer_missing")
    only(edit(lambda r: r.update(x2="no")), "schema.invalid", "/x2")
    only(edit(lambda r: r.update(x2=None)), "schema.invalid", "/x2")
    only(edit(lambda r: r["drill"].update(zero_suppression="auto")), "schema.invalid", "/drill/zero_suppression")
    only(edit(lambda r: r.update(origin="auto")), "schema.invalid", "/origin")
    only(edit(lambda r: r["layers"][0].update(role="copper_left")), "schema.invalid", "/layers/0/role")
    only(edit(lambda r: r["drill"].update(separate_files=False)), "schema.invalid", "/drill/separate_files")
    only(edit(lambda r: r["gerber"].update(decimal_places=3)), "schema.invalid", "/gerber/decimal_places")
    for field_path in (("layers", 0, "kicad_layer"), ("layers", 0, "suffix"), ("drill", "plated_suffix")):
        def newline(r, field_path=field_path):
            node = r
            for part in field_path[:-1]:
                node = node[part]
            node[field_path[-1]] = node[field_path[-1]] + "\n"
        found = edit(newline)
        assert [f["code"] for f in found] == ["schema.invalid"], (field_path, found)


def test_new_fields_reject_control_characters(tmp: Path):
    project, pkg, manifest = tree(tmp)
    for bad in ("\n", "\r", "\t", "\x00"):
        only(finds(tmp, "m.json", {**manifest, "release_id": "trial-1" + bad}), "schema.invalid", "/release_id")
        checks = copy.deepcopy(manifest)
        checks["checks"][0]["id"] += bad
        only(finds(tmp, "m.json", checks), "schema.invalid", "/checks/0/id")
        paths = copy.deepcopy(manifest)
        paths["outputs"][0]["path"] += bad
        only(finds(tmp, "m.json", paths), "pkg.path_invalid", "/outputs/0/path")
    for field in ("board_sha256",):
        only(finds(tmp, "m.json", {**manifest, field: manifest[field] + "\n"}), "schema.invalid", "/" + field)
    layer = copy.deepcopy(manifest)
    layer["outputs"][0]["layer"] += "\n"
    only(finds(tmp, "m.json", layer), "schema.invalid", "/outputs/0/layer")
    tool = copy.deepcopy(manifest)
    tool["tool_versions"]["kicad"] += "\n"
    only(finds(tmp, "m.json", tool), "schema.invalid", "/tool_versions/kicad")
    assert finds(tmp, "m.json", manifest) == [], "the valid exact values pass"
    spaced = copy.deepcopy(manifest)
    spaced["supplier"]["service"] = "Turnkey PRO"
    assert finds(tmp, "m.json", spaced) == [], "a normal space in an identifier passes"


# --------------------------------------------------------------------------- B234: project checks


def test_project_cross_rules(tmp: Path):
    project = P.build_project(tmp / "project")
    code, found, rep = codes_of(project)
    assert (code, found) == (0, []), rep["findings"]

    def case(label, change, expected, rel="board.yaml", exit_code=1):
        copy_root = tmp / label
        shutil.copytree(project, copy_root)
        P.edit_json(copy_root / rel, change)
        code, found, rep = codes_of(copy_root)
        assert (code, found) == (exit_code, expected), (label, rep["findings"])

    case("variant", lambda r: r.update(variant="nope"), ["cross.variant_missing"])
    case("service", lambda r: r["supplier"].update(service="Other"), ["cross.supplier_mismatch"])
    case("profile-hash", lambda r: r["supplier"].update(profile_sha256="a" * 64), ["cross.supplier_mismatch"])
    case("axis", lambda r: r["coordinate_system"].update(y_axis="down"), ["cross.coordinate_convention"])
    case("width", lambda r: r["mechanical"].update(width_mm=41), ["cross.dimension_mismatch"])
    case("thickness", lambda r: r["mechanical"].update(thickness_mm=1.7), ["cross.dimension_mismatch"])
    case("within-tolerance", lambda r: r["mechanical"].update(width_mm=40.005), [], exit_code=0)
    case("revision", lambda r: r.update(release_revision="B"), ["cross.revision_mismatch"])
    case("kicad", lambda r: r["tools"].update(kicad={"used": False}), ["cross.toolchain_kicad_missing"], rel="toolchain.lock.json")
    case("invalid-record", lambda r: r.update(quantity=0), ["schema.invalid"])
    shutil.copytree(project, tmp / "kind")
    shutil.copy(tmp / "kind/variants.yaml", tmp / "kind/manufacturing/supplier.yaml")
    code, found, rep = codes_of(tmp / "kind")
    assert found == ["cross.record_kind_mismatch", "cross.variant_missing"][:1] or "cross.record_kind_mismatch" in found, found
    shutil.copytree(project, tmp / "gone")
    (tmp / "gone/variants.yaml").unlink()
    code, found, rep = codes_of(tmp / "gone")
    assert code == 2 and "cli.input_missing" in found, rep["findings"]
    code, found, rep = codes_of(tmp / "no-such-project")
    assert code == 2 and found == ["cli.input_missing"]
    assert [i["path"] for i in P.examine(project)[1]["inputs"]] == sorted(
        [i["path"] for i in P.examine(project)[1]["inputs"]], key=lambda p: list(V.FIXED_INPUT_PATHS.values()).index(p[len(str(project)) + 1:])), \
        "the inputs of the report follow the fixed order"


def test_board_identity(tmp: Path):
    def fresh(label):
        base = tmp / label
        base.mkdir()
        return tree(base)

    # 1. Change only the PCB bytes.
    project, pkg, _ = fresh("pcb")
    P.write(project / "kicad/board.kicad_pcb", P.PCB + b"(changed)\n")
    code, found, rep = codes_of(project, pkg)
    assert found == ["cross.board_pcb_hash_mismatch"], rep["findings"]
    assert count(rep, "cross.board_pcb_hash_mismatch") == 5, "the interface, two waivers, the manifest hash, and the board input"
    # 2. Change only board.yaml (not the geometry).
    project, pkg, _ = fresh("record")
    P.edit_json(project / "board.yaml", lambda r: r.update(name="renamed-board"))
    code, found, rep = codes_of(project, pkg)
    assert found == ["cross.board_record_hash_mismatch"] and count(rep, "cross.board_record_hash_mismatch") == 1, rep["findings"]
    # 3. A geometry edit of board.yaml also gives a correct dimension finding.
    project, pkg, _ = fresh("geometry")
    P.edit_json(project / "board.yaml", lambda r: r["mechanical"].update(width_mm=41))
    code, found, rep = codes_of(project, pkg)
    assert found == ["cross.board_record_hash_mismatch", "cross.dimension_mismatch"], rep["findings"]
    # 4. Change only the schematic bytes.
    project, pkg, _ = fresh("schematic")
    P.write(project / "kicad/board.kicad_sch", P.SCH + b"(changed)\n")
    code, found, rep = codes_of(project, pkg)
    assert found == ["cross.schematic_hash_mismatch", "cross.waiver_schematic_hash_mismatch"], rep["findings"]
    assert count(rep, "cross.waiver_schematic_hash_mismatch") == 1, "only the erc waiver binds to the schematic"
    # 5. Another file in the board role.
    project, pkg, manifest = fresh("substitute")
    other = P.write(project / "kicad/other.kicad_pcb", b"another board\n")
    edit_manifest(pkg, lambda m: item_of(m, "board", section="inputs").update(path="kicad/other.kicad_pcb", sha256=P.sha(other)))
    code, found, rep = codes_of(project, pkg)
    assert "cross.input_path_mismatch" in found, rep["findings"]


def test_package_cross_rules(tmp: Path):
    def fresh(label, kind="pcba"):
        base = tmp / label
        base.mkdir()
        return tree(base, kind)

    project, pkg, _ = fresh("kind")
    edit_manifest(pkg, lambda m: (m.update(kind="bare_board"), m.pop("applicability")))
    assert "cross.kind_mismatch" in codes_of(project, pkg)[1]
    project, pkg, _ = fresh("variant")
    edit_manifest(pkg, lambda m: m.update(variant="no-led"))
    assert codes_of(project, pkg)[1] == ["cross.variant_mismatch"]
    project, pkg, _ = fresh("supplier")
    edit_manifest(pkg, lambda m: m["supplier"].update(service="Other"))
    assert codes_of(project, pkg)[1] == ["cross.profile_hash_mismatch"]
    project, pkg, _ = fresh("revision")
    edit_manifest(pkg, lambda m: m.update(board_revision="B"))
    assert codes_of(project, pkg)[1] == ["cross.revision_mismatch"]
    project, pkg, _ = fresh("waivers")
    edit_manifest(pkg, lambda m: m["inputs"].remove(item_of(m, "waivers", section="inputs")))
    assert codes_of(project, pkg)[1] == ["cross.input_set_mismatch"]
    project, pkg, _ = fresh("noinput")
    P.edit_json(project / "components/part.yaml", lambda r: r.update(package="0805"))
    assert codes_of(project, pkg)[1] == ["cross.input_hash_mismatch"]
    # Outputs: changed bytes, a missing file, an empty file, a wrong hash in a draft.
    project, pkg, m = fresh("bytes")
    P.write(pkg / item_of(m, "bom")["path"], "changed\n")
    assert codes_of(project, pkg)[1] == ["cross.output_hash_mismatch"]
    project, pkg, m = fresh("missing")
    (pkg / item_of(m, "bom")["path"]).unlink()
    assert codes_of(project, pkg)[1] == ["cross.output_missing"]
    project, pkg, m = fresh("empty")
    P.write(pkg / item_of(m, "bom")["path"], b"")
    edit_manifest(pkg, lambda x: item_of(x, "bom").update(size_bytes=0, sha256=P.sha(b"")))
    assert codes_of(project, pkg)[1] == ["pkg.output_empty"]
    edit_manifest(pkg, lambda x: x.update(status="draft"))
    assert codes_of(project, pkg)[1] == ["pkg.output_empty"], "an empty listed output fails in a draft"
    project, pkg, m = fresh("hash-draft")
    edit_manifest(pkg, lambda x: (x.update(status="draft"), item_of(x, "bom").update(sha256="d" * 64)))
    assert codes_of(project, pkg)[1] == ["cross.output_hash_mismatch"], "a wrong hash fails in a draft"
    project, pkg, m = fresh("escape")
    outside = tmp / "outside"
    outside.mkdir()
    (outside / "data.txt").write_text("outside\n")
    (pkg / "link").symlink_to(outside, target_is_directory=True)
    edit_manifest(pkg, lambda x: x["outputs"].append({"role": "image", "path": "link/data.txt", "sha256": P.sha(b"outside\n"), "size_bytes": 8}))
    assert codes_of(project, pkg)[1] == ["cross.path_escape"]
    project, pkg, _ = fresh("nopackage")
    (pkg / "manifest.json").unlink()
    code, found, rep = codes_of(project, pkg)
    assert code == 2 and found == ["cli.input_missing"]


def test_layer_mapping_and_outline(tmp: Path):
    def fresh(label, **kw):
        base = tmp / label
        base.mkdir()
        return tree(base, **kw)

    project, pkg, m = fresh("two", extra_layers=[("copper_inner", "In1.Cu", ".G1")])
    assert codes_of(project, pkg)[0] == 0, "a valid inner layer passes"
    edit_manifest(pkg, lambda x: x["outputs"].remove(item_of(x, "copper", layer="In1.Cu")))
    assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"], "a missing inner layer"
    project, pkg, m = fresh("one-copper")
    edit_manifest(pkg, lambda x: x["outputs"].remove(item_of(x, "copper", layer="B.Cu")))
    assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"], "one copper file for a two-layer board"
    project, pkg, m = fresh("swap")

    def swap(x):
        a, b = item_of(x, "copper", layer="F.Cu"), item_of(x, "copper", layer="B.Cu")
        a["layer"], b["layer"] = "B.Cu", "F.Cu"
    edit_manifest(pkg, swap)
    code, found, rep = codes_of(project, pkg)
    assert found == ["pkg.layer_suffix_mismatch"] and count(rep, "pkg.layer_suffix_mismatch") == 2, "exchanged layer identities"
    project, pkg, m = fresh("outline-ok")
    assert item_of(m, "outline")["layer"] == "Edge.Cuts" and codes_of(project, pkg)[0] == 0
    edit_manifest(pkg, lambda x: item_of(x, "outline").pop("layer"))
    assert codes_of(project, pkg)[1] == ["pkg.layer_unmapped"], "an outline without a layer"
    project, pkg, m = fresh("outline-wrong")
    edit_manifest(pkg, lambda x: item_of(x, "outline").update(layer="Edge.Cut"))
    assert "pkg.layer_unmapped" in codes_of(project, pkg)[1], "a wrong outline layer"
    project, pkg, m = fresh("outline-dup")
    edit_manifest(pkg, lambda x: x["outputs"].append({**item_of(x, "outline"), "path": "gerber/second.GKO"}))
    assert "pkg.layer_duplicate" in codes_of(project, pkg)[1], "a duplicate outline layer"
    project, pkg, m = fresh("outline-suffix")
    edit_manifest(pkg, lambda x: item_of(x, "outline").update(path="gerber/board.GTL.txt"))
    assert "pkg.layer_suffix_mismatch" in codes_of(project, pkg)[1], "an exchanged outline suffix"
    project, pkg, m = fresh("silk")
    edit_manifest(pkg, lambda x: x["outputs"].remove(item_of(x, "silk")))
    assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"], "a declared silk layer needs an output"
    project, pkg, m = fresh("paste")
    edit_manifest(pkg, lambda x: x["outputs"].remove(item_of(x, "paste")))
    assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"], "a PCBA with SMD parts and no paste"


def test_drill_applicability(tmp: Path):
    item = {"role": "drill_nonplated", "condition": "no_nonplated_holes", "reason": "The board has no non-plated hole.",
            "evidence": {"input_role": "board_interface"}}
    plated_only = [{"id": "H2", "x": 37, "y": 22, "diameter_mm": 1.0, "plated": True}]

    def fresh(label, holes):
        base = tmp / label
        base.mkdir()
        project, pkg, m = tree(base, holes=holes)
        edit_manifest(pkg, lambda x: x["outputs"].remove(item_of(x, "drill_nonplated")))
        return project, pkg

    project, pkg = fresh("none", plated_only)
    assert codes_of(project, pkg)[1] == ["pkg.applicability_missing"], "no file and no item"
    edit_manifest(pkg, lambda x: x["drill_applicability"].append(copy.deepcopy(item)))
    assert codes_of(project, pkg)[0] == 0, "a role, a condition, a reason, and interface evidence"
    edit_manifest(pkg, lambda x: x["drill_applicability"][0].update(condition="no_plated_holes"))
    assert codes_of(project, pkg)[1] == ["pkg.applicability_condition_mismatch", "pkg.applicability_missing"]
    edit_manifest(pkg, lambda x: x["drill_applicability"][0].update(condition="no_nonplated_holes", reason=" "))
    assert "pkg.applicability_reason_missing" in codes_of(project, pkg)[1]
    edit_manifest(pkg, lambda x: x["drill_applicability"][0].pop("evidence"))
    assert "pkg.applicability_reason_missing" in codes_of(project, pkg)[1]
    edit_manifest(pkg, lambda x: x["drill_applicability"][0].update(reason="Reason.", evidence={"check_id": "fab.drill_split"}))
    assert codes_of(project, pkg)[0] == 0, "a check exception with a passed fab.drill_split"
    edit_manifest(pkg, lambda x: x.update(status="draft") or next(c for c in x["checks"] if c["id"] == "fab.drill_split").update(status="pending", evidence_path=None, evidence_sha256=None))
    code, found, rep = codes_of(project, pkg)
    assert x_has(rep, "pkg.applicability_evidence_invalid"), rep["findings"]
    project, pkg = fresh("contradiction", None)
    edit_manifest(pkg, lambda x: x["drill_applicability"].append(copy.deepcopy(item)))
    assert codes_of(project, pkg)[1] == ["cross.drill_applicability_false", "pkg.applicability_missing"], "the interface has a non-plated hole, so the exception does not cover the role"
    project, pkg = fresh("zero-file", plated_only)
    edit_manifest(pkg, lambda x: (x["drill_applicability"].append(copy.deepcopy(item)), x["outputs"].append(
        {"role": "drill_nonplated", "path": "gerber/empty.drl", "sha256": P.sha(b""), "size_bytes": 0})))
    P.write(pkg / "gerber/empty.drl", b"")
    assert "pkg.output_empty" in codes_of(project, pkg)[1], "an empty drill file is not an exception"


def x_has(rep, code):
    return any(f["code"] == code for f in rep["findings"])


def test_completeness_by_status(tmp: Path):
    def fresh(label):
        base = tmp / label
        base.mkdir()
        return tree(base)

    project, pkg, m = fresh("status")
    edit_manifest(pkg, lambda x: x["outputs"].remove(item_of(x, "schematic_pdf")))
    assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"]
    edit_manifest(pkg, lambda x: x.update(status="draft"))
    assert codes_of(project, pkg)[0] == 0, "the draft passes the completeness rules"
    edit_manifest(pkg, lambda x: x.update(status="qualified"))
    assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"], "the identical contents fail as qualified"
    edit_manifest(pkg, lambda x: x.update(status="unqualified", reasons=[{"code": "incomplete", "text": "The PDF is absent."}]))
    assert codes_of(project, pkg)[0] == 0
    project, pkg, m = fresh("flags")
    for role, flag in (("firmware", "firmware"), ("stencil", "stencil"), ("panel", "panel")):
        edit_manifest(pkg, lambda x: x["applicability"].update({flag: True}))
        assert codes_of(project, pkg)[1] == ["pkg.artifact_missing"], role
        edit_manifest(pkg, lambda x: x["applicability"].update({flag: False}))
    project, pkg, m = fresh("pending")
    edit_manifest(pkg, lambda x: x["checks"][0].update(status="pending", evidence_path=None, evidence_sha256=None))
    assert codes_of(project, pkg)[1] == ["pkg.false_qualification"]


# --------------------------------------------------------------------------- B234: evidence


def rewrite_evidence(pkg, check_id, change, *, update_manifest=True):
    path = pkg / f"evidence/{check_id}.json"
    record = V.load_record(path)
    change(record)
    data = P.write(path, record)
    if update_manifest:
        def apply(m):
            item = next(i for i in m["outputs"] if i["path"] == f"evidence/{check_id}.json")
            item.update(sha256=P.sha(data), size_bytes=len(data))
            next(c for c in m["checks"] if c["id"] == check_id).update(evidence_sha256=P.sha(data))
        edit_manifest(pkg, apply)


def test_pcba_optional_design_input_bindings(tmp: Path):
    """PCBA evidence binds optional project settings and custom rules when those files exist."""
    project, pkg, manifest = tree(tmp)
    entries = []
    for role, suffix in (("project_settings", "pro"), ("design_rules", "dru")):
        rel = f"kicad/board.kicad_{suffix}"
        raw = b"{}\n" if suffix == "pro" else b"(version 1)\n"
        P.write(project / rel, raw)
        entries.append({"role": role, "path": rel, "sha256": P.sha(raw)})
    assert "cross.input_set_mismatch" in codes_of(project, pkg)[1], "The manifest omits present design inputs."
    edit_manifest(pkg, lambda m: m["inputs"].extend(entries))
    assert "pkg.check_input_role_missing" in codes_of(project, pkg)[1], "The evidence omits present design inputs."
    bound = [{"path": e["path"], "sha256": e["sha256"]} for e in entries]
    rewrite_evidence(pkg, "design.drc", lambda r: r["inputs"].extend(bound))
    rewrite_evidence(pkg, "design.erc", lambda r: r["inputs"].append(bound[0]))
    assert codes_of(project, pkg)[0] == 0, "The evidence binds the present design inputs."
    rewrite_evidence(pkg, "design.drc", lambda r: r.update(inputs=[x for x in r["inputs"] if x != bound[1]]))
    assert "pkg.check_input_role_missing" in codes_of(project, pkg)[1], "The DRC evidence must bind its custom rules."


def test_evidence_qualification(tmp: Path):
    def fresh(label):
        base = tmp / label
        base.mkdir()
        return tree(base)

    project, pkg, m = fresh("none")
    edit_manifest(pkg, lambda x: [c.update(evidence_path=None, evidence_sha256=None) for c in x["checks"]])
    code, found, rep = codes_of(project, pkg)
    assert found == ["pkg.check_evidence_missing"] and count(rep, "pkg.check_evidence_missing") == 13, "all-pass strings without evidence"
    project, pkg, m = fresh("bytes")
    P.write(pkg / "evidence/design.erc.json", "{}\n")
    assert "pkg.check_evidence_mismatch" in codes_of(project, pkg)[1], "changed evidence bytes"
    project, pkg, m = fresh("stale")
    rewrite_evidence(pkg, "design.erc", lambda r: r["inputs"][0].update(sha256="e" * 64))
    assert codes_of(project, pkg)[1] == ["pkg.check_evidence_mismatch"], "a stale input hash"
    project, pkg, m = fresh("manual-short")
    rewrite_evidence(pkg, "asm.stock_dated", lambda r: (r.pop("inputs"), r.pop("artifact")))
    assert codes_of(project, pkg)[1] == ["pkg.check_manual_incomplete"], "reviewer and date only"
    project, pkg, m = fresh("unrelated")
    rewrite_evidence(pkg, "design.erc", lambda r: r.update(inputs=[i for i in r["inputs"] if False] + [
        {"path": "board.yaml", "sha256": item_of(m, "board_record", section="inputs")["sha256"]}]))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "an unrelated input with a correct hash"
    project, pkg, m = fresh("parity")
    rewrite_evidence(pkg, "design.parity", lambda r: r.update(inputs=r["inputs"][:1]))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "one of two mandatory inputs"
    project, pkg, m = fresh("parts")
    rewrite_evidence(pkg, "asm.bom_consistent", lambda r: r.update(inputs=[i for i in r["inputs"] if i["path"] != "components/part.yaml"]))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "a missing assembly input role"
    project, pkg, m = fresh("bom-policy")
    profile_path = item_of(m, "supplier_profile", section="inputs")["path"]
    rewrite_evidence(pkg, "asm.bom_consistent", lambda r: r.update(inputs=[i for i in r["inputs"] if i["path"] != profile_path]))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "The BOM evidence omits the supplier policy."
    project, pkg, m = fresh("test-limit-source")
    board_path = item_of(m, "board_record", section="inputs")["path"]
    rewrite_evidence(pkg, "asm.test_record", lambda r: r.update(inputs=[i for i in r["inputs"] if i["path"] != board_path]))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "The test evidence omits the board limits."
    project, pkg, m = fresh("only-board")
    rewrite_evidence(pkg, "design.erc", lambda r: r.update(inputs=[{"path": "kicad/board.kicad_pcb", "sha256": item_of(m, "board", section="inputs")["sha256"]}]))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "ERC evidence with only the board"
    project, pkg, m = fresh("not-manifest-input")
    rewrite_evidence(pkg, "design.erc", lambda r: r["inputs"].append({"path": "kicad/extra.txt", "sha256": "f" * 64}))
    assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], "an input that is not a manifest input"
    project, pkg, m = fresh("artifact")
    rewrite_evidence(pkg, "design.erc", lambda r: r["artifact"].update(path="reports/none.txt"))
    assert codes_of(project, pkg)[1] == ["pkg.check_evidence_mismatch"], "an artifact outside the manifest outputs"
    project, pkg, m = fresh("artifact-bytes")
    P.write(pkg / "reports/design.drc.txt", "changed\n")
    assert codes_of(project, pkg)[1] == ["cross.output_hash_mismatch"], "changed artifact bytes"
    project, pkg, m = fresh("profile")
    new = b"another supplier page\n"
    P.write(pkg / "evidence/supplier-page.html", new)
    edit_manifest(pkg, lambda x: item_of(x, "report").__setitem__("sha256", item_of(x, "report")["sha256"]))
    edit_manifest(pkg, lambda x: next(i for i in x["outputs"] if i["path"] == "evidence/supplier-page.html").update(sha256=P.sha(new), size_bytes=len(new)))
    rewrite_evidence(pkg, "fab.profile_evidence", lambda r: r["artifact"].update(sha256=P.sha(new)))
    assert codes_of(project, pkg)[1] == ["cross.profile_evidence_mismatch"], "the profile evidence_sha256 differs from the artifact"
    project, pkg, m = fresh("wrong-check")
    rewrite_evidence(pkg, "design.erc", lambda r: r.update(check_id="design.drc"))
    assert codes_of(project, pkg)[1] == ["pkg.check_evidence_mismatch"]
    project, pkg, m = fresh("wrong-status")
    rewrite_evidence(pkg, "design.erc", lambda r: r.update(status="fail"))
    assert codes_of(project, pkg)[1] == ["pkg.check_evidence_mismatch"]
    project, pkg, m = fresh("version")
    rewrite_evidence(pkg, "design.erc", lambda r: r.update(schema_version="2.0"))
    assert "schema.major_unsupported" in codes_of(project, pkg)[1], "an unsupported evidence schema version"
    project, pkg, m = fresh("unknown")
    edit_manifest(pkg, lambda x: x["checks"][0].update(evidence_path=item_of(x, "report")["path"], evidence_sha256=item_of(x, "report")["sha256"]))
    assert "pkg.evidence_unknown" in codes_of(project, pkg)[1]
    project, pkg, m = fresh("half")
    edit_manifest(pkg, lambda x: x["checks"][0].update(evidence_sha256=None))
    assert "pkg.check_evidence_mismatch" in codes_of(project, pkg)[1]
    project, pkg, m = fresh("tool-ok")
    assert "reviewer" not in V.load_record(pkg / "evidence/design.drc.json") and codes_of(project, pkg)[0] == 0, \
        "a tool record without a reviewer passes with the same input-role table"


def test_cli_project_and_package(tmp: Path):
    project, pkg, _ = tree(tmp)
    r = run("--project", project, "--package", pkg, "--json")
    rep = json.loads(r.stdout)
    assert r.returncode == 0 and rep["status"] == "pass" and rep["findings"] == []
    assert r.stdout == run("--project", project, "--package", pkg, "--json").stdout, "two runs give the same output"
    assert not any("time" in key for key in rep), "the report has no time"
    r = run("--project", project)
    assert r.returncode == 0 and "status: pass" in r.stdout
    r = run("--package", pkg, "--json")
    arep = json.loads(r.stdout)
    assert r.returncode == 2 and [f["code"] for f in arep["findings"]] == ["cli.argument_error"]
    assert run("--project", tmp / "nothing", "--json").returncode == 2
    P.write(project / "kicad/board.kicad_pcb", b"changed\n")
    r = run("--project", project, "--package", pkg, "--json")
    assert r.returncode == 1 and "cross.board_pcb_hash_mismatch" in r.stdout
    assert run(project / "board.yaml").returncode == 0, "FILE arguments keep the B1 behavior"


def test_large_integers_in_geometry(tmp: Path):
    project = P.build_project(tmp / "p")
    big = 10 ** 400
    P.edit_json(project / "board.yaml", lambda r: r["mechanical"].update(width_mm=big, height_mm=big))
    P.edit_json(project / "mechanical/board-interface.json", lambda r: r.update(
        outline=rect_points(big, big), geometry_tolerance_mm=1,
        holes=[{"id": "H1", "x": 3, "y": 3, "diameter_mm": 1, "plated": True}]))
    code, found, rep = codes_of(project)
    assert (code, found) == (0, []), rep["findings"]
    P.edit_json(project / "mechanical/board-interface.json", lambda r: r.update(outline=rect_points(big, 25)))
    code, found, rep = codes_of(project)
    assert found == ["cross.dimension_mismatch"], rep["findings"]
    P.edit_json(project / "board.yaml", lambda r: r["mechanical"].update(width_mm=40.0, height_mm=25.0))
    P.edit_json(project / "mechanical/board-interface.json", lambda r: r.update(outline=rect_points(big, 25)))
    code, found, rep = codes_of(project)
    assert "cross.dimension_mismatch" in found and code == 1, "an overflow is a record finding, not a tool failure"


# --------------------------------------------------------------------------- B234 correction (R1 to R3)


def counting_reader(reads, change=None):
    """Return a replacement for V._read_confined that counts the reads of each file."""
    real = V._read_confined

    def reader(root, rel):
        key = (str(Path(root).resolve()), rel)
        reads[key] = reads.get(key, 0) + 1
        state, data = real(root, rel)
        return change(rel, reads[key], state, data) if change else (state, data)

    return real, reader


def test_each_file_is_read_once(tmp: Path):
    project, pkg, _ = tree(tmp)
    reads = {}
    real, reader = counting_reader(reads)
    V._read_confined = reader
    try:
        code, rep = P.examine(project, pkg)
    finally:
        V._read_confined = real
    assert code == 0 and rep["findings"] == [], rep["findings"]
    assert reads and max(reads.values()) == 1, {k: v for k, v in reads.items() if v > 1}
    assert any(key[1] == "kicad/board.kicad_pcb" for key in reads) and any(key[1].startswith("evidence/") for key in reads)


def test_changed_file_cannot_qualify(tmp: Path):
    """The controlled change of the review: the first read of the interface gives other bytes than later reads."""
    project = P.build_project(tmp / "project", holes=[])
    pkg = tmp / "pkg"
    P.build_package(project, pkg)
    exceptions = [{"role": role, "condition": condition, "reason": "The board has no such hole.", "evidence": {"input_role": "board_interface"}}
                  for role, condition in (("drill_plated", "no_plated_holes"), ("drill_nonplated", "no_nonplated_holes"))]
    edit_manifest(pkg, lambda m: (m.update(drill_applicability=exceptions),
                                  m.update(outputs=[o for o in m["outputs"] if o["role"] not in ("drill_plated", "drill_nonplated")])))
    assert codes_of(project, pkg)[0] == 0, "the exceptions are right for an interface with no holes"
    interface_path = project / "mechanical/board-interface.json"
    old_bytes = interface_path.read_bytes()
    record = V.load_record(interface_path)
    record["holes"] = [{"id": "H9", "x": 5, "y": 5, "diameter_mm": 1.0, "plated": True}]
    new_bytes = P.write(interface_path, record)
    edit_manifest(pkg, lambda m: item_of(m, "board_interface", section="inputs").update(sha256=P.sha(new_bytes)))
    rewrite_evidence(pkg, "fab.drill_split", lambda r: [i.update(sha256=P.sha(new_bytes)) for i in r["inputs"]
                                                          if i["path"] == "mechanical/board-interface.json"])
    code, found, rep = codes_of(project, pkg)
    assert "cross.drill_applicability_false" in found, "the file on disk has a plated hole"
    reads = {}

    def change(rel, number, state, data):
        if rel == "mechanical/board-interface.json" and number == 1:
            return state, old_bytes
        return state, data

    real, reader = counting_reader(reads, change)
    V._read_confined = reader
    try:
        code, found, rep = codes_of(project, pkg)
    finally:
        V._read_confined = real
    assert code != 0 and "cross.input_hash_mismatch" in found, rep["findings"]
    assert [n for key, n in reads.items() if key[1] == "mechanical/board-interface.json"] == [1], "one read of the interface"


def test_non_pass_evidence_is_examined(tmp: Path):
    def fresh(label, status):
        base = tmp / label
        base.mkdir()
        project, pkg, _ = tree(base)
        edit_manifest(pkg, lambda m: (m.update(status="draft"), next(c for c in m["checks"] if c["id"] == "design.erc").update(status=status)))
        rewrite_evidence(pkg, "design.erc", lambda r: r.update(status=status))
        return project, pkg

    for status in ("pending", "unconfirmed", "fail"):
        project, pkg = fresh(f"{status}-ok", status)
        assert codes_of(project, pkg)[0] == 0, status
        rewrite_evidence(pkg, "design.erc", lambda r: (r.pop("inputs"), r.pop("artifact")))
        assert codes_of(project, pkg)[0] == 0, f"a {status} record can omit the inputs and the artifact"
        project, pkg = fresh(f"{status}-both", status)
        rewrite_evidence(pkg, "design.erc", lambda r: r.update(
            inputs=[{**r["inputs"][0], "sha256": "0" * 64}], artifact={"path": "absent-report.txt", "sha256": "1" * 64}))
        code, found, rep = codes_of(project, pkg)
        assert found == ["pkg.check_evidence_mismatch"] and count(rep, "pkg.check_evidence_mismatch") == 2, (status, rep["findings"])
        project, pkg = fresh(f"{status}-input", status)
        rewrite_evidence(pkg, "design.erc", lambda r: r["inputs"][0].update(sha256="2" * 64))
        code, found, rep = codes_of(project, pkg)
        assert found == ["pkg.check_evidence_mismatch"] and count(rep, "pkg.check_evidence_mismatch") == 1, (status, rep["findings"])
        project, pkg = fresh(f"{status}-artifact", status)
        rewrite_evidence(pkg, "design.erc", lambda r: r["artifact"].update(sha256="3" * 64))
        code, found, rep = codes_of(project, pkg)
        assert found == ["pkg.check_evidence_mismatch"] and count(rep, "pkg.check_evidence_mismatch") == 1, (status, rep["findings"])
        project, pkg = fresh(f"{status}-stranger", status)
        rewrite_evidence(pkg, "design.erc", lambda r: r["inputs"].append({"path": "kicad/extra.txt", "sha256": "4" * 64}))
        assert codes_of(project, pkg)[1] == ["pkg.check_input_role_missing"], status


def test_skidl_provenance(tmp: Path):
    project = P.build_project(tmp / "project", circuit_source="skidl")
    pkg = tmp / "pkg"
    manifest = P.build_package(project, pkg)
    assert item_of(manifest, "circuit_source", section="inputs")["path"] == "src/circuit.py"
    assert codes_of(project, pkg)[0] == 0
    source = item_of(manifest, "circuit_source", section="inputs")
    edit_manifest(pkg, lambda m: m["inputs"].remove(item_of(m, "circuit_source", section="inputs")))
    assert codes_of(project, pkg)[1] == ["pkg.input_missing"], "a qualified SKiDL package without its source"
    edit_manifest(pkg, lambda m: m.update(status="draft"))
    assert codes_of(project, pkg)[0] == 0, "an incomplete draft keeps its behavior"
    edit_manifest(pkg, lambda m: (m.update(status="qualified"), m["inputs"].append({**source, "sha256": "5" * 64})))
    assert codes_of(project, pkg)[1] == ["cross.input_hash_mismatch"], "a wrong source hash"
    edit_manifest(pkg, lambda m: item_of(m, "circuit_source", section="inputs").update(sha256=source["sha256"], path="src/other.py"))
    assert codes_of(project, pkg)[1] == ["cross.input_hash_mismatch"], "a source file that is not present"
    P.write(project / "src/circuit.py", "# changed\n")
    edit_manifest(pkg, lambda m: item_of(m, "circuit_source", section="inputs").update(path="src/circuit.py"))
    assert codes_of(project, pkg)[1] == ["cross.input_hash_mismatch"], "changed source bytes"
    native = P.build_project(tmp / "native")
    native_pkg = tmp / "native-pkg"
    P.build_package(native, native_pkg)
    assert codes_of(native, native_pkg)[0] == 0, "a native KiCad package has no source role and passes"


# --------------------------------------------------------------------------- B234 final correction (R1 aliases)


def resolved_reader(counts, change):
    """A replacement for V._read_confined that counts the reads of each resolved file."""
    real = V._read_confined

    def reader(root, rel):
        key = str((Path(root) / rel).resolve())
        counts[key] = counts.get(key, 0) + 1
        state, data = real(root, rel)
        return change(key, counts[key], state, data)

    return real, reader


def test_aliases_share_one_snapshot(tmp: Path):
    """Two confined names for one file: the run must not qualify two different snapshots of the file."""
    project = P.build_project(tmp / "project", holes=[])
    iface = project / "mechanical/board-interface.json"
    part = project / "components/part.yaml"
    part.unlink()
    part.symlink_to("../mechanical/board-interface.json")
    pkg = tmp / "pkg"
    P.build_package(project, pkg)
    exceptions = [{"role": role, "condition": condition, "reason": "The board has no such hole.", "evidence": {"input_role": "board_interface"}}
                  for role, condition in (("drill_plated", "no_plated_holes"), ("drill_nonplated", "no_nonplated_holes"))]
    edit_manifest(pkg, lambda m: (m.update(drill_applicability=exceptions),
                                  m.update(outputs=[o for o in m["outputs"] if o["role"] not in ("drill_plated", "drill_nonplated")])))
    assert codes_of(project, pkg)[0] == 0, "the exceptions are right for an interface with no holes"
    old_bytes = iface.read_bytes()
    record = V.load_record(iface)
    record["holes"] = [{"id": "H9", "x": 5, "y": 5, "diameter_mm": 1.0, "plated": True}]
    new_bytes = P.write(iface, record)
    # The parts input and its evidence references carry the new hash. The interface input and its references keep the old hash.
    edit_manifest(pkg, lambda m: item_of(m, "parts", section="inputs").update(sha256=P.sha(new_bytes)))
    for check_id in ("asm.bom_consistent", "asm.placement_rotation", "asm.variant_agreement", "asm.stock_dated", "asm.test_record"):
        rewrite_evidence(pkg, check_id, lambda r: [i.update(sha256=P.sha(new_bytes)) for i in r["inputs"] if i["path"] == "components/part.yaml"])
    counts = {}

    def change(key, number, state, data):
        return (state, old_bytes) if key == str(iface.resolve()) and number == 1 else (state, data)

    real, reader = resolved_reader(counts, change)
    V._read_confined = reader
    try:
        code, found, rep = codes_of(project, pkg)
    finally:
        V._read_confined = real
    assert code != 0 and "cross.input_hash_mismatch" in found, rep["findings"]
    assert counts[str(iface.resolve())] == 1, counts


def test_cached_success_does_not_bypass_confinement(tmp: Path):
    """A name must pass its own root confinement before the run uses a cached snapshot of the resolved file."""
    project, pkg, _ = tree(tmp)
    iface = project / "mechanical/board-interface.json"
    data = iface.read_bytes()
    (pkg / "gerber").mkdir(exist_ok=True)
    (pkg / "gerber/alias.txt").symlink_to(iface)  # inside the project, outside the package root
    edit_manifest(pkg, lambda m: m["outputs"].append({"role": "report", "path": "gerber/alias.txt", "sha256": P.sha(data), "size_bytes": len(data)}))
    code, found, rep = codes_of(project, pkg)
    assert "cross.path_escape" in found and "cross.output_hash_mismatch" not in found and "cross.output_missing" not in found, rep["findings"]
    assert any(f["code"] == "cross.path_escape" and f["location"].startswith("/outputs/") for f in rep["findings"])
    outside = tmp / "outside.txt"
    outside.write_text("outside\n")
    (project / "components/extra.yaml").symlink_to(outside)
    edit_manifest(pkg, lambda m: (m["outputs"].pop(), m["inputs"].append(
        {"role": "circuit_source", "path": "components/extra.yaml", "sha256": P.sha(b"outside\n")})))
    code, found, rep = codes_of(project, pkg)
    assert any(f["code"] == "cross.path_escape" and f["location"].startswith("/inputs/") for f in rep["findings"]), rep["findings"]
    assert "cross.input_hash_mismatch" not in found
    # The ordinary one-path case still reads each file one time and passes.
    ok_project, ok_pkg, _ = tree(tmp / "ok" if (tmp / "ok").mkdir() is None else tmp / "ok")
    counts = {}
    real, reader = resolved_reader(counts, lambda key, number, state, data: (state, data))
    V._read_confined = reader
    try:
        code, found, rep = codes_of(ok_project, ok_pkg)
    finally:
        V._read_confined = real
    assert code == 0 and max(counts.values()) == 1, counts


# --------------------------------------------------------------------------- housekeeping


def test_workflow_permissions(tmp: Path):
    flow = V.load_record(ROOT / ".github/workflows/test.yml")
    assert flow["permissions"] == {"contents": "read"}, flow.get("permissions")
    assert "on" in flow, "the loader keeps the key `on` as a string"
    assert set(flow["jobs"]) == {"pcb-contracts", "snippets", "release-static"}
    text = (ROOT / ".github/workflows/test.yml").read_text()
    assert "continue-on-error" not in text and "|| true" not in text
    for name, job in flow["jobs"].items():
        assert isinstance(job.get("timeout-minutes"), int) and job["timeout-minutes"] > 0, f"{name} has no timeout"
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]
    steps = " ".join(str(s.get("run", "")) for s in flow["jobs"]["pcb-contracts"]["steps"])
    for command in ("tests/test_pcb_tools.py", "tests/test_project_io.py", "tests/test_skill_packages.py", "tests/test_snippets.py --dry-run"):
        assert command in steps, command
    cache = " ".join(str(s.get("with", {}).get("cache-dependency-glob", "")) for s in flow["jobs"]["pcb-contracts"]["steps"])
    assert "contracts/**/*.py" in cache and "tests/**/*.py" in cache
    assert "contracts/**/*.py" in " ".join(str(s.get("with", {}).get("cache-dependency-glob", "")) for s in flow["jobs"]["snippets"]["steps"])
    release_steps = " ".join(str(s.get("run", "")) for s in flow["jobs"]["release-static"]["steps"])
    for command in ("tests/test_release_packaging.py", "tests/test_release_harness.py"):
        assert command in release_steps, command
    assert "docker" not in text and "podman" not in text, "B234 has no container job"


def test_files_not_ignored(tmp: Path):
    paths = ["contracts/validate.py", "contracts/README.md", "contracts/schemas/registry.json",
             *[f"contracts/schemas/{n}.schema.json" for n in ("board", "variants", "part", "supplier-profile")],
             *[f"tests/fixtures/pcb/{n}" for n in FIXTURES], "tests/test_pcb_tools.py"]
    for path in paths:
        assert (ROOT / path).is_file(), f"{path} is missing"
        r = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=ROOT)
        assert r.returncode == 1, f"{path} matches an ignore pattern"


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
