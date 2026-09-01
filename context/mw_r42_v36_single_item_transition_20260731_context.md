# Task Context: mw_r42_v36_single_item_transition_20260731

Created: 2026-07-31 22:53:37
Objective: Design and offline-prove an idempotent v36 downstream-contract transition for the single r42 fidelity-blocked item without touching immutable rows, 4 candidate-ready items, 15 excluded items, original r42, clone runtime, services, OCR, translation, or prior attempts
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem under this workbench.
- `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md` (preserved checkpoint;
  SHA-256 at intake:
  `d354eb0b4f8b98225c831d76f752b346315949e0e78983f24c6392c91d255130`).
- `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`, especially
  Phase 0A.
- `context/mw_commercial_writing_gap_20260731_context.md`.
- `reviews/mw_commercial_writing_gap_20260731_independent_challenge.md`.
- Current implementation and focused tests connected to batch/item retry,
  repository persistence, chapter translation, fidelity validation, downstream
  planning, and supersession. The exact file set will be recorded after
  structure reconnaissance.
- Original r42 runtime is read-only evidence only:
  `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r42-20260730/slots/A1/lazy_medical_writer/runtime`.
- The sole clone is also read-only in this task:
  `runs/execution/mw_r42_planner_retry_20260731/runtime`.

## Scope

- In scope:
  - Read-only audit of the `completed_with_blocked` batch/item API,
    repository, state transitions, current retry blast radius, and v35→v36
    downstream identity contract.
  - Design of one idempotent and auditable transition for
    `wref_translation_item_4dae08490b884310d35a6198`.
  - Deterministic offline proof using temporary repositories/fakes.
  - The smallest reversible product/test patch only if the current API cannot
    satisfy the single-item contract.
  - Focused and related-surface tests that do not start services or access
    either runtime.
  - Independent delta-only contradiction review after Codex verification.
- Out of scope:
  - Starting services, opening ports, running either original or clone runtime,
    calling product AI, OCR, translation, or oMLX.
  - Re-running triage, candidate lock, download, preparation, OCR, full
    translation, attempts 2/3, 4 candidate-ready items, 15 excluded items, or
    any existing idempotency key.
  - Editing immutable persisted rows or describing clone changes as original
    r42 restoration.
  - Synopsis, CSR, browser/Word release testing, or medical-monitoring files.

## Success Criteria

- Establish whether the existing batch retry can operate on exactly one
  fidelity-blocked item without touching any ready/excluded item.
- If it cannot, implement a dedicated transition that:
  - accepts only the target item and expected current revision/contract;
  - creates new v36 downstream identities and never reuses v35
    plan/chunk/integration/candidate identities;
  - preserves every old immutable row;
  - is idempotent across duplicate request, duplicate worker, and restart;
  - records request, source/target contracts, lineage, result, and audit state;
  - fails closed for invalid state, stale revision, wrong item/batch, identity
    collision, or unresolved clinical abbreviation fidelity.
- Offline tests prove:
  - only the target item changes;
  - original r42, 4 candidate-ready, and 15 excluded objects do not change;
  - ordinary `VISIT`/`SCHEDULE` headings pass under v36;
  - real clinical abbreviations still fail closed;
  - duplicate execution creates no duplicate model call or durable row.
- Codex reviews exact diffs and focused regression output; an independent
  reviewer returns READY or all deltas are repaired.
- Finish with a no-loss checkpoint and a clone-only runtime request; do not run
  the clone without separate user authorization.

## Risk Boundaries

- Allowed task-record writes:
  `context/mw_r42_v36_single_item_transition_20260731_context.md`,
  `plans/mw_r42_v36_single_item_transition_20260731.md`,
  `reviews/codex_mw_r42_v36_single_item_transition_20260731_review.md`,
  `metrics/mw_r42_v36_single_item_transition_20260731_metrics.md`, and a
  dedicated no-loss/authorization-request record. The runner-reserved
  `runs/codex_mw_r42_v36_single_item_transition_20260731.md` and stdout file
  must not be edited directly.
- Product/test writes are allowed only after read-only audit identifies the
  exact connected files; record the baseline hashes and preserve unrelated
  concurrent changes before editing.
- Never write either runtime path, the original r42 evidence, or the preserved
  r42 checkpoint.
