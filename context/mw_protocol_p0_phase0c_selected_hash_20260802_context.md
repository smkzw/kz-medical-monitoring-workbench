# Task Context: mw_protocol_p0_phase0c_selected_hash_20260802

Created: 2026-08-02 00:18:55
Objective: 继续 Protocol P0 Phase 0C：为局部 AI 选区建立持久化 selected_hash 与 authoritative thread 重验证，兼容旧记录并对篡改/漂移失败关闭；不触碰冻结 r42/v36、上游研究/OCR/翻译或医学监查并发线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Immutable no-loss boundary: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.
- Approved route and Phase 0C exit gates:
  `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`.
- Product context and independent challenge:
  `context/mw_commercial_writing_gap_20260731_context.md` and
  `reviews/mw_commercial_writing_gap_20260731_independent_challenge.md`.
- Previous bounded Phase 0C evidence:
  `runs/codex_mw_protocol_p0_phase0c_gap_audit_20260802.md`, its context,
  review, and metrics records.
- Current authoritative implementation and focused tests under
  `services/api/app/`, `packages/contracts/`, and `tests/` in this workbench.
- Current filesystem is final truth. No external generation, OCR, translation,
  download, or frozen-row state is an authority or permitted input for this
  bounded task.

## Scope

- In scope:
  - Add a persisted `RevisionThread.selected_hash` derived from the exact
    normalized selected text, with legacy JSON backfill and strict mismatch
    validation.
  - Populate the hash for newly created AI revision threads and keep it in
    SQLite payloads, immutable revision snapshots, audit payloads, and
    idempotency fingerprints through the existing model serialization.
  - Revalidate the hash against the current authoritative working-copy
    selection before accept/apply or rewrite; paragraph, blank greenfield, and
    table-cell branches must remain isolated.
  - Add deterministic tests for new-thread persistence, legacy compatibility,
    tamper/stale-range fail-closed behavior, and a normal path.
- Out of scope:
  - r42/v36 retry, batch/item transition, preparation, download, OCR,
    translation, attempt 2/3, ready/excluded items, or immutable rows.
  - Synopsis, CSR, full diff/impact graph, DOCX preview, production promotion,
    or final multi-model/multi-role browser/Word release gates.
  - Runtime database changes, service startup, browser automation, model calls,
    or the concurrent medical-monitoring lane.

## Success Criteria

- Every newly created revision thread serializes a lowercase 64-hex
  `selected_hash`; legacy payloads without the field are deterministically
  backfilled from their stored selected text, while a supplied mismatch fails
  closed.
- The authoritative thread gate recomputes the current paragraph/table-cell
  selection hash from the active working copy and rejects a stale or tampered
  thread before AI rewrite or content write.
- Blank greenfield and table-cell paths retain their existing contracts;
  unique paragraph selection and normal persistence remain green.
- Focused deterministic tests pass; no frozen checkpoint hash, unrelated
  process, runtime database, or monitoring file changes.
- The change is only a bounded Phase 0C slice and does not imply Protocol
  release readiness.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:18:55: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Read-only audit confirmed the prior paragraph ambiguity patch
  closed matching-count and durable-preflight gaps, but `RevisionThread` still
  had no persisted `selected_hash`; the durable context hash was not a unified
  authoritative range identity. This task was kept to that one additive gap.
- 2026-08-02: Implemented `RevisionThread.selected_hash` as a lowercase
  64-hex SHA-256 of the stored exact selected text. New models compute it;
  legacy JSON without the field is backfilled at the model boundary; a supplied
  mismatch raises before persistence. The existing SQLite JSON/snapshot schema
  is unchanged.
- 2026-08-02: Added authoritative re-resolution in
  `MedicalWritingRuntimeRepository.require_authoritative_revision_thread()`:
  paragraph/blank-greenfield uses the exact selection normalizer, table-cell
  uses its structured anchor normalizer, and the current selection hash must
  match. Already-applied threads intentionally bypass re-resolution so the
  existing idempotent replay can reach its immutable snapshot lookup; new
  writes still fail through the applied-thread guard.
- 2026-08-02: Added selected-hash fields to submission/accept/apply audit detail
  and deterministic tests for legacy backfill, mismatch rejection, actual
  greenfield AI-thread creation, normal persistence, tampered range rejection,
  table-cell stale text, and idempotent replay. One compatibility correction
  preserved the underlying `selected text` error evidence for existing tests.
- 2026-08-02: Final verification passed: the combined selected-hash,
  revision-application, generation-context, durable, study-binding,
  working-copy, and frontend contract subset returned `142 passed, 106
  deselected in 117.94s`; the greenfield/blank subset returned `3 passed, 15
  deselected in 3.41s`; all changed Python files compile cleanly. No service,
  browser, model, OCR, translation, download, or upstream workload was
  started.
- 2026-08-02: Added one stronger cold-restart assertion that removes
  `selected_hash` from the SQLite payload before reload; the SQLite store suite
  still passes `8 passed in 1.08s` and deterministically backfills the hash.
- 2026-08-02: Independent read-only challenge returned `READY` with no P0–P4
  findings. It verified the legacy v1 idempotency fallback, immutable snapshot
  replay after later edits, missing-snapshot fail-closed behavior, and legacy
  final-approval CAS with temporary databases/deterministic fakes. Current
  fingerprints and the unchanged r42 checkpoint are recorded in the run
  record. Goal remains active; this slice is ready only for bounded Phase 0C
  continuation and is not a Protocol release acceptance.
