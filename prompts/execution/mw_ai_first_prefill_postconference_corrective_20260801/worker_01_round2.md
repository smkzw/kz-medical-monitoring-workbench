Continue the same `worker_01` session. Codex reviewed the current files and rejects one
interpretation in your report.

The current execution context is explicit and authoritative: the single-candidate endpoint
must reject every candidate whose `recommendation_role == "pending_decision"` or
`adoption_mode == "manual_only"`, as well as every server-derived pending candidate,
regardless of whether it currently has evidence bindings. Do not retain the unbound
deterministic-scaffold exception. Historical tests asserting that exception describe obsolete
behavior and must be updated to use the existing composite override/skip path or to expect a
no-mutation conflict, whichever matches their actual intent. Do not add an override flag to
the single endpoint.

Make only this correction and its focused test changes. Preserve all successful catalog
identity, live verifier, and endpoint-helper work from round 1. Re-read shared files before
editing. Run the impacted structured-design, single-gate, journey, composite, and catalog
tests plus the same focused suite. Return the complete worker report schema again, clearly
separating round-2 changes, exact tests, and current hashes.
