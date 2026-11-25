# Via construction implementation

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The existing corner and via decision remains the authority.
The lead will measure via spans from captured board bytes in the locked local image before the supplier reads design results.
The B6 worker remains unchanged.

A blind or buried span can prevent the design inventory from completing.
For that case, the supplier command will return exit 1 and a refused precondition report.
The report will contain the failed `service.via_construction_prohibited` row and the captured source hashes.
It will not claim a complete supplier result or write a success binding.
Thus the command can name the supplier prohibition before the generic inventory refusal hides it.

For supported through spans, the supplier will continue the existing measurements.
Its complete result will include the mandatory `service.via_construction_prohibited` row.
The row will bind the board declaration and the measured spans.
Missing or unconfirmed declarations remain pending. A declared prohibited process fails.
A board without vias passes this condition as not applicable, with the measured zero count.
An unknown declaration refuses as an invalid input with exit 2.

The new worker will read a private copy of the captured board. It will not change the source.
The existing publication gate and input freshness checks remain unchanged.
The owned positive test projects will declare `standard_through` explicitly.
The new negative tests will remove or change that declaration and exercise prohibited spans.
