# Task Context: medical_monitoring_p9_gold_row_binding_hash_exact_20260805

Created: 2026-08-05 19:40:05
Objective: Reject normalized row-fingerprint and structured source-content hash bytes during frozen gold-case authority validation
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_gold_case_authority.py`: frozen-row source locator and row-fingerprint comparisons.
- `tests/test_monitoring_gold_case_authority.py`: frozen authority fixtures and tamper regressions.
- `services/api/app/monitoring_protocol_rules.py`: exact gold row binding contracts.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: remove lower/strip normalization from frozen-row `row_fingerprint` and structured `source_content_sha256` comparisons; add focused tamper regressions and task evidence.
- Out of scope: batch mutation, source registry writes, locator generation, rule/gold-case clinical semantics, provider/runtime/browser activation, API login, real projects and visual/commercial acceptance.

## Success Criteria

- Uppercase/padded/non-canonical row identity hashes fail closed; canonical frozen-row authority, legacy locator binding and field-value checks continue to pass.
- Focused and selected authority/protocol/shadow/readiness tests pass; targeted compilation passes; review-gate is green.
- The formal real-loop gate remains `read_only / blocked` with all activation/provider/runtime/write flags false and ports 8911/5174/8910/4173 empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 19:40:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:41:00: Codex direct source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 19:44:00: Exact frozen-row identity comparisons and focused regressions passed; selected adjacency and compilation passed. Review-gate is green, the nine-row manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
