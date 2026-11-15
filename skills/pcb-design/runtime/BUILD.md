# Build the pcb-design runtime image

This recipe builds one local image. It pins the base images by digest and pins `ngspice`.
It installs no SKiDL package and no Python lock file.

## Build

Run from the skill directory:

```bash
podman build --pull=never --tag localhost/cad-skills-pcb:b6 --file runtime/Containerfile runtime
```

`--pull=never` uses only the local base images. The build needs the network only for `apt-get`.
If the pinned `ngspice` version is missing, the build fails. It never installs another version.

## After the build

1. Read the local image ID: `podman image inspect localhost/cad-skills-pcb:b6 --format '{{.Id}}'`.
2. Run `pcb.py env --image localhost/cad-skills-pcb:b6`. The report lists the measured versions.
3. Compare the image ID and the versions with `toolchain.lock.json`. Revise the lock by an explicit edit
   of `image`, `digest` and the versions. A rebuilt image has another ID. Until you revise the lock, `check` exits 2.
4. A revised lock does not certify the `gui` update adapter for the new image. Keep the adapter disabled
   until its own measurement passes (see SKILL.md).
