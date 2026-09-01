# Task Context: medical_monitoring_provenance_package_hash_refresh_20260804

Created: 2026-08-04 20:26:23
Objective: Refresh hash-bound B6 provenance package after the release coverage source hash changed, without changing authority
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_formal_reviewer_provenance_package_20260802/B6_FORMAL_REVIEWER_PROVENANCE_PACKAGE.json` — current hash-bound package.
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json` — current release coverage snapshot whose byte/hash declaration was refreshed in LOOP 5.125.
- `services/api/app/monitoring_approved_input_dry_run.py` and
  `services/api/app/monitoring_b6_reviewer_packet_revalidation.py` — consumers
  that must replay the package without inferring authority.
- `tests/test_monitoring_approved_input_dry_run.py` and
  `tests/test_monitoring_b6_reviewer_packet_revalidation.py` — regression
  evidence for blocked and synthetic-ready paths.

## Scope

- In scope: update only the release-coverage source SHA in the derived B6
  provenance package and recompute its canonical `package_sha256`; run the
  affected deterministic revalidation tests and record the discovered
  regression.
- Out of scope: B6 reviewer outcomes, C14, source-token/CAS, package content,
  authority flags, runtime/provider/browser/API/SQLite, real projects, or
  medical-writing.

## Success Criteria

- Package source-manifest replay is fresh against the current release coverage
  bytes/hash.
- Current package remains blocked by its existing B6/source/CAS blockers; a
  synthetic complete package remains diagnostic-ready but never writable.
- Focused revalidation tests pass; Hermes review-gate passes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- This is a derived evidence refresh, not a reviewer approval. No authority,
  migration, activation, or write flag may change.
- Direct Codex owns verification; no delegated agent or external provider is
  used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:26:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
