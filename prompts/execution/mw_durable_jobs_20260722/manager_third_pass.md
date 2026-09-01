Continue the same `mw_durable_jobs_20260722` execution-manager session as a read-only current-source integration reviewer. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md` as the workflow operating record, global/project `AGENTS.md`, `/Users/smkzw/.grok/SOUL.md` if available to the native route, the execution context, and the reports listed below.

Hard boundaries:
- Read and test the current workspace only. Do not edit production source, tests, prompts, records, or the runner-managed report.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/manager_third_pass.md`; return the complete report in final text.
- Codex remains final authority. Do not claim browser E4, product-AI E3, DOCX E5, launch, or final acceptance.

Read initially:
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `runs/execution/mw_durable_jobs_20260722/manager_second_pass.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01_followup_shutdown_release_02.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01_followup_attempt_semantics_03.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01_followup_finalize_race_04.md`
- `runs/execution/mw_durable_jobs_20260722/worker_02_followup_integrity_03.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_integration_02.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_concurrency_tests_03.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w3_remediation.md`
- `runs/execution/mw_durable_jobs_20260722/worker_04_followup_integrity_04.md`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/sqlite_runtime_store.py`
- `prompts/execution/mw_durable_jobs_20260722/worker_05.md`

Gate first. Require all exact markers:
- `WORKER_01_GRACEFUL_RELEASE_V3_COMPLETE`
- `WORKER_02_TRIAGE_INTEGRITY_V3_COMPLETE`
- `MANAGER_W3_REMEDIATION_COMPLETE`
- `WORKER_04_TRANSLATION_INTEGRITY_V4_COMPLETE`
If absent, return `MANAGER_THIRD_PASS_BLOCKED` without inventing completion.

Review current source, not report claims. Verify:
1. One shared durable core remains authoritative; graceful shutdown only releases exact live claims, permits immediate restart, does not consume an extra retry attempt, and late old owners cannot write.
2. Every adapter is reconstructable after process restart and does not depend on request-local provider/service objects.
3. Every business write after a long external/product-AI step is preceded by exception-safe fail-closed ownership proof. Cancel, heartbeat failure/exception, lease expiry and takeover leave no old-owner business artifact.
4. Section AI executor can route distinct project IDs to distinct services through one registered job-type executor.
5. Candidate accept+apply remains one SQLite `BEGIN IMMEDIATE` transaction for paragraph and table-cell anchors, including table identity/rich-text/CAS/idempotency/fault rollback. No production two-step escape hatch remains necessary.
6. Retry/live-running conflicts, startup recovery, project isolation, source DOCX immutability, plan/freeze/quarantine guards and independent product-AI routing remain intact.
7. W5 prompt is implementation-ready and requires safe public DTOs, worker wake, project service routing, complete atomic adoption and current markers.

Run the combined deterministic W1-W4 test matrix, including durable core, triage, revision durable/API/application, and translation durable tests. Report exact counts and any collection limitations. Findings must be ordered P0/P1/P2 with source locations, owner and concrete remediation.

Return `MANAGER_THIRD_PASS_READY_FOR_W5` only if no P0/P1 blocks W5 composition. Otherwise return `MANAGER_THIRD_PASS_BLOCKED` and the exact blocker. Include a compact loop trace and do not edit files.
