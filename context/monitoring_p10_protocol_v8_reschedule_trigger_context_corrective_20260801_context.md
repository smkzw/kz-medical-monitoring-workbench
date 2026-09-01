# Task Context: monitoring_p10_protocol_v8_reschedule_trigger_context_corrective_20260801

Created: 2026-08-01 07:05:40
Objective: Implement an offline v8 protocol prompt and context-aware visit-family classifier that treats schedule/window language used only as a reschedule trigger or object as reschedule-only, while preserving true mixed-family rejection, all topic-boundary precedence, candidate-indexed one-repair atomicity, legacy history, and medical-writing isolation.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Immutable v7 canary evidence:
  - `context/monitoring_p10_loop316_protocol_v7_visit_canary_pause_20260801.md`
  - `runs/monitoring_p10_loop316_protocol_v7_visit_canary_terminal_evidence_20260801.md`
  - `runs/codex-subagent_monitoring_p10_loop316_protocol_v7_visit_canary_20260801.md`
  - `reviews/codex_monitoring_p10_loop316_protocol_v7_visit_canary_20260801_review.md`
  - `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- Writable product sources:
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
- Writable tests:
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py` only when a direct prompt-version or cutover assertion requires it.
- Baseline SHA-256 values at 2026-08-01 07:07 CST:
  - `monitoring_ai_service.py`: `d62ff1162794f65cc8894d313d84c5c25c7d043641589608118146de5cb20aba`
  - `monitoring_protocol_preparation_service.py`: `1e43424adb7076fd6a7acf17e933833cde2f942dbd8778b5af03e47262ca1798`
  - `test_monitoring_ai_service.py`: `7e0fb132f2bfd081e1f860422d563fbdd9594aea3f833b29b61d7c16a2234cb5`
  - `test_monitoring_protocol_preparation.py`: `9ad21eb72141f58ced1ce265b98779a851af98b32ac859cdb68c8da59dc0ef1c`
  - `test_monitoring_ai_api.py`: `52691a1ec1f6a35cf4359bdea4aad41d50b1fd2f90f4ad80f48f6d35710768a2`
- No fresh external discovery is required. The immutable local v7 canary and
  independent review isolate a deterministic semantic-role defect; this task
  introduces no new dependency, architecture, or executable component.

## Scope

- In scope:
  - Introduce active prompt identity
    `monitoring-protocol-clause-structuring-v8`.
  - Add v7 to the terminal legacy prompt set while preserving v3-v7 history,
    stale-job handling, and cutover semantics.
  - Make visit-family detection context-aware: schedule/window wording used
    only as a reschedule title, trigger, or action object must not create an
    independent schedule family.
  - Preserve rejection when an independent schedule assertion and a
    reschedule action coexist.
  - Update the provider-visible initial and repair contracts to explain the
    same semantic-role rule.
  - Add focused positive and negative regression tests.
- Out of scope:
  - Runtime databases, runtime backups, job/candidate records, services,
    workers, ports 8911/5174, frontend, `main.py`, APIs unrelated to the prompt
    identity, medical-writing sources/tests, real-project data, and any v8
    canary.
  - Reuse or retry of any v4-v7 terminal job or candidate.
  - Candidate acceptance, rejection, adoption, confirmation, activation, or
    any other user-owned decision.
  - Broad refactors, new dependencies, or global reschedule precedence.

## Success Criteria

- Exact v7 repaired candidate is classified as reschedule-only and passes:
  - title: `计划访视改期原则`
  - text: `若受试者无法在研究流程图规定的访视窗口期内前往研究中心，可在另一时间重新安排访视；应尽一切努力重新安排尽可能接近原始访视日，受试者不应因排程困难而错过方案规定的访视。`
- `调整计划访视日期` is reschedule-only.
- A title/object phrase such as `计划访视改期原则` does not independently
  create the schedule family.
- Trigger clauses introduced by `若` / `如果` / `无法` / `未能` that mention
  `访视窗口` / `访视窗` / `计划访视` do not create the schedule family unless
  there is an independent schedule assertion.
- True mixed-family content remains rejected, including:
  `所有计划访视应在时间窗内完成；若无法到访，应重新安排。`
