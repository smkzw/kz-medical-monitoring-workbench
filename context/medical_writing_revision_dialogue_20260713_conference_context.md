# Conference Context: medical_writing_revision_dialogue_20260713

Created: 2026-07-13 20:35:01
Objective: 将医学写作的一次性要求重写升级为同一来源段落内可追溯、多轮、独立AI驱动的细节修订会话；保留每轮用户反馈、AI候选、证据、父版本和审计，用户选择候选后仍须医学批准并显式应用工作副本。
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

- `packages/contracts/workbench_contracts/models.py`: current `RevisionThread`, `RevisionSuggestion`, action and apply contracts.
- `services/api/app/medical_writing.py`: independent-AI submission/rewrite service and prompt execution boundary.
- `services/api/app/medical_writing_repository.py`: SQLite-backed revision thread, approval and explicit working-copy application boundary.
- `services/api/app/sqlite_runtime_store.py`: atomic thread/action/audit persistence.
- `frontend/src/App.jsx`: current editor-first AI rail and one-shot rewrite UI.
- `frontend/src/styles.css`: current desktop design system and writing layout.
- `tests/test_medical_writing_revision_api.py`: current rewrite behavior.
- `tests/test_medical_writing_real_project_flow.py`: original-protocol independent workflow tests.
- `records/active_slices/medical_writing_ai_change_application_20260713/TASK_RECORD.md`: immediately preceding approved-application closure and remaining boundaries.
- Do not read source protocols or production databases in this design review; Codex will run real-project verification separately.

## Scope

- In scope: add immutable per-turn metadata to each suggestion; preserve the parent candidate and user feedback; pass prior candidate context to the independent AI; show a dense versioned review timeline; keep only the current pending candidate actionable; persist and audit every turn; prove compatibility with old thread payloads.
- Out of scope: free-form general chatbot, autonomous clinical decisions, direct AI edits to formal text, Word tracked changes/comments, DOCX write-back, electronic signature, new document types or new external evidence retrieval.

## Success Criteria

- Every new suggestion records turn number, parent suggestion id, user instruction, user comment, AI run id and created time without breaking old payloads.
- Rewrite generation receives the original source selection plus the immediately preceding candidate and current medical-user feedback; it remains an independent AI call and never invokes Codex.
- Prior candidates remain readable and immutable except for their controlled user-decision transition; only the latest pending candidate can be accepted, rejected or rewritten.
- Medical approval and explicit application continue to target exactly one accepted suggestion; no conversational turn auto-writes a working copy.
- Frontend presents user instruction and AI result as a compact chronological review ledger inside the existing AI rail, with editor still the primary column.
- RUX, D001 and PNH original protocols can each complete at least two rewrite turns in isolated runtime without project-specific rules or cross-project state.
- Destructive tests cover stale action, parent mismatch, duplicate turn, provider failure, persistence/restart and application of the chosen final candidate only.
- Relevant tests, production build, 2048x1024 desktop browser QC, conference review gate and durable logs pass.

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
- Suggestions remain `待医学批准` content; conversation history is not a formal document revision history or electronic signature.
- The client must not submit prior AI proposal text as authority; server reconstructs previous-turn context from the persisted thread.
- Do not expose full source document text or local paths in public thread payloads beyond the already approved selected paragraph boundary.

## Loop Log

- 2026-07-13 20:35:01: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-13: Codex inspected the current implementation and confirmed the existing rewrite path overwrites `thread.user_instruction` and exposes only the latest suggestion in the UI.
