# Conference Context: eligibility_visual_qc_v15_20260712

Created: 2026-07-12
Objective: Review the bounded desktop visual-QC workspace, controlled artifact serving, immutable QC action, and processing-unit reconciliation for D001/MY009 eligibility evidence.
Risk: high

## Active Route

- Codex is main-venue chair and final authority.
- The user requires all future Hermes sub-venue review/synthesis/chair work to use exact `aishuo/MiniMax-M3`.
- This bounded review dispatches only `aishuo/MiniMax-M3`; no silent fallback and no other generated role is active.
- Provider/model/completion markers must be verified from stdout and metrics.

## Source Of Truth

- `services/api/app/eligibility_visual_qc_service.py`
- `services/api/app/eligibility.py`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/eligibility_artifact_store.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/AGENTS.md`
- `tests/test_eligibility_visual_qc_service.py`
- `tests/test_eligibility_source_processing_units.py`
- `tests/test_eligibility_evidence_task_api.py`
- `tests/test_frontend_button_contract.py`
- `records/active_slices/eligibility_next_slice_20260711/REAL_SIX_SUBJECT_EXTRACTION_V14.md`
- `records/active_slices/eligibility_next_slice_20260711/IMPLEMENTATION_LOOP_LOG.md`

## Scope

In scope:

- project/subject/artifact authorization and integrity-verified source-image serving;
- current-source/extraction/evidence binding and fail-closed packet construction;
- immutable visual-QC CAS/idempotency behavior;
- processing-unit close/reopen reconciliation after QC state changes;
- global status filtering, pagination, stale-request suppression and desktop interaction semantics;
- Chinese clinical-trial labels and explicit boundary that visual QC is not eligibility judgment or randomization release;
- test gaps, race conditions, cross-project contamination and privacy leakage.

Out of scope:

- reading original clinical folders, OCR bodies, rendered screenshots or controlled artifact bytes;
- web browsing, browser control, visual acceptance, source edits or production writes;
- making a medical eligibility decision;
- VLM processing or independent semantic AI review of clinical content;
- resolving the remaining DOC/DOCX and archive units.

## Current Evidence

- Isolated runtime: two real projects, six real subjects, 293 evidence spans; all remain `needs_visual_qc/not_reviewed` before human action.
- Codex rebuilt and integrity-read all 293 visual-QC packets: 293/293 passed; no OCR text was emitted by the verification command.
- Chrome read-only QC covered D001 SA07005 (35 packets) and MY009 S01009 (63 packets), including 50+13 pagination, global status filters, rapid filter switching, 100% image zoom, result/reason coupling, 1600x1000 and 2048x1024 layouts. No real QC record was submitted.
- Backend focused tests passed 24/24 after the latest filter, current-source and reconciliation work; Ruff passed.
- Frontend production build passed with the pre-existing >500 kB chunk warning.
- Final backend regression passed 602/602 in 205.49 seconds.
- Exact `aishuo/MiniMax-M3` same-session review and postfix completed without fallback. The review reproduced one stale-source artifact-serving P1; Codex fixed it, added route-level close/reopen coverage, and the postfix found no remaining bounded P0/P1.

## Success Criteria

- Identify every reproducible P0/P1 defect in the bounded source.
- Distinguish defects from accepted open gates and legacy compatibility behavior.
- Verify that no path can treat OCR completion alone as visual-QC pass or eligibility judgment.
- Verify a later failed/manual QC revision reopens its processing unit.
- Verify filtered/paginated queue state cannot be overwritten by a stale request.
- Return concrete file/logic references and narrow corrections; do not overclaim browser or clinical authority.

## Risk Boundaries

- Do not expose or request raw OCR text, images, source paths, identifiers beyond fixture IDs already in tests, full hashes or storage keys.
- Do not recommend bulk auto-pass or a VLM substitute for human visual QC.
- Do not reinterpret `manual_review_required` as pass.
- Do not call the subsystem complete: DOC/DOCX and archive processing plus independent AI review remain open.

## Loop Log

- Backend packet and filter tests passed.
- Codex browser QC reproduced and fixed one stale-filter response race.
- The sub-venue task closed as a bounded source review, not implementation authority. Codex review gate passed and the temporary Hermes session was exported and archived.
