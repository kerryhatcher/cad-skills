# B5 native identity checkpoint review: Codex

Date: 2026-11-14.

**Decision: checkpoint corrections necessary**

I do not accept checkpoint 2 yet. The six valid runs reproduce their recorded results. The runner, evidence records, and three identity comparisons need narrow corrections below. Preserve the current valid runs as historical evidence.

Manifest: `docs/reviews/b5-native-files.sha256`.

Manifest SHA-256: `ab732d880ffb6cecf83b0be90875ae5bfbdb068b57a68f5266cb24c69ea9905c`.

All 67 entries passed before and after review. The manifest hash remained unchanged.

**Measured valid evidence**

`uv run tests/test_trial_identity.py` passed: 9/9, exit 0.

I regenerated the expectations from the frozen baseline snapshot. All seven generator outputs matched their frozen counterparts. The generator reads the baseline and edit definitions only. It does not read an after-board.

I independently read the saved boards for `gate_none`, `gate2_reorder`, `gate2_value`, `gate2_addc2`, `gate2_removed1`, and `gate2_fpr1`:

- Each recomputed snapshot equals its stored snapshot.
- Each comparison gives the recorded expected differences.
- Each GUI summary's after-hash equals the saved-board hash.
- Requested options match the measured after-states.
- All six segments retain their recorded UUIDs, nets, widths, layers, and geometry.

The baseline has seven footprints, six segments, one graphic, and no arcs, vias, or zones. These runs establish no preservation result for an absent class.

**Combined corrections from Pi A–E and the root observations**

I read `b5-native-review-pi.md`. I agree with A, B, D, and E. Apply these minimum corrections:

| Item | Minimum correction |
|---|---|
| A: supported gate status | Return the comparison status from the supported gate runner. Keep exploratory expected failures explicit. A failed supported comparison cannot return success. |
| B: per-board diagnostics | Record full DRC, unconnected-item, and parity findings and exit codes for each valid phase-A board. Bind each report to its board and matching schematic bytes. A GUI update message is not this evidence. |
| D: replace-off expectation | Generate the empty replace-off expectation from the option/edit definition. Let the runner select an explicit expected file. Keep the original wrong-expectation comparison as historical evidence and add the correct comparison. |
| E: invalid attempts | Mark the three invalid first attempts explicitly in their run directories or a small run index. Do not count the invalid reorder result as a gate pass. Preserve `gate_none` as valid. |

The observed `gate()` implementation records `compare_rc` and then unconditionally returns 0. This confirms A.

For C, add focused via, zone, and arc fixtures with unchanged, changed, and named-removal cases. Obtain saved KiCad evidence before a preservation claim for those classes. No general parser is necessary. Correct the record's claim that via and zone paths already have text-fixture tests. The frozen test file has none.

**Independent phase-A diagnostic probes**

I reconstructed matching edited schematics from the frozen native source and edit helper. I ran the saved boards in temporary copies through the existing derived image, offline:

```text
d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2
```

The command used DRC with `--schematic-parity`, `--exit-code-violations`, `--severity-all`, and JSON output.

| Saved board | Exit | Violations | Unconnected items | Parity findings |
|---|---:|---:|---:|---:|
| `gate_none` | 5 | 1 | 2 | 0 |
| `gate2_reorder` | 5 | 1 | 2 | 0 |
| `gate2_value` | 5 | 1 | 2 | 0 |
| `gate2_addc2` | 5 | 1 | 4 | 0 |
| `gate2_removed1` | 5 | 1 | 1 | 0 |
| `gate2_fpr1` | 5 | 1 | 2 | 0 |
| `gate2_fpr1_replace_off` | 5 | 1 | 2 | 2 |

These measurements support the six valid update observations and the exploratory replace-off limit. They do not replace retained, per-run diagnostic artifacts. None of these boards is the final DRC-clean reference board.

**I1: added-footprint comparison omits the expected value**

