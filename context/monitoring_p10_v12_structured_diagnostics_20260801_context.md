# Task Context: monitoring_p10_v12_structured_diagnostics_20260801

Created: 2026-08-01 21:41 CST  
Closed: 2026-08-01 22:22 CST  
State: **Phase A A1-A5 offline gate complete; A6 runtime gate unopened**  
Execution mode: **Codex direct; user required no execution/conference or subagents in this conversation**

## Objective

Close the frozen v11 `visit_window_and_order` controlled-repair gap without weakening any deterministic boundary:

- emit deterministic structured diagnostics for every forbidden visit-topic hit;
- include candidate index, exact user-visible field path, matched token, forbidden family/code and required repair action;
- require the single provider repair to regenerate each affected complete field;
- prove unchanged/partial repair remains terminal fail-closed and complete repair passes;
- preserve all v9-v11 histories and keep product runtimes stopped.

This is Phase A of the project-wide commercialization Goal. It does not authorize real-project execution, runtime database migration, a new clone, zero-submit or canary.

## Source Of Truth

1. `context/medical_monitoring_system_retro_pause_20260801.md`
2. `reviews/medical_monitoring_system_retro_roadmap_20260801.md`
3. `context/monitoring_p10_v11_canary_pause_20260801.md`
4. `runs/execution/monitoring_p10_v11_isolated_canary_20260801/TERMINAL_EVIDENCE.md`
5. `runs/execution/monitoring_p10_v11_zero_submit_gate_20260801/ZERO_SUBMIT_EVIDENCE.md`
6. `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` 3.20-3.21
7. Current filesystem and latest global/workbench `AGENTS.md`.

The deleted parent Session was not restored. This is an evidence-reconstructed continuation.

## Re-Anchored Baseline

- 8911: stopped.
- 5174: stopped.
- 18911: unrelated PID 43191; do not touch.
- v9/v10/v11: frozen; no retry/reuse/salvage/reclassification/candidate action.
- Accepted source/test hashes:
  - `services/api/app/monitoring_ai_service.py`:
    `ca7cdb2a93fe0687a0595170fd857d64ba8f5abb6835fa10dafe4f790c00c3b2`
  - `services/api/app/monitoring_protocol_preparation_service.py`:
    `b012a16c595c7c9c90fd0a4a0d86273581dbdf0a1abd42cb8f9e1729ed31b21f`
  - `tests/test_monitoring_ai_service.py`:
    `d030937c74841581880d42fee69e6f4d26f90ac699d8167bf1570e4d48e6bae7`
  - `tests/test_monitoring_protocol_preparation.py`:
    `7a072ee87f01333ecf02b1dbab1f0523eb8f50afc982099e44c37bad7a911d3d`
  - `tests/test_monitoring_ai_startup_recovery.py`:
    `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`
  - `tests/test_monitoring_ai_api.py`:
    `40f31a5b3cb599e5fb06f9cd4bc5dc329870e957bc636620a5a93ee5b6d7bc65`

The target directory is not a Git worktree. Protect concurrent/user work using accepted hashes, mtimes, exact changed-file inventory and focused diffs.

## Exact v11 Failure

- Candidate 1 remained a valid visit-window candidate.
- Initial claim uncertainty contained excluded dispensing/return/PK wording.
- The single repair removed most excluded wording but retained
  `药物回收相关段落` in a claim uncertainty field.
- The full boundary correctly scans uncertainty and matched `回收`.
- Result: `failed / invalid_ai_output / retryable=0`, two provider outputs,
  zero candidates and zero active jobs.

The validator is correct. The loss occurs because the repair receives only a family-level string instead of the exact field/token hit.

## Working Hypothesis

A server-generated ordered diagnostic list, built while scanning the existing complete user-visible field surfaces, will let the one allowed repair target the exact field without changing validation semantics. The human-readable legacy error remains for compatibility; structured diagnostics are added to the repair payload and echoed in the controlled error deterministically.

## Allowed Product Changes

- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py` solely for
  the v12 prompt cutover and immutable v11 retirement-audit membership
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`,
  `tests/test_monitoring_ai_startup_recovery.py` and
  `tests/test_monitoring_ai_api.py` only where the v12 identity/cutover
  directly changes an assertion
- only directly affected adjacent monitoring tests if evidence requires them
- context/review/metrics/LOOP/roadmap records for this slice

## Hard Boundaries

- Do not start 8911 or 5174.
- Do not touch PID 43191/18911.
- Do not open or write the authoritative or frozen v9-v11 runtime databases.
- Do not retry or reinterpret v9-v11 output.
- Do not weaken any visit, CM/IP, dispensing/return/weighing/adherence/PK,
  withdrawal, safety follow-up, AE/CM collection, study completion or
  visit-family atomicity gate.
- Do not remove uncertainty/user_action from validation.
- Do not mutate provider output after generation or silently delete tokens.
- Do not introduce new external runtime dependencies.
- Preserve medical-writing and unrelated user changes.

## Success Criteria

