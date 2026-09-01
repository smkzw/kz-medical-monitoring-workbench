# Codex review — source-batch five-project alignment — 2026-08-03

## Verdict

**Pass for the bounded contract change; blocked for real-source admission.**

## Boundary check

- Changed production code only in the read-only source-preflight constant and
  the directly affected synthetic assertion.
- The approved-input default was verified to inherit the constant; it was not
  duplicated or broadened elsewhere.
- Historical real-source, B6, C14, CAS, source-token and readiness artifacts
  were read only. No runtime, browser, provider, API login, project import,
  SQLite/risk/disposition write or source promotion occurred.

## Verification

- Five-project source/preflight/approved-input/readiness/execution regression:
  47 passed.
- Ruff check and Python compileall passed.
- Workflow prompt preflight passed after removing the absolute workspace path.
- Current persisted source artifact revalidation is explicitly blocked by
  `source_policy_mismatch` and `project_set_mismatch`; the stale historical
  three-project envelope was not rewritten.
- Listener check: 8911, 5174, 8910 and 4173 were all empty.

## Evidence review

The synthetic fixtures now exercise two explicit rows for each of the five
canonical projects. This proves contract coverage only; it is not evidence
that any real project has two eligible full batches. Current source evidence
still has zero eligible counts for every canonical project, and the approved
input source-binding record remains `approved_input_ready=false`.

## Residual risk and next action

The five-project real LOOP cannot be launched. Formal B6 outcomes are still
absent (`pending_review`, zero accepted review IDs), and the B6 contract still
requires append-only disposition replay plus legacy source-revision-token
revalidation. C14 remains blocked with 46/46 rows blocked. The next safe
authority-bearing action is a newly hash-bound five-project source manifest
after those blockers are resolved; only then may controlled runtime and
Playwright/scientific/UAT be reconsidered.

Hermes review-gate is requested for this bounded slice; Codex remains final
authority.
