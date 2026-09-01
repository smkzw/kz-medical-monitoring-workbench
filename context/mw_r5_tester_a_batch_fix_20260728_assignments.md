# Tester A Batch Repair Assignments

## Source of truth

- `runs/execution/mw_final_4x3_harness_20260727/reviews/TESTER_A_CONSOLIDATED_20260728.md`
- Frozen failed evidence under `rounds/release-r5-20260727/slots/A1`, `A2`, and `A3`
- Current source and focused tests in this workspace

## Shared constraints

- Do not edit frozen `release-r5` evidence.
- Do not restart or mutate the stable product runtime on ports 8911/5174.
- Do not broaden into security or infrastructure audits.
- Preserve unrelated local changes; this workspace is not Git.
- Add focused tests for every changed contract and return exact commands/results.
- Product independent AI remains responsible for medical generation; deterministic code may normalize contracts, state, provenance, and clinically established terminology only.

## Worker A3

Write scope:

- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`
- `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.test.jsx`
- New focused frontend test files only when necessary

Goal:

- Serialize PICOS list-valued paths consistently instead of sending textarea strings.
- Make all-explicitly-skipped pending packages adoptable and auditable without making unresolved fields adoptable.
- Preserve scalar fields and user-entered text after validation errors.

## Worker A2

Write scope:

- `frontend/src/features/medical-writing/MedicalWritingSynopsisProjectIntake.jsx`
- Focused frontend tests for that component
- `frontend/src/App.jsx` only for the synopsis-dialog close boundary

Goal:

- Bound each poll/cancel/resume request, surface terminal failed/recoverable/cancelled states, and release busy state.
- Let users close or cancel a wedged intake without losing the durable job.
- Re-uploading the same failed file must present retry/resume rather than an infinite spinner.

## Worker A1

Write scope:

- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/writing_reference.py` only if required for large-document lineage
- Focused Python tests for these files

Goal:

- Establish deterministic Chinese/English COPD equivalence without fuzzy disease overmatching.
- Preserve CT.gov public Protocol/SAP lineage from search candidate to triage.
- Reconcile `review_ready` triage with a parent pipeline that previously stopped waiting.
- Do not claim or redesign preparation scope until a per-NCT manifest proves retained/excluded membership.

## Codex acceptance

Codex reviews only conflicts, contract changes, clinical overmatching risk, and regression evidence. Accepted changes are exercised together in a new repair round; the frozen failed round remains unchanged.
