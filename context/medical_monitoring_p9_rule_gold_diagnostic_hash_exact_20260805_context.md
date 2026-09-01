# Task Context: medical_monitoring_p9_rule_gold_diagnostic_hash_exact_20260805

Created: 2026-08-05 10:59:01
Objective: Harden protocol gold/diagnostic evidence case source hashes so lineage bytes are exact lowercase SHA-256 values without changing shadow/release semantics
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`: RuleGoldStandardCase and RuleDiagnosticCase factories and immutable case IDs.
- `services/api/app/monitoring_protocol_rule_repository.py`: release-binding checks and persisted gold/diagnostic case reconstruction.
- `tests/test_monitoring_protocol_rules.py`: factory boundary regressions.
- `tests/test_monitoring_protocol_rule_repository_hardening.py`: SQLite persistence tamper regressions.
- The current real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked; it is a boundary, not an implementation target.

## Scope

- In scope: require `source_content_sha256` on gold-standard and diagnostic evidence cases to be an exact lowercase 64-hex SHA-256 string at factory and release-binding boundaries; fail closed on persisted shape tampering; add focused regressions.
- Out of scope: shadow-run case-set algorithms, clinical rule semantics, protocol data, runtime/provider/browser activation, real-project E2E, dependency installation, and production paths outside this workspace.

## Success Criteria

- Padded, uppercase, and non-string case source digests are rejected without normalization.
- Release binding and persisted reconstruction do not accept non-canonical case digests or locator mismatches.
- Focused rule/repository/lifecycle tests pass; source compiles; review-gate passes.
- No service, provider, browser, real-project, or dependency activation occurs while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:59:01: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:00:51: Codex direct route selected; no external Hermes/provider dispatch. Added strict case digest validation at factories and release bindings plus persisted SQLite tamper regression coverage.
