# A3 connection proposal from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Scope: the smallest A3 connection proposal for the accepted PCBA fixtures. This report
writes no product file. It does not commit. It ran no package and no provider call.

## 1. Source fixtures

The accepted manifest is
`/mnt/storage/projects/cad-skills-worktrees/pcba/docs/reviews/pcba/b10-role-doc-freeze-root.sha256`,
SHA-256 `d419688f2e4b5b30a35209985f619c2fc46ae2d58c2a1d949feb9ab24079ca64`, 128 entries.

The A3 source fixtures exist in the PCBA worktree only. The release worktree has no
`tests/fixtures/pcba-design`. Codex raised this path conflict. I agree with the correction:
frozen local copies go under `tests/eval/fixtures/artifacts/A3`, as for A1 and A2.

| Fixture | PCBA source | Files |
|---|---|---|
| Input project | `tests/fixtures/pcba-design/standard-project` | 17 |
| Retained package | `tests/fixtures/pcba-design/retained/pkg-standard` | 42 |

Proposed release copies:

| Fixture | Release path |
|---|---|
| Input project | `tests/eval/fixtures/artifacts/A3/standard-project` |
| Retained package | `tests/eval/fixtures/artifacts/A3/retained/pkg-standard` |

The 59 copied files must be byte-identical to the accepted PCBA entries. The new freeze
records their hashes. A copy hash check contrasts the release copy with the PCBA source
manifest.

Measured reference values:

| Item | Value |
|---|---|
| Project board SHA-256 | `3bda15fa26f711a5647dc6cdd2f074786095e272062bd4737a3773664240f14e` |
| Retained manifest SHA-256 | `58218edd62d12da56f6ebec17af810931499cf0343e549343814a8546fbbfabb` |
| Manifest status | `unqualified` |
| Checks | 13: 10 pass, 2 fail, 1 unconfirmed |
| Fail ids | `design.drc`, `asm.stock_dated` |
| Unconfirmed id | `fab.supplier_rules` |
| Pass ids | `design.erc`, `design.parity`, `fab.profile_evidence`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.test_record` |
| DRC report | `violations` 15, `unconnected_items` 16 |
| Stock fail row | `reports/assembly-neutral.json` `stock` row `EX-LED-0603-G` status `fail` |
| Supplier rules | `evidence/fab.supplier_rules.json` status `unconfirmed` |
| Sierra status | `qualification` `unqualified`, `export_applicability` `unconfirmed` |
| Physical test | `test/test-record.json` `physical_test_passed` false, both items `not measured` |
| Manifest outputs | 41 rows, each with `path`, `role`, `sha256`, `size_bytes` |

## 2. Proposed matrix block

```yaml
A3:
  skill: pcba-design
  freshness: "hash binding of the output manifest to the source bytes (no timestamps)"
  fixture_root: tests/eval/fixtures/artifacts/A3
  run_root: tests/eval/fixtures/artifacts/A3/retained/pkg-standard
  expectations:
    # produced package bytes, base run
    - A3-manifest-status: json_equals manifest.json status unqualified
    - A3-checks-fail: row_set_equals manifest.json checks where {status: fail} id [design.drc, asm.stock_dated]
    - A3-checks-unconfirmed: row_set_equals manifest.json checks where {status: unconfirmed} id [fab.supplier_rules]
    - A3-checks-pass: row_set_equals manifest.json checks where {status: pass} id [10 pass ids]
    - A3-checks-length: length_equals manifest.json checks 13
    - A3-drc-status: json_equals evidence/design.drc.json status fail
    - A3-drc-violations: length_equals reports/drc.json violations 15
    - A3-drc-unconnected: length_equals reports/drc.json unconnected_items 16
    - A3-stock-status: json_equals evidence/asm.stock_dated.json status fail
    - A3-stock-rows: row_set_equals reports/assembly-neutral.json stock where {status: fail} mpn [EX-LED-0603-G]
    - A3-supplier-rules: json_equals evidence/fab.supplier_rules.json status unconfirmed
    - A3-sierra-qualification: json_equals reports/sierra-status.json qualification unqualified
    - A3-sierra-export: json_equals reports/sierra-status.json export_applicability unconfirmed
    - A3-physical-test-false: json_equals test/test-record.json physical_test_passed false
    - A3-physical-test-items: row_set_equals test/test-record.json items where {status: not measured} id [limit.supply_voltage, hand-install.J1]
    - A3-board-binding: sha256_binding manifest.json board_sha256 reference standard-project/kicad/board.kicad_pcb reference_base fixture
    - A3-outputs-binding: row_binding manifest.json outputs path_key path hash_key sha256
    - A3-outputs-length: length_equals manifest.json outputs 41
  fixture_expectations:
    # static input description, base fixture
    - A3-fixture-board-hash: sha256 standard-project/kicad/board.kicad_pcb 3bda15fa...
