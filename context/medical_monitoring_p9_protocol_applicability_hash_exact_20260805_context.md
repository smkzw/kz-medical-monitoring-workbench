# Task Context: medical_monitoring_p9_protocol_applicability_hash_exact_20260805

Created: 2026-08-05 11:14:02
Objective: Harden protocol applicability evidence source hashes so identity bytes are exact lowercase SHA-256 values at factory and persisted-read boundaries
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`: `ProtocolApplicabilityAssignment.create()` evidence source digest admission.
- `services/api/app/monitoring_protocol_rule_repository.py`: persisted applicability-assignment reconstruction.
- `tests/test_monitoring_protocol_rule_repository_hardening.py` and adjacent protocol suites.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: require `evidence_source_content_sha256` to be an exact lowercase 64-hex SHA-256 string at factory and persisted-read boundaries; add focused shape/tamper regressions.
- Out of scope: protocol applicability interpretation, overlap/CAS semantics, clinical rule content, provider/runtime/browser activation, real projects, dependency installation and paths outside this workspace.

## Success Criteria

- Padded, uppercase and non-string applicability evidence digests are rejected without normalization.
- Persisted assignment digest tampering fails closed on read.
- Focused and adjacent protocol/daily-run tests pass; source compiles; review-gate passes.
- No services/providers/browsers/real projects or dependency activation while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:14:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:16:00: Codex direct route selected; no external Hermes/provider dispatch. Hardened applicability evidence digest admission and added factory/persisted tamper regressions.
