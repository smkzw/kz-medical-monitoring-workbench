# Medical Writing Competitor Triage P0 Implementation Context

Updated: 2026-07-20
Owner: Codex architecture and final acceptance
Status: prepared; dispatch only after structured-authority worker releases shared files

## Goal

Implement the product-owned DeepSeek v4-pro competitor Protocol/SAP relevance
triage between the bound ClinicalTrials.gov snapshot and deterministic document
preparation. The runtime must not depend on Codex, Hermes, Qoder, CodeBuddy, or
any execution/conference agent.

## Existing Truth

- The authoring journey endpoint already creates and binds an immutable
  ClinicalTrials.gov search snapshot.
- `DeepSeekPrefillAdapter` is prefill-only and must remain separate.
- Search pagination, document discovery, download, hashing, and storage are
  deterministic backend responsibilities.
- Current relevance decisions are written one NCT at a time to
  `writing_reference.sqlite3`.
- Current corpus triage is projected into
  `medical_writing_authoring_journey.sqlite3`.
- A product AI triage run, immutable prompt/input/output provenance, an
  AI-recommended basket, and a one-action basket confirmation do not exist.

## Transaction Boundary

Do not claim an impossible cross-file SQLite transaction.

The authoritative confirmation record, selected basket, and all relevance
decision rows must be committed atomically in `writing_reference.sqlite3`.
The authoring-journey corpus-triage state is a deterministic idempotent
projection carrying the authoritative confirmation id/hash. The public confirm
command returns success only after projection succeeds. If projection fails,
the authoritative confirmation remains `projection_pending`; retry replays the
same projection without asking the user to approve again.

This preserves one user decision, auditability, crash recovery, and truthful
atomicity.

## Production AI Boundary

- Direct configured DeepSeek supplier, exact model `deepseek-v4-pro`.
- The model receives only minimum project facts and candidate/document metadata
  from the frozen snapshot.
- The model does not browse, paginate, download, or invent NCTs/documents.
- One versioned JSON prompt/schema.
- Server must verify the provider's exact response model identity and reject
  unknown/duplicate/missing NCTs, invalid enum values, malformed confidence,
  and document-role claims outside the frozen snapshot.
- Deterministic filtering may remain a provisional fallback view but must never
  be persisted or labelled as completed AI triage.

## Required State

- Run: queued, running, review_ready, partial_failed, failed, stale, confirmed,
  projection_pending.
- Chunk: deterministic chunk id/order/input hash/status/attempt/error.
- Candidate result: classification, confidence, matching dimensions, document
  suitability, reason, evidence gaps.
- Provenance: provider, exact response model, prompt version, canonical input
  hash, canonical output hash, snapshot id/hash, journey revision and facts
  hash, timestamps.
- Confirmation: selected candidate ids, excluded ids, actor, confirmation hash,
  atomic materialization status, projection status, retry count.

## Acceptance

1. All model-returned NCTs are a complete exact permutation of each input chunk.
2. Unknown, duplicate, missing, or invalid output fails the chunk closed.
3. Partial failure preserves successful chunks and retries only failed chunks.
4. Snapshot or material project-fact changes make the run stale and
   unconfirmable.
5. One confirmation atomically writes the confirmation and all relevance
   decisions in the reference database.
6. Journey projection is idempotent and recoverable without a second user
   decision.
7. A confirmed basket can directly drive the existing preparation batch.
8. Audit evidence contains real model/prompt/input/output identity and hashes.
9. Existing manual relevance endpoints continue as compatibility APIs but are
   not the new default UI path.
10. Focused tests use an injected fake provider; a later isolated real-product
    probe must use the production DeepSeek configuration.

## Non-Goals For This Worker

- No frontend redesign.
- No OCR/Hy-MT2/Flash implementation.
- No 12-lane long run.
- No changes to stable runtime or real user projects.