```

All run expectations use `base: run`. All fixture expectations use `base: fixture`.

## 3. Checker extensions

Two small kinds are necessary. Both follow the existing style.

| Kind | Fields | Behavior |
|---|---|---|
| `length_equals` | `path`, `json_path`, `value` | The array at `json_path` has length `value`. A missing or non-list path fails |
| `row_binding` | `path`, `json_path`, `path_key`, `hash_key`, `base` | For each row, resolve `row[path_key]` under the base and compare its SHA-256 to `row[hash_key]`. A missing file, a missing key, a bad hash, a duplicate `path_key` value, an escaping path or a link component fails |

`length_equals` makes the counts independent. `row_binding` binds all 41 output hashes to the
produced bytes. The duplicate `path_key` refusal plus `length_equals(outputs, 41)` prevents a
manifest that repeats one file and omits another.

Without these kinds, the smallest alternative is a focused test that loops the manifest
`outputs` and the two report arrays. That keeps the matrix smaller but moves the byte check
out of the matrix expectations.

## 4. Fixture and held-out status

- A3 stays held out. No package run and no provider call.
- The fixture stays unqualified: ten pass, DRC and stock fail, supplier rules unconfirmed,
  physical tests not measured.
- The four A3 run expectations read the produced package bytes, not a separate status file.
- The A1/A2 freezes and the packaging freezes are untouched.

## 5. Acceptance for the A3 connection

| ID | Criterion |
|---|---|
| A3-1 | The A3 run expectations read the retained package bytes under the run root |
| A3-2 | The manifest status is `unqualified` |
| A3-3 | The pass, fail and unconfirmed id sets are exact |
| A3-4 | The DRC report counts are 15 violations and 16 unconnected items |
| A3-5 | The stock fail row is `EX-LED-0603-G` |
| A3-6 | The supplier rules are `unconfirmed` |
| A3-7 | Sierra `qualification` is `unqualified` and `export_applicability` is `unconfirmed` |
| A3-8 | `physical_test_passed` is false and both test items are `not measured` |
| A3-9 | Every manifest output hash matches its produced bytes |
| A3-10 | The board binding names the project board hash |
| A3-11 | No provider call and no package run |
| A3-12 | A1, A2 and the fixture bytes stay unchanged |
| A3-13 | The release A3 copies are byte-identical to the accepted PCBA entries |
| A3-14 | `row_binding` refuses a duplicate output path |

## 6. Coordination

Codex agrees that `length_equals` and `row_binding` are the smallest useful additions. Codex
raised one path conflict and I agree with it:

1. The release worktree has no `tests/fixtures/pcba-design`.
2. The A3 source fixtures exist in the PCBA worktree only.
3. The frozen local copies go under `tests/eval/fixtures/artifacts/A3`.
4. `fixture_root` is `tests/eval/fixtures/artifacts/A3` and `run_root` is
   `tests/eval/fixtures/artifacts/A3/retained/pkg-standard`.
5. All package expectations stay at `base: run`.
6. `row_binding` refuses a duplicate output path, together with
   `length_equals(outputs, 41)`.

There is no open conflict.

## Limits

This proposal read the accepted PCBA fixtures and the release matrix. It made no provider
call and ran no package. It changed no product file.
