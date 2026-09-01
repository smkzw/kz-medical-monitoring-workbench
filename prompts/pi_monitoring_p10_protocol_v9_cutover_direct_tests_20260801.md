You are Pi running inside a Codex-controlled finite-code workflow.

First, fully read and comply with the current workspace `AGENTS.md`. State that
you read it fully only if you actually did.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Edit only:
  - `services/api/app/monitoring_ai_repository.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Do not touch prompts/classifiers, protocol preparation implementation,
  medical-writing, frontend, runtime databases or real-project material.
- Do not start services, product/provider calls, ports 8911/5174, browsers,
  real projects or a canary.
- Preserve all current filesystem changes; do not restore baseline files.
- Runner-managed output path:
  `runs/pi_monitoring_p10_protocol_v9_cutover_direct_tests_20260801.md`.
  Never write/edit that path; return the report for the runner to persist.

Read these files only:
- `context/monitoring_p10_protocol_v9_cutover_direct_tests_20260801_context.md`
- `context/monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_pause_20260801.md`
- `runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`

Verify the three frozen hashes in the task context before editing. Stop and
report if any differs.

Task:
Close the exact P2 cutover proof gap in the task context. Work test-first:

1. Add focused repository coverage proving every contract-superseded failure
   code (`superseded_workflow_contract`, `superseded_prompt_contract`,
   `superseded_job_contract`) cannot be revived by `retry_terminal`, while
   ordinary same-revision stale-input retry and candidate restoration remain
   unchanged.
2. Add one decisive protocol v8→v9 execution-level test using the same input
   revision. It must cover completed and failed v8 preservation; queued and
   running v8 retirement; frozen v8 attempts; late running-v8 completion losing
   CAS and persisting zero candidates; no v8 claim/retry/reuse; and creation,
   selection and claim/completion of a distinct v9 job.
3. If and only if the first new test demonstrates a retry escape, make the
   smallest repository-generic correction. Do not special-case protocol v8/v9.

Run only:
- Python compilation for any edited implementation file.
- `python3 -m pytest -q tests/test_monitoring_ai_repository.py
  tests/test_monitoring_protocol_preparation.py`.

Return exact changed files/hashes, the pre-fix reproduction, tests/results,
failed paths, uncertainty and Codex-owned rechecks. Do not claim runtime/canary
or final release acceptance.

Output schema:
1. `# Pi Execution: monitoring_p10_protocol_v9_cutover_direct_tests_20260801`
2. `## Boundary Check`
3. `## Pre-Fix Reproduction`
4. `## Files Changed`
5. `## Implementation`
6. `## Verification`
7. `## Failed Paths And Uncertainty`
8. `## Codex Recheck Targets`
