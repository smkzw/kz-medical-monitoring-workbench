# Task Context: medical_monitoring_p9_shared_fact_hash_exact_20260805

Created: 2026-08-05 19:48:36
Objective: Make shared protocol-fact source hash shape checks exact lowercase without normalizing invalid persisted identities
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/shared_protocol_fact_projection.py`: read-only monitoring protocol-fact adapter and source revision digest shape predicate.
- `tests/test_shared_protocol_fact_projection.py` and `tests/test_shared_protocol_fact_projection_api.py`: projection, consumer allowlist and DTO boundary tests.
- `services/api/app/monitoring_protocol_rules.py`: canonical protocol source version digest contract used by the adapter.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: exact lowercase source digest shape checking in the shared protocol-fact projection adapter; focused malformed-hash predicate regressions and task evidence.
- Out of scope: protocol fact semantics, adapter writes, DTO design, provider/runtime/browser activation, API login, real projects, clinical/scientific/visual/commercial acceptance and unrelated hashes.

## Success Criteria

- Padded, uppercase and non-string source digests are rejected by the projection boundary rather than normalized; valid confirmed projections and consumer isolation continue to pass.
- Focused and selected shared-projection/protocol/readiness tests pass; targeted compilation passes; review-gate is green.
- The formal real-loop gate remains `read_only / blocked` with all activation/provider/runtime/write flags false and ports 8911/5174/8910/4173 empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 19:48:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:49:00: Codex direct source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 19:54:00: Strict raw digest validation implemented; focused, selected, and compile checks passed. No service/provider/browser/real-project path was activated.
- 2026-08-05 19:54:00: Durable checkpoint and LOOP ledger updated; final exact-byte manifest is `records/active_slices/medical_monitoring_p9_shared_fact_hash_exact_20260805/CHANGE_MANIFEST.md` (manifest excludes itself).
