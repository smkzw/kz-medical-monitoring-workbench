# Task Context: medical_monitoring_candidate_source_identity_20260803

Created: 2026-08-03 03:21:34
Objective: Add a read-only fail-closed candidate project source identity revalidation contract for the five user-supplied monitoring projects; verify current protocol/listing bytes and identity boundaries without promotion, runtime, provider, browser, or medical authority.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` and
  `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`.
- Current P10 ledger/traceability and B6/C14 gates under
  `records/active_slices/medical_monitoring_goal_p10_20260730/` and
  `runs/execution/medical_monitoring_phase_{b6_review_gate_20260801,c14_b6_activation_gate_20260802}/`.
- User candidate matrix:
  `records/active_slices/medical_monitoring_candidate_matrix_20260802/CANDIDATE_MATRIX.json`.
- The five declared protocol/listing file pairs recorded in the active slice
  artifact; the source files are read-only and remain outside the workbench.

## Scope

- In scope: a generic pure Python contract that reopens declared protocol and
  listing paths, checks direct-file bytes/SHA-256, detects duplicate content and
  project/adapter/alias identity drift, and reports mapping/source/full-snapshot
  blockers for the five requested projects.
- Out of scope: source registry or SQLite writes, adapter registration, prompt
  manifest changes, B6/C14 changes, provider/runtime/browser work, clinical
  decisions, and all medical-writing surfaces.

## Success Criteria

- Focused tests cover valid replay, missing/tampered/symlink/duplicate files,
  candidate mapping/source blockers and non-monitoring alias reuse.
- Current five file pairs replay with exact byte/SHA agreement, while the
  report remains explicitly `blocked` for unresolved admission conditions.
- Artifact replay reproduces the canonical report digest and all authority flags
  remain false; no listener appears on 8911/5174 and protected frontend hashes
  remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never promote `proj_my008_3_01_candidate` or `proj_my008_3_02_candidate` into
  the current three-project executable set, and never reuse the non-monitoring
  `proj_my008_pnh_3_01` identity for monitoring.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 03:21:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Added the pure identity revalidation contract and focused tests;
  replayed all five current protocol/listing pairs with 10/10 exact byte/SHA
  matches, persisted the blocked 13-issue report, ran 1750 monitoring tests,
  and passed the Hermes review-gate.  No runtime/provider/browser or product
  authority was exercised.
