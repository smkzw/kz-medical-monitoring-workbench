# MODE=CONFERENCE — v2-to-v3 planner contract supersession acceptance

## Objective

Independently review the implemented additive, fail-closed v2-to-v3 planner
contract supersession and migration before any r42 clone retry.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_contract_bump_retry_migration_review.md`
- `runs/codex_mw_r42_contract_supersession_execution.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_contracts.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Review questions

1. Does ordinary retry remain strictly same-contract, with simultaneous
   retry-parent and contract-supersession lineage rejected?
2. Is the only accepted transition exactly
   `flash_toc_planning_v0_2_segment_ranges` to
   `flash_toc_planning_v0_3_server_canonical_ids`?
3. Are accepted v2 plans fully revalidated against the current immutable
   artifact/extraction/document/spans/coverage/role/title/anchor/order and
   downstream contract before deterministic v3 migration?
4. Are v2 source rows preserved, planner calls avoided for migrated plans, and
   v2 chunks/integrations/translations never reused under v3?
5. For a no-plan artifact, is there exactly one fresh v3 root with ordinary
   retry-parent empty and a distinct, fully validated supersession edge to the
   failed generation-2 v2 Flash source?
6. Is transition intent validated before durable-job or business mutation, and
   does every ambiguous/invalid path leave batch, item, idempotency, plan,
   audit, provider, and translation state unchanged?
7. Are identities bound into semantic payloads, fingerprints, persisted rows,
   replay checks, bounded audits, and restart-safe idempotency without
   persisting clinical/provider text or credentials?
8. Do the mixed persisted regression and focused tests truly prove the r42
   attempt-2 shape, including the derived sibling and three accepted v2 plans?
9. Is schema version 8 compatibility truthful for legacy payloads and restart?

## Required verification

Run the focused transition tests and the six-module planner/translation gate.
Report exact commands and outcomes. Review source rather than relying on the
execution report.

## Hard boundaries

- Read-only except the single report below.
- Do not access r42 original/clone runtime, start services, invoke providers,
  acquire oMLX leases, run OCR/translation, or retry items.
- Do not modify source, tests, task context, reviews, or metrics.
- Do not read or write outside the allowlist.

## Output

Write exactly one output file:
`runs/codex_mw_r42_contract_supersession_acceptance_review.md`

Give READY or NOT READY, prioritized findings with exact file/line evidence,
tests and outcomes, boundary compliance, residual risk, and the next safe
action. End with `ACCEPTANCE_REVIEW_COMPLETE`.
