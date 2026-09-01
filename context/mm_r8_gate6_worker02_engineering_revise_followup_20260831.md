# G6 Worker 02 Same-Session Engineering Revision — Binding Matrix And Challenge Fixture

Continue the same admitted `worker_02` session. Do not start a new session, service, browser, model, network call, or subprocess Agent.

## Hard boundaries

- Work only inside the current workbench and only on the allowed files below.
- Do not access real projects, medical-writing source, credentials, external accounts, or paths outside this workbench.
- This is synthetic/offline implementation only. Do not claim G6 acceptance.

## Read these files only

- `reviews/medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831.md`
- `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_02_identity_followup.md`
- current `deploy/medical_monitoring_local/synthetic_ego.py`
- current `tests/test_medical_monitoring_r8_gate6_synthetic_ego.py`
- current `tests/test_medical_monitoring_g6_synthetic_bundle_endpoint.py`

## Independent review findings to close

1. P0: the bundle exposes only alpha/full run binding while the UI allows 2 projects × 3 modes.
2. P1: §15.4 evidence is pre-marked passed instead of defining executable application task initial states.
3. P2: the challenge fixture lacks dense same-day multi-domain events and long Chinese labels.

## Assigned repair

1. Extend the canonical audience bundle with a deterministic, validated `run_bindings` matrix covering every exact project × analysis mode pair (2 × 3 = 6). Each row must carry and validate project_ref, admission_id, run_ref, analysis_mode, fixture/profile/source/output identities and its own distinct run `binding_digest`. Keep profile binding separate from each selected run binding.
2. Update bundle validation to require exactly the complete 6-pair matrix, reject missing/duplicate/wrong-project/wrong-mode/stale/forged bindings, and prove each row equals a direct `build_synthetic_binding` result.
3. Keep `bundle.binding` only if needed for backward-compatible default alpha/full inspection; runtime consumers must use `run_bindings`. Make this distinction explicit in code/tests.
4. Strengthen the fixture without disease/drug/score/listing-format hardcoding:
   - at least one visit date has AE/MH/CM/IP/LAB/PD and other relevant event markers together;
   - include long, natural Chinese event/detail/source labels that exercise wrapping without encoding a real drug/disease;
   - retain 2 projects, 3 centers, 12 subjects, 48 visits, 96 events, 8 domains, three modes, flow split/merge/zero/center differences;
   - independently rebuild and validate chronological order, marker/domain counts, risk binding, flow totals, and table totals.
5. Replace pre-passed §15.4 task evidence semantics with a canonical required-task specification and explicit initial file/application states. A later actual-app task engine must generate per-run evidence only after user actions. Keep replay helpers only as backend oracle support; they must no longer imply audience completion before execution.
6. Update focused synthetic tests for all above and return new canonical fixture/profile/default-run/bundle/task-spec digests. Do not update frontend constants, actual-app manifests, or release hashes in this pass; later same-session workers will consume the new digests.

## Allowed files

- `deploy/medical_monitoring_local/synthetic_ego.py`
- `tests/test_medical_monitoring_r8_gate6_synthetic_ego.py`
- `tests/test_medical_monitoring_g6_synthetic_bundle_endpoint.py` only for canonical-shape assertions not actual-app implementation
- runner-managed worker report only

## Verification

Run the focused synthetic tests without listeners. Report exact counts, all new digests, six pair identities, dense/long-label oracle results, remaining downstream changes, and any uncertainty. Do not claim G6 acceptance.

## Output

Return one compact handoff to the runner-managed output file `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_02_engineering_revise.md`. Do not write that report path directly through file tools.
