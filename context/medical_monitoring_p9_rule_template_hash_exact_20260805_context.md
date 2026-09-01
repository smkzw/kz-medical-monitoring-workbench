# Task Context: medical_monitoring_p9_rule_template_hash_exact_20260805

Created: 2026-08-05 19:25:26
Objective: Reject padded or uppercase rule-template recommendation input revision hashes at the direct service boundary and preserve deterministic decision semantics
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_rule_template_recommendation_service.py`: direct decision-boundary comparison of the expected input-revision digest.
- `services/api/app/monitoring_rule_template_recommendation_router.py`: external request shape and canonical digest pattern.
- `tests/test_monitoring_rule_template_recommendation.py`: deterministic recommendation/decision regressions and test doubles.
- `services/api/app/monitoring_ai_service.py` and `services/api/app/monitoring_ai_contracts.py`: existing exact SHA-256 boundary conventions.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: remove direct-service normalization of `expected_input_revision_sha256`; add focused padded/uppercase regressions; update task-scoped evidence.
- Out of scope: recommendation semantics, mapping/capability policy, AI provider/runtime/browser activation, API login, real projects, clinical/scientific/visual acceptance, and unrelated hash fields.

## Success Criteria

- Padded and uppercase direct-service expected input-revision hashes fail closed while canonical decisions, idempotent replay and router validation continue to pass.
- Focused and selected adjacent tests pass; targeted compilation passes; review-gate is green.
- The formal real-loop gate remains `read_only / blocked` with all activation/provider/runtime/write flags false and ports 8911/5174/8910/4173 empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 19:25:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:26:00: Direct Codex route selected after source inspection; external provider dispatch is prohibited by the current formal gate.
- 2026-08-05 19:33:00: Raw direct-service digest comparison and focused regression passed; selected adjacency and compilation passed. Review-gate is green, the nine-row manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
