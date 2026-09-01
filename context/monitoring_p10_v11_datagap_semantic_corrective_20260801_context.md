# Task Context: monitoring_p10_v11_datagap_semantic_corrective_20260801

Created: 2026-08-01 16:53:10
Objective: Implement the offline v11 DATA_GAP semantic-family corrective, audit trace, frozen v10 cutover, and focused regressions without any runtime or provider call
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and latest global/workbench `AGENTS.md`.
- `runs/execution/monitoring_p10_v10_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
- `reviews/codex_monitoring_p10_v10_isolated_canary_20260801_review.md`
- Independent Luna terminal review in the current Codex task.
- Governed source hashes frozen at task start:
  - `services/api/app/monitoring_ai_service.py`
    `f1e7276a7d6705d258203f879ea89d677a16659f3b36ba7c56a55a2495578ff6`
  - `services/api/app/monitoring_protocol_preparation_service.py`
    `899d2b01d6df4a6efda5e02ac5697348d5f0514272c57f0a5f1af35e33a7ab00`
  - `tests/test_monitoring_ai_service.py`
    `a9d4b16799fa66c9688183269b686e7881a4b47e35469b90be0f66654729177f`
  - `tests/test_monitoring_protocol_preparation.py`
    `48a74f198251563d911a13bac2ff4d412d93ed5aa429997dc500974e94022000`
  - `tests/test_monitoring_ai_startup_recovery.py`
    `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`

External-discovery decision: no new search. This is a deterministic defect in
the current validator/repair/cutover contract, proven by live canary evidence
and pure-function replay. No dependency or architecture choice changes.

## Scope

- In scope:
  - preserve claim-kind semantics in visit action-family classification;
  - exclude only valid `DATA_GAP` claim text from operative family counting
    while retaining it in full boundary, absence, evidence, anchor and conflict
    validation;
  - fail closed when a `DATA_GAP` claim is actually an affirmative protocol
    obligation/action, without allowing claim-kind bypass;
  - add actionable family trace to validation/repair evidence;
  - advance only the protocol prompt identity to v11;
  - add v10 to the retirement-audit set while keeping status legacy v3-v8;
  - add exact canary-shape, anti-bypass, boundary, repair and v10-v11 frozen
    history regressions.
- Out of scope:
  - runtime, service, provider, POST, real project, candidate decision;
  - retry/reuse/salvage/reclassification of v10;
  - regex expansion or global reschedule precedence;
  - repository schema/API/medical-writing/unrelated refactor.

## Success Criteria

- Exact v10 candidate-2 full shape completes initial validation as reschedule
  only and does not enter repair.
- The same mixed-family gap text as FACT/INFERENCE/RECOMMENDATION remains
  fail-closed; affirmative-action DATA_GAP disguise fails a kind-semantics gate.
- DATA_GAP medication/withdrawal/safety/AE-CM and unauthorized absence text
  remain rejected by existing full-surface gates.
- True mixed-family initial output carries actionable trace into repair; an
  unchanged repair remains terminal failed with two outputs and zero candidates.
- Prompt identity is v11; status legacy remains v3-v8; retirement audit includes
  v3-v10.
- Frozen terminal v10 survives v11 cutover with exact status/timestamps/attempt
  hashes/two outputs/zero candidates, and same-key v11 has a distinct job ID.
- Focused and adjacent monitoring regressions pass.

## Risk Boundaries

- Writable product files are exactly the five source/test files listed above.
- Stop before editing if any frozen hash differs.
- Do not modify `main.py`, repository/API files, runtime DBs or medical-writing
  files.
- Tests use temporary databases only.
- No service/browser/provider/real project may be started.
- The failed v10 runtime/evidence is read-only.
- The delegated agent is not final authority; Codex owns verification.

## Timeout Policy

- Dispatch the declared Pi/deepseek-v4-flash max route once and use the 120
  minute runner hard wait. Do not fixed-interval poll, re-dispatch or fallback
  for latency.
- Up to two same-session recovery passes are allowed only after terminal output
  and a concrete acceptance gap.

## Loop Log

- 2026-08-01 16:53:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Execution contract recorded as three work items. They share the same five
  files, so concurrent writers are not dispatched; one bounded Pi worker owns
  the coherent implementation and Codex independently reviews/tests it.
- Pi initial pass completed in session
  `019fbc8a-1e18-7000-9481-41fcae818530` without fallback. Codex rejected two
  concrete gaps: the test substituted a non-exact DATA_GAP sentence, and the
  retrieval-frame predicate admitted affirmative text followed by a gap marker.
- One same-session recovery pass closed both gaps, made non-retrieval DATA_GAP
  kind semantics unconditional, added clause-level mixed-bypass regressions and
  updated the adjacent API identity assertion to v11.
- Final hashes:
  - service:
    `f8211f8b09fd46aab1ef5b0ce3da7b3ca32094dd816bf32b85fd948b23cdcffb`
  - protocol preparation:
    `b012a16c595c7c9c90fd0a4a0d86273581dbdf0a1abd42cb8f9e1729ed31b21f`
  - service tests:
    `a7656834141e5041cbff4ea9ea887f626201307c7bd07e36d46b4cce27fe7e98`
  - preparation tests:
    `c3f321884fdd204c08f674f49871c86e87fa43b71f9fca09bca9cf7e481c6622`
  - startup tests:
    `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`
  - API tests:
    `40f31a5b3cb599e5fb06f9cd4bc5dc329870e957bc636620a5a93ee5b6d7bc65`
- Codex-direct verification: py_compile; core `520 passed`; adjacent `146
  passed`; full monitoring selector excluding only the known unrelated
  medical-writing collection blocker:
  `1481 passed, 4455 deselected, 27 warnings in 615.80s`.
- Final Luna contradiction review is pending. No runtime or POST is authorized
  until that review returns PASS.
