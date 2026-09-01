# Conference Context: medical_writing_table_ai_revision_20260714

Created: 2026-07-14 01:32:39
Objective: 为医学写作结构化表格建立单元格级独立AI细节修订、医学审阅批准与显式应用闭环，保持来源、版本、审计和Word工作副本一致
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User requirements and active goal: every protocol table is synchronously rendered and editable; users must be able to ask AI for detailed revisions; AI output is only a pending formal-content candidate until medical review/approval and explicit application; the system must run independently of Codex.
- Current table slice record: `records/active_slices/medical_writing_soa_builder_20260713/TASK_RECORD.md`.
- Existing paragraph AI loop record: `records/active_slices/medical_writing_ai_change_application_20260713/TASK_RECORD.md` and `records/active_slices/medical_writing_revision_dialogue_20260713/TASK_RECORD.md`.
- Contracts: `packages/contracts/workbench_contracts/models.py` (`RevisionThread`, `RevisionSuggestion`, `MedicalWritingRevisionRequest`, `MedicalWritingRevisionApplyRequest`).
- Service/repository: `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `services/api/app/medical_writing_tables.py`, `services/api/app/sqlite_runtime_store.py`, `services/api/app/main.py`.
- Frontend: `frontend/src/App.jsx`, `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`.
- Tests: `tests/test_medical_writing_revision_api.py`, `tests/test_medical_writing_revision_application.py`, `tests/test_medical_writing_revision_dialogue.py`, table/API/export tests, and frontend medical-writing contracts.

### Current Implementation Facts

- Paragraph revisions already use: independent AI run -> pending suggestion -> accept -> medical approval -> explicit application to a CAS-versioned working copy. Acceptance or approval alone never edits the document.
- Paragraph application currently locates exactly one source-linked block by `source_locator`, requires the selected text exactly once, updates plain/rich text, validates the whole working copy, writes an immutable snapshot and audit event, and records the applied thread id.
- Every protocol/native/generated table is now represented in the same working-copy `content_blocks`; top-level `rows` are the export source, while `structured_table` carries stable row/column/cell/note metadata.
- The table designer exposes stable `block_id`, `table_id`, `row_id`, `column_id` and `cell_id`; cell edits are already saved and restored after reload.
- The frontend currently disables paragraph AI controls whenever a table is selected because no table-cell anchor/application path exists. This prevents unsafe fallback to the first paragraph but blocks desired AI interaction.
- Real backend AI must use the configured independent AI gateway and source registry. The registered protocol document remains a source; a working-copy table cell and its row/column/table context are versioned user content and must not be falsely represented as an original-DOCX quote.
- Current paragraph thread fields are generic strings (`anchor_type`, `anchor_path`, `selected_text`) and can be extended without a new revision-thread storage table if server validation is strict.

## Scope

- In scope: one-cell table AI revision for source-linked and generated working-copy tables; stable server-normalized anchor; table/row/column context packet; independent AI proposal; existing multi-round review, accept, medical approval and explicit application chain; CAS/idempotency/audit/snapshot; deterministic Word working-copy consistency; frontend cell selection and table diff review.
- In scope: destructive validation for stale working-copy revision, changed cell text, wrong section/block/table/cell, duplicate IDs, cross-project/cross-document thread, unapproved thread, replay, and source/structured metadata mismatch.
- In scope: at least two real protocol projects from raw DOCX, including one source table and one generated template table where feasible.
- Out of scope for this first slice: multi-cell rectangle proposal schema, row/column insertion by AI, formula execution, autonomous automatic edits, source DOCX rewrite, Word tracked changes, electronic signature, or formal approval automation.

## Success Criteria

- Selecting a table cell produces a visible table/block/row/column/cell context; no paragraph fallback is possible.
- The server ignores untrusted client localization beyond IDs, resolves the current working-copy cell exactly once, canonicalizes the anchor, and verifies the displayed text against current state.
- The AI allowed-source packet separates original registered protocol/evidence sources from versioned working-copy table context; the table context is never claimed to be original protocol evidence.
- The AI suggestion remains a pending candidate and shows before/after cell content, rationale, evidence and uncertainty.
- Only one accepted and medically approved suggestion can be explicitly applied; application updates every canonical representation of that cell, validates the entire table/document, increments working-copy revision once, creates immutable snapshot/audit, and is idempotent.
- Existing paragraph revisions remain behaviorally unchanged.
- RUX and D001 or PNH pass successful and destructive matrices; frontend desktop flow and Word preview reflect the changed cell; relevant regression/build pass.

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
- Do not let the client submit proposal text to the application endpoint; the server must load the medically approved stored suggestion.
- Do not let `anchor_path` be a free-form query or a paragraph source locator for table edits. IDs and current working-copy state must determine the canonical target.
- Do not treat working-copy cell text as independently verified clinical evidence. Original protocol and medically approved external evidence remain fact sources; table context defines the writing target.
- Do not update only `rows` or only `structured_table.rows` if both representations are present.
- Do not broaden the first slice to autonomous row/column/table restructuring by AI.

## Questions For The Panel

- Can the existing `RevisionThread` safely represent `table_cell`, or is a typed anchor payload required now?
- What canonical anchor format and server parsing rules minimize ambiguity and keep old payloads readable?
- What exact table context should be sent to AI without overloading tokens or misrepresenting evidence?
- Should cell proposals remain plain `proposal_text`, and how should the frontend show a cell-scoped diff?
- Which failure modes must block at submit, rewrite, accept, approval and application stages?
- What is the smallest implementation that supports generated and source-linked tables without duplicating the table or document revision chain?

## Loop Log

- 2026-07-14 01:32:39: Conference initialized by `hermes_workflow_guard.py init-conference`.
