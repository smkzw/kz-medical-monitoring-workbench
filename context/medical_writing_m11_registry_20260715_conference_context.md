# Conference Context: medical_writing_m11_registry_20260715

Created: 2026-07-15 11:01:03
Objective: 设计并审阅服务端版本化中文ICH M11方案模板注册表、旧14节绿地文档兼容迁移、章节交互路由及Word对象扩展边界；不得修改生产代码，Codex负责最终实现与验收
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- This is a non-visual complex conference under the current global `/Users/smkzw/.codex/AGENTS.md` read on 2026-07-15 immediately before initialization; SHA-256 `058c2aba8196d225a0a1ddda7ec77695a12b5c4e46e97ae43bec5bcc4c372a8c`.
- Hermes `aishuo-gpt55 / gpt-5.5` is the single sub-venue chair.
- Independent participants are Hermes `aishuo / MiniMax-M3` and OpenCode Go `deepseek-v4-flash`.
- Each role starts with one complete same-session pass. Codex may request zero or more targeted follow-ups in that same session after quality review.
- If the OpenCode Go Flash role fails, the declared fallback order is Reasonix `deepseek-v4-flash`, then OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`; fallback must be explicit in the run log.
- Direct xAI `grok-4.5` is additive only: one complete pass after a connectivity check, no continuation, no chair role and no replacement of the required panel.
- Reasonix is only the declared first fallback for the Flash participant and is not a chair or second-review venue.

## Source Of Truth

- `records/active_slices/medical_writing_full_gap_review_20260714/source/ich_m11_cn_20250114_extracted.txt`
- `records/active_slices/medical_writing_full_gap_review_20260714/M11_TARGET_MODEL.md`
- `records/active_slices/medical_writing_authoring_journey_20260714/TASK_RECORD.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_greenfield.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/medical_writing_document_exporter.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- Relevant `tests/test_medical_writing_*.py` and `tests/test_frontend_medical_writing_contract.py` only.
- User PDF is authoritative but already extracted into the bounded local text above; conference models must not read outside the workspace.

## Scope

- In scope: canonical versioned Chinese ICH M11 chapter registry; service-owned scaffold generation; stable IDs; applicability and interaction metadata; migration of existing 14-section greenfield documents; preservation of original-DOCX sessions; contracts for synopsis, SoA, study schema, content tables, scales, captions and indices; testable API/frontend boundaries.
- Out of scope: production writes, visual acceptance, final regulatory interpretation, full prose generation, ClinicalTrials.gov retrieval, and replacing the already accepted independent DeepSeek product route.

## Success Criteria

- Produce a compact implementation recommendation that maps every proposal to current code and authoritative M11 source lines.
- Separate immediate production slice from future object extensions; do not require a big-bang rewrite.
- Preserve both authoring entries and one converged StudyDefinition/document runtime.
- Define fail-closed migration and rollback behavior for existing documents and working-copy/audit history.
- Define focused unit/integration/browser/Word checks and identify P0/P1 failure modes.
- Do not invent clinical content, fixed applicability decisions or sponsor clauses.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-15 11:01:03: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-15: Codex initially misread a previously pasted AGENTS version as current and briefly rewrote the conference context toward a GLM-5.2/DeepSeek-Pro/Mimo route. No model was dispatched. The actual current global file was re-opened from disk, and this context was restored to the correct GPT-5.5 chair plus MiniMax/Flash participant route before successful preflight.
