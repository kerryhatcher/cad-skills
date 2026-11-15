# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Run the matrix expectations of A1 and A2 against the frozen fixture roots and their copies.

  uv run tests/test_artifact_expectations.py            # all tests
  uv run tests/test_artifact_expectations.py a2         # only tests with 'a2' in their name

The tests read frozen bytes and copies of them. They start no container, no KiCad process and no
simulator. They call no provider and make no network call.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "eval"))

import check_artifacts as CA  # noqa: E402

MATRIX = yaml.safe_load((ROOT / "tests" / "eval" / "matrix.yaml").read_text(encoding="utf-8"))
A1_CHECK = MATRIX["artifact_checks"]["A1"]
A2_CHECK = MATRIX["artifact_checks"]["A2"]
SUPPLIER = Path("out") / "fab" / "supplier" / "supplier-result.json"


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def failing_ids(result: dict) -> set[str]:
    return {r["id"] for r in result["results"] if not r["pass"]}


def copy_fixture(name: str, tmp: Path) -> Path:
    """Copy a frozen fixture into a temporary directory. Links are copied as links."""
    target = tmp / name
    shutil.copytree(ROOT / MATRIX["artifact_checks"][name]["fixture_root"], target, symlinks=True)
    return target


def roots_of(name: str, fixture: Path) -> tuple[Path, Path]:
    check = MATRIX["artifact_checks"][name]
    run_suffix = Path(check["run_root"]).relative_to(check["fixture_root"])
    return fixture, fixture / run_suffix


def run_a1(fixture: Path) -> dict:
    f, r = roots_of("A1", fixture)
    return CA.run_checks(A1_CHECK["expectations"], f, r)


def run_a2_group(fixture: Path, run_root: Path, group: str) -> dict:
    spec = A2_CHECK[group]
    return CA.run_checks(spec, fixture, run_root)


def frozen_a2() -> tuple[Path, Path]:
    return ROOT / A2_CHECK["fixture_root"], ROOT / A2_CHECK["run_root"]


def produced_supplier(tmp: Path, data) -> Path:
    """Write a produced supplier result into a temporary run root and return that root."""
    run_root = tmp / "run"
    target = run_root / SUPPLIER
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data), encoding="utf-8")
    return run_root


def frozen_supplier() -> dict:
    return json.loads((ROOT / A2_CHECK["run_root"] / SUPPLIER).read_text(encoding="utf-8"))


def a2_run_for(tmp: Path, data) -> dict:
    """Run the A2 run expectations against a temporary run root holding the given supplier result."""
    fixture, _ = frozen_a2()
    run_root = produced_supplier(tmp, data)
    return run_a2_group(fixture, run_root, "expectations")


# ---------------------------------------------------------------- positive: frozen roots


def test_a1_expectations_pass_on_the_frozen_root():
    """Every A1 expectation passes against the frozen A1 fixture."""
    result = run_a1(ROOT / A1_CHECK["fixture_root"])
    expect(result["all_pass"], f"A1 expectations failed: {[r for r in result['results'] if not r['pass']]}")
    expect(len(result["results"]) == len(A1_CHECK["expectations"]), "an A1 expectation was not run")


def test_a2_run_expectations_pass_on_the_frozen_run():
    """Every A2 run expectation passes against the produced supplier result of the frozen run."""
    fixture, run_root = frozen_a2()
    result = run_a2_group(fixture, run_root, "expectations")
    expect(result["all_pass"], f"A2 run expectations failed: {[r for r in result['results'] if not r['pass']]}")


def test_a2_fixture_expectations_pass_on_the_frozen_fixture():
    """The fixture description holds the incomplete state and the counts of the frozen status."""
    fixture, run_root = frozen_a2()
    result = run_a2_group(fixture, run_root, "fixture_expectations")
    expect(result["all_pass"], f"A2 fixture expectations failed: {[r for r in result['results'] if not r['pass']]}")


