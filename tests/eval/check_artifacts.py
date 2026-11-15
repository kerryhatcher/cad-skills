# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Independent artifact checker. It reads produced files and their records. It never reads a model statement.

Each expectation has an `id`, a `kind` and the fields that the kind needs. The field `base` names the
root that holds `path`. The value `fixture` names the fixture root. The value `run` names the run output
root. The default is `fixture`. Both roots are passed to `run_checks`.

Kinds:

- exists: pass when the file exists.
- absent: pass when no file or link exists at the path. A dangling link fails.
- sha256: `value`. Pass when the file hash equals `value`.
- json_equals: `key`, `value`. Pass when the top-level key is present and equals `value`.
- json_path_equals: `json_path`, `value`. The path is a list of object keys (strings) and array indices
  (integers). Pass when every component is present and the value equals `value`.
- row_equals: `json_path` names an array. `match_key` and `match_value` select exactly one row. `field`
  of that row equals `value`. A missing array, a non-list array, a non-object row, no match, a duplicate
  match and a missing field fail.
- row_set_equals: `json_path` names an array. `where` (a mapping of keys to values) selects rows. The
  values of `field` in the selected rows form the exact multiset `value`. A missing array, a non-object
  row and a missing field in a selected row fail.
- length_equals: the array at `json_path` has the integer length `value`.
- row_binding: each array row names a unique file through `path_key` and its hash through `hash_key`.
  An optional `size_key` names the byte count. Missing, linked, escaping or mismatched files fail.
- sha256_binding: `key`, `reference`, and an optional `reference_base`. Pass when the recorded hash in the
  manifest equals the current hash of the reference file. The reference base defaults to `base`.
- record_binding: the record at `path` names `raw_file` and `raw_sha256`. Pass when the raw file has the
  recorded hash. The expectation holds no fixed hash, so it fits outputs that a model produces.

Values compare with their JSON types. A boolean never equals a number or a string. A missing key fails
even when the expected value is null. A path with an absolute start or a `..` part is refused. A path with
a link component is refused. A path that escapes its root is refused. A refused path fails every kind,
including `absent`. The checker never passes a missing or refused file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from common import sha256_file

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _has_link(path: Path) -> bool:
    """Return True when a prefix of the absolute path is a symbolic link."""
    parts = path.absolute().parts
    return any(Path(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1))


def resolve_under(base: Path, rel: str) -> Path | None:
    """Return base/rel. Return None when rel refuses the root, a link or an escape."""
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts or not rel_path.parts:
        return None
    root = Path(base).absolute()
    if _has_link(root):
        return None
    current = root
    for part in rel_path.parts:
        current = current / part
        if current.is_symlink():
            return None
    if not current.resolve().is_relative_to(root.resolve()):
        return None
    return current


