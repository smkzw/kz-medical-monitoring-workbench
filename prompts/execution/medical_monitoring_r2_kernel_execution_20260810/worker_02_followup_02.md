Continue the same worker_02 session for the second and final targeted Batch B repair. Codex confirmed that follow-up 01 closed some original attacks but reproduced fifteen authority bypasses and a net loss of fifteen prior tests. Repair the trust boundaries coherently; do not broaden into Batch C.

Hard boundaries:
- Modify only Batch B-owned files under `poc/medical_monitoring_ai_native_r2/src/mm_r2/` and `poc/medical_monitoring_ai_native_r2/tests/`, plus minimum already-authorized Batch B exports/registry/README extension.
- Preserve Batch A ACCEPT and every prior report/VETO as immutable history. Do not edit Batch A implementation contracts.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_02_followup_02.md`. Do not write this report yourself; return the complete report in the final response.
- Do not edit Batch C, R1, product, medical-writing, real-project, shared-runtime, service, credential, network, or 8911 surfaces.
- Python 3.9 stdlib plus existing pytest only; synthetic/offline only; no dependency install or upgrade.
- Do not delete, replace, skip, xfail, weaken, or rename away prior behavioral tests to make the suite pass. Restore the initial 102 Batch B behavioral checks with signatures adapted to the corrected API, then add direct regressions for every VETO 1 and VETO 2 attack.

Read these files only:
- `reviews/codex_execution_medical_monitoring_r2_batch_b_negative_gate_veto1_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_negative_gate_veto2_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_a_independent_accept_20260810.md`
- `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_02.md`
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`
- `poc/medical_monitoring_ai_native_r2/README.md`
- current files under `poc/medical_monitoring_ai_native_r2/src/mm_r2/`
- current files under `poc/medical_monitoring_ai_native_r2/tests/`

Required coherent repairs:

1. Real acceptance and snapshot binding:
   - BaselineService, RunManager, and DiffService must require the real accepted `AcceptanceService` authority, not duck typing or a hostile subclass. Resolve the registered `SnapshotBinding` and compare the exact project, snapshot ID, revision ID, content digest/hash, row count, structure, mapping, and identity binding relevant to the operation. Same-ID different-content substitution must fail.
   - Reject `blocked=True` records even if their retained state is `snapshot_accepted` or `baseline_eligible`.
   - Run fields for source revision, mapping version, and identity digest must be derived from the live binding or exact-validated against it; fake revision/config strings cannot enter a run.
   - Incremental diff must require a DataBaseline registered in the supplied real BaselineService, with exact baseline hash/project/snapshot binding; fabricated or cross-service baselines fail.

2. No reachable service issuer:
   - Remove ordinary-caller callable `_verified_baseline`, `_verified_mdv`, `_verified_run`, `_verified_instance`, `_verified_adjudication` or equivalent authority factories from service/class/module surfaces. Public constructors remain blocked. Issuance must occur only inside the validated public service operation through a closure or equivalently non-reachable capability.
   - Add regressions that `hasattr(service, issuer_name)` is false and that direct construction still fails.

3. Diff authority and provenance:
   - Remove caller authority over canonical mapping/provenance. Derive field mapping IDs/canonical names from the accepted snapshot binding. For an unmapped changed field emit an explicit nonempty unmapped provenance marker and `is_unknown_field=True`, or fail closed; never silently emit an empty mapping ID.
   - Reject empty record-key definitions and missing/unknown key values, including `UN`, `UNK`, `UNKNOWN`, case-insensitively. Partial dates cover YYYY, YYYY-MM, and case-insensitive UN/UNK components.
   - Preserve full semantic hashing, deterministic ordering, content digest checks, duplicate-key checks, config/data separation, scope/disappearance behavior, and all initial diff tests.

4. Adjudication authority, actors, actions, and targets:
   - User-confirmed issuance must bind exactly the configured local user; an optional `user` argument may only equal that user. Machine issuance can never claim user confirmation.
   - Validate action actor against the configured local user or the declared system-policy actor rather than accepting any nonempty string.
   - An adjudication must bind its intended action and the complete exact target set. Establish evidence must contain the registered candidate ID and match the candidate's nonempty snapshot/rule/mapping/knowledge references. Single-risk actions require the exact registered risk identity. Merge requires all and only merged risk identities; split requires the exact parent plus child-spec digest or equivalent immutable action binding. A foreign-only evidence field cannot authorize anything.
   - Same lifecycle, stored object/hash, project, outcome, action, target set, and evidence must all match at use time.

5. Risk lifecycle integrity:
   - Close must read a real nonblocked accepted coverage snapshot from a real AcceptanceService; remove `coverage_snapshot_accepted` and every caller-asserted authorization boolean.
   - Once any lifecycle transition is user-confirmed, `confirmed_by_user` remains true. High-risk or ever-user-confirmed risks require user-confirmed closure.
   - Establish/transition/merge/split validate actor, instance identity project/domain, complete transition continuity, legal current state, and lineage before mutation. Merge cannot cross project/subject/domain and cannot use an adjudication bound only to a subset. Split cannot cross subject/domain/project and must validate all child specs before mutation.
   - Prepare every new transition/instance and all replacements before committing registries or chain heads; a failure leaves instances, transitions, adjudications, and chain state unchanged.

6. Restore prior behavioral coverage:
   - Reconstitute the original worker report's 35 risk, 18 baseline, 21 mode, and 28 diff behaviors (102 total) with corrected API expectations. Keep every follow-up negative regression in addition; final B collection must not be below 102 and should materially exceed it.
   - Explicitly restore coverage for baseline/history/current advancement; MedicalDecisionVersion histories and signed/exported rules; all mode entry conditions and ordered runs; risk states, legal transitions, immutable identities, evidence validation and chains; diff digest/revision/binding checks, full/incremental taxonomy equivalence, duplicate keys, mapping provenance, unknown/partial values, impact inputs, deterministic output, and config separation.

Required verification:
- All fifteen VETO 2 executable attacks and all nine VETO 1 attacks fail closed.
- Focused new negative tests pass; Batch B collection is at least 102 without xfail/skip; all Batch B and all R2 tests pass with cache disabled and `PYTHONDONTWRITEBYTECODE=1`.
- In-memory syntax compilation passes; no `__pycache__`, `.pytest_cache`, or `.pyc` remains.
- Return exact changed paths, API changes, restored-versus-new test counts, exact commands/results, stable hashes, and residual POC limitations. Do not claim Batch B acceptance.
