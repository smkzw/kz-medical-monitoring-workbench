# Task Context: medical_monitoring_approved_input_dry_run_20260802

Created: 2026-08-02 19:42:58
Objective: Build and verify a pure read-only approved-input dry-run contract for the current formal B6 reviewer/provenance package; current package must fail closed without reviewer/source-token/CAS completion
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_formal_reviewer_provenance_package_20260802/B6_FORMAL_REVIEWER_PROVENANCE_PACKAGE.json`
- `services/api/app/medical_risk_mapping_review.py` for existing fail-closed
  review/approved-input semantics
- `services/api/app/monitoring_source_revision_compatibility.py` and
  `services/api/app/monitoring_aggregate_cas_replay.py` for source/CAS evidence
- `tests/test_medical_risk_mapping_review.py`, source compatibility, aggregate
  replay, release and B6 activation tests

## Scope

- In scope: add a pure Python dry-run contract that consumes the formal package,
  verifies its canonical package hash and an explicit read-only source-manifest
  observation, and reports whether reviewer, source-lineage, residual-blocker
  and aggregate/CAS prerequisites are complete.
- Out of scope: filling reviewer outcomes, source-token synthesis, aggregate
  writes, migration, C14 activation, runtime/API/provider/browser/service
  execution, real projects or product/medical-writing changes.

## Success Criteria

- Current package produces `status=blocked`, `approved_input_ready=false`,
  `write_permitted=false`, `migration_ready=false` with explicit issue codes.
- A complete synthetic package can pass all diagnostic prerequisites while still
  never granting write or migration authority.
- Missing source-manifest observations, package tampering and true authority
  flags fail closed; focused and adjacent tests pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 19:42:58: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 19:43–19:50: Implemented pure `monitoring_approved_input_dry_run.py`
  and five tests. No external route or runtime was started.
- Current formal package replay: source manifest 11/11 verified; dry-run is
  blocked with 14 issues (B6 not ready, 5 reviewer sets missing, 3 MY009
  lineage gaps, 3 residual-blocker rows and 2 CAS cases incomplete).
- Evidence artifact:
  `records/active_slices/medical_monitoring_approved_input_dry_run_20260802/APPROVED_INPUT_DRY_RUN.json`
  report SHA `1b28c3658448dd72002f5ce9307b91b28fc7c318eac22f94ccd7483c3ff88cd2`;
  refreshed artifact SHA `a9d19fc9af3d10b35d84b635bb24ab97991497e256619d217b45fc6bac56a87d`.
