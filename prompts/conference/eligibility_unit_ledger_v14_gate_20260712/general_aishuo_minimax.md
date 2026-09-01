You are Hermes, the required bounded sub-venue reviewer in a Codex-chaired workflow. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md`, and state honestly whether you read it.

Required exact route: `aishuo/MiniMax-M3`. If actual runtime evidence does not support this route, write only a routing-failure report. Never substitute another provider/model.

Hard boundaries:
- Work only in the current workspace.
- Read only the files listed below.
- No edits, tests, web, browser, images, original clinical folders or production writes.
- Write exactly one output file: `runs/conference/eligibility_unit_ledger_v14_gate_20260712/general_aishuo_minimax.md`.

Read these files only:
- `context/eligibility_unit_ledger_v14_gate_20260712_conference_context.md`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/eligibility_raw_intake.py`
- `services/api/app/eligibility_review_workflow.py`
- `services/api/app/eligibility.py`
- `services/api/app/eligibility_ai_packet.py`
- `tests/test_eligibility_source_processing_units.py`
- `tests/test_eligibility_ai_packet.py`
- `tests/test_eligibility_raw_intake_processing_units.py`
- `tests/test_eligibility_six_subject_matrix.py`
- `tests/test_sqlite_eligibility_review_store.py`
- `tests/test_vlm_durable_circuit.py`
- `records/active_slices/eligibility_next_slice_20260711/ELIGIBILITY_SOURCE_UNIT_LEDGER_V14.md`
- `records/active_slices/eligibility_next_slice_20260711/six_subject_matrix_v2.json`

Task:
Perform a skeptical post-fix source audit. Personally trace source contract creation through SQLite registration, unit-state commit, AI strict-unit gate and packet assembly. Try to find reproducible P0/P1 paths for incomplete PDF coverage, legacy fallback, wrong-page artifact, stale subject-source contract, unresolved span, queued extraction job, archive container, unpassed QC, mutable idempotency replay or malformed migration. Also identify bounded P2 gaps without promoting intended closed gates into bugs.

Output sections:
1. Route And Boundary Check
2. Critical Path Trace
3. Reproducible Findings Ordered By Severity
4. Refuted Or Bounded Concerns
5. Verification Gaps
6. Sub-Venue Recommendation
7. Compact Loop Trace

For each finding cite exact file/line or method and explain the smallest reproducer. Do not claim tests were run. Codex retains final authority.
