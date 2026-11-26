#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Validate cad-skills records (board, variants, part, supplier profile).

  uv run contracts/validate.py [--json] [--schemas DIR] FILE [FILE ...]

The tool reads `schema_id` and `schema_version` from each record. It selects the
schema for that exact version from `registry.json`. It then runs the schema and the
rules that compare fields.

Exit status (highest priority first)
  3  Invalid registry, missing or invalid schema, or validator failure.
  2  Incorrect arguments, missing input file, or missing schema directory.
  1  Unreadable file, parse error, or invalid record.
  0  All records pass.

With --json the tool writes one JSON object to standard output and nothing else.
The report holds no time and no random value. Two runs on the same inputs give the
same output.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import re
import sys
from pathlib import Path

import jsonschema
import yaml
from jsonschema import Draft202012Validator, validators

HERE = Path(__file__).resolve().parent
REPORT_VERSION = "1.0"
VERSION_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
MAX_YAML_NODES = 200_000
TAG = "tag:yaml.org,2002:"
SCALAR_TAGS = {TAG + t for t in ("str", "int", "float", "bool", "null")}


# --------------------------------------------------------------------------- findings


def finding(code, file="", location="", message="", severity="error"):
    return {"code": code, "severity": severity, "file": file, "location": location,
            "message": message[:300]}


class RecordError(Exception):
    """A record is not acceptable. `findings` holds the reasons."""

    def __init__(self, findings):
        self.findings = findings
        super().__init__("; ".join(f["code"] + " " + f["message"] for f in findings))


class ToolError(Exception):
    """The registry or a schema is not usable. This is a tool failure (exit 3)."""

    def __init__(self, findings):
        self.findings = findings
        super().__init__("; ".join(f["code"] + " " + f["message"] for f in findings))


def pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


# --------------------------------------------------------------------------- loaders
# Accepted data: JSON-compatible values only. Mappings have string keys. No duplicate
# keys, no merge keys, no recursive aliases, no custom tags, no non-finite numbers.


class _YamlLoader(yaml.SafeLoader):
    """Safe loader with the JSON number and boolean grammar.

    A plain ISO date stays a string. The text `yes`, `no`, `on` and `off` stay strings.
    """


_YamlLoader.yaml_implicit_resolvers = {}
_JSON_INT = r"-?(?:0|[1-9][0-9]*)"
for _tag, _regex, _first in (
    ("bool", r"^(?:true|false)$", "tf"),
    ("int", r"^" + _JSON_INT + r"$", "-0123456789"),
    ("float", r"^" + _JSON_INT + r"(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$", "-0123456789"),
    ("float", r"^(?:[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$", "-+."),
    ("null", r"^(?:null|~)$", "n~"),
    ("merge", r"^<<$", "<"),
):
    _YamlLoader.add_implicit_resolver(TAG + _tag, re.compile(_regex), list(_first))


def _walk_yaml(node, ptr, stack, count, out):
    """Examine the YAML node tree. Add one finding for each defect."""
    if id(node) in stack:
        out.append(("file.recursive_alias", ptr, "A recursive alias is not accepted."))
        return
    count[0] += 1
    if count[0] > MAX_YAML_NODES:
        out.append(("file.too_complex", ptr, "The record has too many nodes."))
        raise StopIteration
    if isinstance(node, yaml.ScalarNode):
        if node.tag not in SCALAR_TAGS:
            out.append(("file.unsupported_tag", ptr, f"The tag {node.tag} is not accepted."))
        return
    stack.add(id(node))
    if isinstance(node, yaml.SequenceNode):
        if node.tag != TAG + "seq":
            out.append(("file.unsupported_tag", ptr, f"The tag {node.tag} is not accepted."))
        for i, child in enumerate(node.value):
            _walk_yaml(child, pointer(ptr, i), stack, count, out)
    else:
        if node.tag != TAG + "map":
            out.append(("file.unsupported_tag", ptr, f"The tag {node.tag} is not accepted."))
        seen = set()
        for key, value in node.value:
            if isinstance(key, yaml.ScalarNode) and key.tag == TAG + "merge":
                out.append(("file.merge_key", ptr, "A merge key is not accepted."))
                continue
            if not (isinstance(key, yaml.ScalarNode) and key.tag == TAG + "str"):
                out.append(("file.non_string_key", ptr, "A mapping key is not a string."))
                continue
            child_ptr = pointer(ptr, key.value)
            if key.value in seen:
                out.append(("file.duplicate_key", child_ptr, f"The key {key.value!r} occurs two times."))
            seen.add(key.value)
            _walk_yaml(value, child_ptr, stack, count, out)
    stack.discard(id(node))


class _Pairs(list):
    """The key-value pairs of one JSON object, before the duplicate-key test."""


def _json_constant(name):
    return {"NaN": math.nan, "Infinity": math.inf, "-Infinity": -math.inf}[name]


def _from_pairs(value, ptr, out):
    if isinstance(value, _Pairs):
        result = {}
        for key, item in value:
            child_ptr = pointer(ptr, key)
            if key in result:
                out.append(("file.duplicate_key", child_ptr, f"The key {key!r} occurs two times."))
            result[key] = _from_pairs(item, child_ptr, out)
        return result
    if isinstance(value, list):
        return [_from_pairs(item, pointer(ptr, i), out) for i, item in enumerate(value)]
    return value


def _scan_non_finite(value, ptr, out):
    if isinstance(value, float) and not math.isfinite(value):
        out.append(("file.non_finite", ptr, "A number is not finite."))
    elif isinstance(value, dict):
        for key, item in value.items():
            _scan_non_finite(item, pointer(ptr, key), out)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _scan_non_finite(item, pointer(ptr, i), out)


def parse_record(raw: bytes, suffix: str, file: str = ""):
    """Parse the bytes of a record. Return the data or raise RecordError."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise RecordError([finding("file.parse_error", file, "", f"The file is not UTF-8: {err}")])
    out = []
    if suffix == ".json":
        try:
            data = json.loads(text, object_pairs_hook=_Pairs, parse_constant=_json_constant)
        except (json.JSONDecodeError, RecursionError) as err:
            raise RecordError([finding("file.parse_error", file, "", f"JSON error: {err}")])
        data = _from_pairs(data, "", out)
    elif suffix in (".yaml", ".yml"):
        try:
            node = yaml.compose(text, Loader=_YamlLoader)
            if node is not None:
                try:
                    _walk_yaml(node, "", set(), [0], out)
                except StopIteration:
                    pass
        except yaml.YAMLError as err:
            raise RecordError([finding("file.parse_error", file, "", "YAML error: " + str(err).replace("\n", " "))])
        if out:
            raise RecordError([finding(c, file, p, m) for c, p, m in out])
        loader = _YamlLoader("")
        try:
            data = loader.construct_document(node) if node is not None else None
        except yaml.YAMLError as err:
            raise RecordError([finding("file.parse_error", file, "", "YAML error: " + str(err).replace("\n", " "))])
        except (ValueError, KeyError, OverflowError) as err:
            # A scalar with an explicit tag (for example `!!int bad`) can have a value that the tag does not accept.
            raise RecordError([finding("file.parse_error", file, "",
                                       f"A scalar value is not valid for its tag ({type(err).__name__}).")])
        finally:
            loader.dispose()
    else:
        raise RecordError([finding("file.parse_error", file, "", f"The suffix {suffix!r} is not .json, .yaml or .yml.")])
    _scan_non_finite(data, "", out)
    if out:
        raise RecordError([finding(c, file, p, m) for c, p, m in out])
    if not isinstance(data, dict):
        raise RecordError([finding("file.not_mapping", file, "", "The root of the record is not a mapping.")])
    return data


def load_record(path) -> dict:
    """Read a record file. Raise RecordError if it is not acceptable."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as err:
        raise RecordError([finding("file.unreadable", str(path), "", f"Cannot read the file: {err}")])
    return parse_record(raw, path.suffix.lower(), str(path))


