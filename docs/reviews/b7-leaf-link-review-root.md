# B7 captured-profile file link

Date: 2026-11-15 UTC. The complete correction still has a C1 defect.

`profile_from_bytes` confines the directory `supplier/captured`. It does not confine the file `supplier/captured/profile.yaml` before `write_bytes`.
A symbolic link at that file path writes outside the project. This includes a dangling link.

Measured source hash: `65f88be99b9fb758fc095e9086f954688eb1b240b5f192d69d9660bceb075f0b`.
Command: `uv run /tmp/b7-leaf-link-root.py`, exit 0.
The retained source is `b7-leaf-link-probe-root.py` in this directory.

The temporary project is `/tmp/b7-leaf-root-ckr2pcf8/project`.
The target `/tmp/b7-leaf-root-ckr2pcf8/outside-profile.yaml` did not exist before the call.
The call returned without refusal. The target exists after the call. The symbolic link remains unchanged.
The target hash is `2aedaa0c8076b18005345bf0f56f97396121e1faae915152d5bfcf10a942ad87`.
The probe changed no product file.

The correction must confine the complete destination before mutation, including the file itself.
Use the accepted atomic helper after confinement, or parse the captured bytes without a scratch file.
Add a focused file-link regression. Keep the directory-link regression.
The reviewers continue the complete correction review before the next repair batch.
