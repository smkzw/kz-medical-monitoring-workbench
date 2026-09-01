# Luna Read-Only Contradiction Review: v9 Runtime Preflight

## Role

Act as an independent high-risk contradiction reviewer. This is a confirmatory
read-only review, not either of the two fresh-discovery rounds and not a release
or full-Goal acceptance.

Hard boundaries:

- Do not modify any file.
- Do not open or query runtime databases.
- Do not run tests, services, providers, browsers, workers, real projects,
  retries, reuse, salvage, or candidate decisions.
- Treat the context's database observations and isolated-copy replay as
  parent-observed evidence; challenge their sufficiency and internal
  consistency against source.
- Do not stop or interact with the existing process on port 18911.
- Runner-managed output path:
  `runs/conference/monitoring_p10_v9_runtime_preflight_20260801/general_codex_luna.md`.
  Return the complete report; do not write the path.

Read these files only:

- `context/monitoring_p10_v9_runtime_preflight_20260801_context.md`
- `context/monitoring_p10_protocol_v9_cutover_direct_tests_pause_20260801.md`
- `services/api/app/main.py`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_worker.py`
- `services/api/app/monitoring_ai_contracts.py`

## Questions

1. Does source path resolution support the project-level runtime database as
   authority and the workbench-local zero-byte file as a stub?
2. Does current repository initialization/backfill plus startup retirement
   occur before any worker claim, and does the broad startup exception handler
   create a mandatory post-start gate?
3. Is the isolated WAL-consistent `.backup` replay sufficient evidence that
   current migration preserves v4-v8 status, attempts, provider failure
   evidence and candidates while permanently closing old retry surfaces?
4. Given zero queued/running jobs, is a future one-topic v9 canary safe only
   under explicit controls for the concurrent full app on port 18911? State
   whether 18911 is a blocker, a conditional residual, or irrelevant, and why.
5. Identify any P0-P4 blocker in this preflight. Keep the provider-only
   identity/SQLite-unique P2 separate unless it actually blocks the prompt
   v8-to-v9 canary.
6. Give an exact gate decision:
   - PASS for preparing a separately controlled one-topic v9 canary;
   - CONDITIONAL PASS with prerequisites; or
   - FAIL CLOSED.
   This must not be phrased as runtime, canary, release, or full-Goal
   acceptance.

## Output

- Boundary check
- P0-P4 findings with source locators
- Evidence sufficiency and no-issue scope
- Residual risks
- Exact gate decision and next safe action
