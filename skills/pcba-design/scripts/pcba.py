#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "openpyxl==3.1.5", "pyyaml==6.0.3"]
# ///
"""Build the supplier-neutral assembly data of a PCBA project.

  uv run skills/pcba-design/scripts/pcba.py neutral --project DIR --board FILE \\
      --variant ID --as-of YYYY-MM-DD [--out FILE]

The command takes the project lock before it reads any input. It reads each input file once,
through one snapshot per resolved file. It derives every value from those bytes.
It refuses on any join, path, token, stock or alias error, and it writes nothing on refusal.
Before the write it rehashes each input. It refuses when any input changed.

Exit status: 0 written, 1 failure, 2 incorrect arguments. A failure is either a refusal before the write
(status refused, nothing written) or a failure after the write (status failure, output_replaced true).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import project_io  # noqa: E402
import sexp  # noqa: E402

import jsonschema  # noqa: E402

# The copied validator is loaded from this skill only. It never imports another skill.
_spec = importlib.util.spec_from_file_location("pcba_contract_validate", SKILL / "contracts" / "validate.py")
validate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate)

MAP_SCHEMA = SKILL / "contracts" / "part-map.schema.json"
MAP_SCHEMA_11 = SKILL / "contracts" / "part-map-1.1.schema.json"
APPROVAL_SCHEMA = SKILL / "contracts" / "alternate-approval.schema.json"
APPROVAL_FILE = "components/alternate-approvals.yaml"
SIERRA_STAGING = "out/pcba/.sierra-staging"
DEFAULT_OUT = "out/pcba/assembly-neutral.json"
LOCK_TASK = "pcba-neutral"
LAYER_SIDE = {"F.Cu": "top", "B.Cu": "bottom"}
REF_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,31}$")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
NUMERIC = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


class Refused(Exception):
    """Stop with one finding before the write. Nothing is written."""

    def __init__(self, code, file, message):
        super().__init__(code)
        self.finding = {"code": code, "file": file, "message": message}


class ReplacedThenFailed(Exception):
    """The new output bytes are in place, but a later synchronization step failed."""

    def __init__(self, out_rel, cause):
        super().__init__("output.replaced_then_failed")
        self.finding = {"code": "output.replaced_then_failed", "file": out_rel,
                        "message": f"The new bytes of {out_rel} are in place, but synchronization failed: {cause}"}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def natural(ref: str):
    """Sort key that orders R2 before R10."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


class Snapshots:
    """One captured snapshot per resolved file. Recorded paths are project-relative."""

    def __init__(self, project: Path):
        self.project = project.resolve()
        self.by_real: dict = {}
        self.absent: set[str] = set()

    def capture(self, rel: str, role: str, under: Path | None = None) -> dict:
        try:
            real = project_io.confine(self.project, rel, must_exist=True)
        except project_io.PathEscape as err:
            raise Refused("path.escape", rel, f"The input path leaves the project: {err}")
        except OSError as err:
            raise Refused("path.missing", rel, f"The input cannot be read: {err}")
        if under is not None and not real.is_relative_to(under):
            raise Refused("map.path_escape", rel,
                          "The resolved part path leaves the components directory.")
        if real not in self.by_real:
            raw = real.read_bytes()
            self.by_real[real] = {"role": role, "path": real.relative_to(self.project).as_posix(),
                                  "real": real, "raw": raw, "sha256": sha256(raw)}
        return self.by_real[real]

    def inputs(self, roles=None) -> list:
        """Return the captured files as manifest inputs. A role filter keeps only the manifest roles."""
        items = [{"role": s["role"], "path": s["path"], "sha256": s["sha256"]} for s in self.by_real.values()
                 if roles is None or s["role"] in roles]
        return sorted(items, key=lambda i: (i["role"], i["path"]))

    def check_unchanged(self) -> None:
        for rel in sorted(self.absent):
            if os.path.lexists(self.project / rel):
                raise Refused("input.changed", rel, "An absent input appeared before publication.")
        for snap in self.by_real.values():
            try:
                raw = snap["real"].read_bytes()
            except OSError:
                raise Refused("input.changed", snap["path"], "An input disappeared before the write.")
            if sha256(raw) != snap["sha256"]:
                raise Refused("input.changed", snap["path"], "An input changed before the write.")


