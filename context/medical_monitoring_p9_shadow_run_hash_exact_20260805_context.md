# Task Context: medical_monitoring_p9_shadow_run_hash_exact_20260805

Created: 2026-08-05 11:06:41
Objective: Harden RuleShadowRun and provisional sample/confirmation frozen digests so identity bytes are exact lowercase SHA-256 values without changing shadow acceptance semantics
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`: `RuleShadowRun.create()` and frozen snapshot digest fields.
- `services/api/app/monitoring_protocol_rule_repository.py`: persisted shadow-run reconstruction and identity checks.
- `tests/test_monitoring_protocol_rules.py`, `tests/test_monitoring_protocol_rule_repository_hardening.py`, `tests/test_monitoring_gold_shadow_p7c.py` and `tests/test_monitoring_rule_lifecycle.py`.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: make gold and diagnostic case-set digests exact lowercase 64-hex values at `RuleShadowRun.create()` and make the shared provisional sample-set/medical-confirmation `_optional_sha256` boundary exact; ensure persisted shadow-run snapshot tampering fails closed; add focused regressions.
- Out of scope: shadow evaluation semantics, clinical rule interpretation, provider/runtime/browser activation, real projects, dependency installation and paths outside this workspace.

## Success Criteria

- Padded, uppercase and non-string gold/diagnostic case-set digests are rejected without normalization.
- Persisted case-set, diagnostic-set, diagnostic-result and coverage digest tampering cannot be read as a valid shadow run.
- Focused shadow/repository/lifecycle tests and adjacent suites pass; source compiles; review-gate passes.
- No services, providers, browsers, real projects or dependency activation while the gate is blocked.
- Provisional sample-set and confirmation factories reject padded, uppercase and non-string non-empty hashes without normalization; omitted optional hashes retain existing empty semantics.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:06:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:07:30: Codex direct route selected; no external Hermes/provider dispatch. Hardened RuleShadowRun case-set digest admission and added persisted snapshot hash tamper coverage.
- 2026-08-05 11:11:00: Extended the same exact-byte boundary to `_optional_sha256` used by `ShadowProvisionalSampleSet` and `ShadowSampleMedicalConfirmation`; added factory regressions. Persisted sample/confirmation readers were already strict and remain unchanged.
