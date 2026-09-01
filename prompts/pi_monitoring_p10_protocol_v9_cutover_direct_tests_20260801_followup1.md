Continue the same Pi session `019fbb21-e8e1-7000-9357-201f74004062`.
This is one consolidated acceptance follow-up, not a new exploration.

First re-read the current workspace `AGENTS.md`.

Hard boundaries:
- Work only inside the runner-provided current workspace.
- Edit only:
  - `services/api/app/monitoring_ai_contracts.py`
  - `services/api/app/monitoring_ai_repository.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Do not edit protocol preparation implementation, prompt/classifier,
  medical-writing, frontend, main startup wiring, runtime databases or real
  projects.
- Do not start services, providers, ports 8911/5174, browsers or a canary.
- Runner-managed output path:
  `runs/pi_monitoring_p10_protocol_v9_cutover_direct_tests_20260801_followup1.md`.
  Never write/edit it; return the report for the runner.

Read these files only:
- `context/monitoring_p10_protocol_v9_cutover_direct_tests_20260801_context.md`
- `services/api/app/monitoring_ai_contracts.py`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`

Accepted pre-follow-up hashes:
- `monitoring_ai_contracts.py`:
  `9ee43b88a2de3e8779d4622a43b077f61c3e747fe0c476bc847cfe43b285cf30`
- `monitoring_ai_repository.py`:
  `dd550fea87787466519103f9afdbe054847d8729e7dd3f7dba25e2db73034e1d`
- `test_monitoring_ai_repository.py`:
  `5461d3d7363a71bab888b3e9a803f042f9c8f9d6464e09938c2f44f3b85d61fa`
- `test_monitoring_protocol_preparation.py`:
  `03da5abd4c1a993ad0873c668dc2297fe4c9fc37f4ab87dc4330be61eb8a9c7b`

Stop and report if any hash differs.

Acceptance defect:
Luna proved the first fix is incomplete. Preserved failed legacy jobs keep
their provider `failure_code`, so they remain retryable. Already-stale obsolete
jobs are skipped by supersession queries and can later be restored/requeued.

Implement the selected minimal durable route:

1. Add immutable/auditable one-to-one retirement metadata to the jobs schema and
   `MonitoringAiJob`:
   - `contract_retirement_code`
   - `contract_retirement_reason`
   - `contract_retired_at`
   Use backwards-compatible SQLite migration defaults.
2. All three supersession operations must mark every obsolete row, including
   preserved completed/failed legacy and already-stale rows. Preserve existing
   status, failure code/message, candidate transitions and changed-count
   semantics. Retain the first retirement marker if already set.
3. `retry_terminal()` must fail closed on the durable retirement marker, not on
   mutable provider failure text. Remove obsolete failure-code-only guard logic.
4. Add regression coverage for:
   - failed v8 preserved with original provider evidence but non-retryable;
   - completed old prompt → `mark_stale` → prompt cutover → old-revision retry,
     candidate remains superseded;
   - `stale_claimed` followed by workflow, prompt and job supersession;
   - representative protocol and non-protocol task types;
   - at least one queued/running v8 using the exact production prepared business
     key before `service.start()`;
   - deterministic service submission returning a permanently retired identity
     fails loudly and does not revive it.
5. Preserve ordinary revision-stale retry and completed-candidate restoration
   where no contract retirement occurred.

Work test-first for the new P1 cases. Keep the implementation repository-generic
and dependency-free.

Run only:
- compile both edited implementation modules;
- `python3 -m pytest -q tests/test_monitoring_ai_repository.py
  tests/test_monitoring_protocol_preparation.py`.

Return exact changes/hashes, pre-fix P1 reproduction, test results, failed
paths, remaining uncertainty and Codex recheck targets. Do not claim runtime or
canary acceptance.

Output schema:
1. `# Pi Follow-up: monitoring_p10_protocol_v9_cutover_direct_tests_20260801`
2. `## Boundary Check`
3. `## P1 Reproduction`
4. `## Files Changed`
5. `## Durable Retirement Implementation`
6. `## Verification`
7. `## Failed Paths And Uncertainty`
8. `## Codex Recheck Targets`
