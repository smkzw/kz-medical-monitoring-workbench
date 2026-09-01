Continue the same conference participant session with a delta-only re-review.
Stay read-only. Do not inspect either prohibited runtime, do not read another
participant output, and do not start services or contact product models.

Hard boundaries:

- Work only inside the current workbench (`.`).
- Do not read or modify production paths.
- Do not edit source, tests, context, plans, reviews, metrics, or reports.
- Runner-managed report path:
  `runs/conference/mw_r42_v36_single_item_transition_review_20260731/general_pi_deepseek_flash_recheck.md`.
  Do not write it through tools; return the complete report and let the runner
  persist it.

Initial read set:
  - `AGENTS.md`
  - `context/mw_r42_v36_single_item_transition_review_20260731_conference_context.md`
  - `services/api/app/writing_reference_translation_batch.py`
  - `services/api/app/main.py`
  - `tests/test_writing_reference_translation_batch.py`
  - `tests/test_writing_reference_translation_durable_jobs.py`
  - `tests/test_mw_v11_translation_alignment.py`

The first-pass implementation has been repaired:

- `writing_reference_translation_batch.py`
  - `_persist_pipeline_stage` now raises `_OwnershipLostError` when the
    item is missing, no longer `running`, has a different attempt, or loses
    its stage-write CAS. It never silently returns success.
  - `_stage_observer` rechecks durable ownership after the stage/call-intent
    transaction commits and before provider invocation.
  - recovery uses `service_restart_interrupted` when there is no call intent
    and records recovered call IDs.
  - ordinary batch retry rejects transition child batches with
    `downstream_contract_transition_child_requires_exact_executor`.
- `main.py`
  - the transition route declares
    `WritingReferenceTranslationDownstreamTransitionResult` as its response
    model.
- `test_writing_reference_translation_batch.py`
  - takeover before intent commit: stale owner calls no model; replacement
    alone calls Hy/QC; one completed Hy ledger row;
  - takeover after intent commit: replacement fails closed with
    `model_call_outcome_unknown_after_restart`; stale owner aborts before the
    provider; no model call is issued;
  - immutable Hy chunk persisted before the after-observer: restart settles
    the dispatched ledger and completes with no second Hy call;
  - pre-dispatch recovery uses `service_restart_interrupted`, and ordinary
    retry of the child batch is rejected;
  - OpenAPI request and response schemas are pinned.

Focused new tests passed 5/5. Full related regression passed 258/258 across
translation batch, durable jobs, and v11 alignment.

Codex decision on your prior P3 question: a committed dispatch intent with no
provable persisted result remains permanently terminal by design. This is the
explicit fail-closed stop condition required to prevent a duplicate call when
the provider has no idempotency/result lookup. No automatic/operator reopen is
added because it would permit an unprovable repeat; later repair requires a
new reviewed contract/version or independent provider-side evidence.

Re-audit the exact changed lines, the two ownership interleavings, persisted
output settlement, the error code, API response contract, and ordinary retry
isolation. Run only focused deterministic offline checks if needed. Return a
complete amended participant report using the original output schema. List
only unresolved P0-P4 findings and state READY only if none remain.
