# Task Context: monitoring_p10_v10_visit_semantic_corrective_20260801

Created: 2026-08-01 13:24:35
Objective: Create an offline v10 visit protocol corrective that fixes reschedule-reference false positives, blocks study-completion/end semantic leakage, strengthens source-faithful prompt constraints, and proves the full repaired five-candidate bundle without starting any runtime or provider
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem.
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT2_TERMINAL_EVIDENCE.md`
- Isolated evidence database:
  `runs/execution/monitoring_p10_v9_isolated_canary_20260801/runtime_attempt2/medical_monitoring_ai.sqlite3`
  (read-only).
- v9 job `monai_5f66dc5d1c9c77c561a637389bc2`, attempt
  `monattempt_8a683aa19e1a4cd790339552da2612bf`, and
  `response_json.provider_outputs[0..1].candidates[0..4]`.
- Current governed source and tests:
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Frozen pre-edit SHA-256:
  - service:
    `4d97114e1bb9a4530954bdd0282abb106cc4dc08b07c40dc3c87eafeaf1f24ee`;
  - service test:
    `a907883c17a6bb61b96a83bb4a22277bcc155b962cd19dbb79c3758915a57ed3`;
  - protocol-preparation test:
    `9bd1daa3d6df252a05ca7e3d09ebba9e5621a68bf0f2894275f328e198ea8b17`.

No fresh external discovery is required. This is a narrow correction of an
already reproduced local semantic classifier and prompt contract; it introduces
no dependency, architecture, executable tool or external-source decision.

## Scope

- In scope:
  - bump protocol-clause prompt identity from v9 to v10 so the terminal v9 job
    can never be retried, reused or silently reclassified;
  - treat `以 <时间窗/访视窗> 为/作为 <参照|依据|基准>` as a reschedule
    reference complement only when the candidate carries a real reschedule
    action, without global reschedule precedence;
  - continue to reject independent schedule obligations, numeric windows,
    study-day/week assertions, ordering and mixed-family candidates;
  - reject visit candidates whose operative fact is subject completion,
    study completion/end, or study start/end determination even if a title or
    context mentions a final/planned visit;
  - strengthen initial and repair prompt constraints against changing
    `原始访视日` into a window reference, expanding `重新安排` into unsupported
    `补访`, hiding excluded source context through euphemism, or retaining
    off-topic completion/end candidates;
  - update v9 cutover assertions to v10 while proving v9 terminal/active
    history is preserved and retired under the fresh identity;
  - add focused positive, negative, mixed-family and exact five-candidate
    repair-output regressions.
- Out of scope:
  - any runtime, provider, canary, real-project, database, port or browser use;
  - changing the isolated v9 evidence or authoritative runtime;
  - provider-only stable-ID/SQLite uniqueness;
  - candidate decisions, mapping, release, or unrelated medical-writing files;
  - broad refactoring or weakening of existing treatment, medication,
    withdrawal, safety-follow-up, AE/CM or evidence-binding boundaries.

## Success Criteria

- Prompt constant and initial/repair instructions are v10 and explicitly encode
  the source-faithful and study-completion/end exclusions.
- The exact v9 candidate-3 referential sentence is reschedule-only when carried
  by a real reschedule rule.
- The following remain mixed and fail closed:
  - all planned visits must be completed plus a reschedule action;
  - a numeric `±3 days` visit window plus reschedule;
  - an independent original-order obligation plus reschedule;
  - an independent planned-visit completion obligation plus reschedule;
  - a referential reschedule clause plus a separate original-order obligation.
- Completion/end assertions are rejected, including
  `视为受试者完成试验`, `视为整个试验结束`, and study start/end
  determinations. A true rule such as `末次访视应于第24周 D169±7d 完成`
  remains schedule.
- An exact full repair-output regression proves candidates 1-4 are accepted
  only after source-faithful cleanup and candidate 5 is rejected or replaced
  by the genuine retrieval gap; no candidate is accepted merely through a
  title-only family hit.
- Focused tests and the existing visit/service/protocol-preparation adjacent
  regressions pass. Worker returns exact changed paths, commands, results,
  hashes and residual risk for Codex verification.

## Risk Boundaries

- Writable product paths are exactly:
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_api.py` (adjacent prompt-contract assertion only)
- Writable task record is runner-owned
  `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801.md`; the
  worker returns its report and does not write that path directly.
