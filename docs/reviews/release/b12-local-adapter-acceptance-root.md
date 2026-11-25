# B12 local adapter acceptance

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers accept the final local repair.
I accept the 41-file freeze b12-final-local-repair-freeze-claude.sha256.
Its hash is efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b.
The measured suites pass: 65 harness, 29 isolation, 25 packaging, 8 skill-package and 11 project-I/O checks.

This acceptance covers local stubs, the measured filesystem and network boundary, baseline refusal and child timeout behavior.
It does not establish authenticated host behavior, credential preservation or model evaluation results.
Temporary HOME applies only to local stubs and installation tests.
No real-HOME mount or authenticated route has acceptance.
The Codex baseline remains refused until its skill set is established.

Artifact fixtures, source retrieval and integrated skill artifacts remain open.
The accepted provider matrix does not authorize dispatch yet. Provider authorization remains zero.
No commit, merge or push occurs through this record.
