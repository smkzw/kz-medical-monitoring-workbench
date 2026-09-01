# Task Context: mw_protocol_p0_phase0c_word_receipt_contract_20260802

Created: 2026-08-02 03:27:30
Objective: 继续 Protocol P0 Phase 0C：建立 Word 已验证最终视图的可审计 receipt/status 合同，使 fast preview 不可冒充 Word verified；仅做离线纯函数与 API contract tests，不启动服务/Word/LibreOffice，不触碰冻结 r42/v36、上游研究/OCR/翻译、真实模型或医学监查并发线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Immutable no-loss boundary: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.
- Approved Protocol-first roadmap: `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`.
- Accepted Phase 0C records: `runs/codex_mw_protocol_p0_phase0c_diff_impact_20260802.md`,
  `runs/codex_mw_protocol_p0_phase0c_protected_tokens_20260802.md`, and
  `runs/codex_mw_protocol_p0_phase0c_fast_preview_contract_20260802.md`, with
  their context/review/metrics evidence.
- Current exporter and API: `services/api/app/medical_writing_document_exporter.py`
  and `services/api/app/main.py`.
- Current contracts and tests under `packages/contracts/` and `tests/`.
- Current filesystem is final truth. No runtime service, browser, Word/
  LibreOffice process, real model, OCR/translation, upstream state, or medical-
  monitoring file is an allowed input for this offline contract slice.

## Scope

- In scope:
  - Add a typed, auditable Word-verification receipt tied to the exact
    ProtocolDocument/front-matter snapshot and generated DOCX hash.
  - Validate that a receipt can mark a preview `word_verified` only when the
    source snapshot, DOCX hash, page evidence, verifier/tool identity and
    evidence hash are complete and internally consistent.
  - Add pure contract/service helpers and deterministic API contract tests; keep
    the current endpoint read-only unless it is only a testable pure transition.
- Out of scope:
  - Starting Microsoft Word, LibreOffice, a browser, any service, model,
    provider, OCR/translation, upstream pipeline, download, production DB, or
    monitoring lane.
  - Claiming a real Word verification run, modifying DOCX export layout, wiring
    frontend buttons, or entering Synopsis/CSR/final multi-provider acceptance.
  - Reusing an arbitrary client-provided hash as proof without a bound source
    snapshot and evidence manifest.

## Success Criteria

- The receipt contract binds the current source snapshot SHA-256, generated
  DOCX SHA-256, verification evidence SHA-256, verifier/tool/version and a
  non-empty page evidence manifest.
- A fast preview cannot transition to `word_verified` without an exact current
  snapshot and matching receipt; stale/missing/mismatched evidence fails closed.
- The transition is deterministic, idempotent and does not mutate the source
  ProtocolDocument or existing DOCX export/atomic revision paths.
- Focused pure/API contract tests, compile checks, review-gate and frozen r42/
  process checks pass. No runtime or external side effect occurs.
- This is a bounded Phase 0C contract increment and does not imply a real Word
  or Protocol release acceptance.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 03:27:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Reused the accepted fast-preview snapshot/style boundary. The
  safe next increment is contract-only because no real Word/LibreOffice run is
  authorized or needed to prove the data boundary.
- 2026-08-02: Added `MedicalWritingWordVerificationPage` and
  `MedicalWritingWordVerificationReceipt`. The receipt binds current source
  snapshot SHA-256, DOCX SHA-256, PDF SHA-256, ordered page evidence, a
  PDF-inclusive evidence-manifest hash, verifier/tool/version, timezone-aware
  timestamp, and idempotency key.
- 2026-08-02: Added the pure
  `build_medical_writing_word_verified_preview(...)` transition. It fails
  closed on wrong project/document, stale source snapshot, or DOCX hash mismatch
  and emits non-estimated pages only from an already-produced receipt. It does
  not run Word, PDF, a service, a browser, or a model.
- 2026-08-02: Receipt/preview tests (8) and protected-token/revision/export
  regressions (43) passed; compileall passed. Frozen r42/process checks remain
  unchanged. Final status is
  `READY_FOR_BOUNDED_PHASE0C_CONTINUATION; NOT_READY_FOR_PROTOCOL_RELEASE`.
