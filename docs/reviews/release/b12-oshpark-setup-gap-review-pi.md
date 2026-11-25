# OSH Park KiCad setup gap review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-oshpark-setup-gap-claude.md` against the source
request `docs/reviews/oshpark-kicad-setup-root.md` in the original worktree and the
release tree. This report writes no product file. It does not commit. It made no supplier
contact and no provider call.

## 1. Agreement

The gap report is accurate. I reproduced the measured coverage.

| Topic | My check |
|---|---|
| Tenting | Absent outside the stored page copies |
| Net classes | Absent from the skill. The phrase appears only in the plan |
| Refill | Absent from the skill. The phrase appears only in the plan |
| Fonts | `fab.py` mentions fonts only |
| X2 | In `semantics.py`, `validate.py`, `workflow.py`, `inspect_slots.py` |
| Mask expansion | Absent |
| Paste | In `semantics.py`, `validate.py`, `workflow.py` |
| Microvia | Absent |
| Three KiCad pages | Not in any manifest. `design-tools/kicad` is cited in the plan and in older reviews |

The proposed project-authored reference and the three manifest entries cover the gap. The
report keeps the accepted export contract, does not infer native KiCad 10 support, and does
not infer microvia support. I agree with those limits.

## 2. Corrections

### R-1 State the storage path of the three page copies

The report says `tests/eval/distribution.yaml` needs no addition because the KiCad pages
are excluded as full copies. That holds only if the stored pages sit under a path that the
existing rules cover.

- If the pages sit under `skills/pcb-fab-package/supplier/pages/`, the skill manifest
  covers D-1 and the `supplier/pages/**` pattern covers distribution. No
  `distribution.yaml` change is necessary.
- If the pages sit outside `skills/*/supplier/**` and outside
  `docs/reviews/sierra-source-evidence/`, D-1 does not cover them and no exclusion pattern
  covers them. They need an entry in the repository manifest.

Correction: name the storage path in the proposal. The smallest path is
`skills/pcb-fab-package/supplier/pages/`, which the current rules already cover.

### R-2 Use the full manifest field set

The report lists five fields: URL, retrieval date, SHA-256, content type, and distribution
decision. The D-2 required set is larger:

`id`, `path`, `retrieved`, `sha256`, `content_type`, `license_state`,
`distribution_decision`, and `magic`.

P-6 requires the `magic` key. `null` is allowed for header text only. A KiCad HTML page
needs `magic: markup`.

Correction: name the full field set in the proposal.

### R-3 Attribute the KiCad version claim

The report says "The OSH Park main page lists KiCad 9.x for native processing." A search of
the stored `skills/pcb-fab-package/supplier/pages/*.html` finds no KiCad version. The
claim comes from `docs/pcb-pcba-plan.md` and the lead's source request, which cite
`https://docs.oshpark.com/design-tools/kicad/`.

Correction: attribute the claim to the plan and the source request. The retrieval will
measure the current page text.

### R-4 Confirm the two new URLs at retrieval

The source request gives three URLs. Only `design-tools/kicad` appears in the current tree.
The paths `kicad-design-rules` and `generating-kicad-gerbers` are unverified until
retrieval.

Correction: record each retrieved URL, its final resolved URL, the retrieval date, and the
bytes hash in the source review. Do not add a manifest entry before the retrieval.

### R-5 Keep the reference free of page text

The project-authored reference must not copy page text. D-7 checks fixture bytes. A copied
sentence does not fail D-7 unless the whole file hash matches. Correction: state the
"no copied text" rule as a review condition, not as a hash-only check.

## 3. Proposed files, reviewed

| Path | Result |
|---|---|
| `skills/pcb-fab-package/references/oshpark-kicad-setup.md` | Agree. Project-authored. Items 1 to 9. Cite each source and the measured KiCad version |
| `skills/pcb-fab-package/sources.yaml` | Agree after R-1 and R-2. Three entries with the full field set |
| `tests/eval/distribution.yaml` | Agree only under R-1. Otherwise add three repository entries |
| `tests/test_release_packaging.py` | Agree. Each entry passes D-1 to D-8. The reference holds no supplier bytes |

## 4. Constraints kept

- The accepted export contract is unchanged.
- Native KiCad 10 support is not inferred.
- Microvia support is not inferred.
- Setup values are reconciled with the selected service limit before a profile change.
- The source review and the profile bindings remain the authority for changed bytes.

## 5. Recommendation

1. The lead releases the frozen adapter and isolation set.
2. The author applies R-1 to R-5 to the proposal.
3. The author retrieves the three sources with a recorded source review, then writes the
   manifest entries and the reference.
4. Codex and Pi review the changed files.

No product file is written before the frozen set is released.

## Limits

This review searched the release tree and read the source request. It made no supplier
contact and no provider call. It changed no product file.
