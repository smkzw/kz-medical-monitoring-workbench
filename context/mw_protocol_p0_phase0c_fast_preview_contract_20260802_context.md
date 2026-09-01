# Task Context: mw_protocol_p0_phase0c_fast_preview_contract_20260802

Created: 2026-08-02 03:05:56
Objective: 继续 Protocol P0 Phase 0C：从现有 ProtocolDocument/DOCX export 同源快照建立诚实的快速分页预览合同与 Word 已验证状态边界；不启动服务、不触碰冻结 r42/v36、上游研究/OCR/翻译、真实模型或医学监查并发线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Immutable no-loss boundary:
  `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.
- Approved Protocol-first roadmap and Phase 0C exit gates:
  `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`.
- Accepted predecessor records:
  `runs/codex_mw_protocol_p0_phase0c_diff_impact_20260802.md` and
  `runs/codex_mw_protocol_p0_phase0c_protected_tokens_20260802.md`, with their
  corresponding context/review/metrics files.
- Current DOCX assembly/export path:
  `services/api/app/medical_writing_document_exporter.py` and the durable
  export adapter in `services/api/app/main.py`.
- Current contracts, runtime document/working-copy repository, frontend and
  deterministic tests under `packages/contracts/`, `services/api/app/`,
  `frontend/src/`, and `tests/`.
- Current filesystem is final truth. No runtime service, browser, Word,
  external model, OCR/translation, download, upstream state, or medical-
  monitoring file is an authority or an allowed input for this bounded task.

## Scope

- In scope:
  - Audit the existing exporter snapshot digest, style-profile/page-layout
    identity, ordered blocks and durable export metadata.
  - Add one deterministic fast-pagination preview contract derived from the
    same `ProtocolDocument` and front-matter snapshot used by DOCX export.
  - Expose explicit `fast_preview` versus `word_verified`/stale semantics and
    page/block locators without claiming browser or Word fidelity.
  - Add a read-only JSON endpoint and focused contract/API tests; preserve the
    existing DOCX export and atomic revision paths.
- Out of scope:
  - Microsoft Word/LibreOffice/PDF rendering or visual acceptance;
    browser/Playwright interaction; pixel-level pagination claims.
  - DOCX exporter rewrites, approval/freeze semantics, Synopsis, CSR, r42/v36,
    upstream research/OCR/translation/download state, real providers/models,
    production runtime databases/services, or medical-monitoring files.

## Success Criteria

- The preview snapshot hash equals the exact digest used by the DOCX export
  assembly for the same document and front-matter overrides.
- Page and block locators are deterministic for identical input, preserve
  section/block identity, and make the estimate/approximation explicit.
- A fast preview can never be labeled Word-verified; stale or missing source
  identity is visible and fail-closed rather than silently rendered current.
- The existing DOCX export/atomic revision paths remain unchanged except for
  additive reuse of the snapshot identity helper.
- Focused tests, compile checks, review-gate, and frozen r42/process checks
  pass. No service, browser, Word, model, OCR/translation, upstream or
  monitoring state is touched.
- This is a bounded Phase 0C increment and does not imply Protocol release
  readiness.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 03:05:56: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Audited the existing DOCX snapshot digest, StyleProfile body
  layout, ordered block projection, visual layout plan, and document export
  assembly. No service, browser, Word/LibreOffice process, model, OCR/
  translation job, upstream state, or monitoring file was started or changed.
- 2026-08-02: Added the additive `MedicalWritingDocumentPreview` contract,
  deterministic page/block locators, and explicit `fast_preview`,
  `word_verified`, and fail-closed `stale` identity rules. The fast preview
  uses the exact DOCX export snapshot digest and the same StyleProfile
  resolution but remains an estimate.
- 2026-08-02: Added the read-only
  `GET /api/projects/{project_id}/medical-writing/document-preview` route.
  It consumes the same assembled/exporter snapshot used by DOCX export and
  returns an explicit warning that the result is not a Microsoft Word verified
  view.
- 2026-08-02: Focused contract/API/export regression suites and compile checks
  passed; frozen r42 remains unchanged. Codex review status is
  `READY_FOR_BOUNDED_PHASE0C_CONTINUATION; NOT_READY_FOR_PROTOCOL_RELEASE`.