def parse_checked(raw: bytes, rel: str, registry: dict, suffix: str = ".yaml") -> dict:
    """Parse a captured record and run the copied validator on it."""
    try:
        data = validate.parse_record(raw, suffix, rel)
    except validate.RecordError as err:
        first = err.findings[0]
        raise Refused(first["code"], rel, first["message"])
    findings = validate.validate_record(data, registry, rel)
    if findings:
        raise Refused(findings[0]["code"], rel, findings[0]["message"])
    return data


def prop(node, name):
    for child in node:
        if isinstance(child, list) and child and child[0] == "property" and len(child) > 2 and child[1] == name:
            return str(child[2])
    return None


def parse_token(token: str, ref: str, field: str, rel: str) -> float:
    """Return the finite value of one board token. Refuse a malformed or non-finite token."""
    try:
        value = float(token)
    except ValueError:
        raise Refused("board.malformed_token", rel,
                      f"Footprint {ref} has a malformed {field} token.")
    if not math.isfinite(value):
        raise Refused("board.nonfinite_token", rel,
                      f"Footprint {ref} has a non-finite {field} token.")
    if not NUMERIC.match(token):
        raise Refused("board.malformed_token", rel,
                      f"Footprint {ref} has a malformed {field} token.")
    return value


def read_board(raw: bytes, rel: str) -> dict:
    """Return {reference: footprint data}. Keep the raw tokens next to the derived values."""
    try:
        tree = sexp.parse(raw.decode("utf-8"))
    except Exception as err:  # the parser raises several error types
        raise Refused("board.parse", rel, f"The KiCad board cannot be parsed: {err}")
    out: dict = {}

    def walk(node):
        if not isinstance(node, list) or not node:
            return
        if node[0] == "footprint":
            ref = prop(node, "Reference")
            if ref is None:
                raise Refused("board.reference_missing", rel, "A footprint has no Reference property.")
            if ref in out:
                raise Refused("board.duplicate_reference", rel, f"The board has two footprints named {ref}.")
            layer_node = next((c for c in node if isinstance(c, list) and c and c[0] == "layer"), None)
            at = next((c for c in node if isinstance(c, list) and c and c[0] == "at"), None)
            layer = str(layer_node[1]) if layer_node else ""
            if layer not in LAYER_SIDE:
                raise Refused("board.layer", rel, f"Footprint {ref} has no supported layer.")
            if at is None or len(at) < 3:
                raise Refused("board.position_missing", rel, f"Footprint {ref} has no position.")
            x_tok, y_tok = str(at[1]), str(at[2])
            angle_tok = str(at[3]) if len(at) > 3 else None
            out[ref] = {
                "footprint": str(node[1]),
                "side": LAYER_SIDE[layer],
                "source_tokens": {"x": x_tok, "y": y_tok, "angle": angle_tok},
                "angle_source": "token" if angle_tok is not None else "implicit_zero",
                "x_mm": parse_token(x_tok, ref, "x", rel),
                "y_mm": parse_token(y_tok, ref, "y", rel),
                "source_rotation_deg": parse_token(angle_tok, ref, "angle", rel) if angle_tok is not None else 0.0,
                "value": prop(node, "Value") or "",
            }
        for child in node:
            walk(child)

    walk(tree)
    return out


def load_map(raw: bytes, rel: str) -> dict:
    """Validate the skill-owned map against cad-skills/part-map 1.0. Return its references."""
    try:
        data = validate.parse_record(raw, ".yaml", rel)
    except validate.RecordError as err:
        first = err.findings[0]
        raise Refused(first["code"], rel, first["message"])
    version = data.get("schema_version")
    if version not in ("1.0", "1.1"):
        raise Refused("map.schema_version", rel, "The part map schema version must be 1.0 or 1.1.")
    for ref, entry in (data.get("references") or {}).items():
        if isinstance(entry, dict) and "mechanical" in entry and "alternates" in entry:
            raise Refused("map.alternate_on_mechanical", rel,
                          f"Reference {ref} is mechanical, so it cannot list alternates.")
    schema_file = MAP_SCHEMA if version == "1.0" else MAP_SCHEMA_11
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        raise Refused("map.schema", rel, f"The part map is invalid: {errors[0].message}")
    return data["references"]


