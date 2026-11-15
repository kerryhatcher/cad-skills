# B7 workflow draft observations

Date: 2026-11-14 UTC. The workflow file is open for implementation.
This is guidance before the final freeze, not a final review.
The examined `workflow.py` hash is `3cb1d04245fe951037e0a317773d61f7ccdfa9e091a3310d451964dd70e9609b`.

The accepted B7 interface retains the earlier runtime, evidence, export, and publication rules.
The current draft does not yet implement several of them.

1. **Path and publication rules.** Confine all writes to the project's `out/fab/` tree before any mutation.
   Refuse existing destinations and escaping links. Do not remove an arbitrary existing stage with `rmtree`.
   Build a package in a fresh temporary directory. Publish it with the accepted `publish_dir` helper.
   Use the accepted lock and atomic-write procedures for shared records.
2. **Runtime identity.** The mutable image tag is a lookup, not evidence.
   Compare its measured image identity with the lock, then run the measured identity.
   Measure tool versions. Do not report a version merely because the lock contains that string.
3. **Input and result bindings.** Snapshot all consumed inputs, including the source rules, export settings, profile, lock, and manual evidence.
   Bind raw results to those bytes. Bind each result to its binding hash.
   At package time, compare the measured inputs with current inputs before a qualified claim.
   Do not attach current hashes to an old success. Schema validation alone cannot establish freshness.
4. **Supplier rules.** Preserve source rules, then append the mandatory supplier rules in the agreed order.
   Set the applicable KiCad violation-type severities to `error` in the staged project.
   A generated rule name is not the key for `rule_severities`.
   Retain the ignore-severity and exclusion regressions from acceptance row 15a.
5. **Complete supplier conditions.** Account for each applicable limit and service/process condition.
   Include layer count, order multiple, selected stackup and process evidence. Inspect both applicable mask layers.
   Implement the agreed manual geometry route for unsupported mask constructs.
   A single silk attestation cannot establish all supplier conditions.
6. **Export semantics.** Restore the accepted seven export checks through an owned derivative of the tested code.
   A file-function substring does not establish the correct layer, copper order, or duplicate declarations.
   Equal drill counts do not establish coordinates, dimensions, or plating agreement.
   Compare the actual file functions and complete hole multisets with the board and export contract.
   Test swapped copper layers, changed drill coordinates with equal counts, and effective X2 and drill-mark settings.

These points restore the accepted interface. They do not add another framework or a new design phase.
The final test record must show the actual positive workflow and these negative cases.
Do not weaken a validator to obtain a passing package result.

## Test-run defect

The lead read `tests/test_pcb_fab_workflow.py` at hash `3c2b369487826fdf6ea8d3c83cbd21f10acfdb4a2b8a68516fde0861769d4993`.
Lines 220 to 229 contain a duplicate main body within `test_design_supplier_package`.
That body calls the same test function again. The test cannot finish through its normal return path.
The lead directed Claude to stop that test process, retain its log, and remove the duplicate body.
No new root test run was necessary to identify this direct recursion.

At the same read, `workflow.py` had hash `bca595484e0298362d5173a5b94ae37360855a3ade8b3e114188c68c412adbb1`.
It still ran the global image tag after the identity measurement.
Its source hash function still covered only three files, and its stage function removed an existing stage.
These observations remain within points 1 to 3 above. They do not change the accepted interface.
