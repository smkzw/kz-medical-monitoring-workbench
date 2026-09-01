Continue the same corrective session for one final narrow pass. Codex accepts the v2 replay/resume direction but found four concrete evidence inconsistencies.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Modify only the same four new integrated-closure files. All accepted modules/tests/UI data remain read-only.
- No network, dependency install, service, browser, real data, product/medical-writing path or port 8911.
- Runner-managed output path: `runs/pi_medical_monitoring_r1_integrated_closure_20260810_followup2.md`. Never write it with a tool; return the report in your final response.

Read these files only:
- `context/medical_monitoring_r1_integrated_closure_20260810_context.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/scripts/run_integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_integrated_closure.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_INTEGRATED_CLOSURE_GAP_AUDIT.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/projections.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_controller.py`

Required corrections, all reproduced by Codex on the current v2 snapshot:

1. On AI failure/skip, `ClosureResult.evidence_state` says `partial` but `store.get_run(run_id).evidence_state.value` is still `not_evaluable`. Persist the authoritative run evidence transition to PARTIAL before returning, and test Store/result equality.
2. `skip_ai=True` leaves the AI work unit PENDING, so audience progress is 6/7 and headline is “医学监查准备继续” although every downstream unit is blocked and there is no current work. Use the existing controller interruption/reconcile contract to create a real declared interrupted capability attempt and close the AI work unit as BLOCKED with zero evidence and an audience-safe Chinese reason, without calling transport. Then all 7 units must be terminal and the audience headline must truthfully say the run ended with unfinished work. Do not bypass Store's AI-work-unit gate.
3. QC currently treats `ai_raw_ref is not None` as verified consumption. Explicitly revalidate the persisted raw output with the Store public verifier and identify/revalidate the actual persisted `ai_candidate` artifact produced by `persist_capability_attempt` (not the later `ai_candidate_review` artifact and not the empty pre-persistence artifact id). QC passes only when deterministic coverage, candidate-only status, raw integrity and persisted candidate integrity all pass. Include both evidence refs and expose booleans in the internal QC payload/output. Add a focused failure-closed test using a controlled Store verifier override/corruption after controller persistence; do not add a production-only corruption switch merely for tests.
4. `_build_dashboard_artifact` writes `projection_count=0` because `ProjectionBundle.as_dict()` has no `projections` key, while the node output correctly records 9. Make artifact count and content match the persisted dashboard/site/subject projection bundle and add an equality test.

Also add a real `INTERRUPT_AFTER_AI` Store-close/reopen continuation test because the public hook currently has no test. Re-run the focused and full suites; the current actual full baseline is 321 passed (285 pre-task + 36 v2), not 320. Update the gap audit and handoff claims accordingly. Do not claim UI runtime connection or R1 overall acceptance.