def load_approvals(raw: bytes, rel: str) -> dict:
    """Validate the alternate approvals. Return {(reference, variant, alternate_name): entry}. Refuse duplicates."""
    try:
        data = validate.parse_record(raw, ".yaml", rel)
    except validate.RecordError as err:
        first = err.findings[0]
        raise Refused(first["code"], rel, first["message"])
    schema = json.loads(APPROVAL_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        raise Refused("approval.schema", rel, f"The alternate approvals are invalid: {errors[0].message}")
    out: dict = {}
    for item in data["approvals"]:
        key = (item["reference"], item["variant"], item["alternate_name"])
        if key in out:
            raise Refused("alternate.approval_conflict", rel,
                          f"Two approvals share the key {key[0]} {key[1]} {key[2]}.")
        out[key] = item
    return out


def check_part_path(rel: str):
    """Reject a map path with a parent step or a path outside components/ before any file is read."""
    parts = Path(rel).parts
    if rel.startswith("/") or ".." in parts or not rel.startswith("components/"):
        raise Refused("map.path_escape", rel, "A part path must be a relative path under components/.")


def normalize_rotation(value: float) -> float:
    """Return the rotation in [0, 360). A source value of 360 gives 0. A source value of -90 gives 270."""
    return ((value % 360) + 360) % 360


def stock_status(mpn_key, part: dict, demand: int, as_of: dt.date, max_age) -> dict:
    """Evaluate one populated part. Fail beats unconfirmed, and unconfirmed beats pass."""
    fails, unknowns = [], []
    lifecycle = part["lifecycle"]
    if lifecycle == "obsolete":
        fails.append("lifecycle_obsolete")
    elif lifecycle in ("unknown", "nrnd"):
        unknowns.append(f"lifecycle_{lifecycle}")
    stock = part["stock"]
    age = None
    if stock["status"] == "unknown":
        unknowns.append("stock_unknown")
    else:
        if stock["quantity"] < demand:
            fails.append("stock_below_demand")
        retrieved = dt.date.fromisoformat(stock["retrieved"])
        age = (as_of - retrieved).days
        if age < 0:
            raise Refused("stock.retrieved_after_as_of", part["mpn"],
                          "The stock retrieval date is after the --as-of date.")
        if max_age != "no_age_limit" and age > max_age:
            fails.append("stock_stale")
    status = "fail" if fails else ("unconfirmed" if unknowns else "pass")
    return {"manufacturer": mpn_key[0], "mpn": mpn_key[1], "lifecycle": lifecycle,
            "demand": demand, "stock_quantity": stock.get("quantity"), "stock_retrieved": stock.get("retrieved"),
            "age_days": age, "status": status, "reasons": fails + unknowns}


def output_target(project: Path, out_rel: str) -> Path:
    """Return the output path inside the project. Refuse an escaping path or a directory."""
    try:
        target = project_io.confine(project, out_rel)
    except (project_io.PathEscape, OSError):
        raise Refused("output.path_invalid", out_rel, f"The output path {out_rel} is not inside the project.")
    if target.is_dir():
        raise Refused("output.path_invalid", out_rel, f"The output path {out_rel} is a directory.")
    return target


def check_output_alias(target: Path, snapshots: Snapshots, out_rel: str) -> None:
    """Refuse an output that is the same file as any consumed input, by path or by file identity."""
    for snap in snapshots.by_real.values():
        if target == snap["real"]:
            raise Refused("output.aliases_input", out_rel,
                          f"The output path {out_rel} is an input file.")
        if target.exists() and os.path.samefile(target, snap["real"]):
            raise Refused("output.aliases_input", out_rel,
                          f"The output path {out_rel} is a hard link to an input file.")


def build(project: Path, board_rel: str, variant_id: str, as_of: dt.date, out_rel,
          snapshots: "Snapshots | None" = None) -> dict:
    snapshots = snapshots if snapshots is not None else Snapshots(project)
    proj = snapshots.project
    components_real = (proj / "components").resolve()
    registry = validate.load_registry(validate.HERE / "schemas")

    board_snap = snapshots.capture("board.yaml", "board_record")
    board = parse_checked(board_snap["raw"], "board.yaml", registry)
    pcba_ext = (board.get("extensions") or {}).get("pcba") or {}
    policy = pcba_ext.get("stock")
    if not isinstance(policy, dict) or "max_age_days" not in policy:
        raise Refused("stock.policy_missing", "board.yaml",
                      "Set extensions.pcba.stock.max_age_days to an integer or to no_age_limit.")
    max_age = policy["max_age_days"]
    if max_age != "no_age_limit" and not (isinstance(max_age, int) and not isinstance(max_age, bool) and max_age >= 1):
        raise Refused("stock.policy_invalid", "board.yaml", "max_age_days must be a positive integer or no_age_limit.")
    if board["variant"] != variant_id:
        raise Refused("variant.board_mismatch", "board.yaml", "The board record selects a different variant.")

    footprints = read_board(snapshots.capture(board_rel, "board")["raw"], board_rel)

    variants_snap = snapshots.capture("variants.yaml", "variants")
    variants = parse_checked(variants_snap["raw"], "variants.yaml", registry)["variants"]
    selected = next((v for v in variants if v["id"] == variant_id), None)
    if selected is None:
        raise Refused("variant.unknown", "variants.yaml", f"No variant is named {variant_id}.")

    map_snap = snapshots.capture("components/parts-map.yaml", "parts")
    entries = load_map(map_snap["raw"], "components/parts-map.yaml")

    # Every reference of every declared variant needs one map entry. Exclusions need one too.
    declared_states: dict = {}
    for v in variants:
        for ref, state in v["references"].items():
            declared_states.setdefault(ref, set()).add(state)
    for ref, states in sorted(declared_states.items(), key=lambda kv: natural(kv[0])):
        if ref not in entries:
            if states & {"populate", "dnp"}:
                raise Refused("map.missing_entry", "components/parts-map.yaml",
                              f"Reference {ref} is populated or DNP in a variant and has no map entry.")
            raise Refused("map.missing_exclusion_entry", "components/parts-map.yaml",
                          f"Reference {ref} is excluded and has no explicit map entry.")
    for ref, entry in entries.items():
        if ref not in declared_states:
            raise Refused("map.unused_entry", "components/parts-map.yaml", f"No declared variant uses {ref}.")
        if ref not in footprints:
            raise Refused("map.unknown_reference", "components/parts-map.yaml", f"{ref} is not on the board.")
        if "mechanical" in entry and declared_states[ref] & {"populate", "dnp"}:
            raise Refused("map.mechanical_used", "components/parts-map.yaml",
                          f"{ref} is marked mechanical but a variant populates or DNPs it.")

    # Load each part through one snapshot per resolved file. Confine it to components/.
    part_of: dict = {}
    for ref, entry in sorted(entries.items(), key=lambda kv: natural(kv[0])):
        if "part" not in entry:
            continue
        rel = entry["part"]
        check_part_path(rel)
        snap = snapshots.capture(rel, "parts", under=components_real)
        record = parse_checked(snap["raw"], rel, registry)
        if record["schema_id"] != "cad-skills/part":
            raise Refused("part.schema_id", rel, "The map entry does not name a part record.")
        part_of[ref] = {"path": snap["path"], "sha256": snap["sha256"], "record": record}

    # Population rules for the selected variant.
    states = dict(selected["references"])
    for ref in states:
        if ref not in footprints:
            raise Refused("board.missing_reference", "board", f"Variant {variant_id} names {ref}, not on the board.")
    for ref in footprints:
        if ref not in states:
            raise Refused("variant.unlisted_reference", "variants.yaml",
                          f"Board reference {ref} is not listed in variant {variant_id}.")
    hand: dict = {}
    for item in selected.get("hand_installed", []):
        ref = item["reference"]
        if ref in hand:
            raise Refused("variant.hand_installed_duplicate", "variants.yaml", f"{ref} is listed twice.")
        if states.get(ref) != "populate":
            raise Refused("variant.hand_installed_state", "variants.yaml",
                          f"{ref} is hand installed but its state is not populate.")
        hand[ref] = item["reason"]

    # Alternates: load each listed alternate, select the named ones, and check each selection.
    alt_of: dict = {}
    for ref, entry in sorted(entries.items(), key=lambda kv: natural(kv[0])):
        names = set()
        for alt in entry.get("alternates", []):
            if alt["name"] in names:
                raise Refused("map.alternate_duplicate", "components/parts-map.yaml",
                              f"Reference {ref} lists the alternate {alt['name']} twice.")
            names.add(alt["name"])
            check_part_path(alt["part"])
            snap = snapshots.capture(alt["part"], "parts", under=components_real)
            record = parse_checked(snap["raw"], alt["part"], registry)
            alt_of[(ref, alt["name"])] = {"path": snap["path"], "sha256": snap["sha256"], "record": record}

    selections = pcba_ext.get("selected_alternates") or {}
    if not isinstance(selections, dict):
        raise Refused("alternate.selection_invalid", "board.yaml", "selected_alternates must map a reference to a name.")
    for sel_ref, sel_name in selections.items():
        if not (isinstance(sel_ref, str) and isinstance(sel_name, str)
                and REF_PATTERN.match(sel_ref) and NAME_PATTERN.match(sel_name)):
            raise Refused("alternate.selection_invalid", "board.yaml",
                          "Each selected alternate needs a reference and a name, both plain text.")
    approvals: dict = {}
    if (proj / APPROVAL_FILE).is_file():
        approvals = load_approvals(snapshots.capture(APPROVAL_FILE, "parts", under=components_real)["raw"], APPROVAL_FILE)
    for key in approvals:
        if key[0] not in declared_states or key[1] not in [v["id"] for v in variants]:
            raise Refused("alternate.approval_unused", APPROVAL_FILE,
                          f"The approval {key[0]} {key[1]} {key[2]} names no declared reference or variant.")
    chosen: dict = {}
    for ref, name in sorted(selections.items(), key=lambda kv: natural(kv[0])):
        if ref not in entries or "mechanical" in entries[ref] or (ref, name) not in alt_of:
            raise Refused("alternate.unknown", "board.yaml", f"No alternate {name} is listed for {ref}.")
        if states.get(ref) not in ("populate", "dnp"):
            raise Refused("alternate.reference_excluded", "board.yaml",
                          f"{ref} is excluded in variant {variant_id}, so it cannot take an alternate.")
        primary, alt = part_of[ref], alt_of[(ref, name)]
        approval = approvals.get((ref, variant_id, name))
        if approval is None:
            raise Refused("alternate.unapproved", APPROVAL_FILE,
                          f"No approval for {ref} in variant {variant_id} with alternate {name}.")
        if (approval["primary_part_path"], approval["primary_sha256"]) != (primary["path"], primary["sha256"]) or \
                (approval["alternate_part_path"], approval["alternate_sha256"]) != (alt["path"], alt["sha256"]):
            raise Refused("alternate.approval_stale", APPROVAL_FILE,
                          f"The approval for {ref} with alternate {name} does not match the current part bytes.")
        pr, ar = primary["record"], alt["record"]
        for field, code in (("footprint", "alternate.footprint_mismatch"), ("polarity", "alternate.polarity_mismatch"),
                            ("pin_map", "alternate.pin_map_mismatch"), ("package", "alternate.package_mismatch"),
                            ("ratings", "alternate.electrical_mismatch"),
                            ("temperature_range_c", "alternate.electrical_mismatch")):
            if pr[field] != ar[field]:
                raise Refused(code, alt["path"], f"The alternate {name} differs from {ref} in {field}.")
        if ar["footprint"] != footprints[ref]["footprint"]:
            raise Refused("alternate.footprint_mismatch", alt["path"], f"The alternate {name} does not fit {ref}.")
        chosen[ref] = {"name": name, "info": alt}

    # Conflicting stock or lifecycle records for one manufacturer and MPN stop the run.
    by_key: dict = {}
    for info in list(part_of.values()) + list(alt_of.values()):
        rec = info["record"]
        key = (rec["manufacturer"], rec["mpn"])
        signature = json.dumps({"lifecycle": rec["lifecycle"], "stock": rec["stock"]}, sort_keys=True)
        if key in by_key and by_key[key][0] != signature:
            raise Refused("stock.conflicting_records", info["path"],
                          f"Two part records for {key[0]} {key[1]} disagree on stock or lifecycle.")
        by_key.setdefault(key, (signature, rec))

    rows = []
    for ref in sorted(states, key=natural):
        state = states[ref]
        board_fp = footprints[ref]
        entry = entries[ref]
        method = "hand_installed" if ref in hand else "automatic"
        row = {
            "reference": ref,
            "variant_state": state,
            "installation_method": method,
            "assembly_instruction": hand.get(ref, ""),
            "side": board_fp["side"],
            "x_mm": board_fp["x_mm"],
            "y_mm": board_fp["y_mm"],
            "source_tokens": board_fp["source_tokens"],
            "angle_source": board_fp["angle_source"],
            "source_rotation_deg": board_fp["source_rotation_deg"],
            "rotation_deg": normalize_rotation(board_fp["source_rotation_deg"]),
            "footprint": board_fp["footprint"],
            "value": board_fp["value"],
            "datum": "kicad_footprint_origin",
            "midpoint_mapping": "unconfirmed",
            "board_quantity": board["quantity"],
            "per_board_quantity": 1 if state in ("populate", "dnp") else 0,
            "selected_alternate": chosen[ref]["name"] if ref in chosen else "",
        }
        if "mechanical" in entry:
            row.update({"part_path": None, "part_sha256": None, "manufacturer": None, "mpn": None,
                        "reason": "mechanical"})
        else:
            part = chosen[ref]["info"] if ref in chosen else part_of[ref]
            if part["record"]["footprint"] != board_fp["footprint"]:
                raise Refused("part.footprint_mismatch", part["path"],
                              f"{ref} uses {board_fp['footprint']}, but the part record names "
                              f"{part['record']['footprint']}.")
            row.update({"part_path": part["path"], "part_sha256": part["sha256"],
                        "manufacturer": part["record"]["manufacturer"], "mpn": part["record"]["mpn"]})
        rows.append(row)

    # BOM groups: populated and DNP rows only. The key includes the installation method and instruction.
    groups: dict = {}
    for row in rows:
        if row["variant_state"] not in ("populate", "dnp"):
            continue
        key = (row["manufacturer"], row["mpn"], row["variant_state"], row["installation_method"],
               row["assembly_instruction"])
        groups.setdefault(key, []).append(row["reference"])
    quantity = board["quantity"]
    bom = []
    for (manufacturer, mpn, state, method, instruction), refs in sorted(groups.items(), key=lambda kv: str(kv[0])):
        per_board = len(refs)
        bom.append({"manufacturer": manufacturer, "mpn": mpn, "variant_state": state,
                    "installation_method": method, "assembly_instruction": instruction,
                    "references": sorted(refs, key=natural),
                    "quantity_per_board": per_board, "board_quantity": quantity,
                    "order_quantity": per_board * quantity if state == "populate" else 0})

    # Stock demand counts each populated reference once. Identical records share one stock result.
    demand: dict = {}
    for group in bom:
        if group["variant_state"] == "populate":
            key = (group["manufacturer"], group["mpn"])
            demand[key] = demand.get(key, 0) + group["order_quantity"]
    stock = [stock_status(key, by_key[key][1], demand[key], as_of, max_age) for key in sorted(demand)]

    result = {
        "schema": "pcba-design/neutral",
        "schema_version": "1.0",
        "variant": variant_id,
        "board_quantity": quantity,
        "as_of": as_of.isoformat(),
        "stock_policy": {"max_age_days": max_age},
        "inputs": snapshots.inputs(),
        "rows": rows,
        "bom_groups": bom,
        "stock": stock,
    }
    data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if out_rel is None:
        return result
    target = output_target(proj, out_rel)
    check_output_alias(target, snapshots, out_rel)
    snapshots.check_unchanged()
    try:
        project_io.atomic_write(proj, target, data)
    except project_io.PostReplaceError as err:
        raise ReplacedThenFailed(out_rel, err.__cause__ or err) from err
    except OSError as err:
        raise Refused("output.write_failed", out_rel, f"The output path {out_rel} cannot be written: {err.strerror}.")
    return result


def load_sierra_module():
    spec = importlib.util.spec_from_file_location("pcba_sierra", SKILL / "scripts" / "sierra.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_sierra(project: Path, board_rel: str, variant_id: str, as_of: dt.date, out_dir: str) -> dict:
    """Write the complete Sierra draft set, or nothing. The caller holds the project lock.

    Order: output validity, then profile presence and hash, then restriction review, then policy.
    All inputs are captured once through one Snapshots object. The set is staged, the inputs are
    checked for freshness, and the staged directory is published once. An existing destination is refused.
    """
    sierra = load_sierra_module()
    proj = project.resolve()
    registry = validate.load_registry(validate.HERE / "schemas")

    # 1. Output validity first.
    try:
        dest = project_io.confine(proj, out_dir)
    except (project_io.PathEscape, OSError):
        raise Refused("output.path_invalid", out_dir, f"The output path {out_dir} is not inside the project.")
    if dest.exists() and not dest.is_dir():
        raise Refused("output.path_invalid", out_dir, f"The output path {out_dir} is a file.")
    # The destination must not overlap the fixed staging directory: no equality, ancestor or descendant.
    staging = proj / SIERRA_STAGING
    dest_real, staging_real = dest.resolve(), staging.resolve()
    if dest_real == staging_real or dest_real.is_relative_to(staging_real) or staging_real.is_relative_to(dest_real):
        raise Refused("output.path_invalid", out_dir,
                      f"The output path {out_dir} overlaps the staging directory {SIERRA_STAGING}.")
    # A pre-existing staging entry, including a dangling symbolic link, is refused before any mutation.
    if os.path.lexists(staging) and staging.is_symlink():
        raise Refused("output.staging_link", SIERRA_STAGING,
                      "The staging path is a symbolic link. Remove it, then run again.")
    if staging.exists():
        raise Refused("output.staging_exists", SIERRA_STAGING,
                      "A staging directory from an earlier run is present. Remove it, then run again.")
    if dest.exists():
        raise Refused("output.exists", out_dir,
                      f"The output directory {out_dir} exists. Choose a new directory.")

    # Neutral capture through the shared snapshot object.
    snap = Snapshots(proj)
    result = build(project, board_rel, variant_id, as_of, None, snapshots=snap)
    board = parse_checked(snap.capture("board.yaml", "board_record")["raw"], "board.yaml", registry)

    # 2. Profile presence and hash, captured through the same snapshot object.
    try:
        profile_snap = snap.capture("manufacturing/supplier.yaml", "supplier_profile")
    except Refused as err:
        if err.finding["code"] == "path.missing":
            raise Refused("supplier.profile_missing", "manufacturing/supplier.yaml", "The supplier profile is missing.")
        raise
    profile = parse_checked(profile_snap["raw"], "manufacturing/supplier.yaml", registry)
    if profile["content_sha256"] != board["supplier"]["profile_sha256"]:
        raise Refused("supplier.profile_mismatch", "manufacturing/supplier.yaml",
                      "The supplier profile content hash does not match the board record.")

    # 3. Restriction review. Nonempty restrictions stop the Sierra export. The text is kept.
    restrictions = board.get("restrictions") or []
    if restrictions:
        texts = " | ".join(item["text"] for item in restrictions)
        raise Refused("supplier.restriction_review", "board.yaml",
                      f"The board has restrictions that need supplier review before a Sierra export: {texts}")

    # 4. Hand-installed BOM policy.
    declared = ((profile.get("extensions") or {}).get("pcba") or {}).get("hand_installed_bom")
    policy = declared if declared in ("include_in_bom", "exclude_from_bom") else (
        "missing" if declared is None else "unknown")
    bom_produced = policy in ("include_in_bom", "exclude_from_bom")
    status = json.loads(sierra.status_bytes(board["supplier"]["profile_sha256"], policy,
                                           bom_produced, board["supplier"]["id"]))
    status["inputs"] = snap.inputs()

    files = {
        "placement/sierra-xy-draft.csv": sierra.xy_csv_bytes(result),
        "test/test-record.json": sierra.test_record_bytes(result, board["electrical_limits"]),
        "reports/sierra-status.json": (json.dumps(status, indent=2, sort_keys=True) + "\n").encode(),
    }
    if bom_produced:
        table = sierra.bom_table(result, board["name"], board["release_revision"], policy)
        files["bom/sierra-bom.xlsx"] = sierra.xlsx_bytes(table)

    # Stage the complete set. Publish only after every write and the final freshness check succeed.
    written = []
    try:
        for rel, data in sorted(files.items()):
            try:
                project_io.atomic_write(proj, staging / rel, data)
            except OSError as err:
                raise Refused("output.write_failed", f"{out_dir}/{rel}",
                              f"The staged output {out_dir}/{rel} cannot be written: {err.strerror}.")
            written.append(f"{out_dir}/{rel}")
        snap.check_unchanged()
        dest.parent.mkdir(parents=True, exist_ok=True)
        project_io.publish_dir(proj, staging, dest)
    except project_io.PostRenameError as err:
        raise ReplacedThenFailed(out_dir, err.__cause__ or err) from err
    except Refused:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    except OSError as err:
        shutil.rmtree(staging, ignore_errors=True)
        raise Refused("output.write_failed", out_dir, f"The output {out_dir} cannot be published: {err.strerror}.")
    return {"status": "written", "bom": "produced" if bom_produced else "not_produced",
            "hand_installed_bom": policy, "files": sorted(written)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="pcba.py")
    sub = parser.add_subparsers(dest="command", required=True)
    neutral = sub.add_parser("neutral", help="Write the supplier-neutral assembly data.")
    neutral.add_argument("--project", required=True, type=Path)
    neutral.add_argument("--board", required=True, help="KiCad board file, relative to the project.")
    neutral.add_argument("--variant", required=True)
    neutral.add_argument("--as-of", required=True, help="Comparison date, YYYY-MM-DD. The tool never reads the clock.")
    neutral.add_argument("--out", default=DEFAULT_OUT)
    package_cmd = sub.add_parser("package", help="Write one complete PCBA package.")
    package_cmd.add_argument("--project", required=True, type=Path)
    package_cmd.add_argument("--board", required=True)
    package_cmd.add_argument("--variant", required=True)
    package_cmd.add_argument("--as-of", required=True)
    package_cmd.add_argument("--package-id", required=True)
    check_cmd = sub.add_parser("check", help="Run the copied validator on a project and one package.")
    check_cmd.add_argument("--project", required=True, type=Path)
    check_cmd.add_argument("--package", required=True, type=Path)
    sierra_cmd = sub.add_parser("sierra", help="Write the Sierra draft outputs for a variant.")
    sierra_cmd.add_argument("--project", required=True, type=Path)
    sierra_cmd.add_argument("--board", required=True)
    sierra_cmd.add_argument("--variant", required=True)
    sierra_cmd.add_argument("--as-of", required=True)
    sierra_cmd.add_argument("--out-dir", default="out/pcba/sierra")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    if args.command == "check":
        code, payload = validate.build_report([], validate.HERE / "schemas", args.project, args.package)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return code
    try:
        as_of = dt.date.fromisoformat(args.as_of)
    except ValueError:
        print(json.dumps({"status": "error", "message": "--as-of must be YYYY-MM-DD."}))
        return 2
    try:
        with project_io.project_lock(args.project, LOCK_TASK):
            if args.command == "package":
                import package as package_mod
                payload = package_mod.build_package(sys.modules[__name__], args.project, args.board,
                                                    args.variant, as_of, args.package_id)
                print(json.dumps(payload, indent=2, sort_keys=True))
                return 0
            if args.command == "sierra":
                payload = build_sierra(args.project, args.board, args.variant, as_of, args.out_dir)
                print(json.dumps(payload, indent=2, sort_keys=True))
                return 0
            result = build(args.project, args.board, args.variant, as_of, args.out)
    except Refused as refusal:
        print(json.dumps({"status": "refused", "findings": [refusal.finding]}, indent=2, sort_keys=True))
        return 1
    except ReplacedThenFailed as failure:
        print(json.dumps({"status": "failure", "output_replaced": True, "findings": [failure.finding]},
                         indent=2, sort_keys=True))
        return 1
    except project_io.LockHeld as err:
        print(json.dumps({"status": "refused", "findings": [{"code": "project.locked", "file": "",
                                                              "message": str(err)}]}))
        return 1
    print(json.dumps({"status": "written", "rows": len(result["rows"]),
                      "bom_groups": len(result["bom_groups"]), "stock": result["stock"]},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
