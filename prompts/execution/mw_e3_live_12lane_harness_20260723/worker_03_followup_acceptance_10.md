You are continuing Hermes/aishuo/cms-model W3 session
`20260723_231116_362f2f`. Read and comply with
`/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.hermes/SOUL.md`, and the
closest project `AGENTS.md`. Current routing remains Hermes until
2026-07-25 01:00 Asia/Shanghai.

Read first:
- `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_fresh_completion_09.md`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_behavior_helpers.mjs`
- `frontend/tests/final_release_12lane_behavior_acceptance_09.mjs`
- `frontend/tests/final_release_12lane_behavior_pydantic_acceptance_09.py`
- `tests/test_medical_writing_durable_job_integration.py`
- `tests/test_medical_writing_revision_application.py`
- `tests/test_medical_writing_revision_durable.py`
- actual FastAPI accept-and-apply route and repository/service it calls

Hard boundaries:

- Write only current W3 child/pipeline/helpers/durable-client/acceptance_10
  files, the focused Pydantic/route test, and the narrow backend request model
  or route if an actual test proves a defect.
- Do not edit W1, W2, W4, fixtures, protocols, credentials, stable runtimes,
  unrelated product code, or reports.
- Runner-managed report path:
  `runs/execution/mw_e3_live_12lane_harness_20260723/worker_03_followup_acceptance_10.md`.
  Return the report in final text; never write that path.

Codex rejects acceptance_09 for four directly observed false claims:

1. `runResumableStages` and `CRASH_BOUNDARIES` are imported only by the test.
   `child.mjs` never imports or calls the driver. The eight tests execute a
   parallel `makeStages()` mock map whose endpoints all point to a generic
   revision-thread mock, not the child's product orchestration. Integrate one
   stage driver into the actual child journey and make tests invoke that exact
   child orchestration seam with injected adapters. Do not maintain a parallel
   test-only stage implementation.
2. The Pydantic test imports request models directly; it never issues a request
   to the FastAPI route despite its docstring. Add TestClient/ASGI endpoint
   cases using the exact JS-builder payload. Prove extra/missing/wrong-type
   payloads return 422 before the handler and a valid exact payload reaches the
   handler boundary (non-422, with the expected 404/409/success for fixture
   state). Reuse existing focused tests where valid.
3. The mock adoption replay increments its handler twice and does not maintain
   backend state or prove one logical commit; the rollback test merely makes a
   second unrelated request return 409. Exercise the actual repository/service
   and FastAPI route: same key twice must return the same persisted result and
   one revision/audit/commit; injected faults at real transaction checkpoints
   must leave thread, working copy, audit, project facts and idempotency record
   unchanged. Existing repository fault tests can be included only if rerun
   and connected to this accepted command list.
4. `EXPECT_RED` currently calls `assert.fail()` unconditionally. That proves
   only that the test runner can count an intentional failure. Replace it with
   a stable runtime fault/broken-adapter mode that violates one real acceptance
   invariant (for example, duplicate a completed POST or tamper promoted
   evidence) and is detected by the same assertion used in green mode.

Required acceptance_10:

- Actual child imports and calls the single resumable orchestration driver.
- Eight fault points correspond to the child's real project creation,
  competitor search, preparation, translation, candidate generation,
  pre-adoption, post-adoption and post-evidence boundaries.
- Restart uses persisted checkpoint/locators and real pipeline adapters; exact
  completed operations do not refire, especially adoption and evidence.
- Keep the already-correct shared source/candidate/adoption/export/evidence
  verifier calls and canonical pipeline payload builders.
- Add exact FastAPI route 422/non-422 matrix from emitted JS builder JSON.
- Run existing real repository idempotent replay and multi-checkpoint rollback
  tests plus route tests, not substitute mocks.
- Await and count each case once. Exclude acceptance_06/07/09 and disconnected
  simulations from the accepted count.

Run syntax checks, the new acceptance_10 green and genuine fault-mode red run,
focused endpoint tests, and focused real repository idempotency/rollback tests.
Report exact commands, exit codes, case names/counts, child import/call graph,
eight restart outcomes, route statuses, persisted commit/audit/revision counts,
rollback invariants and residual uncertainty.

End exactly:
`WORKER_03_E3_ACCEPTANCE_REMEDIATION_10_COMPLETE`
