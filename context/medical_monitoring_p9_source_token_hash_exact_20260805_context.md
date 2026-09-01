# Task Context: medical_monitoring_p9_source_token_hash_exact_20260805

Created: 2026-08-05 18:57:21
Objective: Enforce exact lowercase SHA-256 bytes across read-only source-token evidence revalidation while preserving not-proven and fail-closed semantics
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_source_token_evidence_revalidation.py`
- `tests/test_monitoring_source_token_evidence_revalidation.py`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- `context/medical_monitoring_real_loop_gate_audit_20260804_context.md`
- Current filesystem and the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: exact validation of source-token artifact and inventory expected SHA-256 inputs; focused regression and evidence.
- Out of scope: source-token discovery/rescan, token synthesis, CAS or B6 activation, provider/runtime/browser activation, real-project data, production paths, and unrelated modules.

## Success Criteria

- Artifact, source-inventory and archive-inventory expected hashes reject padding/non-canonical bytes; canonical lowercase values continue to pass.
- Focused and adjacent tests pass; targeted compilation passes; review-gate is green.
- The formal real-loop gate remains blocked/read-only with all activation/provider/runtime/write flags false and ports 8911/5174/8910/4173 empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 18:57:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 18:58:00: Direct Codex route selected after source inspection; no Hermes/external provider dispatch permitted by the current gate.
- 2026-08-05 18:59:00: `_valid_sha` and all three file-level expected hashes were tightened to exact lowercase 64-hex bytes; focused/adjacent tests and compilation passed. A guessed content-revalidation test path was absent; the inventory-listed source-token and real-loop suites were used instead.
