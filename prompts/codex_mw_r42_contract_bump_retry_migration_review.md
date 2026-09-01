# MODE=CONFERENCE — planner contract-bump retry migration review

## Objective

Determine the safe persisted behavior before a second isolated retry after
`FLASH_PLANNING_PROMPT_VERSION` changed from v2 to
`flash_toc_planning_v0_3_server_canonical_ids`.

The isolated batch currently has:

- one artifact with no accepted plan and a generation-2 failed Flash parent
  under v2;
- three artifacts with accepted v2 plans, but items failed later at Hy-MT2;
- all five items retain generation-2 retry metadata;
- batch attempt 2 is terminal partial failure.

No retry may be issued until this review proves how v2 lineage/plans transition
to v3 without fabricated calls or stale-identity reuse.

## Read these files only

Read these files only:
- `runs/mw_r42_planner_retry_controlled_replay_20260731.md`
- `runs/codex_mw_r42_server_canonical_chapter_ids_execution.md`
- `runs/codex_mw_r42_server_canonical_chapter_ids_review.md`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Questions

1. Will the current code replay/fail when a generation-2 retry parent has v2
   prompt version but the new request uses v3?
2. Will the three accepted v2 plans be safely reused, deterministically
   canonicalized, or unnecessarily replanned?
3. What invariant should distinguish ordinary same-contract retry from
   server-owned contract supersession?
4. Is the safest route:
   - bounded deterministic migration of accepted v2 plans to canonical IDs;
   - a new generation with explicit supersession ancestry;
   - controlled cross-prompt retry-parent validation;
   - or another minimal mechanism?
5. What exact persisted-path regression must pass for the one no-plan artifact,
   the three old-plan translation failures, duplicate execution, and worker
   restart?

## Hard boundaries

- Read-only except for the single report below.
- Do not access original/clone runtime, start services, invoke providers,
  acquire leases, run translation/OCR, or retry items.
- Do not edit source/tests or weaken versioning/idempotency/lineage.
- Do not read/write outside the explicit list.

## Output

Write exactly one output file:
`runs/codex_mw_r42_contract_bump_retry_migration_review.md`

Give READY-AS-IS or NOT READY, root cause, selected/rejected design, exact
file/test plan, compatibility/privacy analysis, and next safe action. End with
`ACCEPTANCE_REVIEW_COMPLETE`.
