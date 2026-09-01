# MODE=EXECUTION — r42 clone attempt-3 controlled recovery

## Objective

Apply the accepted v2-to-v3 planner contract transition exactly once to the
isolated r42 clone and observe the durable terminal result. Recover only the
five retained failed items; never touch the original r42 runtime or repeat
triage, download, OCR, preparation, or the full batch.

## Source of truth

- Project: `proj_user_68cf6466bd71`
- Batch: `wref_translation_batch_ad27f97d2f06c106b0c2a158`
- Original runtime, read-only:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/runtime`
- Isolated clone, the only business runtime allowed to mutate:
  `runs/execution/mw_r42_planner_retry_20260731/runtime`
- Accepted implementation/reviews:
  - `runs/codex_mw_r42_contract_supersession_execution.md`
  - `runs/codex_mw_r42_generation2_fixture_rereview.md`
- Prior attempt-2 evidence:
  `runs/mw_r42_planner_retry_controlled_replay_20260731.md`
- Hy-MT2 route evidence:
  `runs/execution/mw_r42_hymt2_model_recovery_20260731/RECOVERY_REPORT.md`

## Read these files only

Read these files only:
- `runs/codex_mw_r42_contract_supersession_execution.md`
- `runs/codex_mw_r42_generation2_fixture_rereview.md`
- `runs/mw_r42_planner_retry_controlled_replay_20260731.md`
- `runs/execution/mw_r42_hymt2_model_recovery_20260731/RECOVERY_REPORT.md`
- `services/api/app/main.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/omlx_workload_gate_client.py`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/runtime`
- `runs/execution/mw_r42_planner_retry_20260731/runtime`

Normal Python imports needed to start the product service are execution, not
permission to broaden manual source inspection.

## Mandatory preflight

Before starting any service, fail closed unless all are true:

1. Original batch remains `partial_failure`, attempt 1, with item counts
   `2 candidate_ready / 13 excluded / 5 failed_retryable`, 23 upper-layer
   stage runs, latest `2026-07-30T06:22:31.832611+00:00`.
2. Clone batch remains `partial_failure`, attempt 2, with the same item-state
   counts, 28 upper-layer stage runs, 12 plans, and no durable job later than
   `mwjob_2d6bbc9bad1e71d030c3afa5`.
3. The five failed clone items retain the exact artifact/item identities and
   generation-2 lineage from the prior report; three have accepted v2 plans
   and translation failures, while the two-item artifact has one canonical
   planner failure source plus one derived sibling.
4. No process listens on the chosen isolated API port.
5. `127.0.0.1:8000/v1/models` returns HTTP 200 and includes exactly
   `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`.
6. `/Users/smkzw/.codex/tools/omlx_workload_gate.py status` reports zero active
   and queued OCR/translation leases and the translation default is that exact
   model.
7. The six-module offline gate is already accepted at 198 passed; do not
   rerun it here.

Capture bounded counts/hashes only. Do not copy secrets or clinical/provider
text into the report.

## Single controlled action

- Start one isolated single-process API using the clone runtime, a new
  localhost-only port, `WORKBENCH_INCLUDE_REFERENCE_PROJECTS=false`, and
  `WORKBENCH_CLIENT_CONTRACT_MODE=enforce`.
- Use the clone's existing runtime settings and role bindings. Do not rewrite
  credentials or route configuration.
- Confirm health/readiness, exact client contract, exact translation model,
  and gate visibility before mutation.
- Submit exactly one POST to:
  `/api/projects/proj_user_68cf6466bd71/medical-writing/references/translation-batches/wref_translation_batch_ad27f97d2f06c106b0c2a158/retry`
- Use actor `medical_manager`, current contract header, and the new unique
  idempotency key `r42-planner-contract-v3-generation3-20260731`.
- Require HTTP 202, batch attempt 3, and one durable job ID. Do not send a
  duplicate request.
- Leave the single launched route pending and wait for the existing durable
  worker to reach terminal state. Use one bounded terminal watcher with
  backoff/event-based waiting and a 120-minute hard deadline; do not perform
  fixed-interval controller polls, redispatch, or manual worker reclaims.
- The product's integrated oMLX gate must own translation leases. Do not call
  Hy-MT2 outside the product path and do not override the gate-selected model.
- On terminal completion, stop only the service process started by this task
  and confirm its port is closed. Never kill by broad process pattern.

## Postconditions to verify

Read the original and clone again and report:

- original batch/item/stage-run/plan state is unchanged;
- clone terminal batch/item counts and new durable-job state;
- exact new v3 plan migrations for the three accepted v2 plans, with no
  planner provider call and immutable v2 rows preserved;
- exactly one fresh v3 planner root plus one distinct supersession edge for
  the canonical two-item artifact, with no sibling planner call;
- no ordinary cross-prompt retry lineage;
- no duplicated plan/stage/audit/provider/translation rows across durable
  attempts or restart-safe reuse;
- new chunk/integration/translation/QC/fidelity outcomes, bounded stable error
  codes, and remaining failed item identities if any;
- oMLX gate returns to zero active/queued leases.

Do not declare recovery merely because HTTP 202 was returned. Classify the
terminal outcome from persisted state.

## Hard boundaries

- Never modify the original r42 runtime.
- The clone runtime is the only allowed product-state write surface.
- Do not modify product source, contracts, tests, prompts, context, reviews,
  or metrics.
- Do not rerun triage, download, OCR, preparation, full batch creation, or any
  ready/excluded item.
- Do not download models or start a second oMLX server.
- Do not expose secrets, prompt/provider text, translated clinical text, or
  credentials in logs or reports.

## Output

Task-created service logs and bounded snapshots may be stored only under:
`runs/execution/mw_r42_attempt3_controlled_recovery_20260731/`

Write exactly one output file:
`runs/mw_r42_attempt3_controlled_recovery_20260731.md`

Report preflight, the single request, durable terminal result, exact persisted
delta, non-repetition/original-runtime proof, cleanup, residual risk, and next
safe action. End with `EXECUTION_COMPLETE`.