def same_json(a, b) -> bool:
    """Compare two JSON values with their types. A boolean never equals a number or a string."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_json(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same_json(a[k], b[k]) for k in a)
    return False


def _lookup(data, components: list) -> tuple[bool, object]:
    """Walk a list of keys and indices. Return (found, value). A missing component is not found."""
    node = data
    for part in components:
        if isinstance(node, dict):
            if not isinstance(part, str) or part not in node:
                return False, None
            node = node[part]
        elif isinstance(node, list):
            if isinstance(part, bool) or not isinstance(part, int) or not 0 <= part < len(node):
                return False, None
            node = node[part]
        else:
            return False, None
    return True, node


def _array_at(data, components) -> tuple[bool, object]:
    """Return (True, list) for an array at the path. Return (False, reason) otherwise."""
    if not isinstance(components, list) or not components:
        raise ValueError("json_path must be a non-empty list")
    found, value = _lookup(data, components)
    if not found:
        return False, "the array path is absent"
    if not isinstance(value, list):
        return False, "the array path does not name a list"
    return True, value


def _result(item: dict, passed: bool, evidence: str) -> dict:
    return {"id": item["id"], "pass": bool(passed), "evidence": evidence,
            "reason": "" if passed else item.get("reason", "expectation not met")}


def _refused(item: dict, rel: str) -> dict:
    return _result(item, False, f"{rel} is refused: an absolute, escaping or linked path")


def _load_json(path: Path) -> tuple[bool, object]:
    try:
        return True, json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return False, error.__class__.__name__


def _row_equals(item: dict, data) -> dict:
    ok, rows = _array_at(data, item["json_path"])
    if not ok:
        return _result(item, False, rows)
    matches = []
    for row in rows:
        if not isinstance(row, dict):
            return _result(item, False, "a row is not an object")
        if item["match_key"] in row and same_json(row[item["match_key"]], item["match_value"]):
            matches.append(row)
    if not matches:
        return _result(item, False, "no row matches")
    if len(matches) > 1:
        return _result(item, False, f"{len(matches)} rows match: a duplicate match is refused")
    row = matches[0]
    if item["field"] not in row:
        return _result(item, False, f"the matching row lacks field {item['field']}")
    actual = row[item["field"]]
    return _result(item, same_json(actual, item["value"]), f"{item['field']}={actual!r}")


def _row_set_equals(item: dict, data) -> dict:
    ok, rows = _array_at(data, item["json_path"])
    if not ok:
        return _result(item, False, rows)
    where = item["where"]
    if not isinstance(where, dict) or not where:
        raise ValueError(f"where must be a non-empty mapping in expectation {item['id']}")
    if not isinstance(item["value"], list):
        raise ValueError(f"value must be a list in expectation {item['id']}")
    selected = []
    for row in rows:
        if not isinstance(row, dict):
            return _result(item, False, "a row is not an object")
        if all(key in row and same_json(row[key], want) for key, want in where.items()):
            if item["field"] not in row:
                return _result(item, False, f"a selected row lacks field {item['field']}")
            selected.append(row[item["field"]])
    actual = sorted(selected, key=repr)
    expected = sorted(item["value"], key=repr)
    return _result(item, same_json(actual, expected), f"selected={actual!r}")


def _row_binding(item: dict, data, base: Path) -> dict:
    """Compare each named output with its recorded hash and optional byte count."""
    ok, rows = _array_at(data, item["json_path"])
    if not ok or not rows:
        return _result(item, False, "the output array is absent, invalid or empty")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return _result(item, False, "an output row is not an object")
        rel, recorded = row.get(item["path_key"]), row.get(item["hash_key"])
        if not isinstance(rel, str) or not isinstance(recorded, str) or not HEX64.fullmatch(recorded):
            return _result(item, False, "an output row has no valid path and hash")
        target = resolve_under(base, rel)
        if target is None:
            return _refused(item, rel)
        resolved = target.resolve()
        if resolved in seen:
            return _result(item, False, f"the output path {rel} repeats")
        seen.add(resolved)
        if not target.is_file():
            return _result(item, False, f"the output {rel} is absent")
        if sha256_file(target) != recorded:
            return _result(item, False, f"the output hash differs for {rel}")
        if "size_key" in item:
            count = row.get(item["size_key"])
            if type(count) is not int or target.stat().st_size != count:
                return _result(item, False, f"the output byte count differs for {rel}")
    return _result(item, True, f"{len(rows)} output bindings match")


def check_one(item: dict, roots: dict) -> dict:
    kind = item["kind"]
    base_name = item.get("base", "fixture")
    if base_name not in roots:
        raise ValueError(f"unknown base '{base_name}' in expectation {item['id']}")
    base = roots[base_name]
    if "path" not in item:
        return _result(item, False, "the expectation names no path")
    path = resolve_under(base, item["path"])
    if path is None:
        return _refused(item, item["path"])
    if kind == "absent":
        return _result(item, not path.exists() and not path.is_symlink(), f"{item['path']} exists=False")
    if kind == "exists":
        return _result(item, path.is_file(), f"{item['path']} exists={path.is_file()}")
    if not path.is_file():
        return _result(item, False, f"{item['path']} is missing")
    if kind == "sha256":
        actual = sha256_file(path)
        return _result(item, actual == item["value"], f"sha256={actual}")
    if kind in ("json_equals", "json_path_equals", "row_equals", "row_set_equals",
                "sha256_binding", "record_binding", "length_equals", "row_binding"):
        ok, data = _load_json(path)
        if not ok:
            return _result(item, False, f"unreadable JSON: {data}")
    if kind == "json_equals":
        found, actual = _lookup(data, [item["key"]])
        if not found:
            return _result(item, False, f"{item['key']} is absent")
        return _result(item, same_json(actual, item["value"]), f"{item['key']}={actual!r}")
    if kind == "json_path_equals":
        components = item.get("json_path")
        if not isinstance(components, list) or not components:
            raise ValueError(f"json_path must be a non-empty list in expectation {item['id']}")
        found, actual = _lookup(data, components)
        if not found:
            return _result(item, False, f"json_path {components!r} is absent")
        return _result(item, same_json(actual, item["value"]), f"json_path {components!r}={actual!r}")
    if kind == "row_equals":
        return _row_equals(item, data)
    if kind == "row_set_equals":
        return _row_set_equals(item, data)
    if kind == "length_equals":
        if type(item["value"]) is not int or item["value"] < 0:
            raise ValueError("The expected length must be a nonnegative integer.")
        ok, rows = _array_at(data, item["json_path"])
        return _result(item, ok and len(rows) == item["value"], f"array length={len(rows) if ok else 'unavailable'}")
    if kind == "row_binding":
        return _row_binding(item, data, base)
    if kind == "sha256_binding":
        ref_base_name = item.get("reference_base", base_name)
        if ref_base_name not in roots:
            raise ValueError(f"unknown reference base '{ref_base_name}' in expectation {item['id']}")
        reference = resolve_under(roots[ref_base_name], item["reference"])
        if reference is None:
            return _refused(item, item["reference"])
        if not reference.is_file():
            return _result(item, False, f"reference {item['reference']} is missing")
        found, recorded = _lookup(data, [item["key"]])
        if not found:
            return _result(item, False, f"manifest key {item['key']} is absent")
        current = sha256_file(reference)
        return _result(item, recorded == current, f"recorded={recorded} current={current}")
    if kind == "record_binding":
        found_raw, raw_rel = _lookup(data, ["raw_file"])
        found_hash, recorded = _lookup(data, ["raw_sha256"])
        if not (found_raw and found_hash and isinstance(raw_rel, str)
                and isinstance(recorded, str) and HEX64.match(recorded)):
            return _result(item, False, "the binding record is incomplete")
        raw = resolve_under(base, raw_rel)
        if raw is None:
            return _refused(item, raw_rel)
        if not raw.is_file():
            return _result(item, False, f"raw file {raw_rel} is missing")
        current = sha256_file(raw)
        return _result(item, current == recorded, f"recorded={recorded} current={current}")
    return _result(item, False, f"unknown kind '{kind}'")


def run_checks(expectations: list[dict], root: Path, run_root: Path | None = None) -> dict:
    """Run every expectation. `root` is the fixture root. `run_root` is the run output root.

    When `run_root` is None, the run output root is the fixture root.
    """
    roots = {"fixture": Path(root), "run": Path(run_root) if run_root is not None else Path(root)}
    seen: set[str] = set()
    results = []
    for item in expectations:
        if item["id"] in seen:
            raise ValueError(f"duplicate expectation id {item['id']}")
        seen.add(item["id"])
        results.append(check_one(item, roots))
    return {"results": results, "all_pass": bool(results) and all(r["pass"] for r in results)}