def test_fixture_description_does_not_enter_the_run_outcome():
    """No fixture expectation appears in the run outcome, and no run expectation reads the fixture status."""
    run_ids = {e["id"] for e in A2_CHECK["expectations"]}
    fixture_ids = {e["id"] for e in A2_CHECK["fixture_expectations"]}
    expect(not (run_ids & fixture_ids), "a fixture expectation is also a run expectation")
    expect(all(e.get("base") == "run" for e in A2_CHECK["expectations"]), "a run expectation does not read the run root")


# ---------------------------------------------------------------- negative: A1 bytes and claims


def test_changed_interface_byte_fails_the_bound_hash(tmp: Path):
    """A synthetic changed byte in the interface fails the expectation that binds its hash."""
    fixture = copy_fixture("A1", tmp)
    interface = fixture / "after" / "mechanical" / "board-interface.json"
    interface.write_bytes(interface.read_bytes() + b"\n")
    result = run_a1(fixture)
    expect("A1-interface-binding" in failing_ids(result), "the changed interface did not fail its binding")
    expect(not result["all_pass"], "the changed fixture passed")


def test_complete_a2_claim_fails(tmp: Path):
    """A synthetic complete claim fails in both groups. The status says complete, and a package is present."""
    fixture = copy_fixture("A2", tmp)
    status_path = fixture / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["overall"] = "complete"
    status_path.write_text(json.dumps(status), encoding="utf-8")
    (fixture / "project" / "out" / "fab" / "package").mkdir(parents=True)
    (fixture / "project" / "out" / "fab" / "package" / "manifest.json").write_text("{}", encoding="utf-8")
    _, run_root = roots_of("A2", fixture)
    fixture_result = run_a2_group(fixture, run_root, "fixture_expectations")
    expect("A2-fixture-overall" in failing_ids(fixture_result), "the complete claim passed the fixture description")
    run_result = run_a2_group(fixture, run_root, "expectations")
    expect("A2-package-absent" in failing_ids(run_result), "a present package passed the run expectations")


# ---------------------------------------------------------------- negative: paths


def test_linked_artifact_path_is_refused(tmp: Path):
    """A linked expectation file fails, because the checker refuses a link."""
    fixture = copy_fixture("A1", tmp)
    target = fixture / "after" / "expect" / "r2-value.json"
    outside = tmp / "outside.json"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    result = run_a1(fixture)
    expect("A1-exists-expect" in failing_ids(result), "a linked expectation file was not refused")
    row = next(x for x in result["results"] if x["id"] == "A1-exists-expect")
    expect("refused" in row["evidence"], f"the refusal reason is missing: {row['evidence']}")


def test_escaping_artifact_path_is_refused(tmp: Path):
    """A path that climbs out of its root fails with a refusal."""
    (tmp / "root").mkdir()
    spec = [{"id": "escape", "kind": "exists", "path": "../secret.txt", "base": "fixture"}]
    result = CA.run_checks(spec, tmp / "root")
    expect(not result["all_pass"], "an escaping path passed")
    expect("refused" in result["results"][0]["evidence"], "an escaping path was not refused")


def test_dangling_link_fails_the_absent_expectation(tmp: Path):
    """A dangling link at the package path fails the absent expectation."""
    fixture = copy_fixture("A2", tmp)
    package = fixture / "project" / "out" / "fab" / "package"
    package.symlink_to(tmp / "nowhere")
    _, run_root = roots_of("A2", fixture)
    result = run_a2_group(fixture, run_root, "expectations")
    expect("A2-package-absent" in failing_ids(result), "a dangling link passed the absent expectation")


def test_absent_passes_when_nothing_exists(tmp: Path):
    """A missing path passes the absent expectation. This is the positive case for the same kind."""
    result = CA.run_checks([{"id": "none", "kind": "absent", "path": "missing.json"}], tmp)
    expect(result["all_pass"], f"absent did not pass for a missing path: {result}")


# ---------------------------------------------------------------- negative: JSON paths and records


