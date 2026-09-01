# Task Context: medical_monitoring_phase_b3_mapping_dryrun_20260801

Created: 2026-08-01 23:20:18
Objective: Produce a deterministic, non-writing legacy-to-current medical risk identity mapping review and in-memory dry-run for the five disposition mismatches found in the isolated clone; preserve explicit approval gates and residual source/version/state blockers.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- B2 report: `runs/execution/medical_monitoring_phase_b2_reconciliation_20260801/ACTUAL_CLONE_RECONCILIATION.json`.
- `services/api/app/medical_risk_authority.py` and `services/api/app/medical_risk_reconciliation.py`.
- A6 task-owned clone risk/disposition databases opened read-only only.
- Existing `RiskCase` and `RuxRiskDispositionRecord` contracts; no runtime store writes.

## Scope

- In scope: deterministic candidate mapping from each of the five B2 identity mismatches to the latest current risk row; explicit basis/confidence/review flags; in-memory remap dry-run through the B2 reconciler; focused tests and evidence.
- Out of scope: approval of mappings, database mutation, schema migration, dual-write, router/frontend changes, real-project execution, or medical-writing changes.

## Success Criteria

- Every B2 mismatch has zero or one deterministic candidate based only on stable legacy risk_id/risk_key/project evidence.
- Candidate mappings are marked `approved=false`, `write_permitted=false`, and require medical/engineering review.
- In-memory remap never mutates original Pydantic records and exposes residual source-version/chain/state issues.
- Output is deterministic, JSON-safe and independently reviewable; focused and existing risk tests pass.

## Risk Boundaries

- Only source/test files inside this workbench plus task-scoped context/review/metrics/evidence records may change.
- Do not modify runtime databases, `sqlite_runtime_store.py`, migration versions, frontend, or medical-writing files.
- Do not start 8911/5174 or touch 18911; frozen v9-v12 jobs remain untouched.
- Mapping candidates are not accepted medical identity decisions; no record may be rewritten in this slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 23:20:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 23:20: B2 produced five identity mismatches; B3 will only derive candidates and run an in-memory remap, preserving approval and write boundaries.
- 2026-08-01 23:24: Added review-only mapping candidates and in-memory remap. All five actual clone records received unique high-confidence exact-risk-id candidates, but all remain unapproved.
- 2026-08-01 23:24: Dry-run result: 2 dispositions match after identity remap; 3 MY009 source-version mismatches and 1 aggregate-state drift remain. Focused 4 and combined 112 tests passed; static checks passed.

## Closure And Next Safe Action

- B3 candidate mapping/dry-run is complete; this does not authorize any migration or identity decision.
- Next safe action is a review-only residual decision package: verify the three MY009 source-version lineage records and the RUX instance replacement against source snapshots, then rerun the dry-run with an explicitly approved mapping file.
- Until that review produces explicit approval, do not dual-read promote, write a mapping, migrate schema, start services, or delete/alter legacy records.
