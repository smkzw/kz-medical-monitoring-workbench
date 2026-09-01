# Writing Reference Preparation Reconciliation P0

Updated: 2026-07-20
Owner: Codex
Status: prepared; dispatch after shared `main.py` writer is free

## Observed Failure

A real product journey downloaded and extracted a public CT.gov Protocol/SAP.
Content validation correctly returned `mismatch`, causing the preparation item
and batch to end in `review_required`.

The product already exposes:

`POST /api/projects/{project_id}/medical-writing/references/documents/{artifact_id}/content-validation/override`

The batch item includes `artifact_id`. The defect is not a missing override API.
After a successful override, preparation retry selects only `failed` items and
does not reconcile `review_required` items, so the batch remains stale and the
normal translation-batch path stays blocked.

## Existing Capability To Preserve

- GLM-OCR-bf16 contract, 200 DPI minimum, concurrency 8.
- Flash document planning/chapter recognition.
- Hy-MT2 chapter/chunk body translation.
- Flash integration and boundary QC.
- Translation batch lineage, retry, and model/prompt/hash records.

Do not rebuild these capabilities unless a real isolated call proves a concrete
missing link.

## Target

The medical manager's single override action is the decision. The document
validation becomes `user_overridden`, every current `review_required`
preparation item for that artifact is reconciled idempotently to `prepared`,
batch counts/status are recomputed, and the normal translation-batch action
becomes available. No second medical approval.

## Acceptance

1. Existing document override route remains the only validation override
   authority.
2. Override success atomically or idempotently reconciles matching current batch
   items; stale/superseded artifacts are rejected.
3. A second identical call is a replay, not another decision.
4. `failed` retry semantics remain unchanged.
5. Batch counts/status reflect prepared/review-required items correctly after
   reconciliation.
6. A translation-batch preview/create can proceed immediately afterward.
7. Text-native PDF records OCR as not applicable; scanned/image pages execute
   GLM-OCR at >=200 DPI and <=8 concurrency through the existing pipeline.
8. Real isolated probe preserves PDF/hash and actual model lineage or exact
   local-service failure.

