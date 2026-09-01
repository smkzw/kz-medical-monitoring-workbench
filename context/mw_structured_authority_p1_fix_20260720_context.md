# Task Context: mw_structured_authority_p1_fix_20260720

Created: 2026-07-20 14:37:47
Objective: Fix three reproduced medical-writing P1 defects: omit interim-analysis headings when planned=false, materialize active-comparator IP regimen authority, and materialize background-treatment non-IP BACKGROUND authority, with deterministic projections and isolated DOCX regression.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: guard defaulted to Codex. Per the user's project routing,
implementation is delegated to a fresh Hermes/aishuo/cms-model execution
worker; QoderVIP/Qwen3.8-Max-Preview will perform a later manager review in a
new session because its current autonomy task is unrelated. Codex remains final
authority.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `plans/codex_mw_structured_authority_p0_20260720.md`
- `reviews/codex_execution_mw_release_execution_round2_20260720_review.md`
- `runs/execution/mw_final_release_12lane_e2e_20260720/hy3/followup_01.md`
- `runs/execution/mw_final_release_12lane_e2e_20260720/hy3/artifacts/structured_authority_evidence.json`
- The two retained Hy3 DOCX artifacts and current source/tests.

## Scope

- In scope: omit interim-analysis headings/content when planned=false;
  materialize active-comparator IP regimen and background-treatment non-IP
  BACKGROUND authority in the normal prefill/adoption/commit path; preserve
  deterministic legacy projections; focused backend/OOXML tests.
- Out of scope: frontend duplicate-field cleanup, independent-AI competitor
  triage, 12-lane harness, stable runtime and real project data.

## Success Criteria

1. Phase I `planned=false` DOCX has zero `期中分析` headings/body/summary rows.
2. Phase III active comparator persists an IP regimen with
   `product_role=active_comparator`; dose/route/frequency/duration are not an
   independent truth in structured study design or comparator free text.
3. Background treatment persists as a non-IP `rule_class=background` rule;
   ordinary CM and IP dose adjustment remain distinct.
4. Structured authority projects legacy fields deterministically without
   overwriting unrelated confirmed values.
5. Existing legacy payloads remain loadable; migration is deterministic.
6. Focused/adjacent tests and isolated DOCX assertions pass; stable runtime
   hashes remain unchanged.

## Risk Boundaries

- Writable product paths are limited by the worker assignment.
- Do not infer comparator regimen details from generic investigational-product
  `intervention_dose_regimen`.
- Optional structured candidates may carry explicit comparator regimen fields;
  when absent, preserve missing details explicitly.
- Preserve legacy background strings losslessly and do not infer a stronger
  treatment policy than the source supports.
- Never project CM dose changes into IP adjustment rules.
- Do not modify stable runtime, user originals, credentials, frontend, harness,
  or the runner-managed report.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 14:37:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-20: Direct Hy3 API/OOXML failures were converted into this bounded
  implementation contract. All three targets are P1.
