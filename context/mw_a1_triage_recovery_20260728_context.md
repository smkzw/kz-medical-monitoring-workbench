# Task Context: mw_a1_triage_recovery_20260728

Created: 2026-07-28 08:50:02
Objective: 修复医学写作 A1 分诊超时后的幂等续跑、真实状态和前端重试，并完成确定性与浏览器复测
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r6-20260728/slots/A1/lazy_medical_writer/EXTERNAL_TESTER_REPORT.md`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r6-20260728/DEFECTS.md`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r6-20260728/FIX_RETEST_LEDGER.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- Focused backend/frontend tests under `tests/` and `frontend/tests/`.

## Scope

- In scope: parent pipeline timeout/failure projection; retry of the same frozen
  triage run and snapshot; pending/failed-only chunk replay; preservation of
  succeeded chunks; user-visible failure, progress, and one-click retry;
  deterministic and real-browser recovery verification.
- Out of scope: A2/A3 scenario changes; corpus/PICOS/DOCX feature redesign;
  mutation of immutable `release-r6-20260728` evidence; treating the stable
  8911/5174 runtime as post-fix evidence before restart; restarting search or
  replacing the locked competitor snapshot/basket.

## Success Criteria

- A triage timeout leaves the parent in a truthful retryable failed state.
- One idempotent product action resumes the same `triage_run_id` and
  `snapshot_id`, replays only non-succeeded chunks, and preserves successful
  chunk payloads/provenance byte-for-byte.
- Repeated retry with the same idempotency key does not duplicate work.
- Once that run reaches `review_ready`, status reconciliation promotes the
  parent to `awaiting_triage_confirm` without starting preparation.
- The browser shows terminal failure, real chunk progress, and a single clear
  retry action instead of an indefinite spinner.
- Focused deterministic tests, frontend tests/build, and an isolated browser
  reproduction pass before a new immutable release round is created.

## Risk Boundaries

- Do not restart ClinicalTrials.gov search or change the immutable snapshot.
- Do not reset or overwrite succeeded triage chunks.
- Do not use corpus-gate override or skeleton content as PASS evidence.
- Do not mutate the frozen `release-r6-20260728` run directory.
- Do not promote the stable runtime until focused and browser recovery checks pass.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-28 08:50:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-28: Confirmed A1 failure is a parent/child state-machine gap:
  parent pipeline timed out while the persisted triage job remained queued;
  existing UI watched the child run only and exposed neither parent failure
  nor a recovery action.
- 2026-07-28 09:09 CST: Focused recovery implementation is present in the
  current product source. Parent status now projects compact child progress,
  exposes one idempotent same-run/same-snapshot retry, and reconciles
  `review_ready` back to `awaiting_triage_confirm`. Triage retry preserves
  succeeded chunks and selects every non-succeeded chunk.
- 2026-07-28 09:10 CST: Real headed-browser recovery against an isolated copy
  of the failed A1 runtime found one additional contract defect: concatenating
  every incomplete chunk ID exceeded the 300-character durable business-key
  ceiling. Replaced it with a deterministic hash of the incomplete chunk set
  and added an 80-chunk order-independent regression. The second real click
  retained the same project, snapshot and triage run and successfully started
  the independent-AI continuation at 4/19 completed chunks.
- 2026-07-28 09:12 CST: Deterministic acceptance after integration:
  184 focused backend/frontend contracts passed; the later bounded-key backend
  slice passed 67 tests; `triagePresentationState` passed 12 assertions;
  durable frontend job state passed 52 assertions; Vite production build
  passed with only the pre-existing chunk-size warning.
- 2026-07-28 09:13 CST: Removed a premature editor blocker from the pre-document
  research/design phase by requiring a real `editorSessionAvailable` before
  freeze/version readiness may surface. The actual editor's version recovery,
  freeze and mismatch warnings remain unchanged. Added a static regression,
  reran the focused frontend contracts, and rebuilt successfully.
- 2026-07-28 09:14 CST: Browser visual recheck is intentionally deferred until
  the active independent-AI continuation completes. The frontend hot update
  changed its expected API fingerprint while the isolated API still carries
  the startup fingerprint; restarting it now would terminate the 15-chunk
  product-AI job. No contract override was used. After the job reaches a
  terminal state, restart both isolated services from the same source, re-open
  the real page, and verify the blocker is absent before freezing new evidence.

## Current Runtime Boundary

- Isolated API: `http://127.0.0.1:51464`
- Isolated frontend: `http://127.0.0.1:51465`
- Project: `proj_user_a58eb8b86667`
- Snapshot: `wref_search_18e53d2757970660a603`
- Triage run: `ct_run_b9d2d959625a38c326ab`
- Parent pipeline: `mwpipe_4a7528da70b876b3a1ed`
- Recovery job: `mwjob_36466fbe38cee910bbab3fcc`
- Last observed product state at 09:13 CST: `triaging`, 4/19 complete,
  15 pending, no failed chunks. Do not restart the API before this job reaches
  a terminal state.

## Next Safe Actions

