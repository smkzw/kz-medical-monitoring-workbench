# Task Context: medical_monitoring_principal_digest_exact_20260805

Created: 2026-08-05 09:54:05
Objective: Reject non-canonical principal digests and preserve exact identity-boundary bytes in the monitoring frontend
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`
  defines the server-issued monitoring principal shape and digest boundary.
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.test.mjs`
  is the focused pure regression contract.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  define the active P9 boundary and the blocked P10 activation gate.

## Scope

- In scope: require `session_id_sha256`, `verification_ref_sha256` and optional
  `identity_hash` to be exact lowercase 64-hex SHA-256 strings; add regressions
  for uppercase and whitespace-padded values; run pure suites and the frontend
  build; record the source-only result.
- Out of scope: backend authentication or authorization, hashing or identity
  generation, runtime activation, services, ports, browser/Playwright, provider
  calls, API login, real study data, B6/C14 review or migration, medical-writing
  content, and any commercial-release claim.

## Success Criteria

- Non-canonical digest bytes are rejected rather than normalized into a valid
  principal; canonical lowercase digests continue to pass unchanged.
- Focused principal tests, all frontend medical-monitoring pure modules, Vite
  build and source syntax checks pass.
- The authoritative real-loop gate remains read-only/blocked and all reserved
  ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This patch is a frontend trust-boundary hardening only. It must not be read as
  proof of server-side authentication, authorization, or clinical correctness.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:54:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 09:55: Source review found that `digest()` accepted values after
  `trim().toLowerCase()`, so uppercase or padded claims could become a different
  accepted identity reference. The correction preserves exact incoming bytes and
  validates the canonical lowercase SHA-256 grammar without changing identity.
- 2026-08-05 09:56: Added focused regressions for uppercase and whitespace-padded
  session/verification digests; the focused principal suite passed (**17**).
- 2026-08-05 09:57: All **33** medical-monitoring frontend pure modules passed;
  Vite build passed in **1.74s** with the existing >500 kB main-chunk warning;
  `node --check` passed. No runtime, service, port, browser, provider or real
  project was started.

## Source digests at checkpoint

- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`:
  `dc66e1aa4dd27f7366236d1c199c55273306c836b467bffeffd8f947cf9fbede`
- `frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.test.mjs`:
  `e66873a72ecac7bdf11a85be59807f0f43d6626afdaeea8ff8ac807568bf054e`
