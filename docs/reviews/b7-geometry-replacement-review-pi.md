# B7 geometry replacement checkpoint review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: the six corrections in
`b7-geometry-replacement-checkpoint-claude.md` (SHA-256
`6882cb65f604fa60745162786c8b215adaf5c6b7445f43d0e77e4c22018e5eef`).

This report gives the review result only. It does not change the six files. Full B7/B8 acceptance stays
pending.

## Hash check

The six measured hashes match the replacement checkpoint before and after this review. The last measurement
follows.

```text
7d0e6592dcd504e662a4944107367f948b7833caa205d64e73d4706e479f1192 skills/pcb-fab-package/scripts/inspect_mask.py
c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d skills/pcb-fab-package/scripts/macro_defs.py
5be010bffda38af71ad1fba753d460bb65534d1d6c887999d8a1049d60ce759b skills/pcb-fab-package/scripts/export_inspect.py
9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc skills/pcb-fab-package/scripts/inspect_slots.py
ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838 skills/pcb-fab-package/scripts/board_inventory_slots.py
070440293e9520dd75999a8acd4daebdf87947b1e547330f49cb7d04c6c3a5bb tests/test_pcb_fab_package.py
```

The old checkpoint `docs/reviews/b7-geometry-checkpoint-claude.md` stays unchanged at
`7c7ed0f019bddb5ba453cd17c476419bbbc1ab7f76be0a4d27d90527e1e94122`.

## Declared command

I ran the declared command one time. It returned exit 0 and 93 of 93 passed. I did not repeat it.

## Independent correction verification

I ran focused probes with my own inputs. The probe inputs and outputs stay in
`/tmp/b7-geo-replacement-out.json` on this host. Each probe targets one correction.

1. G1 macro start:
   - The macro on the units line returns `exit 2` and `unsupported "a macro definition does not start a
     line"`.
   - The macro after one leading space returns the same refusal.
   - The two overlapping 10 mm circles with an inline macro return the same refusal.
2. G2 one byte snapshot:
   - The `Path.read_bytes` hook counts one read.
   - The run returns status 0.
   - The report hash equals the SHA-256 of the measured bytes.
3. G3 time budget (cooperative check):
   - `inspect(..., max_seconds=0.0)` raises `Unsupported` with "the elapsed-time limit of 0.0 seconds was
     exceeded during reading". The check fires.
   - The dense 10,000-flash probe returns `exit 2`, `unsupported "more than 2000000 candidate pairs"`, in
     1.708 s. The pair cap fires before the two-second budget on this host.
   - These checks are cooperative. They run between stages and every 1000 pair checks. They do not prove
     the interruption of a slow parser or of one slow operation. The hard full-operation bound is
     unmeasured here. Codex examines that bound.
4. G4 aperture holes:
   - The circle aperture `%ADD10C,2X1.9*%` returns `exit 2` and `unsupported "uses an aperture with a
     hole, which is not measured"`.
   - The rectangle aperture `%ADD10R,2X2X1.5*%` returns the same refusal.
5. G5 RoundRect parameters:
   - The diagonal corner order returns `exit 2` and `unsupported "the RoundRect corners are not the four
     corners of one rectangle"`.
   - The rotation of 90 returns `exit 2` and `unsupported "a rotated RoundRect is not measured"`.
   - The radius above half the smaller side returns `exit 2` and `unsupported "the RoundRect radius is
     outside the measured range"`. This is a policy of the accepted subset. It is not a general
     mathematical validity rule for a Minkowski rounded rectangle. Codex examines that point.
6. G6 Excellon terminal state:
   - The missing terminal `M30` returns `UnsupportedRecord` with "the drill file has no terminal M30".
   - The record after `M30` returns `UnsupportedRecord` with "a record follows the terminal M30".

One old passing case stays: two rectangles that touch on an edge return `exit 0` and `merged_opening 1`.

## Observations and limits

- A comment after `M30` follows the normal comment rule. A known comment is skipped. An unknown comment is
  refused as "unsupported header comment". The reader does not treat a comment as a record. This is
  consistent with the accepted comment subset.
- The macro text comparison is exact. The behavior on CRLF input is unmeasured.
- The G5 radius check is a subset policy, not a general mathematical validity rule. The diagonal-order and
  rotation checks are parameter checks for the measured form. Codex examines the general geometry question.
- The G1 regression assertion reduces to `code == 2`. The test does not assert the refusal reason. This is a
  test-quality note, not a functional defect.
- The G2 regression holds a dead `pathlib.Path.read_bytes` expression. It is harmless. This is a
  test-quality note.
- Full B7/B8 acceptance stays pending. It is outside this geometry scope.

## Verdict

I agree that the six corrections are present and correct in the replacement checkpoint. Each correction has
a focused regression, and each regression has my independent match. The replacement checkpoint is consistent
with its declared tests. The replacement is suitable as the corrected geometry basis. I make no hard timeout
claim and no general geometry-validity claim. The cooperative time budget and the RoundRect radius policy
stay subject to the Codex examination. Full B7/B8 acceptance stays pending.

## Agreement on the final geometry decisions

I read `b7-geometry-final-decisions-root.md` (SHA-256
`e1becdb43bce77e30e12a8103e50bedda20806de11d8ac25036a3106f0de9407`). I confirm both narrow resolutions.

1. Remove the radius limit relative to the core side. I agree. The limit is a policy of the earlier accepted
   subset, not a validity rule for the Minkowski core-distance model. The corrected form keeps a positive
   finite radius, finite coordinates, the supported axis-aligned rectangle shape, and the correct corner
   cycle. The independent case with a radius above half the smaller core side must use the core-distance
   formula `max(0, d_core - r1 - r2)`. The overlap refusals stay. I make no general geometry-validity claim.
2. Keep the cooperative budget in the helper. Add the two-second subprocess timeout at each public caller.
   I agree. The helper budget runs between stages and every 1000 pair checks. It cannot interrupt an active
   parser call. The caller timeout is the hard bound. A timeout must return exit 2 with a resource-limit
   finding. It must not publish a passing result and must not reuse an earlier report. A fresh report path
   for each run prevents a stale success. The controlled stalled worker test through the public caller is the
   right regression. The timeout includes ordinary process-start and termination overhead, so the report must
   not claim exact real-time scheduling. The dependency setup stays separate from the bounded inspection.

The other accepted corrections stay. Full B7/B8 workflow acceptance stays separate. No new parser or design
phase is necessary.
