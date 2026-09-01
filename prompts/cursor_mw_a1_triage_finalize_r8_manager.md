You are Cursor CLI running as the execution manager for a bounded finite-code
repair. Read and comply with the workspace `AGENTS.md`. Cursor CLI is separate
from Hermes, Codex and the product's independent AI.

Task id: `mw_a1_triage_finalize_r8`
Provider/model: `cursor-cli` / `auto`

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Read the files listed below before judging the worker result.
- You may make only bounded remediation edits to the product/test files listed
  below. Do not touch frozen r8 evidence, shared runtime, credentials, corpus
  content, clinical classifications, or unrelated UI.
- Do not start a browser E2E round and do not claim release acceptance.
- Runner-managed output path:
  `runs/cursor_mw_a1_triage_finalize_r8_manager.md`. Never invoke a write/edit
  tool on this report path; return the complete report in your final response
  and let the runner persist it.

Read these files only:
- `AGENTS.md`
- `context/mw_a1_triage_finalize_r8_context.md`
- `records/handoffs/CODEX_NO_LOSS_PAUSE_A1_R8_20260728.md`
- `runs/hermes_mw_a1_triage_finalize_r8.md`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/triagePresentationState.mjs`
- `frontend/src/features/writing-reference/triagePresentationState.test.mjs`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_medical_writing_triage_recovery_api.py`
- `tests/test_medical_writing_research_pipeline_minimum_start.py`
- `tests/test_frontend_medical_writing_translation_batch_contract.py`

Writable remediation scope:
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- the four focused test files and triage presentation test listed above.

Objective:
Review the Hermes worker's repair of `MW-A1-002`, perform bounded remediation
if needed, and return an evidence-backed execution-manager report.

Manager checks:
1. Verify translation has one effective retained-candidate authority:
   post-PICOS finalized corpus triage is preferred; otherwise only a confirmed
   discovery projection for the current locked snapshot is accepted.
2. Verify preview/create and frozen-lineage checks use the identical authority
   and continue to reject missing confirmation, stale snapshot, wrong latest
   snapshot, and mismatched preparation scope.
3. Verify the single bulk confirmation action advances the parent pipeline
   without reconfirming each candidate or requiring a second user click.
4. Analyze durable job idempotency and state transitions in detail:
   business key, request hash, repeat click, reload, concurrent confirm,
   queued/running/failure, and whether showing `preparing` can falsely imply a
   worker actually started.
5. Verify no duplicate download/extraction work is introduced.
6. Prefer behavioral tests. Treat source-string tests as supporting evidence
   only and add/repair behavioral coverage if a material branch is otherwise
   unproved.
7. Reproduce the focused suites. Investigate the worker's two broader failures
   enough to determine whether they are caused by this patch, a stable missing
   environment, or an actual product regression. Do not waive them by assertion.
8. Keep the user-facing flow AI-first and batch-oriented; do not add log-heavy
   status or per-item approval.

If the worker needs a same-session follow-up rather than manager remediation,
write one precise consolidated rerun request. Otherwise make the smallest
authorized fix and run the decisive tests.

Return exactly this report schema:
# Execution Output: mw_a1_triage_finalize_r8_manager
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

Codex owns final conflict/risk review, real browser acceptance, new clean round,
clinical judgment and release status.
