# A1 and A2 artifact fixture review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/artifact-a1-a2-freeze-claude.sha256`. This review is
separate from the BOM text batch and the harness. It writes no product file. It does not
commit. It made no provider call.

## 1. Freeze and hashes

The freeze file `docs/reviews/artifact-a1-a2-freeze-claude.sha256` has SHA-256
`87ea9b62a2b6b665eb0690685b4302b34e46c4b13442b642862e7b30b824f11b`. It matches the author
message.

| Item | Before | After |
|---|---|---|
| Entries | 155 | 155 |
| `sha256sum -c` | 155 of 155 OK | 155 of 155 OK |
| Freeze file hash | `87ea9b62...` | `87ea9b62...` |

The freeze holds 154 fixture files and `tests/test_artifact_fixtures.py`.

## 2. Test reproduced

`uv run tests/test_artifact_fixtures.py` gives 11 of 11 passed, exit 0. No container, KiCad
process or simulator runs.

## 3. A1 check

| Check | Result |
|---|---|
| The before tree matches the accepted RC template byte for byte | Pass |
| The only schematic change is the Value line of R2, 10k to 20k | Pass |
| The hand-written expectation names the one change and matches the identity reader | Pass |
| The interface names the edited board. The result binds the prior board, the expectation and the interface hashes | Pass |
| The simulation expected value is computed from the RC formula, not copied from tool output | Pass. 3.3 × (1 - exp(-0.5)) equals 1.298 V |

The A1 tree holds retained ERC, DRC, update and simulation records, GUI screenshots, and the
toolchain lock. The ERC result is `pass`, the DRC result is `pass`, and the update state is
`ready`.

## 4. A2 check

| Check | Result |
|---|---|
| Every template input is present with the same bytes. Only `out/fab` is added | Pass |
| The profile copy equals the skill profile and the tool binds its content hash | Pass |
| Each line of `sources.sha256` names a repository file with that hash | Pass |
| The design step exits 0 | Pass |
| Quantity 5 fails the multiple-of-3 rule by an independent calculation | Pass |
| The supplier step exits 1. The status is incomplete and matches the result rows | Pass |

A2 is deliberately incomplete: design passes, supplier exits 1, `service.order_multiple`
fails, `silk_line_min_short_text` is pending, and `package` and `review-source` are not run.

## 5. Owned isolation and independent values

- The A1 before tree is the accepted template. The A2 project tree is the same template plus
  `out/fab`. The fixtures are owned copies.
- The test imports the standard library only. It runs the `pcb-design` identity reader. It
  does not import another skill.
- The A1 expected simulation value and the A2 order failure come from an independent
  calculation in the test. They are not copied from tool output.
- The interface result binds the prior board, the expectation and the interface by hash.
  The ERC and DRC bindings name the container image and image ID, the command, the raw file
  hash, and the closure hashes.

## 6. Findings

### F-1 The A1 focused test does not check the ERC, DRC and ready records

The author reports "ERC and DRC pass, check --for ready exits 0". The retained records say
`erc.result.json` status `pass`, `drc.result.json` status `pass`, and `update.result.json`
state `ready`. The focused test checks the identity, the interface and the simulation. It
does not read the ERC, DRC or ready records. The matrix `artifact_checks.A1` also has no
expectations yet.

Correction: add focused checks for the three records. Assert the status values, the ready
state, the operation names, the tool exit 0, the raw file hash, and the closure hashes.
These read the frozen bytes. No KiCad process is necessary.

Severity: medium. The freeze hash catches tampering, but the test does not assert the
semantics of the readiness claim.

### F-2 The A1 after README describes the before state

`tests/eval/fixtures/artifacts/A1/after/README.md` says "R2 = 10 kohm ... 2.086 V at 1 ms".
The after fixture uses R2 = 20k and 1.298 V.

Correction: state that the after tree keeps the template README and that the single
schematic value change is the only edit. Or update the README. Low.

### F-3 The GUI screenshots and logs are supporting evidence only

The A1 tree holds GUI screenshots and stdout and stderr logs. The test does not read them.
That is acceptable. They are retained evidence for the interface step.

## 7. Verdict

The A1 and A2 fixtures are correct within their scope. The A1 before tree matches the
template. The A2 project matches the template. The expected values are independent. The
interface and bindings are byte-bound. A2 is correctly incomplete.

Add F-1 before A1 is called ready in a release report. F-2 is low. F-3 needs no change.

Provider authorization stays zero. No provider call occurred.

## Limits

This review ran the focused fixture test and read the frozen bytes. It made no provider call
and no CAD call. It changed no product file.
