Continue the same worker_02 session. This is a targeted Batch B repair after Codex VETO; do not broaden into Batch C, R1, product, medical writing, real projects, services, or 8911.

Hard boundaries:
- Modify only Batch B-owned files under `poc/medical_monitoring_ai_native_r2/src/mm_r2/` and `poc/medical_monitoring_ai_native_r2/tests/`, plus the minimum already-authorized public exports and README extension.
- Preserve the accepted Batch A record and all prior reports/VETO records as immutable history. Do not redesign or weaken Batch A contracts.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_02_followup_01.md`. Do not write this report yourself; return the complete report in the final response.
- Do not edit Batch C, R1, product, medical-writing, real-project, shared-runtime, service, credential, network, or 8911 surfaces.
- Python 3.9 stdlib plus the existing pytest only. Use synthetic/offline data only; do not install or upgrade dependencies.
- Make coherent authority-boundary repairs, not test-specific patches. Codex and the independent reviewer own acceptance.

Read these files only:
- `reviews/codex_execution_medical_monitoring_r2_batch_b_negative_gate_veto1_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_a_independent_accept_20260810.md`
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`
- `poc/medical_monitoring_ai_native_r2/README.md`
- current files under `poc/medical_monitoring_ai_native_r2/src/mm_r2/`
- current files under `poc/medical_monitoring_ai_native_r2/tests/`

The current 338 passing tests are insufficient. Repair every reproduced fail-open below and add direct negative regressions:

1. Remove all caller-asserted acceptance booleans. BaselineService, RunManager, and DiffService must bind real live `AcceptanceService` records/bindings. DataBaseline promotion must derive baseline eligibility and evidence hash from the service; it must reject unregistered, noneligible, blocked, mismatched-project/snapshot/content objects. Validate identity/mapping references. Direct public construction of authoritative baseline/run records must not bypass the service.
2. `MODE_CONTRACTS` must be an immutable mapping. Run creation must bind a real accepted snapshot/revision, not fake IDs; public direct MonitoringRun construction cannot bypass entry gates. Cross-mode carry-forward must explicitly include the immediate prior run and remain same-project.
3. Incremental diff must bind a real DataBaseline and real acceptance authority; full/incremental compare accepted full snapshots only. Unregistered/noneligible/blocked snapshots fail. Reject missing/unknown record-key components. Preserve field-level mapping provenance rather than empty mapping IDs. Expand partial-date handling to YYYY, YYYY-MM, and UN/UNK forms. `SnapshotDiff.diff_hash` must bind full DiffEntry hashes and full ConfigChange semantics/digests so same IDs with different values cannot collide.
4. RiskCandidate ID must always be deterministic, or a supplied ID must exactly match. Same-ID/different-content registration must fail and never overwrite.
5. AdjudicationRecord must be service-issued under RiskLifecycle or an equally sealed authority. Public direct construction cannot self-declare user confirmation. Machine issuance can never set `user_confirmed`. User-confirmed issuance must bind the configured local user, actual registered candidate or risk, and evidence. Establish, transition, merge, and split accept only adjudications issued and registered by the same lifecycle and consistent with project, action, and targets.
6. Establish must require candidate registration and exact identity project, subject, and domain match. Do not convert `severity_hint` into confirmed severity; confirmed severity must be explicit and evidence-authorized.
7. Close, reopen, and other material transitions must bind a valid adjudication. Close requires an accepted coverage snapshot. High-risk or previously user-confirmed risk must not auto-close without user-confirmed adjudication. Validate transition-chain continuity and target identity.
8. Merge and split must validate actor, supporting adjudication, project, target-risk bindings, and lineage. Merge cannot cross subjects or domains. Prevalidate all originals and children before any mutation so failure leaves no partial instance or transition.

Required verification:
- Add direct negative tests for all nine reproduced attacks in the VETO record and all adjacent must-cover cases listed there.
- Preserve all 236 accepted Batch A tests.
- Run focused new negative tests, every `test_r2_b_*`, and all R2 tests with cache disabled and `PYTHONDONTWRITEBYTECODE=1`.
- Run in-memory syntax compilation for the target package and tests; leave no `__pycache__` or `.pytest_cache`.
- Return exact changed paths, repaired attacks, commands and test counts, stable hashes, and residual boundary. Do not claim Batch B acceptance.
