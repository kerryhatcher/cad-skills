# Standalone runtime boundary

The first standalone trial used a filesystem boundary that hid `/mnt/storage/projects`.
The first command failed during Python discovery. An explicit proc and dev mount corrected that boundary.
The next trial could not inspect the local container image through the native Podman route.
The native route reported an invalid internal status and a missing `conmon.pid` for an unrelated container.
The lead did not stop or migrate containers and did not change their metadata.

The existing local Podman service can inspect the accepted image and run `kicad-cli version`.
The image ID remains `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`.
The version remains 10.0.5. The existing containers still report their prior running state.
The continued trial uses `CONTAINER_HOST=unix:///run/user/1000/podman/podman.sock`.
The service is local. Its worker commands retain `--network none` and `--pull=never`.

The filesystem boundary proves that the installed Python process cannot read the repository.
The local container service retains host access. This trial does not claim isolation of that service.
The worker commands mount only the captured input directories and the installed skill files.
The source retrieval uses five retained pages through an offline transport, not public GET requests.
