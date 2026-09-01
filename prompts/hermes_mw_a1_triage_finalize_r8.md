You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Do not read or modify shared production runtime or frozen r8 evidence.
- This is an authorized edit round, limited to the writable product/test paths
  declared in the task context.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/hermes_mw_a1_triage_finalize_r8.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/mw_a1_triage_finalize_r8_context.md`
- `records/handoffs/CODEX_NO_LOSS_PAUSE_A1_R8_20260728.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r8-20260728/slots/A1/lazy_medical_writer/DEFECTS.md`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_medical_writing_triage_recovery_api.py`
- `tests/test_medical_writing_research_pipeline_minimum_start.py`
- `tests/test_frontend_medical_writing_translation_batch_contract.py`
- `frontend/src/features/writing-reference/triagePresentationState.mjs`
- `frontend/src/features/writing-reference/triagePresentationState.test.mjs`

Do not expand beyond these files. Only the writable paths declared in the task
context may be edited.

Task:
Implement the smallest coherent fix for `MW-A1-002`.

The known architectural conflict is:
- preparation already accepts a current authoritative
  `discovery_basket_projection` before PICOS;
- translation requires `journey.corpus_triage.status == finalized`, which
  cannot occur until PICOS is complete;
- competitor Protocol/SAP translation is needed to inform PICOS;
- the visible one-click basket confirmation also leaves the parent research
  pipeline at `awaiting_triage_confirm`, forcing a redundant second action.

Requirements:
1. Reuse the preparation service's authority semantics instead of inventing a
   weaker path: prefer finalized corpus triage, otherwise accept only the
   current locked-snapshot confirmed discovery projection.
2. Apply the same effective retained scope in translation preview/create and
   frozen-lineage validation.
3. Preserve stale/wrong-snapshot/missing-confirmation failures.
4. Make the single visible bulk confirmation action advance the parent
   pipeline without a second user click, with idempotent refresh/re-entry.
5. Do not add per-candidate confirmation, override, or log-heavy UI.
6. Add focused deterministic service/API/frontend regressions and run them.
7. Record exact files changed, tests, remaining uncertainty and the browser
   recheck Codex must perform.

Output schema:
1. `# Hermes Execution Handoff: mw_a1_triage_finalize_r8`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Implementation`
5. `## Tests Run`
6. `## Failed Paths Or Uncertainty`
7. `## Codex-Owned Verification`
8. `## Next Recommended Action`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not claim browser or release acceptance.