- Do not inspect or modify concurrent medical-monitoring files.
- Do not use destructive git/filesystem operations or broad cleanup.
- Route resolution: the current global Section 12 and workflow guard are
  executable truth. The guard selected Codex direct. Dated local routing text
  is not used where it conflicts with the current global route contract.
- External discovery is not repeated because this bounded phase introduces no
  new dependency or tool choice; reopen discovery only if implementation
  requires a material external component.
- The delegated agent is not final authority; Codex owns verification and
  acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-31 22:53:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-31 23:xx CST: Read-only API/repository audit completed. Existing
  batch retry selects only `failed_retryable`; with clone `0 failed` it is a
  no-op that preserves 4 ready/15 excluded but cannot transition the blocked
  item. Batch-wide retry is rejected as the transition route because its
  executor does not enforce payload `failed_item_ids`.
- 2026-07-31 23:xx CST: Clone DB was queried with SQLite `query_only` /
  `-readonly` only. Exact source identity is recorded in
  `plans/mw_r42_v36_single_item_transition_20260731.md`; no runtime file was
  changed.
- 2026-07-31 23:xx CST: Selected minimal design is an immutable semantic
  transition record plus a deterministic one-item child batch and new v36
  plan identity. The source batch/item and all v35 immutable rows remain
  unchanged.
- 2026-07-31 23:xx CST: Independent repository audit identified an exact-once
  gap across process death after external-call dispatch. The implementation
  must persist a transition-scoped external-call intent before invocation and
  fail closed on an unknown outcome rather than repeat the call.
- 2026-07-31 23:40-23:52 CST: Initial independent conference passes ran once
  on the guard-selected native Codex and Pi/DeepSeek routes. The native pass
  reproduced a P1 takeover race in a temporary repository: stale stage
  persistence silently returned, so two owners could both invoke Hy while
  only one call intent was recorded.
- 2026-07-31 23:58 CST: The race was repaired without changing the selected
  architecture. A stale/missing stage CAS now raises `_OwnershipLostError`,
  and ownership is checked again after the call-intent transaction commits
  and before provider invocation. Added deterministic ownership interleavings
  before and after intent commit, direct persisted-chunk settlement, distinct
  pre-dispatch restart status, child-batch retry rejection, and explicit
  OpenAPI response-contract coverage.
- 2026-07-31 23:59 CST: Five new focused tests and the complete connected
  regression passed. Result: `258 tests in 12.287s, OK`. Same-session
  delta-only participant re-review is pending; clone runtime remains
  unauthorized and untouched.
- 2026-08-01 00:08 CST: Both same-session participant rechecks returned
  `READY`, no unresolved P0-P4.
- 2026-08-01 00:20 CST: Pi/Alibaba chair independently traced the repaired
  implementation, reran `258` tests, and returned `READY`. Codex final hashes
  matched the frozen post-remediation values; preserved connected hashes and
  the r42 checkpoint still match intake. Ports 55342/55343/55344 have no
  listener.
- 2026-08-01 00:20 CST: Durable READY/no-loss record and clone-only request
  written to
  `runs/MW_R42_V36_SINGLE_ITEM_READY_AND_CLONE_AUTH_REQUEST_20260801_0020.md`.
  The task is paused before service start or POST.
- 2026-08-01 00:49-00:58 CST: User supplied the exact clone-only
  authorization. Codex revalidated frozen code/source identities, created a
  complete 1,422-file APFS clone, started only the authorized single-worker
  API on 55344, and sent the approved POST exactly once.
- 2026-08-01 00:53 CST: The unique job
  `mwjob_0b3a7a26f3f7189c913bd57c` completed on attempt 1. The single new
  child item reached `candidate_ready` under the exact v36/Hy contract.
- 2026-08-01 00:54-00:58 CST: Post-run logical diff proved every pre-existing
  database row has `0 modified / 0 deleted`; the protected r42/v35 collection
  hash is identical, original r42 hashes are unchanged, DB integrity is OK,
  55344 is closed, and gate leases are zero.
- 2026-08-01 00:58 CST: A contract-scope delta was isolated. The child
  integration-QC path appended two upper-layer stage runs (Flash degraded,
  Pro failed terminal) and one escalation record. They are fully tied to the
  new child and did not alter other data, but those two table classes were not
  named in the authorization whitelist. Detailed evidence and the next
  decision are in
  `runs/MW_R42_V36_CLONE_TRANSITION_SCOPE_DELTA_PAUSE_20260801_0058.md`.
