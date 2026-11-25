# Review of the final B9 neutral repair

Date: 2026-11-15 UTC.

Reviewed the 30 file rows in `docs/reviews/pcba/b9-final-neutral-repair-claude.md`. I checked all 30 hashes. All matched. The author reports 40 focused tests passed. I did not rerun them. The snippet route remains a release integration item. Alternates remain unsupported. Sierra conversion and B10 publication remain outside scope.

## Before and after hashes

| File | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `da3d22eb0cd74078fbb35ae175126f3595e7e265b8d4802d53b1a6e3315ec91f` | `a7315a7b6c3dd7a504268cfb18b57edc3a2a8ec11f1e1dbd22f77337d01e759d` |
| `skills/pcba-design/scripts/pcba.py` | `1e69b6f3bced2cb9b30556829a6ced51b6d8330a0a1c1353239e2033bc3471a4` | `8cda4a6b473a8f98b095f78b23d749cf07061364ebb688aa9618440b4a6ee5b7` |
| `tests/test_pcba_design.py` | `123592419d4cbe7a7ee3953a8e1ffb09bccc0e8cac6912c8326689efc905b454` | `2adf25817a32ab75acfbaa30de2f4969bbb32a64f0eae1ac433a8334633a5010` |

## Review result

The final repair corrects the guide wording. It adds a held-lock test. It returns one `output.path_invalid` finding for an escaping path or directory. It returns an `output.write_failed` finding for a write error. The alias finding names the requested path.

Snapshot reuse, component confinement, resolved project-relative paths, input freshness, output alias checks, finite token values, stock conflict rules, hand-install instructions, row fields, and BOM grouping remain correct in this revision.

## Blocker

The write handler catches every `OSError` from `project_io.atomic_write`. This includes `project_io.PostReplaceError`. `PostReplaceError` means the new output bytes are already in place, but a later sync step failed. The command then reports `output.write_failed` as a refusal. The CLI contract says a refusal writes nothing. An existing output can also lose its prior bytes.

Handle `PostReplaceError` separately. Do not report a refusal that claims no output exists after the atomic replace. Add a test that forces a post-replace failure and examines the output and prior bytes. Keep the ordinary pre-replace failure test.

## Scoped decision

The five final repair items pass code review, except for the post-replace write error above. Do not accept the batch until this write outcome has a clear result and focused test. This review accepts no alternate support, Sierra conversion, B10 publication, or release integration work.

This report changes no product file or shared contract.
