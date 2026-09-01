# Task Context: mw_protocol_p0_phase0c_word_receipt_persistence_20260802

Created: 2026-08-02 03:33:49
Objective: 继续 Protocol P0 Phase 0C：为 Word verification receipt 建立独立、幂等、来源绑定的 SQLite/repository 持久化合同与临时库证明；不启动服务/Word/LibreOffice，不触碰冻结 r42/v36、上游研究/OCR/翻译、真实模型或医学监查并发线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Immutable no-loss boundary: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.
- Accepted Phase 0C records: the diff/impact, protected-token, fast-preview,
  and Word receipt contract run/context/review/metrics files under `runs/`,
  `context/`, `reviews/`, and `metrics/`.
- Current runtime persistence patterns:
  `services/api/app/medical_writing_repository.py`,
  `services/api/app/sqlite_runtime_store.py`, and existing medical-writing
  durable/audit tests.
- Current receipt contracts:
  `packages/contracts/workbench_contracts/models.py` and the exporter helper.
- The current filesystem is final truth. Use only a temporary SQLite database
  or deterministic fake for this task; do not open production runtime state.

## Scope

- In scope:
  - Add a dedicated receipt repository/storage contract with source/document
    identity, idempotency key, immutable receipt payload, status and audit
    metadata.
  - Make duplicate same-key writes return the persisted receipt without a
    second record; reject same-key different-payload and stale/foreign writes.
  - Prove restart/reload and concurrent same-key behavior against a temporary
    SQLite database or deterministic fake.
- Out of scope:
  - Starting the API/service, Word/LibreOffice/PDF, browser, model/provider,
    OCR/translation, upstream pipeline, downloads, production DB, or medical-
    monitoring lane.
  - Claiming any real Word verification, changing DOCX rendering, frontend
    buttons, Synopsis/CSR, or final multi-provider visual acceptance.
  - Modifying the immutable ProtocolDocument or existing revision rows.

## Success Criteria

- Receipt writes are append-only/immutable and bound to project/document,
  source snapshot, DOCX/PDF hashes and evidence manifest.
- Idempotency is deterministic across duplicate requests, worker restart and
  same-key concurrency; conflicting payloads fail closed.
- Reads return the exact stored receipt and never silently promote a stale
  snapshot. No existing medical-writing repository behavior regresses.
- Focused tests, compile checks, review-gate and frozen r42/process checks pass.
- This remains a bounded storage contract, not real Word or Protocol release
  acceptance.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 03:33:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Chose an isolated receipt SQLite file rather than extending the
  shared `SqliteRuntimeStore` schema. This preserves the concurrent medical-
  monitoring/runtime migration boundary and makes the proof reversible.
- 2026-08-02: Added append-only receipt and audit tables with immutable triggers,
  source/DOCX hash checks, same-key idempotency and conflict detection, restart
  reload, stale reads, and concurrent worker serialization.
- 2026-08-02: Added a lazy, controlled API integration at
  `POST /api/projects/{project_id}/medical-writing/document-preview/word-verification`.
  It accepts a receipt only when the referenced completed DOCX export artifact,
  current assembled document snapshot, DOCX hash, project/document identity and
  receipt all agree; it then persists through the isolated repository and
  returns the non-estimated Word/PDF preview plus replay/audit metadata. The
  repository is still not initialized on import and no product service was run.
- 2026-08-02: Temporary SQLite tests passed (4 repository tests); combined
  receipt/fast-preview/export/protected-token/revision API tests passed (80),
  compileall passed, and r42/process checks remain unchanged.
- 2026-08-02: Status is
  `READY_FOR_BOUNDED_PHASE0C_CONTINUATION; NOT_READY_FOR_PROTOCOL_RELEASE`.