# --------------------------------------------------------------------------- hashes


def _json_tree_problems(value, ptr, ancestors, out):
    """Find each part of a value that is not JSON-compatible. Add (pointer, message) to `out`."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            out.append((ptr, "A number is not finite."))
        return
    if not isinstance(value, (dict, list)):
        out.append((ptr, f"The type {type(value).__name__} is not JSON-compatible."))
        return
    if id(value) in ancestors:
        out.append((ptr, "The record has a cycle."))
        return
    ancestors.add(id(value))
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                _json_tree_problems(item, pointer(ptr, key), ancestors, out)
            else:
                out.append((pointer(ptr, key), "A mapping key is not a string."))
    else:
        for i, item in enumerate(value):
            _json_tree_problems(item, pointer(ptr, i), ancestors, out)
    ancestors.discard(id(value))


def canonical_bytes(record: dict) -> bytes:
    """JSON bytes of the record without the root `content_sha256` field.

    The record must hold JSON-compatible data only: mappings with string keys, lists,
    strings, booleans, null, integers and finite floats. Other types and cycles raise RecordError.
    """
    if not isinstance(record, dict):
        raise RecordError([finding("file.not_json_compatible", "", "", "The root of the record is not a mapping.")])
    body = {k: v for k, v in record.items() if k != "content_sha256"}
    problems = []
    try:
        _json_tree_problems(body, "", set(), problems)
    except RecursionError:
        problems = [("", "The record has too many levels.")]
    if problems:
        raise RecordError([finding("file.not_json_compatible", "", p, m) for p, m in problems])
    try:
        text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as err:
        raise RecordError([finding("file.not_json_compatible", "", "", f"Cannot hash the record: {err}")])
    return text.encode("utf-8")


def canonical_hash(record: dict) -> str:
    """SHA-256 of `canonical_bytes`, as lowercase hexadecimal text."""
    return hashlib.sha256(canonical_bytes(record)).hexdigest()


# --------------------------------------------------------------------------- schemas


def _is_integer(_checker, value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(_checker, value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True  # An integer has no upper limit here. Do not convert it to a float.
    return isinstance(value, float) and math.isfinite(value)


_TYPE_CHECKER = (Draft202012Validator.TYPE_CHECKER
                 .redefine("integer", _is_integer).redefine("number", _is_number))
StrictValidator = validators.extend(Draft202012Validator, type_checker=_TYPE_CHECKER)


def parse_version(text):
    match = VERSION_RE.fullmatch(text) if isinstance(text, str) else None
    return (int(match.group(1)), int(match.group(2))) if match else None


def load_registry(schemas_dir: Path):
    """Return {schema_id: {"schemas": {version: validator}}}. Raise ToolError."""
    problems = []

    def bad(code, message):
        problems.append(finding(code, str(schemas_dir), "", message))

    reg_path = schemas_dir / "registry.json"
    try:
        data = parse_record(reg_path.read_bytes(), ".json", str(reg_path))
    except OSError as err:
        raise ToolError([finding("tool.registry_invalid", str(reg_path), "", f"Cannot read the registry: {err}")])
    except RecordError as err:
        raise ToolError([finding("tool.registry_invalid", str(reg_path), f["location"], f["message"]) for f in err.findings])
    records = data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, dict) or not records:
        raise ToolError([finding("tool.registry_invalid", str(reg_path), "/records", "The registry has no `records` mapping.")])
    registry = {}
    for schema_id, entry in sorted(records.items()):
        schemas = entry.get("schemas") if isinstance(entry, dict) else None
        if not isinstance(schemas, dict) or not schemas or parse_version(entry.get("latest")) is None \
                or entry.get("latest") not in schemas:
            bad("tool.registry_invalid", f"The registry entry {schema_id!r} is not valid.")
            continue
        validators_by_version = {}
        for version, name in sorted(schemas.items()):
            if parse_version(version) is None or not isinstance(name, str) or "/" in name or "\\" in name:
                bad("tool.registry_invalid", f"The registry entry {schema_id!r} version {version!r} is not valid.")
                continue
            schema_path = schemas_dir / name
            try:
                schema = parse_record(schema_path.read_bytes(), ".json", str(schema_path))
            except OSError:
                bad("tool.schema_missing", f"The registry names the schema file {name!r}, which is not present.")
                continue
            except RecordError as err:
                bad("tool.schema_invalid", f"The schema file {name!r} is not valid: {err.findings[0]['message']}")
                continue
            try:
                Draft202012Validator.check_schema(schema)
            except jsonschema.SchemaError as err:
                bad("tool.schema_invalid", f"The schema file {name!r} is not valid: {err.message}")
                continue
            validators_by_version[version] = StrictValidator(
                schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        registry[schema_id] = {"schemas": validators_by_version}
    if problems:
        raise ToolError(problems)
    return registry


def check_version(record: dict, entry: dict, file: str = ""):
    """Return (version_key, findings). `entry` is a registry entry."""
    sid, ver = record.get("schema_id"), record.get("schema_version")
    if "schema_version" not in record:
        return None, [finding("schema.missing_id", file, "/schema_version", "The record has no `schema_version`.")]
    parsed = parse_version(ver)
    if parsed is None:
        return None, [finding("schema.version_malformed", file, "/schema_version",
                              f"The version {ver!r} is not a string of the form MAJOR.MINOR.")]
    supported = {parse_version(v): v for v in entry["schemas"]}
    if parsed[0] not in {m for m, _ in supported}:
        return None, [finding("schema.major_unsupported", file, "/schema_version",
                              f"The major version of {ver} is not supported for {sid}.")]
    if parsed in supported:
        return ver, []
    if parsed[1] > max(n for m, n in supported if m == parsed[0]):
        return None, [finding("schema.minor_newer", file, "/schema_version",
                              f"The version {ver} is newer than the supported versions of {sid}.")]
    return None, [finding("schema.version_unsupported", file, "/schema_version",
                          f"The version {ver} is not in the registry for {sid}.")]


# --------------------------------------------------------------------------- rules

# (schema name, required property) -> finding code. This keeps one finding for one defect.
MISSING_CODES = {("part", "mpn"): "part.missing_mpn"}


def _schema_findings(file, kind, record, validator):
    found = {}
    errors = sorted(validator.iter_errors(record), key=lambda e: (list(map(str, e.absolute_path)), e.validator))
    for err in errors:
        base = ""
        for part in err.absolute_path:
            base = pointer(base, part)
        path = list(err.absolute_path)
        if err.validator == "additionalProperties" and err.schema.get("additionalProperties") is False:
            allowed = set(err.schema.get("properties", {}))
            for extra in sorted(set(err.instance) - allowed):
                loc = pointer(base, extra)
                found.setdefault(loc, finding("schema.unknown_field", file, loc, f"The field {extra!r} is not in the schema."))
            continue
        if err.validator == "required":
            for name in err.validator_value:
                if name not in err.instance:
                    loc = pointer(base, name)
                    code = MISSING_CODES.get((kind, name), "schema.invalid") if not path else "schema.invalid"
                    found.setdefault(loc, finding(code, file, loc, f"The field {name!r} is missing."))
            continue
        code = "schema.invalid"
        if kind == "part" and path == ["mpn"] and err.validator == "pattern":
            code = "part.missing_mpn"
        elif kind == "variants" and len(path) == 4 and path[0] == "variants" and path[2] == "references":
            code = "variants.unknown_state"
        found.setdefault(base, finding(code, file, base, err.message))
    return list(found.values())


def _rules_variants(file, record):
    out, seen = [], set()
    for i, variant in enumerate(record["variants"]):
        if variant["id"] in seen:
            out.append(finding("variants.duplicate_id", file, f"/variants/{i}/id", f"The variant ID {variant['id']!r} occurs two times."))
        seen.add(variant["id"])
    return out


def _rules_supplier_profile(file, record):
    out = []
    if record["content_sha256"] != canonical_hash(record):
        out.append(finding("profile.hash_mismatch", file, "/content_sha256", "The content hash does not match the record."))
    for name, limit in record["limits"].items():
        loc = pointer("/limits", name)
        if limit["kind"] == "unconfirmed":
            if "value" in limit or "value_kind" in limit:
                out.append(finding("profile.unconfirmed_with_value", file, loc, "An unconfirmed limit has a value."))
            continue
        missing = [f for f in ("value_kind", "value", "source_url", "retrieved") if f not in limit]
        if missing:
            out.append(finding("profile.limit_incomplete", file, loc, "The limit has no " + ", ".join(missing) + "."))
        elif limit["kind"] in ("minimum", "maximum") and limit["value_kind"] != "number":
            out.append(finding("profile.limit_not_numeric", file, loc, "A minimum or maximum limit must have a numeric value."))
    opts = record.get("fabrication_options")
    if opts is not None:
        bt = opts["board_thickness"]
        if bt["min_mm"] > bt["max_mm"]:
            out.append(finding("profile.options_invalid", file, "/fabrication_options/board_thickness",
                               "The minimum board thickness is larger than the maximum."))
        else:
            for i, val in enumerate(bt["allowed_mm"]):
                if val < bt["min_mm"] or val > bt["max_mm"]:
                    out.append(finding("profile.options_invalid", file, f"/fabrication_options/board_thickness/allowed_mm/{i}",
                                       "The allowed thickness is outside the minimum and maximum limits."))
            if "manual_review_below_mm" in bt and not (bt["min_mm"] <= bt["manual_review_below_mm"] <= bt["max_mm"]):
                out.append(finding("profile.options_invalid", file, "/fabrication_options/board_thickness/manual_review_below_mm",
                                   "The manual-review thickness is outside the minimum and maximum limits."))
        mc = opts["mask_color"]
        if "bridge_min_by_color" in mc and set(mc["bridge_min_by_color"]) != set(mc["allowed"]):
            out.append(finding("profile.options_invalid", file, "/fabrication_options/mask_color/bridge_min_by_color",
                               "The mask bridge map keys differ from the allowed mask colors."))
    return out


RULES = {"variants": _rules_variants, "supplier-profile": _rules_supplier_profile}


def validate_record(record: dict, registry: dict, file: str = ""):
    """Return the findings for one parsed record."""
    sid = record.get("schema_id")
    if not isinstance(sid, str) or "schema_id" not in record:
        return [finding("schema.missing_id", file, "/schema_id", "The record has no `schema_id` string.")]
    entry = registry.get(sid)
    if entry is None:
        return [finding("schema.unknown_id", file, "/schema_id", f"The schema ID {sid!r} is not in the registry.")]
    version, problems = check_version(record, entry, file)
    if problems:
        return problems
    kind = sid.split("/", 1)[-1]
    problems = _schema_findings(file, kind, record, entry["schemas"][version])
    if not problems and kind in RULES:
        problems = RULES[kind](file, record)
    return problems


# --------------------------------------------------------------------------- B234 constants

INPUT_ROLES = ("board_record", "board", "schematic", "variants", "supplier_profile", "export_settings",
               "toolchain", "board_interface", "waivers", "parts", "circuit_source", "supplier_rules", "supplier_settings",
               "project_settings", "design_rules")
OUTPUT_ROLES = ("copper", "mask", "silk", "paste", "outline", "drill_plated", "drill_nonplated", "bom", "placement",
                "schematic_pdf", "fabrication_drawing", "assembly_drawing", "test_record", "firmware", "stencil",
                "panel", "report", "image", "evidence")
LAYERED_ROLES = ("copper", "mask", "silk", "paste", "outline")
FIXED_INPUT_PATHS = {
    "board_record": "board.yaml", "board": "kicad/board.kicad_pcb", "schematic": "kicad/board.kicad_sch",
    "variants": "variants.yaml", "supplier_profile": "manufacturing/supplier.yaml",
    "export_settings": "manufacturing/export.yaml", "toolchain": "toolchain.lock.json",
    "board_interface": "mechanical/board-interface.json", "waivers": "manufacturing/waivers.yaml",
    "project_settings": "kicad/board.kicad_pro", "design_rules": "kicad/board.kicad_dru",
}
# role -> schema kind for the records that --project parses. The tool reads the PCB and the schematic as bytes only.
PROJECT_RECORDS = {
    "board_record": "board", "variants": "variants", "supplier_profile": "supplier-profile",
    "export_settings": "export-settings", "toolchain": "toolchain-lock", "board_interface": "board-interface",
    "waivers": "waivers",
}
NECESSARY_PROJECT = ("board_record", "board", "schematic", "variants", "supplier_profile", "export_settings", "toolchain")
NECESSARY_INPUTS = NECESSARY_PROJECT + ("board_interface",)
BARE_CHECKS = ("design.erc", "design.drc", "design.parity", "fab.profile_evidence", "fab.export_inventory",
               "fab.layer_order", "fab.drill_split", "fab.supplier_rules")
PCBA_CHECKS = BARE_CHECKS + ("asm.bom_consistent", "asm.placement_rotation", "asm.variant_agreement",
                             "asm.stock_dated", "asm.test_record")
REQUIRED_CHECKS = {"bare_board": BARE_CHECKS, "pcba": PCBA_CHECKS}
CHECK_INPUT_ROLES = {
    "design.erc": ("schematic",),
    "design.drc": ("board",),
    "design.parity": ("schematic", "board"),
    "fab.profile_evidence": ("supplier_profile",),
    "fab.export_inventory": ("board", "export_settings"),
    "fab.layer_order": ("board", "export_settings"),
    "fab.drill_split": ("board", "board_interface", "export_settings"),
    "fab.supplier_rules": ("board", "supplier_profile", "export_settings", "supplier_rules", "supplier_settings", "toolchain"),
    "asm.bom_consistent": ("parts", "variants", "board_record", "supplier_profile"),
    "asm.placement_rotation": ("board", "parts", "variants"),
    "asm.variant_agreement": ("board_record", "variants", "parts"),
    "asm.stock_dated": ("parts", "board_record"),
    "asm.test_record": ("board", "parts", "variants", "board_record"),
}
OPTIONAL_CHECK_INPUT_ROLES = {"design.drc": ("project_settings", "design_rules"),
                            "design.erc": ("project_settings",)}
HASH_CODES = {"board": "cross.board_pcb_hash_mismatch", "board_record": "cross.board_record_hash_mismatch",
              "schematic": "cross.schematic_hash_mismatch"}
WILDCARDS = {"*", "all", "any"}
DRILL_CONDITIONS = {"drill_plated": "no_plated_holes", "drill_nonplated": "no_nonplated_holes"}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def family_of(role: str) -> str:
    """The role family of an export layer role: `copper_top` gives `copper`."""
    return role.split("_", 1)[0]


def _path_problem(path):
    """Return a message if `path` is not a safe relative POSIX path, else None."""
    if not isinstance(path, str) or path == "":
        return "The path is empty."
    if any(ord(c) < 32 or ord(c) == 127 for c in path):
        return "The path has a control character."
    if "\\" in path:
        return "The path has a backslash."
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return "The path is absolute."
    for part in path.split("/"):
        if part in ("", ".", ".."):
            return "The path has an empty, `.` or `..` segment."
    return None


def _resolve_confined(root: Path, rel: str):
    """Test `rel` against `root`. Return (status, resolved path). The status is ok, missing or escape.

    This function reads no file. Each requested path passes this test on its own.
    """
    try:
        base = root.resolve()
        target = (root / rel).resolve()
    except (OSError, RuntimeError):
        return "escape", None
    if base != target and base not in target.parents:
        return "escape", None
    if not target.is_file():
        return "missing", None
    return "ok", target


def _read_confined(root: Path, rel: str):
    """Read `rel` under `root`. Return (status, bytes). The status is ok, missing or escape."""
    status, target = _resolve_confined(root, rel)
    if status != "ok":
        return status, None
    try:
        return "ok", target.read_bytes()
    except OSError:
        return "missing", None


# --------------------------------------------------------------------------- geometry (point lists only)


def _orient(a, b, c):
    value = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (value > 0) - (value < 0)


def _on_segment(a, b, c):
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def _segments_cross(p1, p2, p3, p4):
    o1, o2, o3, o4 = _orient(p1, p2, p3), _orient(p1, p2, p4), _orient(p3, p4, p1), _orient(p3, p4, p2)
    if o1 != o2 and o3 != o4:
        return True
    return ((o1 == 0 and _on_segment(p1, p2, p3)) or (o2 == 0 and _on_segment(p1, p2, p4))
            or (o3 == 0 and _on_segment(p3, p4, p1)) or (o4 == 0 and _on_segment(p3, p4, p2)))


def _polygon_problem(points):
    """Return a message if the point list is not a simple polygon, else None."""
    count = len(points)
    if count < 3:
        return "The polygon has fewer than 3 points."
    xy = [(p["x"], p["y"]) for p in points]
    try:
        for i in range(count):
            if xy[i] == xy[(i + 1) % count]:
                return "The last point repeats the first point." if i == count - 1 else "A point repeats the point before it."
        if sum(xy[i][0] * xy[(i + 1) % count][1] - xy[(i + 1) % count][0] * xy[i][1] for i in range(count)) == 0:
            return "The polygon has zero area."
        for i in range(count):
            for j in range(i + 1, count):
                if j == i + 1 or (i == 0 and j == count - 1):
                    continue
                if _segments_cross(xy[i], xy[(i + 1) % count], xy[j], xy[(j + 1) % count]):
                    return "Two segments of the polygon cross."
    except OverflowError:
        return "A coordinate is too large for the geometry test."
    return None


def _inside(point, points):
    x, y = point
    inside = False
    count = len(points)
    for i in range(count):
        x1, y1 = points[i]["x"], points[i]["y"]
        x2, y2 = points[(i + 1) % count]["x"], points[(i + 1) % count]["y"]
        if (y1 > y) != (y2 > y):
            # Compare without a division, so that a large integer does not overflow a float.
            left, right = (x - x1) * (y2 - y1), (x2 - x1) * (y - y1)
            if (left < right) if y2 > y1 else (left > right):
                inside = not inside
    return inside


# --------------------------------------------------------------------------- B234 record rules


def _rules_waivers(file, record):
    out, ids, pairs = [], set(), set()
    for i, waiver in enumerate(record["waivers"]):
        loc = f"/waivers/{i}"
        if waiver["id"] in ids:
            out.append(finding("waiver.duplicate_id", file, loc + "/id", f"The waiver ID {waiver['id']!r} occurs two times."))
        ids.add(waiver["id"])
        if waiver["rule"].strip().lower() in WILDCARDS:
            out.append(finding("waiver.wildcard", file, loc + "/rule", "A rule name cannot be a wildcard."))
        for j, obj in enumerate(waiver["objects"]):
            if obj.strip().lower() in WILDCARDS:
                out.append(finding("waiver.wildcard", file, f"{loc}/objects/{j}", "An object name cannot be a wildcard."))
            pair = (waiver["kind"], waiver["rule"], obj)
            if pair in pairs:
                out.append(finding("waiver.duplicate_pair", file, f"{loc}/objects/{j}",
                                   "The same kind, rule and object occur in two waivers."))
            pairs.add(pair)
    return out


def _rules_evidence(file, record):
    out = []
    if record["status"] == "pass":
        missing = [f for f in ("inputs", "artifact") if not record.get(f)]
        if record["method"] == "tool":
            if not record.get("tool"):
                missing.insert(0, "tool")
            if missing:
                out.append(finding("evidence.tool_incomplete", file, "", "A passed tool record has no " + ", ".join(missing) + "."))
        else:
            missing = [f for f in ("reviewer", "observed_on") if not record.get(f)] + missing
            if missing:
                out.append(finding("pkg.check_manual_incomplete", file, "", "A passed manual record has no " + ", ".join(missing) + "."))
    paths = [(f"/inputs/{i}/path", item["path"]) for i, item in enumerate(record.get("inputs", []))]
    if record.get("artifact"):
        paths.append(("/artifact/path", record["artifact"]["path"]))
    for loc, path in paths:
        problem = _path_problem(path)
        if problem:
            out.append(finding("pkg.path_invalid", file, loc, problem))
    return out


def _rules_board_interface(file, record):
    out = []
    problem = _polygon_problem(record["outline"])
    if problem:
        out.append(finding("iface.outline_invalid", file, "/outline", problem))
    for i, cutout in enumerate(record["cutouts"]):
        problem = _polygon_problem(cutout)
        if problem:
            out.append(finding("iface.cutout_invalid", file, f"/cutouts/{i}", problem))
    seen = set()
    for name in ("holes", "connector_frames"):
        for i, item in enumerate(record[name]):
            if item["id"] in seen:
                out.append(finding("iface.duplicate_id", file, f"/{name}/{i}/id", f"The ID {item['id']!r} occurs two times."))
            seen.add(item["id"])
    if not out:
        try:
            for i, hole in enumerate(record["holes"]):
                point = (hole["x"], hole["y"])
                if not _inside(point, record["outline"]) or any(_inside(point, c) for c in record["cutouts"]):
                    out.append(finding("iface.hole_outside_outline", file, f"/holes/{i}", "The hole center is outside the board area."))
        except OverflowError:
            out.append(finding("iface.hole_outside_outline", file, "/holes", "A coordinate is too large for the geometry test."))
    return out


def _rules_toolchain(file, record):
    out = []
    for name in ("libraries", "models"):
        seen = set()
        for i, item in enumerate(record[name]):
            key = (item["name"], item["version"])
            if key in seen:
                out.append(finding("toolchain.duplicate_item", file, f"/{name}/{i}", "The name and version occur two times."))
            seen.add(key)
            if item["license"] == "unknown" and not str(item.get("notes", "")).strip():
                out.append(finding("toolchain.unknown_license_no_notes", file, f"/{name}/{i}/license", "An unknown license needs notes."))
    for tool, entry in record["tools"].items():
        if entry.get("license") == "unknown" and not str(entry.get("notes", "")).strip():
            out.append(finding("toolchain.unknown_license_no_notes", file, f"/tools/{tool}/license", "An unknown license needs notes."))
    return out


def _rules_export_settings(file, record):
    out, seen, suffixes = [], set(), {}
    for i, layer in enumerate(record["layers"]):
        key = (layer["role"], layer["kicad_layer"])
        if key in seen:
            out.append(finding("export.duplicate_layer", file, f"/layers/{i}", "The role and layer occur two times."))
        seen.add(key)
        suffixes.setdefault(layer["suffix"], []).append(f"/layers/{i}/suffix")
    for name in ("plated_suffix", "nonplated_suffix"):
        suffixes.setdefault(record["drill"][name], []).append(f"/drill/{name}")
    for suffix, places in suffixes.items():
        for place in places[1:]:
            out.append(finding("export.suffix_duplicate", file, place, f"The suffix {suffix!r} occurs two times."))
    roles = {layer["role"] for layer in record["layers"]}
    for role in ("outline", "copper_top"):
        if role not in roles:
            out.append(finding("export.layer_missing", file, "/layers", f"The settings have no {role} layer."))
    return out


def _rules_manifest(file, record):
    """Rules that need only the manifest. Completeness rules apply to `qualified` only."""
    out = []
    qualified = record["status"] == "qualified"
    for name in ("inputs", "outputs"):
        seen = set()
        for i, item in enumerate(record[name]):
            loc = f"/{name}/{i}/path"
            problem = _path_problem(item["path"])
            if problem:
                out.append(finding("pkg.path_invalid", file, loc, problem))
            elif item["path"] == "manifest.json":
                out.append(finding("pkg.self_reference", file, loc, "The manifest cannot list itself."))
            if item["path"] in seen:
                out.append(finding("pkg.duplicate_path", file, loc, "The path occurs two times."))
            seen.add(item["path"])
    in_paths = {item["path"] for item in record["inputs"]}
    for i, item in enumerate(record["outputs"]):
        if item["path"] in in_paths:
            out.append(finding("pkg.input_output_overlap", file, f"/outputs/{i}/path", "The path is also an input."))
        if item["size_bytes"] == 0:
            out.append(finding("pkg.output_empty", file, f"/outputs/{i}", "The output has a size of 0."))
        has_layer = "layer" in item
        if item["role"] in LAYERED_ROLES and not has_layer:
            out.append(finding("pkg.layer_unmapped", file, f"/outputs/{i}", "An output of this role needs a layer."))
        elif item["role"] not in LAYERED_ROLES and has_layer:
            out.append(finding("pkg.layer_unmapped", file, f"/outputs/{i}/layer", "This role has no layer."))
    seen_layers = set()
    for i, item in enumerate(record["outputs"]):
        if item["role"] in LAYERED_ROLES and "layer" in item:
            key = (item["role"], item["layer"])
            if key in seen_layers:
                out.append(finding("pkg.layer_duplicate", file, f"/outputs/{i}", "The role and layer occur two times."))
            seen_layers.add(key)
    ids = [check["id"] for check in record["checks"]]
    for i, check in enumerate(record["checks"]):
        if check["id"] in ids[:i]:
            out.append(finding("pkg.check_duplicate", file, f"/checks/{i}/id", "The check ID occurs two times."))
    if record["status"] == "unqualified" and not record["reasons"]:
        out.append(finding("pkg.reasons_required", file, "/reasons", "An unqualified package needs a reason."))
    if qualified and record["reasons"]:
        out.append(finding("pkg.reasons_required", file, "/reasons", "A qualified package has no reason."))
    if qualified:
        if not record["outputs"]:
            out.append(finding("pkg.no_outputs", file, "/outputs", "The package has no output."))
        roles = {item["role"] for item in record["inputs"]}
        needed = set(NECESSARY_INPUTS) | ({"parts"} if record["kind"] == "pcba" else set())
        for role in sorted(needed - roles):
            out.append(finding("pkg.input_missing", file, "/inputs", f"The input role {role} is absent."))
        status = {check["id"]: check["status"] for check in record["checks"]}
        for check_id in REQUIRED_CHECKS[record["kind"]]:
            if check_id not in status:
                out.append(finding("pkg.check_missing", file, "/checks", f"The required check {check_id} is absent."))
            elif status[check_id] != "pass":
                out.append(finding("pkg.false_qualification", file, "/checks", f"The required check {check_id} is not pass."))
    return out


RULES.update({
    "waivers": _rules_waivers, "evidence": _rules_evidence, "board-interface": _rules_board_interface,
    "toolchain-lock": _rules_toolchain, "export-settings": _rules_export_settings, "manifest": _rules_manifest,
})


# --------------------------------------------------------------------------- project and package checks


class _Ctx:
    """Collects findings and input hashes for the project and package modes."""

    def __init__(self, registry):
        self.registry = registry
        self.findings = []
        self.inputs = []
        self.snapshots = {}

    def read(self, root, rel):
        """Read a file under `root` one time in this run. Later calls return the same bytes.

        Each requested path first passes its own confinement test against its own root.
        Only a successful read is shared, by the resolved file path. Two names for one file,
        and the same name in two roots that resolve to one file, then use one snapshot.
        The parse, the hash comparisons and the evidence comparisons all use this snapshot.
        A missing file and a path that leaves its root give the same result as before.
        """
        status, target = _resolve_confined(Path(root), rel)
        if status != "ok":
            return status, None
        key = str(target)
        if key not in self.snapshots:
            result = _read_confined(Path(root), rel)
            if result[0] != "ok":
                return result  # A failed read is not shared.
            self.snapshots[key] = result
        return self.snapshots[key]

    def add(self, code, file, location, message):
        self.findings.append(finding(code, file, location, message))

    def record(self, name, raw, suffix):
        """Hash, parse and validate one record. Return the record, or None if it has a defect."""
        self.inputs.append({"path": name, "sha256": sha256_hex(raw)})
        try:
            record = parse_record(raw, suffix, name)
        except RecordError as err:
            self.findings.extend(err.findings)
            return None
        problems = validate_record(record, self.registry, name)
        self.findings.extend(problems)
        return None if problems else record


def _project_rules(ctx, project, records, shas):
    board = records.get("board_record")
    name = lambda role: f"{project}/{FIXED_INPUT_PATHS[role]}"  # noqa: E731
    profile, variants = records.get("supplier_profile"), records.get("variants")
    interface, waivers, toolchain = records.get("board_interface"), records.get("waivers"), records.get("toolchain")
    if board and variants and board["variant"] not in {v["id"] for v in variants["variants"]}:
        ctx.add("cross.variant_missing", name("board_record"), "/variant", "The selected variant is not in variants.yaml.")
    if board and profile:
        for field in ("id", "service"):
            if board["supplier"][field] != profile[field]:
                ctx.add("cross.supplier_mismatch", name("board_record"), f"/supplier/{field}", f"The supplier {field} differs from the profile.")
        if board["supplier"]["profile_sha256"] != profile["content_sha256"]:
            ctx.add("cross.supplier_mismatch", name("board_record"), "/supplier/profile_sha256", "The profile hash differs from the profile content hash.")
    if board:
        cs = board["coordinate_system"]
        if (cs["x_axis"], cs["y_axis"], cs["units"]) != ("right", "up", "mm"):
            ctx.add("cross.coordinate_convention", name("board_record"), "/coordinate_system", "The board must use x_axis right, y_axis up, and units mm.")
    if board and interface:
        try:
            xs, ys = [p["x"] for p in interface["outline"]], [p["y"] for p in interface["outline"]]
            tol = interface["geometry_tolerance_mm"]
            mech = board["mechanical"]
            if (abs((max(xs) - min(xs)) - mech["width_mm"]) > tol or abs((max(ys) - min(ys)) - mech["height_mm"]) > tol
                    or abs(interface["thickness_mm"] - mech["thickness_mm"]) > tol):
                ctx.add("cross.dimension_mismatch", name("board_interface"), "/outline", "The interface dimensions differ from board.yaml by more than the tolerance.")
        except OverflowError:
            ctx.add("cross.dimension_mismatch", name("board_interface"), "/outline", "A dimension is too large for the comparison.")
        if board["release_revision"] != interface["board_revision"]:
            ctx.add("cross.revision_mismatch", name("board_interface"), "/board_revision", "The revision differs from release_revision.")
    if board and waivers:
        for i, waiver in enumerate(waivers["waivers"]):
            if waiver["revision"] != board["release_revision"]:
                ctx.add("cross.revision_mismatch", name("waivers"), f"/waivers/{i}/revision", "The revision differs from release_revision.")
    pcb, schematic = shas.get("board"), shas.get("schematic")
    if pcb and interface and interface["board_sha256"] != pcb:
        ctx.add("cross.board_pcb_hash_mismatch", name("board_interface"), "/board_sha256", "The hash differs from the PCB file bytes.")
    if waivers:
        for i, waiver in enumerate(waivers["waivers"]):
            if pcb and waiver["board_sha256"] != pcb:
                ctx.add("cross.board_pcb_hash_mismatch", name("waivers"), f"/waivers/{i}/board_sha256", "The hash differs from the PCB file bytes.")
            if schematic and waiver["schematic_sha256"] is not None and waiver["schematic_sha256"] != schematic:
                ctx.add("cross.waiver_schematic_hash_mismatch", name("waivers"), f"/waivers/{i}/schematic_sha256", "The hash differs from the schematic file bytes.")
    if toolchain and not toolchain["tools"]["kicad"]["used"]:
        ctx.add("cross.toolchain_kicad_missing", name("toolchain"), "/tools/kicad/used", "The project has a PCB, so tools.kicad.used must be true.")


def _load_project(ctx, project):
    """Read the project files. Return (records, hashes)."""
    records, shas = {}, {}
    for role, rel in FIXED_INPUT_PATHS.items():
        name = f"{project}/{rel}"
        status, raw = ctx.read(project, rel)
        if status == "escape":
            ctx.add("cross.path_escape", name, "", "The path resolves outside the project.")
            continue
        if status == "missing":
            if role in NECESSARY_PROJECT:
                ctx.add("cli.input_missing", name, "", "The project file is not present.")
            continue
        shas[role] = sha256_hex(raw)
        kind = PROJECT_RECORDS.get(role)
        if kind is None:
            ctx.inputs.append({"path": name, "sha256": shas[role]})
            continue
        record = ctx.record(name, raw, Path(rel).suffix)
        if record is not None and record.get("schema_id") != f"cad-skills/{kind}":
            ctx.add("cross.record_kind_mismatch", name, "/schema_id", f"The record must have the schema ID cad-skills/{kind}.")
            record = None
        if record is not None:
            records[role] = record
    return records, shas


def _package_rules(ctx, project, package, records, shas):
    name = f"{package}/manifest.json"
    status, raw = ctx.read(package, "manifest.json")
    if status != "ok":
        ctx.add("cli.input_missing", name, "", "The manifest is not present.")
        return
    manifest = ctx.record(name, raw, ".json")
    if manifest is None:
        return
    if manifest.get("schema_id") != "cad-skills/manifest":
        ctx.add("cross.record_kind_mismatch", name, "/schema_id", "The record must have the schema ID cad-skills/manifest.")
        return
    board, profile = records.get("board_record"), records.get("supplier_profile")
    exp, interface = records.get("export_settings"), records.get("board_interface")
    if board:
        if board["assembly"] != manifest["kind"]:
            ctx.add("cross.kind_mismatch", name, "/kind", "The kind differs from board.assembly.")
        if board["variant"] != manifest["variant"]:
            ctx.add("cross.variant_mismatch", name, "/variant", "The variant differs from board.variant.")
        if board["release_revision"] != manifest["board_revision"]:
            ctx.add("cross.revision_mismatch", name, "/board_revision", "The revision differs from release_revision.")
        if board["supplier"] != manifest["supplier"]:
            ctx.add("cross.profile_hash_mismatch", name, "/supplier", "The supplier differs from board.yaml.")
    if "board" in shas and manifest["board_sha256"] != shas["board"]:
        ctx.add("cross.board_pcb_hash_mismatch", name, "/board_sha256", "The hash differs from the PCB file bytes.")
    # Inputs
    roles = {}
    for i, item in enumerate(manifest["inputs"]):
        roles.setdefault(item["role"], []).append(item)
        loc = f"/inputs/{i}"
        fixed = FIXED_INPUT_PATHS.get(item["role"])
        if fixed is not None and item["path"] != fixed:
            ctx.add("cross.input_path_mismatch", name, loc + "/path", f"The role {item['role']} must use the path {fixed}.")
            continue
        state, data = ctx.read(project, item["path"])
        if state == "escape":
            ctx.add("cross.path_escape", name, loc + "/path", "The path resolves outside the project.")
        elif state == "missing":
            ctx.add("cross.input_hash_mismatch", name, loc, "The input file is not present.")
        elif sha256_hex(data) != item["sha256"]:
            ctx.add(HASH_CODES.get(item["role"], "cross.input_hash_mismatch"), name, loc + "/sha256", "The hash differs from the file bytes.")
    if board and board.get("circuit_source") == "skidl" and manifest["status"] == "qualified" and "circuit_source" not in roles:
        ctx.add("pkg.input_missing", name, "/inputs", "A qualified SKiDL package needs the circuit_source input.")
    if ("waivers" in shas) != ("waivers" in roles):
        ctx.add("cross.input_set_mismatch", name, "/inputs", "The waiver file and the waivers input do not agree.")
    if manifest["kind"] == "pcba":
        for role in ("project_settings", "design_rules"):
            if (role in shas) != (role in roles):
                ctx.add("cross.input_set_mismatch", name, "/inputs",
                        f"The project file and the {role} input do not agree.")
    # Outputs
    outputs = {item["path"]: item for item in manifest["outputs"]}
    for i, item in enumerate(manifest["outputs"]):
        loc = f"/outputs/{i}"
        state, data = ctx.read(package, item["path"])
        if state == "escape":
            ctx.add("cross.path_escape", name, loc + "/path", "The path resolves outside the package.")
        elif state == "missing":
            ctx.add("cross.output_missing", name, loc, "The output file is not present.")
        else:
            if len(data) == 0 and item["size_bytes"] != 0:
                ctx.add("pkg.output_empty", name, loc, "The output file has 0 bytes.")
            elif sha256_hex(data) != item["sha256"] or len(data) != item["size_bytes"]:
                ctx.add("cross.output_hash_mismatch", name, loc, "The hash or the size differs from the file.")
    # Layer mapping
    layers = {}
    if exp:
        layers = {(family_of(e["role"]), e["kicad_layer"]): e for e in exp["layers"]}
        for i, item in enumerate(manifest["outputs"]):
            if item["role"] in LAYERED_ROLES and "layer" in item:
                entry = layers.get((item["role"], item["layer"]))
                if entry is None:
                    ctx.add("pkg.layer_unmapped", name, f"/outputs/{i}/layer", "The layer is not declared for this role in the export settings.")
                elif not item["path"].endswith(entry["suffix"]):
                    ctx.add("pkg.layer_suffix_mismatch", name, f"/outputs/{i}/path", f"The path must end with {entry['suffix']}.")
    # Checks and evidence
    valid_pass = _evidence_rules(ctx, project, package, manifest, records, outputs, roles, name)
    # Drill applicability
    out_roles = {item["role"] for item in manifest["outputs"]}
    covered = set()
    for i, item in enumerate(manifest["drill_applicability"]):
        loc = f"/drill_applicability/{i}"
        if DRILL_CONDITIONS[item["role"]] != item["condition"]:
            ctx.add("pkg.applicability_condition_mismatch", name, loc + "/condition", "The condition does not pair with the role.")
            continue
        evidence = item.get("evidence")
        if not str(item.get("reason", "")).strip() or not isinstance(evidence, dict):
            ctx.add("pkg.applicability_reason_missing", name, loc, "The item needs a reason and evidence.")
            continue
        if "input_role" in evidence:
            if not interface:
                ctx.add("pkg.applicability_evidence_invalid", name, loc + "/evidence", "The board interface is not available.")
                continue
            plated = [h["plated"] for h in interface["holes"]]
            if (item["condition"] == "no_plated_holes" and any(plated)) or (item["condition"] == "no_nonplated_holes" and not all(plated)):
                ctx.add("cross.drill_applicability_false", name, loc, "The holes in the board interface contradict the condition.")
                continue
        elif "fab.drill_split" not in valid_pass:
            ctx.add("pkg.applicability_evidence_invalid", name, loc + "/evidence", "The check fab.drill_split is not pass with valid evidence.")
            continue
        covered.add(item["role"])
    if manifest["status"] != "qualified":
        return
    # Completeness (qualified only)
    kind, applic = manifest["kind"], manifest.get("applicability", {})
    needed = []
    for entry in (exp["layers"] if exp else []):
        family = family_of(entry["role"])
        if family in ("copper", "mask", "outline", "silk") or (family == "paste" and kind == "pcba"):
            needed.append((family, entry["kicad_layer"]))
    present = {(item["role"], item.get("layer")) for item in manifest["outputs"]}
    for key in needed:
        if key not in present:
            ctx.add("pkg.artifact_missing", name, "/outputs", f"The output {key[0]} for the layer {key[1]} is absent.")
    wanted = ["schematic_pdf", "fabrication_drawing"]
    if kind == "pcba":
        wanted += ["bom", "placement", "assembly_drawing", "test_record"]
        wanted += [r for r, flag in (("paste", "smd_parts"), ("firmware", "firmware"), ("stencil", "stencil"), ("panel", "panel")) if applic.get(flag)]
    for role in wanted:
        if role not in out_roles:
            ctx.add("pkg.artifact_missing", name, "/outputs", f"The output role {role} is absent.")
    for role in ("drill_plated", "drill_nonplated"):
        if role not in out_roles and role not in covered:
            ctx.add("pkg.applicability_missing", name, "/drill_applicability", f"The drill role {role} has no file and no applicability item.")


def _evidence_rules(ctx, project, package, manifest, records, outputs, roles, mname):
    """Examine the evidence of each check. Return the set of check IDs with a valid passed evidence."""
    valid_pass = set()
    inputs_by_path = {item["path"]: item for item in manifest["inputs"]}
    profile = records.get("supplier_profile")
    for ci, check in enumerate(manifest["checks"]):
        loc = f"/checks/{ci}"
        path, digest = check["evidence_path"], check["evidence_sha256"]
        if (path is None) != (digest is None):
            ctx.add("pkg.check_evidence_mismatch", mname, loc, "The manifest sets only one of evidence_path and evidence_sha256.")
            continue
        if path is None:
            if check["status"] == "pass":
                ctx.add("pkg.check_evidence_missing", mname, loc, "A passed check has no evidence.")
            continue
        item = outputs.get(path)
        if item is None or item["role"] != "evidence":
            ctx.add("pkg.evidence_unknown", mname, loc + "/evidence_path", "The path is not an output item with the role evidence.")
            continue
        state, raw = ctx.read(package, path)
        if state != "ok":
            continue  # The output rules report a missing file or an escape.
        ename = f"{package}/{path}"
        if sha256_hex(raw) != digest:
            ctx.add("pkg.check_evidence_mismatch", mname, loc + "/evidence_sha256", "The evidence file bytes differ from the hash.")
            continue
        before = len(ctx.findings)
        evidence = ctx.record(ename, raw, Path(path).suffix.lower())
        if evidence is None:
            continue
        if evidence.get("schema_id") != "cad-skills/evidence":
            ctx.add("pkg.evidence_unknown", ename, "/schema_id", "The file is not an evidence record.")
            continue
        if evidence["check_id"] != check["id"] or evidence["status"] != check["status"]:
            ctx.add("pkg.check_evidence_mismatch", ename, "", "The check ID or the status differs from the manifest.")
            continue
        listed = set()
        for k, entry in enumerate(evidence.get("inputs", [])):
            member = inputs_by_path.get(entry["path"])
            if member is None:
                ctx.add("pkg.check_input_role_missing", ename, f"/inputs/{k}", "The input is not a manifest input.")
                continue
            listed.add(entry["path"])
            if member["sha256"] != entry["sha256"]:
                ctx.add("pkg.check_evidence_mismatch", ename, f"/inputs/{k}/sha256", "The input hash differs from the manifest input.")
        artifact = evidence.get("artifact")
        if artifact:
            member = outputs.get(artifact["path"])
            if member is None or member["sha256"] != artifact["sha256"]:
                ctx.add("pkg.check_evidence_mismatch", ename, "/artifact", "The artifact is not a manifest output with the same path and hash.")
        if evidence["status"] != "pass":
            continue  # Only passed evidence needs the mandatory roles and the profile comparison.
        for role in CHECK_INPUT_ROLES.get(check["id"], ()):
            members = roles.get(role, [])
            if not members or any(m["path"] not in listed for m in members):
                ctx.add("pkg.check_input_role_missing", ename, "/inputs", f"The evidence does not list every manifest input with the role {role}.")
        if manifest["kind"] == "pcba":
            for role in OPTIONAL_CHECK_INPUT_ROLES.get(check["id"], ()):
                if any(member["path"] not in listed for member in roles.get(role, [])):
                    ctx.add("pkg.check_input_role_missing", ename, "/inputs",
                            f"The evidence does not bind the optional {role} input.")
        if check["id"] == "fab.profile_evidence" and profile and artifact and artifact["sha256"] != profile["evidence_sha256"]:
            ctx.add("cross.profile_evidence_mismatch", ename, "/artifact/sha256", "The artifact hash differs from the profile evidence_sha256.")
        if len(ctx.findings) == before:
            valid_pass.add(check["id"])
    return valid_pass


# --------------------------------------------------------------------------- command line


class _ArgError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgError(message)


def _versions():
    out = {"python": ".".join(map(str, sys.version_info[:3]))}
    for name in ("jsonschema", "PyYAML"):
        out[name.lower()] = importlib.metadata.version(name)
    return out


def _exit_code(findings):
    codes = [f["code"] for f in findings if f["severity"] == "error"]
    if any(c.startswith("tool.") for c in codes):
        return 3
    if any(c.startswith("cli.") for c in codes):
        return 2
    return 1 if codes else 0


def build_report(files, schemas_dir, project=None, package=None):
    findings, inputs, unprocessed = [], [], []
    registry = None
    if not schemas_dir.is_dir():
        findings.append(finding("cli.schemas_missing", str(schemas_dir), "", "The schema directory is not present."))
    else:
        try:
            registry = load_registry(schemas_dir)
        except ToolError as err:
            findings.extend(err.findings)
    for name in files:
        path = Path(name)
        if not path.exists():
            findings.append(finding("cli.input_missing", name, "", "The input file is not present."))
            continue
        if registry is None:
            unprocessed.append(name)
            continue
        try:
            try:
                raw = path.read_bytes()
            except OSError as err:
                raise RecordError([finding("file.unreadable", name, "", f"Cannot read the file: {err}")])
            inputs.append({"path": name, "sha256": sha256_hex(raw)})
            record = parse_record(raw, path.suffix.lower(), name)
            findings.extend(validate_record(record, registry, name))
        except RecordError as err:
            findings.extend(err.findings)
        except Exception as err:  # noqa: BLE001 - report each tool failure as exit 3
            findings.append(finding("tool.validator_failure", name, "", f"{type(err).__name__}: {err}"))
            unprocessed.append(name)
    if project is not None:
        pj = Path(project)
        if not pj.is_dir():
            findings.append(finding("cli.input_missing", str(project), "", "The project directory is not present."))
        elif registry is None:
            unprocessed.append(str(project))
        else:
            ctx = _Ctx(registry)
            try:
                records, shas = _load_project(ctx, pj)
                _project_rules(ctx, pj, records, shas)
                if package is not None:
                    pk = Path(package)
                    if not pk.is_dir():
                        ctx.add("cli.input_missing", str(package), "", "The package directory is not present.")
                    else:
                        _package_rules(ctx, pj, pk, records, shas)
            except Exception as err:  # noqa: BLE001 - report each tool failure as exit 3
                ctx.add("tool.validator_failure", str(project), "", f"{type(err).__name__}: {err}")
                unprocessed.append(str(project))
            findings.extend(ctx.findings)
            inputs.extend(ctx.inputs)
    findings.sort(key=lambda f: (f["file"], f["location"], f["code"]))
    code = _exit_code(findings)
    return code, {
        "report_schema_version": REPORT_VERSION,
        "status": "pass" if code == 0 else "fail" if code == 1 else "error",
        "exit_code": code,
        "tool_versions": _versions(),
        "inputs": inputs,
        "findings": findings,
        "unprocessed": unprocessed,
        "outputs": [],
    }


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _Parser(prog="validate.py", description="Validate cad-skills records.")
    parser.add_argument("files", nargs="*", metavar="FILE", help="a .json, .yaml or .yml record")
    parser.add_argument("--json", action="store_true", help="write one JSON report to standard output")
    parser.add_argument("--schemas", default=str(HERE / "schemas"), metavar="DIR",
                        help="the directory with registry.json and the schema files")
    parser.add_argument("--project", metavar="DIR", help="examine the records of a project directory and their relations")
    parser.add_argument("--package", metavar="DIR", help="examine a package directory (needs --project)")
    try:
        args = parser.parse_args(argv)
        if not args.files and args.project is None and args.package is None:
            raise _ArgError("give at least one FILE, --project or --package")
        if args.package is not None and args.project is None:
            raise _ArgError("--package needs --project")
    except _ArgError as err:
        if "--json" in argv:
            report = {"report_schema_version": REPORT_VERSION, "status": "error", "exit_code": 2,
                      "tool_versions": _versions(), "inputs": [],
                      "findings": [finding("cli.argument_error", "", "", str(err))],
                      "unprocessed": [], "outputs": []}
            print(json.dumps(report, indent=2))
        else:
            parser.print_usage(sys.stderr)
            print(f"validate.py: error: {err}", file=sys.stderr)
        return 2
    code, report = build_report(args.files, Path(args.schemas), args.project, args.package)
    if args.json:
        print(json.dumps(report, indent=2))
        print(f"validate.py: {report['status']} (exit {code})", file=sys.stderr)
    else:
        for f in report["findings"]:
            print(f"{f['file']}{f['location']}: {f['code']}: {f['message']}")
        for name in report["unprocessed"]:
            print(f"{name}: not processed")
        print(f"status: {report['status']} ({len(report['inputs'])} files read)")
    return code


if __name__ == "__main__":
    sys.exit(main())
