# Task Context: medical_monitoring_p9_prompt_manifest_hash_exact_20260805

Created: 2026-08-05 19:15:58
Objective: Enforce exact lowercase prompt hashes in the offline real-loop prompt manifest without activating providers or runtime
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_prompt_manifest.py`
- `tests/test_monitoring_real_loop_prompt_manifest.py`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- `context/medical_monitoring_real_loop_gate_audit_20260804_context.md`
- Current filesystem and the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: exact lowercase prompt SHA-256 admission in the offline real-loop prompt manifest; focused regression and evidence.
- Out of scope: prompt content redesign, provider/runtime/browser activation, real-project data, production paths, and unrelated manifest fields.

## Success Criteria

- Padded/uppercase/non-canonical prompt hashes fail closed; the canonical 40-row manifest and exact UTF-8 prompt-text hash binding continue to pass.
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

- 2026-08-05 19:15:58: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:16:00: Direct Codex route selected after source inspection; no Hermes/external provider dispatch permitted by the current gate.
- 2026-08-05 19:17:00: Prompt manifest hash admission now preserves raw bytes; focused/adjacent tests and compilation passed. An initially guessed prompt-manifest replay test path was absent; the inventory-listed suites were used instead. Final review-gate is green, the 9-row manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
