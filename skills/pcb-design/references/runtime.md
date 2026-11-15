# Runtime

## Image

The runtime is the local image `localhost/cad-skills-pcb:b6`, built from `runtime/Containerfile`. The lock file `toolchain.lock.json` names the image and its ID. The ID of the local image must equal the lock digest. Otherwise `check` and every tool command exit 2 with `runtime.image_mismatch`.

## Execution routes

`--runtime auto|container|native` selects the route. `auto` follows the lock field `execution`. Nothing falls back silently. A conflicting explicit route exits 2 (`runtime.conflict`).

- Container route: each tool runs in the image by podman, as described below.
- Native route: the controller runs the same tool commands directly, with the `/work` and `/worker` paths mapped to the staged directories. Each operation checks its own prerequisites: `erc` and `drc` need `kicad-cli`, `sim` needs `ngspice`, and `export` needs `kicad-cli` and `pcbnew`. A missing ngspice therefore does not block ERC. The measured native versions must equal the lock for the tools that the operation uses. A different version exits 2 (`runtime.version_mismatch`).
- Measured coverage: the native route ran inside the existing runtime image with a native lock (the native test of the focused test file). The host has no KiCad installation, so `--runtime native` on the host exits 2 with `runtime.native_unavailable`. The host installation is not measured.

## Measured versions

| Tool | Version | Command |
|---|---|---|
| KiCad CLI | 10.0.5 | `kicad-cli version` |
| ngspice | 44.2 | `ngspice --version` |
| uv | 0.12.5 | `uv --version` |
| pcbnew | 10.0.5 | `/usr/bin/python3 -c "import pcbnew"` |

Run `uv run scripts/pcb.py env --project PROJECT` to measure the versions again.

## Image identity for the gui adapter

The controller certifies the gui update adapter only for the measured image IDs in `GUI_IMAGE_IDS`. A matching KiCad version alone does not satisfy the check. Another image ID exits 2 with `update.adapter_unavailable`, and the manual route stays available. The standalone rebuild (see below) has another ID, so it needs its own measurement before certification.

## Container rules

Each command uses:

`podman run --rm --pull=never --network none --security-opt label=disable -w /work -v STAGE:/work IMAGE ...`

`STAGE` is a new staging directory under `${PROJECT}/out/staging/`. It holds a copy of the input files. The controller does not mount the live project. It copies the worker to `STAGE/worker` and mounts it read-only. A normal command never pulls or builds an image.

The measurement covers `kicad-cli version`, file writes and file ownership with `--security-opt label=disable`. The full ERC, DRC, export and worker path ran with this option. SKILL.md does not claim SELinux confinement.

## Standalone setup

`../runtime/BUILD.md` describes the build. We built the recipe once with `--no-cache` for this measurement. Its checks ran on the new image, in a copy whose lock we revised by an explicit edit. The build pins the base images by digest and `ngspice`. It installs no SKiDL package and no Python lock file. A rebuilt image has another ID. Revise the lock by an explicit edit after the `env` comparison. A revised lock does not certify the `gui` adapter.
