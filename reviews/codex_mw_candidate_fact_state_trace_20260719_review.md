# Codex Review: mw_candidate_fact_state_trace_20260719

Date: 2026-07-19
Delegated-agent output: `runs/codex_mw_candidate_fact_state_trace_20260719.md`

## Verdict

PASS for the backend candidate-fact-state and persistence slice. This verdict
does not promote the frontend or stable runtime.

## Boundary Check

- Qoder performed read-only source review and wrote only the requested reports
  under `records/qoder_full_system_audit_20260719/`.
- Codex production edits were limited to the revision contracts, revision
  service/repository, SQLite revision-action persistence and focused tests.
- No clinical content, stable runtime database, DOCX exporter or frontend file
  was changed by this slice.

## Codex Verification

- Confirmed candidates are created as `candidate_only`.
- Confirmed source types derive only from evidence spans actually cited by the
  candidate.
- Confirmed ACCEPT records
  `medical_manager_explicit_selection` and does not change protocol text.
- Confirmed application writes a new working-copy revision in `AI_DRAFT`.
- Confirmed legacy JSON is normalized on both sides of optimistic concurrency.
- Added persistence-boundary model reconstruction because
  `WorkbenchModel` does not enable assignment validation.
- Final focused suite: `30 passed`; Ruff: pass.
- Final full suite:
  `532 passed in 159.19s`.

## Delegated-Agent Output Review

- Qoder correctly identified the original traceability gap and the absence of a
  second same-role approval requirement.
- Codex corrected Qoder's initial field-name and audit-shape mismatches.
- Qoder later corrected its assignment-validation claim.
- Qoder's statement that `model_dump()` itself reruns validators was not
  accepted. The final implementation explicitly revalidates at the write
  boundary, and the negative test proves inconsistent state is not persisted.
- Qoder's two P3 rewrite-union test observations are closed.

## Hermes Routing

Hermes was not dispatched for this bounded backend patch review because the
user's current route makes QoderCLI PID 39908 the first-priority complex-task
executor/reviewer. The guard requirement is satisfied by recording that routing
decision explicitly; Codex performed the final source and test acceptance.

## Residual Risk

- Frontend state labels and candidate-selection interactions are not accepted
  by this backend review.
- Stable `8911/5174` is intentionally not restarted until the parallel frontend
  task completes, preventing runtime fingerprint drift during its isolated
  tests.
