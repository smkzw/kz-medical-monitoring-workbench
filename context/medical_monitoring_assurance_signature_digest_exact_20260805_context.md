# Task Context: medical_monitoring_assurance_signature_digest_exact_20260805

Created: 2026-08-05 10:03:15
Objective: Reject non-canonical assurance audit signature evidence digests without downstream normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py`,
  `MonitoringAssuranceAuditContext.__post_init__`.
- `tests/test_monitoring_assurance.py` and adjacent assurance/identity/runtime
  route contracts.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  for the active P9 boundary and blocked P10 gate.

## Scope

- In scope: preserve optional empty signature evidence, but require any
  non-empty `signature_evidence_sha256` passed into the assurance write context
  to be an exact lowercase 64-hex SHA-256 string; add direct context negative
  regressions and run assurance adjacency/compile checks.
- Out of scope: authentication or e-signature verification, provider/runtime/
  browser/API login/real-project activity, schema migration, medical-writing
  data, B6/C14 review, release activation or clinical/commercial claims.

## Success Criteria

- Padded, uppercase, malformed and non-string non-empty signature evidence is
  rejected without `str()`, trim or case normalization; empty/absent optional
  evidence retains current behavior.
- Assurance and identity/runtime adjacency tests, compileall and review-gate
  pass; reserved ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The signature value remains only a contract token; this slice does not verify
  an external electronic signature or create medical approval.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:03:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 10:04: Source audit found `MonitoringAssuranceAuditContext` used
  `str(...).strip().lower()` for optional signature evidence, allowing
  non-canonical bytes to become a different digest at the downstream write
  boundary.
- 2026-08-05 10:05: Replaced normalization with exact raw-string validation;
  added four direct context negative regressions. Focused signature subset:
  **4 passed**; assurance/identity/runtime adjacency: **134 passed** in 1.99s.
  Compileall passed; Ruff is unavailable. No runtime, service, port, browser,
  provider or real project was started.

## Source digests at checkpoint

- `services/api/app/monitoring_assurance_repository.py`:
  `c4cc4cb8276d3dc64d16c8a3337eed325709974798573c6921425987c511f099`
- `tests/test_monitoring_assurance.py`:
  `5d72107c04dbb395a8a00a5bc08a6f935370de71ebb72de2489fba4cb20ffa96`
