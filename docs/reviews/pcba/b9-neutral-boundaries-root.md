# B9 neutral batch path boundaries: root record

Date: 2026-11-15. Measured by the lead. Confirmed by pi-pcba-dev with independent probes.

The frozen batch is `docs/reviews/pcba/b9-neutral-batch-claude.md`. The batch record has 30
hash rows, including the interface and `COPY_SHA256.txt`. It does not have 32 rows.

## Defect 1: the `components/` boundary is not enforced for a symlink

A symlink under `components/` can point to a file outside `components/` but inside the project.
The map path `components/link.yaml` passes the lexical check. The project confinement accepts
the target, because the target is inside the project root.

Probe:

```bash
cp tests/fixtures/pcba-design/project/components/resistor-10k.yaml /tmp/p/components/../outside.yaml
ln -s ../outside.yaml /tmp/p/components/link.yaml
# set the R1 part path to components/link.yaml
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/p --board board.kicad_pcb \
    --variant base --as-of 2026-11-15
```

Result: exit 0. The neutral row for R1 uses `components/link.yaml`. Interface section 4
requires a rejection of a symlink that leaves `components/`.

## Defect 2: `--out` can replace an input file

The `neutral` step accepts an output path that equals one of its inputs.

Probe:

```bash
cp -r tests/fixtures/pcba-design/project /tmp/q
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/q --board board.kicad_pcb \
    --variant base --as-of 2026-11-15 --out board.yaml
```

Result: exit 0. The board record `board.yaml` is replaced by the neutral JSON. Its SHA-256
changes from `95901a4b284357c2b6507f7eb4d7dcb39a84228587cb6d759c71743cf7a9257a` to
`6f4b0c7acdcbe69caabb59e174ead5bc7189b787199b8d4134df34003cbdf3d3`.

## Effect

Both defects break the capture rule. A step must derive outputs from captured input bytes and
must not change an input. Both defects leave the frozen set unchanged.