1. Preserve the long polling interval; observe the current product-AI job only
   after a meaningful wait.
2. On `review_ready`, capture parent/child lineage and succeeded-chunk hashes,
   then verify automatic promotion to `awaiting_triage_confirm`.
3. Restart the isolated API/frontend together from the current source and run
   headed-browser visual acceptance, including the removed premature blocker.
4. Write evidence to a new recovery run directory. Never mutate
   `release-r6-20260728`.
5. Freeze a new source fingerprint and rerun A1 from a zero-project runtime
   through full DOCX/PDF/native Word acceptance before starting the remaining
   serial tester matrix.

## Final Tester Contract Correction

- The latest user instruction replaces the former Alibaba/Qwen tester with
  `Codex subAgent/gpt-5.6-luna-high` (`gpt-5.6-luna`, reasoning `high`).
- Harness constants, matrix configuration and harness tests were updated; the
  18 harness tests pass.
- The existing Qwen A1 recovery remains defect evidence only. It cannot satisfy
  the corrected final tester matrix.
- Authoritative source verification currently fails closed on the active A1
  repair files, as intended. Refresh those SHA-256 receipts only after browser
  recovery acceptance freezes the implementation.

## Adjacent Release-Gate Verification While Product AI Runs

- Expanded A1 triage, recovery, empty-state and frontend contracts:
  `248 passed`; only existing FastAPI `on_event` deprecation warnings.
- Corpus analysis, indication-layer generalization and revision prompt
  contracts: `125 passed`.
- The current corpus contract already separates
  `wording_convention`, `clinical_design_requirement` and
  `regulatory_common_structure`; requires same-indication evidence to remain
  layered by phase, purpose, mechanism/technology, dosage form, route and design
  module; blocks disease-specific wording/design transfer across indications;
  preserves counterexamples and sponsor/source independence; and conservatively
  degrades sparse evidence. No duplicate prompt rewrite was made in this slice.
- At 09:18 CST the real recovery worker had an active heartbeat and progressed
  from 4/19 to 7/19 successful chunks with the same snapshot and run. Continue
  long polling; do not inspect intermediate model text.
- At 09:35 CST the research-stage banner was corrected to project the live
  child-triage percentage and a single current `已完成 x/y 个分诊分块` line.
  It no longer combines the retry-time parent detail or stale parent percentage
  with current child progress. The dedicated projection regression passed
  3 assertions; the adjacent pending-body notice, triage presentation and
  durable-job-state suites passed 64 assertions; the Vite production build
  passed with only the existing chunk-size warning. The running independent-AI
  continuation was not restarted.
- At 09:41 CST the low-frequency durable-job observation remained healthy:
  the same project, snapshot and triage run reached 16/19 succeeded chunks,
  3 pending, 0 failed, with an updated heartbeat and 84% child progress.
  The stored parent detail remains the retry-start audit statement (4/19);
  this confirms why the accepted frontend must project only the live child
  progress while running. No stall, fallback or restart condition exists.
- At 09:52 CST the durable recovery completed `19/19`, triage reached
  `review_ready`, and the parent reconciled to `awaiting_triage_confirm`.
  Canonical JSON result hashes for all four pre-timeout successful chunks
  remained unchanged.
- The isolated API and frontend were then restarted together from current
  source. Their API build fingerprint matched
  `api-182bff23cbfbf28e`; the frontend build was
  `web-71d77cc4a039a846`. Headed-browser acceptance confirmed no premature
  editor-session blocker, no stale `4/19` text, and one batch-confirm action
  over the 665-study AI-classified review set.
- Recovery evidence is frozen at
  `runs/execution/mw_final_4x3_harness_20260727/recovery-a1-triage-20260728/`.
  It is repair evidence only, not a final tester pass.
- Headed visual QC found and corrected one embedded-only horizontal overflow:
  the full-page candidate filter minimum columns exceeded the 480px drawer.
  After the scoped CSS change, the drawer body measured equal scroll and
  client widths (464px), no horizontal scrollbar was visible, 2 dedicated
  overflow assertions and 67 adjacent frontend assertions passed, and the
  production build passed.
- Both recovery services were stopped after acceptance. The copied SQLite and
  screenshot evidence was hashed, and the exact task-created temporary runtime
  was moved recoverably to Trash. No frozen evidence was removed.
- The user's latest tester contract contains five testers, not the previously
  frozen four: night-window Alibaba Qwen, Aishuo CMS, CodeBuddy Hy3,
  Antigravity Gemini Flash, and Codex Luna subAgent. Before preparing the next
  immutable round, upgrade the final matrix from 4x3 to 5x3 and assign 15
  mutually distinct indications. The completed recovery job must not be
  counted as the night-window Qwen final slot.
- A separate 5x3 harness, matrix, prompt package and isolated runtime
  orchestrator now exist without altering historical 4x3 files. Cross-review
  found that the first 5x3 draft locked only prompt/record hashes; product
  source drift could have escaped validation. The matrix now fail-closes on
  51 prompt, record, product, repair, regression, harness and runtime receipts.
  All receipts match and 43 harness/runtime tests pass.