def test_missing_key_fails_even_when_expected_is_null(tmp: Path):
    """A missing key is a failure, even when the expected value is null."""
    (tmp / "data.json").write_text(json.dumps({"present": 1}), encoding="utf-8")
    spec = [{"id": "null-missing", "kind": "json_path_equals", "path": "data.json", "json_path": ["absent_key"], "value": None}]
    result = CA.run_checks(spec, tmp)
    expect(not result["all_pass"], "a missing key passed against a null expectation")


def test_array_index_out_of_range_fails(tmp: Path):
    """An index beyond the array fails, and a key does not index an object as an array."""
    (tmp / "items.json").write_text(json.dumps([{"expected": 1.0}]), encoding="utf-8")
    spec = [{"id": "index-high", "kind": "json_path_equals", "path": "items.json", "json_path": [5, "expected"], "value": 1.0},
            {"id": "index-key", "kind": "json_path_equals", "path": "items.json", "json_path": ["expected"], "value": 1.0}]
    result = CA.run_checks(spec, tmp)
    expect(failing_ids(result) == {"index-high", "index-key"}, f"out-of-range or key-as-index passed: {result}")


def test_record_binding_fails_when_the_raw_file_changes(tmp: Path):
    """The raw output of the ERC record no longer matches its recorded hash after a change."""
    fixture = copy_fixture("A1", tmp)
    erc_binding = json.loads((fixture / "after" / "out" / "reports" / "erc.binding.json").read_text(encoding="utf-8"))
    raw = fixture / "after" / erc_binding["raw_file"]
    raw.write_bytes(raw.read_bytes() + b" ")
    result = run_a1(fixture)
    expect("A1-raw-erc" in failing_ids(result), "a changed raw file passed its record binding")


# ---------------------------------------------------------------- negative: A2 produced rows (R-1 to R-12)


ROW_IDS = {"A2-row-order-status", "A2-row-order-mandatory", "A2-row-silk-status", "A2-row-silk-mandatory",
           "A2-set-mandatory-fail", "A2-set-mandatory-pending"}


def test_minimal_run_fails_the_row_expectations(tmp: Path):
    """R-1. A run that holds only {"exit": 1} fails. The exit and the absent package still pass."""
    result = a2_run_for(tmp, {"exit": 1})
    expect(not result["all_pass"], "the minimal run passed all expectations")
    expect(ROW_IDS <= failing_ids(result), f"row expectations did not fail on the minimal run: {failing_ids(result)}")
    expect(not ({"A2-supplier-exit", "A2-package-absent"} & failing_ids(result)),
           "the exit or package expectation failed on the minimal run")


def test_minimal_run_does_not_enter_fixture_status(tmp: Path):
    """R-5. The fixture description is not part of the run outcome, even when the run is minimal."""
    result = a2_run_for(tmp, {"exit": 1})
    ids = {r["id"] for r in result["results"]}
    expect(not any(i.startswith("A2-fixture-") for i in ids), "a fixture expectation entered the run outcome")


def test_missing_order_row_fails(tmp: Path):
    """A missing match fails the order row expectations."""
    data = frozen_supplier()
    data["rows"] = [r for r in data["rows"] if r["condition"] != "service.order_multiple"]
    result = a2_run_for(tmp, data)
    expect({"A2-row-order-status", "A2-row-order-mandatory"} <= failing_ids(result), "a missing order row passed")


def test_duplicate_order_row_is_refused(tmp: Path):
    """R-9. Two matching rows fail with a duplicate refusal."""
    data = frozen_supplier()
    data["rows"].append(dict(next(r for r in data["rows"] if r["condition"] == "service.order_multiple")))
    result = a2_run_for(tmp, data)
    expect("A2-row-order-status" in failing_ids(result), "a duplicate order row was not refused")
    row = next(x for x in result["results"] if x["id"] == "A2-row-order-status")
    expect("duplicate" in row["evidence"], f"the duplicate reason is missing: {row['evidence']}")


