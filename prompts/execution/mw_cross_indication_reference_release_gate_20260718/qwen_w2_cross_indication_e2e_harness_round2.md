# Qwen W2 Cross-Indication E2E Harness Round 2

Continue the same qwen3.7-plus session. Your previous report claimed four harness files and 34 passing tests, but Codex verified that none of those source files exists. Only the report exists. That pass is rejected.

Read the current source and actually implement the bounded frontend/test work. Source and test edits are authorized changes and are not the runner's single output report. The "exactly one output file" rule below means one final execution report, not zero implementation files.

## Read these files only as the initial context

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/CROSS_INDICATION_E2E_MATRIX.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/quality_scorecard.schema.json`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/SOURCE_GOLDEN_FACTS.md`
- `frontend/tests/medical_writing_new_project_isolated_qc.mjs`
- `frontend/tests/medical_writing_soa_section_isolated_qc.mjs`
- `frontend/tests/medical_writing_reference_progress_journey_qc.mjs`
- `frontend/src/features/writing-reference/progressJourneyLogic.mjs`
- `frontend/src/features/writing-reference/WritingReferenceProgressJourney.jsx`
- `services/api/app/main.py`

## Required implementation files

Create and save these real files:

1. `frontend/tests/cross_indication_e2e_config.mjs`
2. `frontend/tests/cross_indication_e2e_parent.mjs`
3. `frontend/tests/cross_indication_e2e_child.mjs`
4. `frontend/tests/cross_indication_e2e_harness_structure_qc.mjs`

The implementation contract is unchanged from Round 1:

- AD phase 2, PNH phase 3 and obesity phase 2.
- Random API/Vite ports and a separate temporary runtime/project per indication.
- Production AI environment inherited.
- Stable 5174/8911 runtime SQLite/files hashed before and after.
- Product new-project flow, fresh ClinicalTrials.gov search and official document
  rediscovery; never register the local probe PDFs as product inputs.
- Product-visible controls for user actions where available; API only for
  assertions or operations without a UI control.
- Explicit gates for search, triage, basket lock, download, content validation,
  extraction/OCR, structure review, Flash planning, Hy-MT2 translation, Flash
  integration QC, medical review, corpus admission, chapter mapping, product
  DeepSeek Pro candidate generation and DOCX export.
- Every unavailable stage fails with a stable explicit gate code; no stage is
  silently skipped or marked passed.
- Emit the fixed JSON artifacts, screenshots and logs specified by
  `CROSS_INDICATION_E2E_MATRIX.md`.
- Candidate generation must produce 3-5 versions for at least two chapters per
  indication and prove the working-copy hash/revision is unchanged before the
  user explicitly accepts one.
- Preserve all comparator symbols and source facts in `SOURCE_GOLDEN_FACTS.md`.
- Browser checks at 1920x1080 and 1600x1000 include active, failed/retry and
  completed progress states, page errors, failed HTTP responses, horizontal
  overflow, `aria-busy` and keyboard actions.
- Do not modify backend production source, stable runtime, credentials or real
  clinical source files.

The child may terminate at the first unavailable backend gate during current
development, but it must already contain executable implementations for all
later steps rather than placeholder comments or invented endpoint names. Verify
each endpoint against current `main.py` and each selector against current
frontend source.

Run:

`node frontend/tests/cross_indication_e2e_harness_structure_qc.mjs`

Also run `node --check` on all four files. Do not claim a test count unless the
terminal output proves it.

Before reporting, use `ls -l` and reread all four files to prove they are on
disk. The report must include exact byte sizes and test output.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/qwen_w2_cross_indication_e2e_harness_round2.md`

The report must list changed files, exact commands/results, unresolved live
dependencies and a compact loop trace. Do not claim live E2E or final visual
acceptance.
