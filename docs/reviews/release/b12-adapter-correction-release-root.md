# B12 local adapter correction release

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers agree with C-1 to C-7. I release the narrow local correction.
Use the Codex review and the Pi correction and conflict records.

Remove Codex flags that ignore rules or configuration.
Remove the explicit workspace-write permission override. Record the host default as unmeasured where necessary.
Keep skills enabled for skill runs.
The Claude baseline can use --disable-slash-commands only in the declared baseline mode.
Record that this flag disables commands as well as skills.
A Codex baseline with unmeasured user skills cannot claim an empty skill set.
Refuse that baseline for measured evaluation until its skill set is established.

The current batch runs local stubs only.
Keep the temporary HOME for those credential-free stub tests and the local installation tests.
Do not mount the real HOME or expose credentials to make a stub test pass.
Host command construction must not override HOME or ignore host configuration.
The authenticated host route is not established by a stub test.
Record credential and configuration preservation as unmeasured for that future route.
There is no authorization for a provider call.

Record full safe argv, flags, probe errors, exits and hashes.
Use an owned outside control file.
Test the network namespace interfaces and a local listener with no external endpoint.
For the child timeout, first prove that the child writes ticks before the timeout.
Then prove that the tick file stops after termination. Record the observation interval and the stop reason.
Do not claim that an unchanged empty file proves child termination.
Keep one attempt and no automatic retry.

Run the affected local tests and freeze one complete replacement.
Preserve the earlier freeze and the separate packaging acceptance.
Do not merge, commit or push before acceptance.
