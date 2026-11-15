# B6 design review: lead

Date: 2026-11-14. Review target: `b6-proposal-claude.md`, SHA-256 `441af68ebbb33b72072c7aad358cece51930d5ffd107bdbdf7d0108715ff9c76`.

The lead accepted B5. The B6 proposal is not ready for implementation. Resolve the points below with both reviewers. Keep the batch focused on `pcb-design`.

## R1. Skill scope and agent workflow

Separate the CLI scope from the skill scope. The CLI does not automatically design arbitrary circuits. The skill must guide circuit design, native schematic edits, placement, routing, and review. It must do more than inspect a completed template.

Give the design workflow its planned references and examples. State how the agent preserves symbol and footprint identities. State where datasheet, footprint, power, and return-path decisions enter the procedure.

B5 measured a scripted GUI route on the fixed image. Examine an optional adapter for that exact environment before discarding it. Keep the native-installation manual fallback. Neither route is a headless schematic-update CLI. Define the actual action for an agent without GUI access. Do not imply that a template-only test proves an edited-board workflow.

## R2. Runtime and standalone files

Define native and container invocation. The host has no KiCad installation, but it has the tested image. State image selection, mounted paths, the system-Python worker, and missing-prerequisite behavior. Do not pull an image or change unrelated filesystem labels during a normal command.

Let the environment report operate before a project exists. Test the bundled validator's schema path from an unrelated working directory. State the template's complete project records and toolchain data.

## R3. General export expectations

The unchanged identity reader does not supply all pad drills, plating classes, or geometric transforms. It cannot alone establish expected holes for a general board.

Define a small board-inventory worker or another tested source for those values. Keep the accepted identity reader unchanged. Account for local pad positions, footprint rotation, board side, vias, and non-plated holes. State unsupported geometry and fail explicitly when it occurs. Do not silently omit a slot or pad.

Derive layer functions from the selected export settings and actual copper order. The nine-file trial map cannot serve all four-layer and six-layer boards. Keep the trial's independent constants as test evidence.

## R4. Reports, failures, and freshness

Resolve the contradiction between exit 0 with no error finding and failure on a DRC warning. Define the unwaived-violation policy and the exact waiver behavior. Missing or stale mandatory reports cannot produce a successful readiness result.

Define exit precedence when several problems occur. The simulation table gives exit 2 for a missing measured value, but the general table assigns malformed tool results to exit 3. Use one rule.

Raw tool reports contain dates and other variable bytes. Preserve those bytes and their hashes. Limit deterministic-byte claims to operations that can satisfy them. Do not remove evidence to force repeatability.

Refill does not necessarily change a board's bytes. Test the resulting hash and report binding. Do not demand a hash change from an already filled board.

## R5. Writes and publication

A lock alone does not protect against an interrupted tool write. Define temporary execution, board replacement, report publication, and export publication with the accepted project-I/O helpers. Keep the stated limits before and after replacement.

Specify behavior for an existing output directory. Prevent stale output files from satisfying a failed export. State which clean reports are necessary before a normal export. Keep settings changes explicit and invalidate affected report bindings.

## R6. Acceptance tests

Test the host-to-container path and the standalone installed skill. Include one meaningful agent design or edit task, followed by independent artifact checks. A prebuilt-template audit alone is insufficient.

Use focused tests for the new behavior. Do not repeat unchanged trial experiments or build a new test framework.
