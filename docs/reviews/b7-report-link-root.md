# B7 fresh report path

Date: 2026-11-14 UTC.

The lead measured `fab.py` at hash `d6d13ab732190b7be0a029fb1f3ce27c81506fd8f94c83e1989cffe2cbc2adeb`.
The caller tests `rep.exists()` before it starts the mask worker.
A dangling symbolic link fails that existence test.

The temporary directory is `/tmp/b7-report-link-root-4txjmfxs`.
Its `report.json` link points to the absent `new-target.json` in that directory.
The lead ran this command from the repository root:

```sh
uv run --quiet skills/pcb-fab-package/scripts/fab.py inspect-mask \
  --gerber tests/fixtures/pcb-fab-package/mask/m41.gts \
  --limit-mil 4 \
  --report /tmp/b7-report-link-root-4txjmfxs/report.json
```

The command returned exit 0. The link stayed, and the worker wrote its report to `new-target.json`.
This result violates the agreed fresh-path rule.

The narrow correction rejects an existing path or a symbolic link before the worker starts.
The regression must return exit 2, preserve the link, and leave its target absent.
The lead also requested a period in place of the new docstring semicolon.
No broader geometry or parser change is necessary.
