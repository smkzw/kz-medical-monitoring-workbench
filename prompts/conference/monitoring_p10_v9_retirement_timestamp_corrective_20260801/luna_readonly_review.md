Continue the existing native Luna session for one bounded read-only review.

Hard boundaries:
- Work only inside the current workbench workspace.
- Do not modify any file.
- Do not open runtime databases, start services, providers, tests, browsers,
  projects, ports, workers, candidates, retries or reuse.
- Parent-recorded commands/results are secondary evidence; challenge them
  against source and tests.
- Runner-managed output path:
  `runs/conference/monitoring_p10_v9_retirement_timestamp_corrective_20260801/general_codex_luna.md`.
  Return the complete report; do not write the path.

Read these files only:
- `context/monitoring_p10_v9_retirement_timestamp_corrective_20260801_context.md`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT1_ZERO_SUBMIT_GATE.md`
- `runs/pi_monitoring_p10_v9_retirement_timestamp_corrective_20260801.md`
- `services/api/app/monitoring_ai_repository.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`

Task:
Independently review the timestamp-preservation corrective and report P0-P4
findings with exact source/test locators.

Challenge:

1. Whether removing `updated_at` from the marker-only UPDATE preserves terminal
   and already-stale audit timestamps without allowing active queued/running
   rows to retain a misleading pre-retirement timestamp.
2. Whether `retired_ids` is always a subset of `job_ids` across prompt,
   workflow and business-key supersession, and whether the second UPDATE still
   covers every actual status transition.
3. Whether first-marker immutability, retry refusal, provider failure evidence,
   candidates, input-only compatibility and pre-marker backfill remain intact.
4. Whether the three new tests sufficiently prove the intended distinction or
   whether a direct workflow/job-code timestamp assertion is a blocker before
   attempt 2.
5. Whether the parent-observed real-snapshot fingerprint replay is sufficient
   to close the concrete 12-row startup defect.
6. Give an exact gate decision for **attempt-2 zero-submit preparation only**.
   Do not claim canary, provider, runtime, release or full-Goal acceptance.

Parent-recorded verification:
- compile pass;
- repository/protocol/API `86 passed`;
- full monitoring excluding one known unrelated writing collection file
  `1413 passed, 4301 deselected, 27 warnings`;
- adjacent sample `142 passed, 17 warnings`;
- real-snapshot replay fingerprints exactly equal before/after, integrity ok,
  `3 job + 9 prompt`, zero unmarked/active/v9.

Output schema:
1. `# Luna Review: v9 Retirement Timestamp Corrective`
2. `## Boundary Check`
3. `## P0-P4 Findings`
4. `## Evidence And No-Issue Scope`
5. `## Residual Risk`
6. `## Gate Decision And Next Action`