Location: `scripts/identity.py:152` and `scripts/gate_expect.py`, `add-c2`.

Reproduction: change `C2`'s Value property in the saved `gate2_addc2` board to `WRONG`. Generate a fresh snapshot and compare it with the unchanged add-C2 expectation.

Both CLI commands return exit 0. The comparison gives one observed difference, one expected difference, and `equal`. The added-footprint difference contains the reference, library ID, and pad nets, but omits the value.

Include the known added value in the difference and expectation. Derive that value from the baseline and edit definition, not the observed output. Add a wrong-added-value negative test. Do not predict random new UUIDs or add placement-policy features.

**I2: duplicate expected differences falsely satisfy exact equality**

Location: `scripts/identity.py:180`.

Reproduction: compare the saved R2-value edit with two copies of the same expected value difference. The result is:

```text
observed: 1
expected: 2
status: equal
```

Membership tests do not compare multiplicity. Reject duplicate expected records, or compare their occurrence counts. Add this one negative case. Retain the existing missing and unexpected difference tests.

**I3: duplicate UUIDs can hide a routing object**

Location: `scripts/identity.py:100`, snapshot dictionary assignments.

Reproduction: copy a baseline segment with its UUID unchanged. Change the copy's end coordinate to 999. Insert it before the original segment.

The later dictionary assignment overwrites the altered copy. Snapshot comparison against the baseline gives zero observed differences and `equal`.

Reject duplicate UUIDs before assignment for the handled UUID-keyed objects. Reject a missing required UUID with a clear input problem. Add a duplicate-segment negative test. This is an identity-key guard, not a general KiCad parser.

**Scope and limits**

The valid saved-board observations remain useful. Expectations must continue to use only baseline data and the specified edit. Do not repair a failing gate by copying its observed result into the expectation.

GUI screenshots referenced by the summaries are outside this frozen manifest. My option assessment uses the frozen summaries and saved-board effects. I did not repeat a GUI operation.

Repeat gates, remaining source paths, other limit probes, and actual via/zone preservation remain later trial evidence. The final clean board, exports, analytical simulation and negative case, and explicit draft package also remain necessary.

All probes used temporary files. Container commands used `--pull=never` and `--network none`. I did not rebuild, pull, relabel the repository, or run unrelated suites. I changed only this report.

## Pi agreement with I1 to I3 (appendix)

Date: 2026-11-14.

I examined the three items at the named lines. I reproduced each one on the host fixture. I agree with I1, I2 and I3 at the narrow scope that Codex records. I have no objection.

| Item | Line | Measured result | Agreement |
|---|---|---|---|
| I1 | `scripts/identity.py:152`, `scripts/gate_expect.py` (`add-c2`) | The added-footprint record has `lib_id` and `pad_nets` only. It has no `value`. A wrong added value gives `status: equal`. The expectation also has no `value`. | Agree. Include the known added value in the observed difference and the expectation. Derive it from the baseline and the edit definition. Add the wrong-added-value negative test. |
| I2 | `scripts/identity.py:180` | One observed value difference against two copies of that same difference gives `observed: 1`, `expected: 2`, `status: equal`. | Agree. Reject duplicate expected records, or compare occurrence counts. Add this one negative test. |
| I3 | `scripts/identity.py:101` and the other snapshot dictionary assignments | A duplicate segment UUID overwrites the earlier object. The comparison with the baseline gives `status: equal`. A missing UUID becomes the mapping key `None`, which JSON writes as `null`. | Agree. Reject duplicate UUIDs before assignment for the UUID-keyed classes. Reject a missing required UUID with a clear input problem. Add the duplicate-segment negative test. |

These confirmations used host scripts and read-only copies of the frozen fixture. I ran no container probe. I agree with the scope limit. These are identity-key guards, not a general parser.

The correction will preserve the historical results. It changes only the named helpers, tests and evidence.
