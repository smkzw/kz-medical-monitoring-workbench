# Task Context: d017_v7_independent_clinical_review

Created: 2026-07-25 00:59:04
Objective: Read-only independent clinical scientific review of all 67 frozen D017 competitor-triage records; verify 17 excluded and 50 indirect, distinguish candidate basket from automatic confirmation, and write reviews/d017_v7_independent_clinical_review_20260725.md
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/evidence/d017_competitor_triage_v7_20260725/run_response_final.json`
- `runs/evidence/d017_competitor_triage_v7_20260725/acceptance_report.json`
- `runs/evidence/d017_competitor_triage_v4_20260724/search_snapshot.json`
- `reviews/d017_v6_independent_clinical_review.md`
- `services/api/app/medical_writing_competitor_triage.py`
- Frozen local evidence only. No network refresh or substitution is permitted.

## Scope

- In scope: independent clinical-scientific review of all 67 v7 classifications;
  focused recheck of the 17 excluded and 50 indirect-reference records; explicit
  review of NCT05731050, NCT06978699, and NCT07212426; distinction between a
  reviewer candidate basket and authoritative medical-manager confirmation.
- Allowed output: `reviews/d017_v7_independent_clinical_review_20260725.md`
  plus the workflow guard's task-record surfaces.
- Out of scope: code/data changes, live ClinicalTrials.gov checks, document
  downloads, protocol/SAP full-text review, production confirmation, and basket
  projection.

## Success Criteria

- A complete 67-row NCT-level decision table with no missing or duplicate NCT.
- Independent verdicts for all 17 excluded and all 50 indirect-reference items.
- P0/P1/P2 findings, final conclusion, and residual evidence boundaries.
- Explicit statement that `review_ready`/acceptance is not automatic clinical
  confirmation and confirmation requires a separate medical-manager action.
- Final report reread and deterministic count/coverage checks pass.

## Risk Boundaries

- Do not modify source code, frozen JSON evidence, database state, or runtime.
- Do not use network evidence to replace or silently update the frozen snapshot.
- Do not infer D017 technology type, route, target/mechanism, or direct
  competitive status when those project facts are absent.
- Do not equate structural acceptance with clinical correctness.
- The report is an independent review aid; the medical manager remains the
  authority for final basket confirmation.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 00:59:04: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25: Verified v7 has 67 unique results: 17 excluded and 50
  indirect_reference; all five chunks succeeded and the run remains
  `review_ready` with no `confirmation_id`.
- 2026-07-25: Confirmed NCT05731050, NCT06978699, and NCT07212426 are reasonably
  corrected to indirect_reference.
- 2026-07-25: Identified two clinically incorrect exclusions:
  NCT02591862 (British spelling `Haemoglobinuria`) and NCT03439839 (PNH with
  active-hemolysis qualifier). Both are same-indication phase II pharmacologic
  studies and should remain reviewer candidates.
- 2026-07-25: Verified all 50 indirect-reference items contain explicit
  pharmacologic interventions and no wrong-indication item; three historical
  or supportive-treatment items remain low-priority, medical-manager decisions.
