# Task Context: medical_monitoring_p9_signal_revalidation_hash_exact_20260805

Created: 2026-08-05 18:53:45
Objective: Enforce exact lowercase SHA-256 bytes for signal-lifecycle artifact revalidation inputs while preserving read-only fail-closed authority
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_signal_lifecycle_revalidation.py`
- `tests/test_monitoring_signal_lifecycle_revalidation.py`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- `context/medical_monitoring_real_loop_gate_audit_20260804_context.md`
- Current filesystem and the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: exact validation of the persisted signal-lifecycle artifact expected SHA-256 input; focused regression and evidence.
- Out of scope: provider/runtime/browser activation, real-project data, medical approval, production paths, and unrelated monitoring or medical-writing modules.

## Success Criteria

- Padded expected SHA-256 values are rejected before artifact comparison; canonical lowercase exact values continue to pass.
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

- 2026-08-05 18:53:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 18:54:00: Direct Codex route selected after source inspection; no Hermes/external provider dispatch permitted by the current gate.
- 2026-08-05 18:55:00: `_valid_sha` was changed to exact lowercase 64-hex matching; focused/adjacent tests and compilation passed. Task-scoped review, metrics, record and manifest were written; final review-gate is green, the manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