- An independent week schedule plus `调整计划访视日期` remains rejected.
- Pure schedule, pure reschedule, and pure unscheduled classification remains
  correct, as do all existing negative combinations.
- Boundary precedence remains medication -> dispensing/PK -> withdrawal ->
  safety -> collection -> visit family.
- Candidate-indexed complete deterministic errors, exactly one controlled
  repair, whole-response atomicity, C1-C5, C3 8-to-15, and
  structure/evidence blockers do not regress.
- Focused tests pass in the delegated slice. Codex will independently run
  compile, the focused three-file suite, full monitoring regression, the
  medical-writing adjacent suite, and a direct in-memory counterexample matrix.

## Risk Boundaries

- Write only the explicit product/test paths above. Preserve unrelated
  filesystem changes.
- Do not write task context, run, review, metrics, ledger, or pause files; Codex
  owns those records and the runner owns the delegated report.
- Do not access or mutate runtime databases or backups.
- Do not start any service, worker, browser, 8911/5174 listener, real-project
  run, or canary.
- Do not adopt global reschedule precedence: it would mask true mixed-family
  clauses. Use semantic role and clause/segment context.
- Do not weaken established medication, dispensing/PK, withdrawal, safety, or
  collection boundaries.
- Do not change candidate lifecycle behavior or user-owned decision semantics.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 07:05:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01 07:07 CST: Codex reverified the five governed baseline hashes,
  confirmed v8 has no runtime state, and bounded this task to offline product
  and test changes only.
- 2026-08-01 07:07 CST: Local v7 terminal evidence was accepted as the
  discovery basis. The next action is one preflighted Pi finite-code dispatch;
  no service, runtime, or real-project action is authorized.
- 2026-08-01: Pi/deepseek-v4-flash session
  `019fba70-4de6-7000-b944-c145c409f6db` completed the initial v8 edit and two
  same-session recoveries. The initial edit established v8 identity, v7
  terminal legacy history, provider-visible semantic-role wording, and the
  first context-aware classifier. The two recoveries closed title/target,
  cross-field delimiter, quantifier and schedule-predicate scope cases.
- 2026-08-01: Independent Luna review repeatedly challenged the implementation
  with withheld counterexamples. After the two Pi recovery passes were
  exhausted, the declared native Codex fallback reused child handle
  `/root/v7_lexical_corrective` and modified only the service and its direct
  tests. It closed modal/auxiliary action objects, predicate-before/after
  schedule obligations, bounded numeric window definitions, and
  `进行/完成` when directly governing reschedule or unscheduled action heads.
- 2026-08-01: The independent reviewer reused
  `/root/rux_protocol_v4_audit` and returned final PASS. No blocking
  counterexample remains inside this task's bounded semantic-role contract.
- 2026-08-01: Final Codex verification passed:
  - compile for all five governed Python files;
  - focused three-file suite: `376 passed in 10.34s`;
  - direct final semantic-role matrix and targeted delta controls: all passed;
  - full monitoring: `1371 passed, 4299 deselected, 27 warnings in 679.52s`;
  - five-file adjacent medical-writing contract: `200 passed in 1.50s`.
- 2026-08-01 08:52 CST: Final runtime read-only check showed v4/v5/v6/v7
  job-attempt-candidate counts unchanged at `8/8/8`, `1/1/0`, `1/1/0`,
  `1/1/0`; v8 remains `0/0/0`. Ports 8911/5174 have no listeners and no task
  pytest, runner or monitoring worker remains active.

## Final Offline State

- Offline v8 corrective: PASS.
- This is not a canary, release, candidate decision, RUX protocol-gate pass, or
  MY009 authorization.
- v4-v7 terminal jobs must not be retried or reused.
- Candidate accept/reject/adopt/confirm/activate remains user-owned.
- 8911 and 5174 must remain stopped during the pause.
- Next safe action, only after the user explicitly continues this Goal:
  reverify hashes/listeners/runtime counts, create a consistent pre-canary
  backup of the 21 runtime databases, start only 8911, and run at most one new
  RUX v8 `visit_window_and_order` canary with a new job identity, one hard wait,
  no fixed polling/retry/reuse, immediate service stop at terminal state, and
  independent read-only review before any broader gate.
