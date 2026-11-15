# A2: fabrication package input (incomplete status)

This fixture holds an owned copy of the accepted RC bare board, and the OSH Park two-layer supplier profile that it binds.

- `project/`: the accepted template `skills/pcb-design/templates/rc-bare-board`, unchanged. The `out/fab/` folder holds the measured results of the fab commands.
- `profile/oshpark-two-layer.yaml`: a byte copy of the selected profile.
- `sources.sha256`: the SHA-256 of each source file, with its repository path.
- `status.json`: the measured status of each command.

Measured results (2026-11-15 UTC):

- `profile`: exit 0. The profile is valid.
- `design`: exit 0. ERC, DRC with parity, exports, inventory and the drawing sheet pass.
- `supplier`: exit 1. Thirteen of fifteen mandatory conditions pass. `service.order_multiple` fails, because the board order quantity is 5 and the profile requires a multiple of 3. `silk_line_min_short_text` is pending. It needs manual evidence. Two recommendations are reported and never fail.
- `review-source` and `package`: not run. No review record exists, and the supplier status is incomplete.

The status is incomplete. The fixture does not claim a qualified package. The order quantity is kept as the template value. Changing it would hide the failure.

This fixture makes no supplier contact. It uses no network at test time. It uses no file from another skill at run time. The profile copy is the only supplier-related input.
