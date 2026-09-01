# Task Context: medical_monitoring_phase_b4_residual_decision_20260801

Created: 2026-08-01 23:25:54
Objective: Assemble a source-grounded residual decision package for the five review-only risk identity mappings, comparing legacy/current source-version lineage and disposition chains without approving or writing any mapping.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- B2 report `runs/execution/medical_monitoring_phase_b2_reconciliation_20260801/ACTUAL_CLONE_RECONCILIATION.json`.
- B3 report `runs/execution/medical_monitoring_phase_b3_mapping_dryrun_20260801/MAPPING_REVIEW_AND_DRYRUN.json`.
- A6 isolated clone databases, read-only, and current stable source-version helper semantics.
- `services/api/app/medical_risk_authority.py`, `medical_risk_reconciliation.py`, and `medical_risk_mapping.py`.

## Scope

- In scope: source-grounded residual package for five mapping candidates; parse legacy/current source tokens, compare risk-meaning tokens, summarize disposition chains and aggregate replay requirements; keep approval/write flags explicit.
- Out of scope: approval, migration, runtime writes, schema changes, dual-read promotion, service startup, frontend, real-project execution, or medical-writing changes.

## Success Criteria

- Every candidate has source lineage evidence and a clear residual decision status.
- Source revision changes are not treated as harmless; equal meaning token and changed source token remain a revalidation requirement.
- Disposition chains are shown in order and aggregate state is marked replay-required instead of overwritten.
- Package is deterministic, JSON-safe, linked to B2/B3 hashes, and independently reviewable.

## Risk Boundaries

- Only task-scoped evidence/review/metrics/context and a read-only analysis script may change.
- No runtime database, schema, service, router, frontend, or medical-writing file may be changed.
- No mapping may be marked approved; no service may start; frozen v9-v12 remain untouched.
- Medical identity and disposition meaning require explicit review; source-token comparison is evidence, not a clinical decision.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:25:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:27: B3 dry-run leaves three MY009 source-version mismatches and one aggregate-state drift; B4 will package evidence without approval.
- 2026-08-01 23:31: Built `B4_RESIDUAL_DECISION_PACKAGE.json` from read-only clone and B2/B3 evidence. Five decisions remain unapproved; RUX has exact-after-identity source versions; MY009 uses legacy meaning-only source-version format without a source token and needs revalidation; the latest submitted state requires append-only replay.
- 2026-08-01 23:31: Package is deterministic, all flags remain non-writing, and static checks passed. No service or runtime DB was touched.

## Closure And Next Safe Action

- B4 residual decision package is complete; it does not approve a mapping or authorize migration.
- Next safe action is to obtain/record explicit review outcomes for the five candidates and residual blockers, then rerun the package/dry-run with an approved mapping input. Until then, keep runtime stores unchanged and services stopped.
