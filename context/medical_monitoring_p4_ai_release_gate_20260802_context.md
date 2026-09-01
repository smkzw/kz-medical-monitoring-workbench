# Phase F P4 AI release-gate — context checkpoint

Date: 2026-08-02 07:51 CST  
State: **offline evidence contract complete; runtime integration blocked**

## Source of truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` §40.3 and §40.5;
- `services/api/app/monitoring_ai_quality.py` immutable quality observations;
- `services/api/app/monitoring_ai_evaluation_matrix.py` real/unseen matrix;
- `services/api/app/monitoring_ai_release.py` prompt/model release snapshots;
- B6 `B6_REVIEW_OUTCOME_GATE.json` and C13 blocked activation report.

## Completed

- Added `monitoring_ai_release_gate.py` and its eight-test focused suite.
- The gate joins matrix coverage, per-observation human review, citation/locator review,
  six failure modes, five deterministic fallback surfaces and prompt/model approval.
- Gate output is immutable and hashable. `ready_for_controlled_activation` is only a
  controlled evidence status; runtime activation, provider calls and writes remain false.
- `.venv` AI regression: 631 passed; shared assurance/frontend/timeline contracts: 80 passed;
  pycompile, Ruff check and format check passed.

## Not done / blocked

- No real three-project or unseen-project product-AI observations, citation science review,
  runtime telemetry, rollback rehearsal, browser acceptance or UAT.
- B6 remains `pending_review`, 5 candidates/0 outcomes/2 blockers; C13 remains schema-only and
  `activation_allowed=false`.
- 8911/5174 must remain stopped; 18911/PID 43191 is unrelated and must not be touched.

## Parallel-change observation

During the final filesystem check, a group of `medical_writing_*`, `chapter_translation_pipeline.py`,
`workbench_inbox.py`, `workbench_notifications.py` and `writing_reference*` sources shared a new
mtime of **2026-08-02 07:47:25 CST**. They are outside this slice and were not opened for semantic
review, edited, reformatted, or included in the monitoring hashes; treat them as parallel user work
until their owner provides a separate handoff.

## Next safe action

Keep this gate offline until an authorized reviewer supplies hash-bound outcomes for all five B6
candidates, append-only disposition chains are replayed into the aggregate, and MY009 legacy source
revision tokens are revalidated. Then re-read current files and decide whether an approved-input
in-memory dry-run is authorized. Do not connect this contract to runtime or provider before that gate.
