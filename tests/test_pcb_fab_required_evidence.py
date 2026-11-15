# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Refuse a generated package that omits the supplier-rule check."""
import json
import tempfile
from pathlib import Path
import test_pcb_fab_acceptance as base


def main():
    with tempfile.TemporaryDirectory(prefix="fab-required-evidence-") as directory:
        project, review_path, review_hash = base.prepared(Path(directory), "project")
        dest = project / "out/fab/packages/required-evidence"
        base.workflow.package(project, base.PROFILE, "trial-1", review_path, dest,
                              project / "out/fab/design", project / "out/fab/supplier", review_hash)
        manifest_path = dest / "manifest.json"
        record = json.loads(manifest_path.read_text())
        base.check("The generated package contains fab.supplier_rules.",
                   any(row["id"] == "fab.supplier_rules" for row in record["checks"]))
        record["checks"] = [row for row in record["checks"] if row["id"] != "fab.supplier_rules"]
        manifest_path.write_text(json.dumps(record, indent=2) + "\n")
        code, report = base.workflow.VAL.build_report([str(manifest_path)], base.workflow.SCHEMAS, project, dest)
        findings = report["findings"]
        base.check("The full validator refuses the absent supplier-rule check.",
                   code != 0 and any(row["code"] == "pkg.check_missing" and "fab.supplier_rules" in row["message"] for row in findings),
                   report)
        print(json.dumps({"validator_exit": code, "findings": findings}, sort_keys=True))
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
