# Task Context: mw_protocol_p0_phase0c_word_receipt_runtime_integration_20260802

Created: 2026-08-02 04:08:48
Objective: 在全新临时 runtime 中以真实 HTTP 服务验证医学写作 DOCX artifact 绑定的 Word 回执提交、幂等重放、重启读取及 stale/mismatch fail-closed；不触碰 r42/v36 冻结数据、不运行 OCR/翻译/上游阶段。
Task type: `multimodal_document_precheck`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/AGENTS.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `runs/codex-subagent_mw_protocol_p0_word_native_final_gate_fixture_20260802.md`
- `context/mw_protocol_p0_word_native_final_gate_fixture_20260802_context.md`
- `services/api/app/main.py` (Word-verification route and export callbacks)
- `services/api/app/medical_writing_document_export_jobs.py` (durable artifact/job contract)
- `services/api/app/medical_writing_word_verification_repository.py` (receipt persistence contract)
- `tests/test_medical_writing_word_verification.py` and `tests/test_medical_writing_word_verification_api.py` (synthetic contract fixture)
- `tests/test_medical_writing_document_export_api.py` (export-job fixture patterns)
- `tests/test_medical_writing_greenfield_runtime.py` (greenfield document fixture constants)
- User authorization in the current task permits routine local runtime verification; it does not authorize altering frozen r42/v36 records or claiming Protocol release.

## Scope

- In scope: a fresh task-owned temporary `WORKBENCH_RUNTIME_DIR`; one synthetic ProtocolDocument; one real Uvicorn HTTP process; durable DOCX artifact packaging; POST Word-verification route; same-key replay; new repository instance after simulated restart; stale source-snapshot and DOCX-hash rejection; route/job/receipt/audit evidence.
- In scope: direct Codex execution and final acceptance; no delegated worker is required for this bounded local proof.
- Out of scope: r42/v36 runtime trees; clone/original translation rows; production `runtime/`; OCR, PaddleOCR, GLM-OCR, translation, download, model/provider calls; upstream research/triage; greenfield authoring UI; Synopsis/CSR; final multi-provider visual loop; any product-source change unless a narrowly isolated defect is proven.

## Success Criteria

- The service starts only against a new temporary runtime root and exits cleanly.
- A durable export job reaches `completed`, the artifact manifest binds `project_id`, `document_id`, `mode`, source snapshot and DOCX SHA-256, and the job is readable through the route-owned service.
- One real HTTP POST returns `200`, `preview.preview_status=word_verified`, `replayed=false`, and one audit event.
- Repeating the identical POST returns `200`, `replayed=true`, the same audit identifier, and no second receipt/audit row.
- A newly constructed receipt repository reads the same committed receipt/audit after the process-local restart simulation.
- A stale source snapshot and a mismatched DOCX hash fail closed with `422`; neither creates a new audit event.
- No file under the protected r42/v36 runtime changes; no model/OCR/translation call occurs.
- Evidence is written only to the task context/run/review/metrics and task-owned temp root.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Use a random task-owned temp root and an unused localhost port; never set `WORKBENCH_RUNTIME_DIR` to the stable workbench runtime or `runs/execution/mw_r42_planner_retry_20260731/runtime`.
- The HTTP process is synthetic-fixture-only. A pass proves route/job/persistence integration, not Word UI rendering or Protocol release; the independent real Word/PDF fixture remains the separate evidence source.
- Do not copy credentials, provider settings, or user source documents into the temp root.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 04:08:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 04:10:00: Sources, scope, success criteria, risk boundaries, and allowed temp output defined. Direct Codex execution selected; no child dispatch or external provider call.
- 2026-08-02 04:12:20: Real Uvicorn HTTP integration completed on temporary port 18928. Durable export completed; first receipt 200/word_verified; exact retry 200/replayed; restart read same receipt with one audit; stale snapshot and DOCX mismatch each 422; service stopped and port cleared. Evidence: `/private/tmp/mw_word_runtime_integration.tTUCV1/runtime_integration_evidence.json`.
- 2026-08-02 04:13:00: Codex review-gate passed with `PASS_FOR_BOUNDED_RUNTIME_INTEGRATION; NOT_READY_FOR_PROTOCOL_RELEASE`. Next safe action is reconcile this result with the Word/PDF fixture and retain the canonical page-hash adapter as an explicit release gate.
- 2026-08-02 04:16:00: The default `/opt/homebrew` pytest interpreter lacked `cryptography` during API-test collection; no product change was made. Re-running the same focused suite with `/usr/bin/python3 -m pytest` passed `13 passed` (17 deprecation warnings only).
