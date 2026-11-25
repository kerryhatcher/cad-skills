# Source-path normalization text r3 review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: text-only review of `docs/reviews/b12-source-path-normalization-freeze-r3-claude.sha256`
and `docs/reviews/release/b12-source-path-normalization-text-r3-claude.md`. This report
writes no product file. It does not commit. It made no provider call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-source-path-normalization-freeze-r3-claude.sha256` has
SHA-256 `ffdfd3897fec469be7440f034bef6d787747f56c0840646b2010afe42e8ff7df`. It matches the
author message.

| Item | Value |
|---|---|
| Entries | 5 |
| `sha256sum -c` | 5 of 5 OK |
| Supersedes | `407e030d...` |

The manifest is unchanged at
`fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`. The A1 and A2 freeze r2
still matches 155 of 155.

## 2. Text diff

Three lines in `tests/test_release_packaging.py` change:

| Line | New text |
|---|---|
| The docstring of `test_fixture_symlinked_manifest_directory_is_refused` | "The parser refuses a linked manifest directory and a linked parent." |
| The linked-directory failure message | "The parser accepted a linked manifest directory." |
| The linked-parent failure message | "The parser accepted a linked parent." |

Each is one complete active sentence. No semicolon.

## 3. No executable change

The `if "D-9" not in codes(found)` conditions are unchanged. Only the docstring and the two
failure strings change. `py_compile` passes. No functional suite ran, per the lead
decision.

The freeze holds the same `tests/eval/packaging.py` hash `01e29212...` and the same manifest
hash. The A1 and A2 files are unchanged.

## 4. Low observation

### o1 Two terms name the same object

The new lines say "parser". The adjacent OLE2 docstrings say "parser". The module docstring
and the link-test docstring say "checker". STE rule 1.11 asks for one term for one item. The
mixed term is low impact because each sentence is clear. Consider "checker" in a later STE
pass. No change is necessary for this batch.

## 5. Verdict

The three text lines are clear, complete, and active. No executable change occurred. The
manifest and the A1/A2 files are unchanged. The freeze has five entries and all match.

I accept the text. The functional acceptance of the normalization freeze r2 is unchanged.
Provider authorization stays zero.

I made no edit during this review.

## Limits

This review read the text diff and compiled one file. It made no provider call. It changed
no product file.