- 2026-08-01 01:02 CST: Full 1,422-file post-run comparison also found
  physical hash changes in the clone's monitoring-batches and
  monitoring-daily-runs SQLite/SHM files. Snapshot/current logical table
  comparison is identical with zero row/schema delta and integrity OK. This
  is recorded as a strict file-boundary delta; no monitoring business data or
  external concurrent monitoring workspace changed.
- 2026-08-01 01:05 CST: Read-only source trace confirmed both deltas are
  deterministic current-product behavior. `completed_degraded` is an explicit
  automatic Pro-escalation trigger with Flash/Hy fallback when Pro fails.
  Importing full `main:app` unconditionally constructs monitoring repositories
  whose initialization sets WAL mode and opens write transactions. No current
  medical-writing-only app or monitoring-disable/lazy-init entrypoint exists.

## Final Status And Next Safe Action

`RUNTIME_ACCEPTED / PHASE_0A_CLOSED`.

On 2026-08-01 08:45 CST, the user explicitly accepted:

- the two target-bound upper-layer stage runs and one target-bound escalation
  as the child integration-QC lineage; and
- the clone-local monitoring SQLite/SHM physical changes with zero logical
  schema or row delta.

The r42 v36 downstream transition is therefore runtime accepted and Protocol
Phase 0A is closed. The authorized POST remains completed and must not be
repeated; do not restore the snapshot, resend the request, or rerun any frozen
r42 stage. The next safe action is to rebaseline the remaining Protocol P0
gates from the current filesystem, while preserving the concurrent
medical-monitoring boundary.

## Current Product/Test Hashes

SHA-256 after the ownership-race remediation:

- `services/api/app/writing_reference_translation_batch.py`:
  `85d16300e98753d932465a35efe0c5238fa664a90b7537be5c3bf6a314d0431c`
- `services/api/app/main.py`:
  `e00da4ec5d7c0e0a98c4ad9e280eacb7654f42eaeeeba17ab6ff61f6da3f4a06`
- `packages/contracts/workbench_contracts/models.py`:
  `e2ae86cc7bff01459ee62cde9ec0392e88b87f565d05b2c14b221161c85f7ff6`
- `tests/test_writing_reference_translation_batch.py`:
  `3a6667fe81022cb3fa04d0710614e3b68409fa2b17ca6a5bc4bc966d0b094b01`

Preserved connected files still match intake exactly:

- `writing_reference_repository.py`: `807dd494…adfe4d`
- `writing_reference.py`: `1b3efedf…c07b5`
- `chapter_translation_pipeline.py`: `e7154470…00cbd`
- `test_writing_reference_translation_durable_jobs.py`: `61c3595e…24e8c`
- `test_mw_v11_translation_alignment.py`: `4f92fc91…007c`
- r42 checkpoint: `d354eb0b…55130`

## Connected File Baseline

SHA-256 before the Phase 0A product/test patch:

- `services/api/app/writing_reference_translation_batch.py`:
  `cfb402f2922081a113613ff54151bfbf73b0a1093c60df938f8acca22bd02b1a`
- `services/api/app/writing_reference_repository.py`:
  `807dd494362d344a7f139adb000f9b4d51de477d93a8c56bfc1616c309adfe4d`
- `services/api/app/main.py`:
  `13194efb6f1c931ec183b70878166dd1f59c4d8cacb0fb5a958a5bf1ef685501`
- `packages/contracts/workbench_contracts/models.py`:
  `4ab7113ca20d5ab48d14afbd382575625a10c30f78f4191e2442361027616025`
- `tests/test_writing_reference_translation_batch.py`:
  `56144f621e9ab6444f98b3a49bc09fcfa5f65ed5e5f9846e07f93df11933b563`
- `tests/test_writing_reference_translation_durable_jobs.py`:
  `61c3595e7c4c74483c5c907edf599b26e0e59c15b0c34e1cf3a4ab624ae24e8c`
- `tests/test_mw_v11_translation_alignment.py`:
  `4f92fc9192227e2e6896f9437a00330bb4ac127cf87dd9fca3dc4b4609e7007c`
- `services/api/app/writing_reference.py`:
  `1b3efedfa8693e808b655a2eca8219993c242489793049571c6fa86368cc07b5`
- `services/api/app/chapter_translation_pipeline.py`:
  `e7154470e24664692f568acf7c6e4c0cd37afeaaa60c1a89423d943f05d00cbd`
