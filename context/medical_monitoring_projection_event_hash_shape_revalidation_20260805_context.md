# Task Context: medical_monitoring_projection_event_hash_shape_revalidation_20260805

Created: 2026-08-05 07:45:57
Objective: Harden optional declared SHA-256 read-boundaries in clinical event and projection contracts without changing missing-hash compatibility
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_clinical_event_contract.py`
- `services/api/app/monitoring_clinical_projection_contract.py`
- `tests/test_monitoring_clinical_event_contract.py`
- `tests/test_monitoring_clinical_projection_contract.py`
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 shape checks for declared hashes at the
  event/projection read boundaries, while preserving the existing optional
  omission behavior used by older payloads; focused and adjacent source-only
  regressions.
- Out of scope: changing producer digest generation, requiring hashes that are
  currently optional, clinical inference, API/provider/browser activation,
  real projects, medical-writing data, B6/C14 or release claims.

## Success Criteria

- When a declared digest is present, non-string, padded, uppercase, malformed,
  or mismatched values fail closed without normalization.
- Missing/empty optional declarations retain current compatibility and are
  recomputed from canonical content.
- Focused and adjacent Python tests pass; compile check passes; no service,
  port, provider, browser, API login, or real-project activity occurs.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.
- Do not weaken canonical digest generation or alter missing-hash compatibility.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:45:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 07:46:xx: Reconnaissance found optional `str(...).strip()` hash
  declarations in the event, scope, context and read-model `from_dict` paths;
  the bounded slice will validate only non-empty declarations without changing
  omission semantics.
- 2026-08-05: Added exact lowercase validators for optional event/projection
  declarations and required projection event digests; added malformed-shape,
  omission and empty-string regressions. The existing consumer test was
  updated to assert the earlier projection boundary now rejects an uppercase
  digest before handoff assembly.
- 2026-08-05: Verification: focused event/projection **51 passed**; adjacent
  consumer/adapter/onboarding/identity/runtime suite **108 passed**; compileall
  passed; all reserved ports empty; Ruff unavailable; no runtime/provider/
  browser/real-project activity.
