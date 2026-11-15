# B7 workflow W1 correction review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-workflow-w1-record-claude.md`
(SHA-256 `05066cdf94300516a0a46785d050842e2bac894c6668344a85d647ff0f76dc81`), combined with my
checkpoint-1 review. My focus is stage and source preservation, current evidence against package
qualification, and row 15a.

## Hash binding: the record does not match the current code

The record declares these hashes:

```text
efe3f47659a121e617b483ea9d77eb57e9c599370b1f3ac55264528ee4830441 skills/pcb-fab-package/scripts/workflow.py
8ff06d569a103f0da310379e66f3fc4ec8ecbdbaf152144a36342d59e7d99216 tests/test_pcb_fab_workflow.py
```

The current files are:

```text
ca33910a5921c00a7ed8b57d35a7c79c1ff9a7ac053a94eaa7d7e9b2cc803f04 skills/pcb-fab-package/scripts/workflow.py
7cc2f7d80b0c3bad067962ae708aa24dd215cccf4ddeca67e9376c2fc37c83b1 tests/test_pcb_fab_workflow.py
```

The two pairs differ. The modification times show the order: the record and the 68/68 log are 07:03:05,
`workflow.py` is 07:03:18, and the test is 07:03:27. The code changed after the record and after the log.
The 68/68 log does not cover the current code. The record cannot be bound to the reviewed bytes.

## Current code, by inspection (unbound)

- W1: `captured` reads each input once. `digest` hashes those bytes. `stage_project` writes `data[rel]` and
  returns `digest(data)`, so the staged bytes and the recorded digests use the same bytes. `extra_inputs`
  carries the profile and the manual record. `write_result` uses `project_io.atomic_write`. This matches the
  agreed correction.
- W2: `REPORT_KEYS` and `violations_for` exist. `effective_pro` sets every report key for each rule to
  `error`. The supplier loop counts with `violations_for`. This addresses the drill and edge report types.
- Manual evidence: the package compares the manual record key against the copied `manual-evidence.json`
  (lines 569 to 575). The manual artifact content itself is still not re-checked at package time.

These items need a fresh record and a fresh retained run for the current hashes. I do not accept them on
inspection alone.

## Row 15a: the test remains invalid

`test_row_15a` still sets `rule_severities.supplier_min_trace = "ignore"` at line 337 and still uses
`track_width|1000000|1000000|<nil>|<nil>` at line 338. The accepted key is the violation type `track_width`,
and the retained positive fixture is section 10 variant I:
`track_width|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000`.
The check at line 353 asserts `supplier_min_trace == "error"`, which is the generated rule name. It does not
assert `track_width == "error"`. The test still does not establish that the source first hides the target
violation.

The product now sets the report key to `error`, so the product side of W2 is present. The test must assert the
report key and use the retained exclusion.

## Verdict

The W1 record is not accepted. Its declared hashes do not match the current files, and the 68/68 log predates
the current code. The current code appears to address W1 and W2 by inspection, but it needs a fresh record and
a fresh retained run. The `test_row_15a` correction remains open. No full 68-check repeat was run here.

## Agreement on the combined correction decisions

I read `b7-workflow-correction-decisions-root.md` (SHA-256
`88fe5f8421870437f06dac4655c58066b9297f9dea44d2e6e27df257ad10f244`). I confirm agreement with all four
decisions. They match the accepted interface and the W1, W2, and row 15a findings. I have no concrete
conflict.

1. Capture and consume the same bytes. This matches W1 and the input-binding rule. Include the selected
   profile, optional source rules, manual record, and referenced manual artifact. Preserve absence. Compare
   current inputs with the capture before publication.
2. Use the existing lock and atomic helpers. `project_lock` across the operation, `atomic_write` for shared
   records, confined writes including nested paths and links, and `publish_dir` after the final gates.
3. Complete the raw report, binding, and result sequence. Retain raw report bytes, bind inputs and artifacts,
   write the result last, reject a missing or changed binding, and compare current artifacts before
   publication. Do not attach a current artifact hash to an old pass. No index or generic framework.
4. Use the measured report keys. The six mappings, no unmeasured aliases, row 15a with `track_width` and the
   retained exclusion that matches a measured marker, and separate ignored-severity and effective-exclusion
   cases.

The focused evidence list covers my findings: capture change, changed profile or manual inputs, held lock and
nested link, interrupted binding sequence, changed raw report or artifact, the measured severity and
exclusion cases, and the drill and copper-edge report types.
