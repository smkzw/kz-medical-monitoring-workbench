# Task Context: medical_monitoring_p9_rule_source_hash_exact_20260805

Created: 2026-08-05 11:17:48
Objective: Harden persisted monitoring rule source_text_sha256 validation so canonical source lineage bytes cannot be normalized on read
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py`: persisted rule reconstruction and source hash comparison.
- `services/api/app/monitoring_protocol_rules.py`: canonical rule source hash factory semantics.
- `tests/test_monitoring_protocol_rule_repository_hardening.py` and adjacent rule/protocol/shadow suites.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: make persisted `MonitoringRuleDefinition.source_text_sha256` validation exact lowercase 64-hex without normalization; add focused persisted shape regressions.
- Out of scope: rule clinical semantics, source-reference creation, protocol applicability, provider/runtime/browser activation, real projects, dependency installation and paths outside this workspace.

## Success Criteria

- Padded, uppercase and non-string persisted rule source hashes fail closed rather than being normalized.
- Valid canonical source hashes continue to load and identity checks remain stable.
- Focused and adjacent suites pass; source compiles; review-gate passes.
- No services/providers/browsers/real projects or dependency activation while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:17:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:20:00: Codex direct route selected; no external Hermes/provider dispatch. Replaced persisted rule source hash normalization with exact raw-byte validation and added SQLite shape regressions.