def test_wrong_order_status_fails(tmp: Path):
    """R-3. A produced order row that passes fails the status expectation and the failure set."""
    data = frozen_supplier()
    next(r for r in data["rows"] if r["condition"] == "service.order_multiple")["status"] = "pass"
    result = a2_run_for(tmp, data)
    expect({"A2-row-order-status", "A2-set-mandatory-fail"} <= failing_ids(result), "a wrong order status passed")


def test_wrong_silk_mandatory_flag_fails(tmp: Path):
    """R-6. A changed mandatory flag fails the flag expectation, and the pending set is no longer exact."""
    data = frozen_supplier()
    next(r for r in data["rows"] if r["condition"] == "silk_line_min_short_text")["mandatory"] = False
    result = a2_run_for(tmp, data)
    expect({"A2-row-silk-mandatory", "A2-set-mandatory-pending"} <= failing_ids(result), "a changed flag passed")


def test_string_flag_is_not_a_boolean(tmp: Path):
    """R-10 and type preservation. The string "true" does not equal the boolean true."""
    data = frozen_supplier()
    next(r for r in data["rows"] if r["condition"] == "silk_line_min_short_text")["mandatory"] = "true"
    result = a2_run_for(tmp, data)
    expect("A2-row-silk-mandatory" in failing_ids(result), "a string flag matched a boolean expectation")


def test_unexpected_mandatory_failure_fails(tmp: Path):
    """R-12. A second mandatory failure fails the exact failure set."""
    data = frozen_supplier()
    next(r for r in data["rows"] if r["condition"] == "silk_line_min_short_text")["status"] = "fail"
    result = a2_run_for(tmp, data)
    expect("A2-set-mandatory-fail" in failing_ids(result), "an unexpected mandatory failure passed the set")


def test_missing_compared_field_fails_even_for_null(tmp: Path):
    """R-10. A missing compared field fails. A present null field matches a null expectation."""
    fail_spec = [{"id": "row-missing", "kind": "row_equals", "path": "d.json", "json_path": ["rows"],
                  "match_key": "k", "match_value": "a", "field": "status", "value": None}]
    pass_spec = [{"id": "row-null", "kind": "row_equals", "path": "d.json", "json_path": ["rows"],
                  "match_key": "k", "match_value": "a", "field": "status", "value": None}]
    (tmp / "d.json").write_text(json.dumps({"rows": [{"k": "a"}]}), encoding="utf-8")
    expect(not CA.run_checks(fail_spec, tmp)["all_pass"], "a missing field passed against a null expectation")
    (tmp / "d.json").write_text(json.dumps({"rows": [{"k": "a", "status": None}]}), encoding="utf-8")
    expect(CA.run_checks(pass_spec, tmp)["all_pass"], "a present null field did not match a null expectation")


def test_non_list_array_and_non_object_row_are_refused(tmp: Path):
    """R-11. A non-list array fails. A row that is not an object fails the whole expectation."""
    spec = [{"id": "as-dict", "kind": "row_equals", "path": "d.json", "json_path": ["rows"],
             "match_key": "k", "match_value": "a", "field": "k", "value": "a"},
            {"id": "row-scalar", "kind": "row_equals", "path": "e.json", "json_path": ["rows"],
             "match_key": "k", "match_value": "a", "field": "k", "value": "a"}]
    (tmp / "d.json").write_text(json.dumps({"rows": {"k": "a"}}), encoding="utf-8")
    (tmp / "e.json").write_text(json.dumps({"rows": ["a", {"k": "a"}]}), encoding="utf-8")
    result = CA.run_checks(spec, tmp)
    expect(failing_ids(result) == {"as-dict", "row-scalar"}, f"a non-list or non-object row passed: {result}")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and key in n]
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                if fn.__code__.co_argcount:
                    fn(tmp)
                else:
                    fn()
                print(f"ok   {name}")
            except Exception as error:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(error).__name__}: {error}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
