# P10 v12 structured diagnostics — lossless pause checkpoint

Date: 2026-08-01 22:22 CST  
State: **Historical A1-A5 checkpoint; superseded by completed A6 runtime gate**  
Goal state: **project-wide commercialization Goal remains active and incomplete**

## Recovery statement

The deleted parent Session was not restored. This checkpoint is an
evidence-reconstructed continuation based on the current filesystem, frozen
run evidence and deterministic tests.

## Completed in this slice

1. Re-anchored the v11 terminal failure, zero-submit evidence, LOOP 3.20-3.21,
   six accepted hashes and stopped-runtime boundary.
2. Advanced the protocol-clause prompt identity to v12.
3. Added deterministic visit-topic diagnostics containing:
   - code and schema version;
   - zero-based candidate index and one-based candidate number;
   - exact user-visible field path;
   - exact matched token and span;
   - forbidden family;
   - full-field regeneration action.
4. Required the one controlled repair to regenerate every affected complete
   user-visible field and prohibited token deletion, output post-processing
   and unsupported new facts/sources.
5. Persisted residual diagnostics when the repair remains invalid, while
   preserving terminal fail-closed, two outputs and zero candidates.
6. Preserved v11 as immutable retired history and proved a distinct v12 job is
   created for the same business key.
7. Completed Codex-only source review and offline regression.
8. Updated the project roadmap so future UI/risk work must use one shared
   Profile/Timeline/AE-risk/event/evidence identity with concise progressive
   disclosure and project→site→subject drilldown.

## Verification evidence

- New v12 focused: `5 passed`.
- Service module: `432 passed`.
- Preparation: `40 passed`.
- API + startup: `20 passed, 17 warnings`.
- Core: `533 passed, 17 warnings in 16.83s`.
- Adjacent: `146 passed, 17 warnings in 5.23s`.
- Full monitoring with only the known unrelated medical-writing collector
  ignored:
  `1494 passed, 4480 deselected, 27 warnings in 695.60s`.
- Python compilation and Ruff static check: PASS.
- Codex source review: PASS; P0-P4 none for the offline delta.

The standard `-k monitoring` selector remains collection-blocked by the
unrelated medical-writing private-symbol import in
`tests/test_medical_writing_dynamic_section_matrix.py`. It was not modified.

## Final governed hashes

| File | SHA-256 |
|---|---|
| `services/api/app/monitoring_ai_service.py` | `1fce0bf1c18803b9901039e38d700ae34715441d8857a0135f278cc851f2ebe5` |
| `services/api/app/monitoring_protocol_preparation_service.py` | `35ecbd629151d98e39499c7f7ae45481d6e813e4a477022a89aeb7b8bcab427a` |
| `tests/test_monitoring_ai_service.py` | `bb65b3ddf12f34b5892099cbc338721e74ed2895d72317f350a5422a47372b44` |
| `tests/test_monitoring_protocol_preparation.py` | `2ba514090a8ac44fae822325b5e09975369770c9bbefa9667b33c750cde6d9fe` |
| `tests/test_monitoring_ai_startup_recovery.py` | `2b406c3445271986c289d54ae2cc48ada3dc44b34d42b942e69a6e521fe0d9bb` |
| `tests/test_monitoring_ai_api.py` | `e89cb84d26013682ffaeede50a556c018281a33c42e2282597b9844663fffb41` |

## Frozen history and runtime boundary

- v11 job `monai_3632c414655546ad250ce8bf7dbd` and attempt
  `monattempt_564f58bf463c42758a4c394f190be9de` remain frozen.
- v9/v10/v11 must not be retried, reused, salvaged, reclassified or used for a
  candidate decision.
- 8911: no listener; **must remain stopped**.
- 5174: no listener; **must remain stopped**.
- 18911: unrelated PID 43191; do not touch.
- No runtime database, provider, POST, browser, clone, real project or
  authority migration was used in this slice.

## Durable evidence

- Review:
  `reviews/codex_monitoring_p10_v12_structured_diagnostics_20260801_review.md`
- Metrics:
  `metrics/monitoring_p10_v12_structured_diagnostics_20260801_metrics.md`
- Working context:
  `context/monitoring_p10_v12_structured_diagnostics_20260801_context.md`
- LOOP:
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- Project roadmap:
  `reviews/medical_monitoring_system_retro_roadmap_20260801.md`

Record hashes at closure:

| Record | SHA-256 |
|---|---|
| `context/monitoring_p10_v12_structured_diagnostics_20260801_context.md` | `b7efb2ee4e13e63831fb5966c6e71a74e51099494e3bc74dfb114ab30b2bfb4e` |
| `context/medical_monitoring_system_retro_pause_20260801.md` | `58463e54e6e438ab9e2e79701774d33370d09fb7d6e05759ddc6475fecf5bba7` |
| `reviews/codex_monitoring_p10_v12_structured_diagnostics_20260801_review.md` | `d6142b807e6504342a07aa725a387397d4eccc3e58ec437be3df13d0e0031565` |
| `reviews/medical_monitoring_system_retro_roadmap_20260801.md` | `9c1ffd52223aef2b16f1e887cbee69f4d92d1030a170a8b299c10f58eef86a25` |
| `metrics/monitoring_p10_v12_structured_diagnostics_20260801_metrics.md` | `3682a1e6a2f7dd31f25fc541bfd83157f58921b8d2820335b3ce9d7ea78bc1aa` |
| `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` | `b1749b0de1683e2a8db5b283dd2df240cae4500d5b0450ea6a9137b0147d1211` |
| `.hermes/plans/2026-08-01_210824-medical-monitoring-commercialization-goal.md` | `9a6e4561ada0d190cf007ffa977303dfc85be0d1ed7084c306ada773cc2efa44` |

## Historical next action (superseded)

1. Fully reread the latest global/workbench `AGENTS.md` and this checkpoint.
2. Recompute the six governed hashes and confirm 8911/5174 remain stopped.
3. Confirm v9-v11 frozen records and authority hashes before any runtime work.
4. Only if the user separately authorizes runtime execution, create a
   brand-new isolated clone and complete a zero-submit gate.
5. Only after that gate passes, allow at most one project, one
   `visit_window_and_order` topic and one POST; wait once to terminal.
6. Accept only a validated candidate or a precise non-retryable fail-closed
   result with zero candidates; then stop 8911 immediately and perform Codex
   review.
7. Do not start Phase B writes or claim Phase A/runtime/commercial completion
   until A6 evidence is closed.

This was the exact pause boundary before A6. The current runtime checkpoint is
`context/medical_monitoring_p10_v12_runtime_gate_20260801_context.md`; no
background task or product service was left running after A6 either.
