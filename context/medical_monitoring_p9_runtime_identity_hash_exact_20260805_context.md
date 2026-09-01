# Task Context: medical_monitoring_p9_runtime_identity_hash_exact_20260805

Created: 2026-08-05 11:43:49
Objective: Harden runtime identity evidence hash admission and report preservation so evidence, principal and attestation digests remain exact lowercase SHA-256 bytes
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_runtime_identity_evidence_revalidation.py`: persisted runtime-identity evidence revalidator and read-only report contract.
- `tests/test_monitoring_runtime_identity_evidence_revalidation.py` plus readiness, upstream-assembly and authorization adjacency suites.
- The active real-loop gate at `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked.

## Scope

- In scope: require exact raw lowercase 64-hex evidence, principal-identity and attestation digests; preserve canonical values in diagnostic reports while invalid inputs remain blocked.
- Out of scope: authentication, attestation execution, provider/runtime activation, authority flags, real projects, dependency installation, and medical-writing paths.

## Success Criteria

- Uppercase, padded and non-string identity evidence hashes produce fail-closed diagnostics rather than normalization or accidental verification.
- Valid canonical not-proven/proven observations keep existing status and all authority flags false.
- Focused and adjacent suites pass; changed modules compile; preflight and review-gate pass.
- No services/providers/browsers/real projects or dependency activation while the gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 11:43:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 11:44-11:47: Codex direct route selected; no external Hermes/provider dispatch. Removed identity evidence `.strip().lower()` admission and report normalization; added fail-closed regressions.
- 2026-08-05 11:47: Focused runtime identity suite **8 passed**; runtime identity/readiness/upstream adjacency **56 passed**; release evidence/gate/dossier adjacency **35 passed**; identity authorization/route adjacency **22 passed**.
- 2026-08-05 11:47: Gate remains `read_only / blocked`; authority flags remain false and ports 8911/5174/8910/4173 remain empty.
