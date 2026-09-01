Continue the same Codex-controlled execution session. This is the first
same-session recovery pass. Do not restart from scratch.

Hard boundaries:
- Work only inside the runner's current workspace.
- Do not read or modify production paths or runtime databases.
- Writable files are limited to the six files listed below.
- Runner-managed output path:
  `runs/pi_monitoring_p10_v11_datagap_semantic_corrective_20260801_followup.md`.
  Do not write this report path; return the report for the runner to persist.

Read these files only:
- `context/monitoring_p10_v11_datagap_semantic_corrective_20260801_context.md`
- `runs/execution/monitoring_p10_v10_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_startup_recovery.py`
- `tests/test_monitoring_ai_api.py`

Codex does not accept the initial pass yet. Preserve all valid current work and
fix only these concrete gaps:

1. The test claimed to use the exact failed-canary DATA_GAP text but substituted
   a different sentence. The exact text must be used verbatim:

   `当前证据包未检索到改期访视的量化允许范围、是否必须仍落在原访视窗内或可超出原访视窗的明确规则。`

   Reconstruct the full real shape already recorded in terminal evidence:
   exact title, text, subject_scope, condition, time_window, three required
   actions, fact claim and this exact DATA_GAP claim. Prove initial validation
   completes without repair and all non-gap operative surfaces together are
   reschedule-only.

2. The current retrieval-frame gate has a documented fail-open residual:
   affirmative visit action/obligation text followed by a retrieval marker is
   excluded wholesale. Close it deterministically. A DATA_GAP is excludable
   from family counting only when every visit-family-bearing clause is under
   retrieval/question/uncertainty framing. Split at sentence/semicolon/newline
   and adversative/additive boundaries as needed. A leading affirmative clause
   such as `所有计划访视均应在时间窗内完成；当前证据包未检索到量化依据`
   or the same shape joined by `但/然而/同时` must fail the DATA_GAP
   kind-semantics gate. Do not add global reschedule precedence.

3. A non-retrieval DATA_GAP that affirmatively states an action/obligation must
   always fail kind semantics, even if it adds no new family relative to the
   rest of the candidate. Remove the current `family set changed` condition.
   Add same-family and additional-family disguise regressions.

4. Keep valid DATA_GAP text in all full boundary/absence/evidence/anchor/conflict
   gates. Add focused regressions for the exact DATA_GAP sentence and mixed
   affirmative-plus-gap bypass cases. Keep FACT/INFERENCE/RECOMMENDATION
   operative and fail-closed.

5. The v11 identity makes one adjacent API assertion stale. Editing
   `tests/test_monitoring_ai_api.py` is now explicitly authorized only for the
   minimal test name/business-key/expected prompt-version update. Its frozen
   pre-followup SHA is
   `545b8bb74e888d1b5702f9fc0dee49ce72846df9a6e02a5dc247eb59a2c37bf6`.
   Do not change API production code.

6. Re-run the focused visit tests, complete AI service/preparation/API/startup
   suites, and the same adjacent monitoring sets. Report exact results and new
   hashes. Do not start services, runtime DBs, providers, browsers or real
   projects.

Writable files for this recovery pass are the five already authorized files
plus only `tests/test_monitoring_ai_api.py`. Stop if its frozen hash differs.
Return a delta execution report. The runner owns the report file.
