# B10 Role and Drill Freeze Review

Review date: 2026-11-15
Reviewer: `codex-pcba-dev`
Freeze record: `b10-role-and-drill-freeze-root.md`

## Freeze hashes

| File | Before review | After review |
|---|---|---|
| `b10-role-and-drill-freeze-root.md` | `ea61f15d810c974aa4703f249c8e55ca5d29352a6208177f46896093de7e32b6` | `ea61f15d810c974aa4703f249c8e55ca5d29352a6208177f46896093de7e32b6` |
| `b10-role-and-drill-freeze-root.sha256` | `8210ec10b93a34695c3ef7a8b998117ab541937fad0702856876698d883f65aa` | `8210ec10b93a34695c3ef7a8b998117ab541937fad0702856876698d883f65aa` |

All 124 entries in the freeze manifest pass `sha256sum -c` before and after this review.

## Review result

One documentation defect blocks closure.

`contracts/README.md` and `skills/pcba-design/contracts/README.md` list mandatory input roles for `asm.test_record` as `board`, `parts` and `variants`. The shared validator, the PCBA validator copy, `report.py` and interface section 14 also require `board_record`. The freeze record says both documentation copies include this role, but their tables do not.

This mismatch can cause a caller to omit the `board.yaml` input hash from test evidence, even though the validator rejects that evidence. Add `board_record` to both tables, then update their manifest hashes and freeze record.

## Corrections examined

The shared validator and PCBA copy list `board_record` for `asm.test_record`. The package captures `board.yaml`, reads `electrical_limits` from it, and records the role in evidence. The shared negative test checks that missing role refusal works.

The package validates the combined export record against its schema before it checks supported drill settings. The new setting check supports absolute origin, inch units, trailing-zero suppression, four decimal places and separate PTH/NPTH files. It refuses unsupported settings before an export tool call. The focused log records all six refusal cases, including the combined-file schema case.

The earlier final integrity gate and board-derived hole inventory remain in the frozen code. This review found no new defect in those accepted areas.

## Retained evidence

The retained focused log records 106 passed and exit 0. The shared role test log records 59 passed and exit 0. The copy log records 15 passed and exit 0. The retained package record reports unqualified status, with DRC and stock failures and supplier rules unconfirmed.

The retained initial log records 105 passed, one failed test and exit 1. The failure expected the custom setting error before schema refusal for `separate_files`. The corrected focused log records schema refusal first and passes. The freeze record discloses the restored historical logs. I found no evidence that the failed log changed product behavior.

## Scope

I reviewed the freeze record, its 124 hashes, the role tables, validator role lists, package capture path, drill setting refusal path, focused test records and retained package evidence. I did not edit product files or run tests.
