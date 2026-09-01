# Task Context: medical_monitoring_p9_gold_locator_hash_exact_20260805

Created: 2026-08-05 19:35:41
Objective: Reject uppercase hash bytes embedded in canonical gold-case row locators without altering frozen-row authority semantics
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_gold_case_authority.py`: canonical row-locator parsing and frozen-source authority checks.
- `tests/test_monitoring_gold_case_authority.py`: locator/source authority regressions and `_canonical_row_locator` tests.
- `tests/test_monitoring_protocol_rules.py` and `services/api/app/monitoring_protocol_rules.py`: exact source-locator contracts used by gold/diagnostic cases.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: require lowercase hex in hashes embedded in canonical `listing:<hash>:sheet:<sheet>:row:<row>` locators; add a focused regression and task evidence.
- Out of scope: frozen batch/source authority, legacy locator migration, rule/gold-case clinical semantics, provider/runtime/browser activation, API login, real projects and visual/commercial acceptance.

## Success Criteria

- Uppercase canonical-locator hash bytes fail closed; valid lowercase locators, structured locator agreement and legacy locator binding continue to pass.
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

- 2026-08-05 19:35:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:36:00: Codex direct source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 19:40:00: Exact canonical-locator hash comparison and focused regression passed; selected adjacency and compilation passed. Review-gate is green, the nine-row manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
