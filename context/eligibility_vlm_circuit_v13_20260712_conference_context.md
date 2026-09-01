# Conference Context: eligibility_vlm_circuit_v13_20260712

Created: 2026-07-12
Objective: Review the bounded SQLite v13 durable multi-process VLM circuit, worker admission accounting, migration safety, and remaining production gates without authorizing clinical images or a production VLM profile.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: participant passes followed by required sub-venue chair and independent main-venue review.

## Codex Main Venue

- Chair and final authority: Codex.
- Codex owns source boundaries, tests, production writes, and final acceptance.
- Hermes sub-venue chair: exact provider/model `aishuo / MiniMax-M3`.
- Independent high-risk main review: Reasonix CLI `deepseek-pro`.
- DeepSeek V4 must not run through Hermes, OpenCode Go, buddy, or direct DeepSeek.

## Source Of Truth

- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/vlm_gateway.py`
- `services/api/app/eligibility_evidence_worker.py`
- `tests/test_vlm_durable_circuit.py`
- `tests/test_eligibility_vlm_runtime.py`
- `records/active_slices/eligibility_next_slice_20260711/VLM_DURABLE_CIRCUIT_V13.md`
- `records/active_slices/eligibility_next_slice_20260711/IMPLEMENTATION_LOOP_LOG.md`

## Scope

In scope:
- SQLite v13 migration and circuit table integrity.
- Exact profile isolation, wall-clock/restart behavior, rolling samples, permits, replay protection and half-open concurrency.
- Worker admission ordering, provider-attempt accounting and open-circuit deferral.
- Whether the bounded implementation has a reproducible P0/P1 defect.
- Canonical remaining production gates.

Out of scope:
- Real clinical images or real subject data.
- Production model/profile approval or capability probing.
- Opening public VLM APIs.
- Authentication/RBAC/tenant implementation.
- Visual QC approval, evidence spans or medical decisions.
- Web, browser, visual, PPT or PDF acceptance.

## Verification Evidence

- Ruff passed on changed Python files.
- Focused durable-circuit/VLM-worker suite passed 38/38.
- Authoritative backend regression passed 551/551 in 207.602 seconds.
- Frontend production build passed with the existing chunk warning.
- No non-temporary v13 database existed during migration development.
- No real clinical image was processed.

## Success Criteria

- Every material finding cites exact source/test evidence.
- Closed release gates are not misclassified as implemented behavior.
- Any P0/P1 is reproduced or supported by a concrete execution path.
- The required chair route is verified from stdout markers with no silent fallback.
- Codex review and metrics contain no placeholders and pass review-gate.

## Risk Boundaries

- Production remains fail-closed.
- No participant may edit source, run tests, browse, or process images.
- Outputs are advisory; Codex remains final authority.