1. Structured diagnostic entries have stable deterministic ordering and deduplication.
2. Each forbidden hit carries:
   - `code`;
   - zero-based `candidate_index` aligned with the provider JSON path;
   - one-based `candidate_number` for human display;
   - exact `field_path`;
   - exact `matched_token`;
   - `forbidden_family`;
   - `repair_action=regenerate_entire_user_visible_field`.
3. The repair envelope carries the structured diagnostics and an explicit full-field regeneration contract.
4. Legacy family-level validation text remains present for compatibility.
5. Exact tests cover title, text, structured string fields, claim text,
   uncertainty and user_action.
6. Exact v11-shaped initial output plus partial repair fails with the residual
   uncertainty field/token; a complete repair passes.
7. Existing visit/CM/IP and adjacent monitoring contracts do not regress.
8. Pycompile, focused, core, adjacent and full monitoring regression pass.
9. Codex source review closes all high-priority findings.
10. Final hashes, tests, review, metrics and LOOP evidence are persisted while
    8911/5174 remain stopped.

## Implemented Contract

- The protocol clause prompt identity is now
  `monitoring-protocol-clause-structuring-v12`.
- v11 is part of the immutable retirement-audit set and remains outside the
  status-compatible legacy set.
- `MonitoringAiOutputValidationError` can carry structured diagnostics without
  changing the existing bounded human-readable error.
- The existing complete user-visible visit boundary is represented as ordered
  exact field paths. No surface was removed: title, text, subject scope,
  structured list values, claim text, uncertainty and user action remain
  governed.
- Every forbidden hit records schema/code, zero-based candidate index,
  one-based candidate number, exact path/token/span, family and
  `regenerate_entire_user_visible_field`.
- The single repair must regenerate each complete affected field and must not
  perform token-only deletion, post-generation mutation or introduce
  unsupported facts/sources.
- Residual structured diagnostics are persisted with the terminal invalid
  attempt. Unchanged and partial repair remain non-retryable with zero
  candidates; a valid complete-field regeneration can pass.

## Verification Closure

- Python compilation: PASS.
- Ruff static check: PASS.
- New focused v12 cases: `5 passed`.
- Service module: `432 passed`.
- Preparation: `40 passed`.
- API + startup recovery: `20 passed, 17 warnings`.
- Core monitoring: `533 passed, 17 warnings in 16.83s`.
- Adjacent monitoring: `146 passed, 17 warnings in 5.23s`.
- Full monitoring, ignoring only the known unrelated medical-writing
  collection blocker:
  `1494 passed, 4480 deselected, 27 warnings in 695.60s`.
- Codex source review: PASS; no P0-P4 finding in the offline delta.

The unmodified standard `-k monitoring` selector remains collection-blocked
before test execution by
`tests/test_medical_writing_dynamic_section_matrix.py` importing removed
private medical-writing symbol `_REQUIRED_CORE_BODY_SEMANTIC_IDS`. That
parallel subsystem was not changed. `ruff format --check` proposes baseline
format churn for all governed files and was deliberately not applied.

## Final Governed Hashes

- `services/api/app/monitoring_ai_service.py`:
  `1fce0bf1c18803b9901039e38d700ae34715441d8857a0135f278cc851f2ebe5`
- `services/api/app/monitoring_protocol_preparation_service.py`:
  `35ecbd629151d98e39499c7f7ae45481d6e813e4a477022a89aeb7b8bcab427a`
- `tests/test_monitoring_ai_service.py`:
  `bb65b3ddf12f34b5892099cbc338721e74ed2895d72317f350a5422a47372b44`
- `tests/test_monitoring_protocol_preparation.py`:
  `2ba514090a8ac44fae822325b5e09975369770c9bbefa9667b33c750cde6d9fe`
- `tests/test_monitoring_ai_startup_recovery.py`:
  `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb`
- `tests/test_monitoring_ai_api.py`:
  `e89cb84d26013682ffaeede50a556c018281a33c42e2282597b9844663fffb41`

## Closed LOOP Record

- **Locate:** source-of-truth files, hashes, ports and frozen histories were
  rechecked; no unreported monitoring source write was found before the
  corrective.
- **Hypothesis:** confirmed offline. Exact field/token diagnostics preserve the
  full fail-closed boundary while preventing the repair contract from losing
  the actionable location.
- **Action:** implemented v12 diagnostics, complete-field repair instructions,
  residual persistence, immutable v11 cutover and exact fixtures.
- **Observe:** focused, core, adjacent and accepted full monitoring regressions
  passed; Codex source review found no P0-P4 issue in the delta.
- **Persist:** review, metrics, roadmap, LOOP 3.22 and a lossless pause
  checkpoint were written.
- **Runtime boundary:** 8911/5174 remain stopped; 18911/PID 43191 remains
  unrelated and untouched. No clone, zero-submit, provider call or canary ran.
- **Next safe action:** only after separate runtime authorization, reverify
  hashes/ports and create a brand-new isolated A6 clone followed by
  zero-submit; a single canary remains separately gated.
