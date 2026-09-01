You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the runner-provided workspace root (`.`).
- Do not read or modify production paths.
- This is the authorized edit round. You may modify exactly:
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  and no other product file.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/monitoring_p10_v10_visit_semantic_corrective_20260801_context.md`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT2_TERMINAL_EVIDENCE.md`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/runtime_attempt2/medical_monitoring_ai.sqlite3`
  (read-only and only if needed for exact fixtures)

Task:
Implement the bounded offline v10 corrective described in the task context.
First verify every frozen hash. Then:

1. Bump the protocol-clause prompt identity from v9 to v10 and update the
   cutover tests so existing v9 terminal/active history is preserved/retired
   and fresh work is v10. Never make v9 retryable or reusable.
2. Fix only the semantic-role defect: a schedule term inside
   `以 <时间窗/访视窗> 为/作为 <参照|依据|基准>` is a reschedule
   reference complement when the same operative candidate has a real
   reschedule action. Do not give reschedule global precedence. Keep
   independent schedule, quantified/normative completion, numeric-window,
   week/day and ordering assertions mixed and rejected.
3. Add a deterministic topic-boundary rejection for subject completion, study
   completion/end, and study start/end determination masquerading as a visit
   candidate through a title/context mention. Preserve genuine final-visit
   schedules such as `末次访视应于第24周 D169±7d 完成`.
4. Strengthen both the initial prompt and the single repair constraint so the
   provider must preserve `原始访视日`, may not expand `重新安排` to
   unsupported `补访`, may not euphemize excluded source context, and must
   omit/redirect completion/end facts rather than title them as visit schedule.
5. Add precise positive/negative/mixed-family regressions, plus an exact
   five-candidate v9 repair-output replay: the original repaired candidate 3
   must still fail for its source-faithfulness defects or be represented by a
   source-faithful fixture; candidate 5 completion/end must fail topic
   validation; a cleaned candidates 1-4 plus genuine retrieval-gap candidate
   must pass. Keep tests deterministic and avoid provider/runtime/network use.
6. Run compilation and focused/adjacent tests proportionate to this patch.

Prefer the smallest coherent implementation. Do not broadly weaken existing
visit-family, treatment, medication, withdrawal, safety, AE/CM, evidence,
structural or prompt-cutover gates.

Output schema:
1. `# Hermes Execution Report: monitoring_p10_v10_visit_semantic_corrective_20260801`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Changes`
5. `## Verification`
6. `## Exact Hashes`
7. `## Residual Risk`
8. `## Codex-Owned Next Action`

Quality gates:
- Stop if a frozen hash mismatches.
- No service, provider, port, browser, runtime DB mutation or real-project run.
- Report every changed path and exact test command/result.
- Do not claim canary, scientific, release or full-Goal acceptance.