- Stop without editing if any frozen hash differs.
- Preserve unrelated user and parallel-agent changes.
- Do not touch runtime, backups, provider configuration, medical-writing
  source or any other product path.
- Do not start services, providers, browsers, real projects, ports, workers or
  candidates.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Dispatch Pi/deepseek-v4-flash once at max effort and leave it pending on the
  runner hard wait up to 120 minutes. Do not fixed-interval poll, duplicate,
  interrupt or fallback because of latency or unchanged output.
- One same-session completion pass is allowed only after terminal output and a
  concrete acceptance gap. Fallback requires terminal failure or a failed gate
  after controlled recovery.

## Loop Log

- 2026-08-01 13:24:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Trigger evidence: the only real v9 canary terminated fail-closed after one
  provider response and one controlled repair. The exact classifier false
  positive is a reschedule reference complement; independent review also found
  a separate study-completion/end topic leak and source/evidence fidelity
  problems in candidates 2-4. v9 is frozen and cannot be retried or reused.
- `init-execution` was used to record the three required first-line work items,
  but its generated three-worker plan was not dispatched because all three
  items share the same service and test files and are not safely independent.
  The task therefore uses the guard-selected single finite-code Pi route,
  avoiding concurrent edits while preserving the declared work-item contract.
- Pi completed the initial pass once with no fallback. Codex accepted its
  necessary adjacent v10 assertion in `tests/test_monitoring_ai_api.py`, then
  found four actionable gaps through direct read-only probes: unscheduled-only
  candidates inherited the reschedule reference exemption; numeric/week/day/
  ordering reference terms were over-suppressed; the cleaned bundle retained
  unsupported inferences and an altered window-reference sentence; and
  unsupported `补访` remained prompt-only. One same-session targeted
  completion pass is authorized to close only these gaps.
- The first completion pass closed those four gaps and Codex independently
  reproduced the intended compact forms. A second Luna challenge then found
  four additional Chinese/semantic edge blockers: common Chinese week/D-day/
  hour/working-day/order reference variants still over-exempt; study-end visit
  names and temporal anchors are mistaken for study-completion facts;
  conflict-only evidence can authorize affirmative `补访`; and cleaned
  candidate 2 retains an unsupported open-label phase premise outside its
  deleted inference claim. The second and final same-session completion pass is
  authorized for exactly these four blockers.
- Pi session `019fbbc9-de60-7000-99a4-e2ba0c08a8a6` completed exactly the
  initial pass plus two controlled same-session completion passes. There was no
  fallback, re-dispatch, service start, provider canary, runtime mutation or
  real-project execution. The adjacent v10 API prompt-contract assertion was
  accepted by Codex as a necessary shared-contract regression.
- Codex and the reused Luna reviewer subsequently challenged the study-end
  determination boundary. The final narrow correction makes
  `视为研究结束访视` and `视为研究终止访视` schedule names rather than
  completion determinations, while `视为整个试验结束`, `视为本研究终止`
  and equivalent actual determinations remain fail-closed. Luna's final
  delta-only verdict is PASS with no P0/P1/P2/P4; the only P3 is that
  `视为本研究终止` was proved by a direct pure-function probe but is not a
  separately named persisted parameter in the suite.
- Final product hashes:
  - `services/api/app/monitoring_ai_service.py`
    `f1e7276a7d6705d258203f879ea89d677a16659f3b36ba7c56a55a2495578ff6`
  - `tests/test_monitoring_ai_service.py`
    `a9d4b16799fa66c9688183269b686e7881a4b47e35469b90be0f66654729177f`
  - `tests/test_monitoring_protocol_preparation.py`
    `0bb75558acca3e91e77fba7da5cdee4b38f8b5b679a495efe2e09c1a003d0d5d`
  - `tests/test_monitoring_ai_api.py`
    `545b8bb74e888d1b5702f9fc0dee49ce72846df9a6e02a5dc247eb59a2c37bf6`
- Final verification:
  - compile and focused/adjacent combination: `674 passed, 17 warnings`;
  - full monitoring selection, excluding only the unrelated medical-writing
    private-symbol collection blocker:
    `1468 passed, 4391 deselected, 27 warnings in 594.07s`;
  - Luna final delta gate: PASS for **v10 zero-submit preparation only**.
- This task is now losslessly paused. It does not authorize a v10 POST,
  provider call, canary, candidate decision, runtime migration or release.
