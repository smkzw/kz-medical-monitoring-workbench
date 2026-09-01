Continue the same Codex-controlled execution session. This is the second and
final same-session recovery pass. Preserve accepted work; do not restart.

Hard boundaries:
- Work only inside the runner's current workspace.
- Do not read or modify production paths or runtime databases.
- Writable files are limited to the six files listed below.
- Runner-managed output path:
  `runs/pi_monitoring_p10_v11_datagap_semantic_corrective_20260801_followup2.md`.
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

Luna final contradiction review returned FAIL. Fix all blockers below, then run
focused and adjacent tests. No runtime/provider/POST.

1. Replace delimiter-based DATA_GAP framing with retrieval-scope dominance over
   family spans. Within strong boundaries (`。；！？` and newline), a retrieval,
   question or uncertainty marker may govern family-bearing text only at or
   after that marker. A later marker must never retroactively wash an earlier
   affirmative family assertion.

   Required matrix:
   - FAIL: `所有计划访视均应在时间窗内完成，当前证据包未检索到量化依据`
   - FAIL with the same leading assertion joined by `；/但/然而/同时`
   - PASS framing:
     `当前证据包未检索到改期访视是否必须仍落在原访视窗内，并可超出原访视窗的适用条件。`
   - PASS the exact real gap:
     `当前证据包未检索到改期访视的量化允许范围、是否必须仍落在原访视窗内或可超出原访视窗的明确规则。`

   Do not split `且/并/而` unconditionally. A retrieval scope established
   before the first family span may propagate forward across coordination.
   Prefer fail-closed for postpositive framing that would require reverse scope.

2. Make family trace semantically reliable and bounded:
   - schedule locators must identify an actual independent schedule span, not
     the first raw schedule token consumed by a reschedule object;
   - fix the `re.Match` unpacking bug in fallback;
   - reuse/refactor the real semantic schedule classification so trace and
     validation cannot diverge;
   - emit at most one concise deterministic locator per family per candidate;
   - bound each candidate diagnostic before response aggregation so every
     failing candidate retains its `candidate N (title)` marker and at least
     one locator inside the global 4000-character controlled error. Add a
     multi-candidate long-output regression proving later candidate markers
     survive into the repair envelope.

3. Correct evidence language. Rename/comment the canary regression as
   `exact known surfaces plus deterministic reconstruction`; do not claim the
   synthetic subject/condition/time-window/fact text, evidence ID, attempt
   payload or hashes are exact runtime replay.

4. Add concise provider-visible initial and repair rules:
   a DATA_GAP claim must report a retrieval/evidence/question uncertainty and
   cannot contain an affirmative protocol action before its framing marker;
   FACT/INFERENCE/RECOMMENDATION remain operative. The deterministic validator
   stays authoritative.

5. Re-run focused visit tests, complete AI service/preparation/API/startup
   suites and adjacent monitoring sets. Report exact hashes/results and all
   remaining residual risk.

Current frozen hashes before this final recovery pass:
- service `f8211f8b09fd46aab1ef5b0ce3da7b3ca32094dd816bf32b85fd948b23cdcffb`
- preparation service `b012a16c595c7c9c90fd0a4a0d86273581dbdf0a1abd42cb8f9e1729ed31b21f`
- service tests `a7656834141e5041cbff4ea9ea887f626201307c7bd07e36d46b4cce27fe7e98`
- preparation tests `c3f321884fdd204c08f674f49871c86e87fa43b71f9fca09bca9cf7e481c6622`
- startup tests `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`
- API tests `40f31a5b3cb599e5fb06f9cd4bc5dc329870e957bc636620a5a93ee5b6d7bc65`

Stop before editing if any differs. Return a delta execution report.
