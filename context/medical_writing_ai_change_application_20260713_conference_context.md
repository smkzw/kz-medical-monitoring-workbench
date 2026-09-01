# Conference Context: medical_writing_ai_change_application_20260713

Created: 2026-07-13 18:50:40
Objective: 实现医学写作AI建议经医学批准后显式、可追溯、CAS安全地应用到版本化工作副本，并用RUX、D001、PNH真实方案完成前后端验证
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

- User requirements and durable logs:
  - `logs/subsystems/medical_writing_log.md`
  - `logs/system_build_log.md`
  - `frontend/AGENTS.md`
- Existing implementation contracts:
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/medical_writing.py`
  - `services/api/app/medical_writing_repository.py`
  - `services/api/app/sqlite_runtime_store.py`
  - `services/api/app/main.py`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
- Existing verification surfaces:
  - `tests/test_medical_writing_revision_api.py`
  - `tests/test_medical_writing_working_copy_persistence.py`
  - `tests/test_sqlite_medical_writing_store.py`
  - `tests/test_frontend_medical_writing_contract.py`
- Real document services already bind three independent protocol projects: `proj_rux_03_002`, `proj_d001`, and `proj_my008_pnh_3_01`. Participants must not read the underlying production source files; Codex alone runs real-project verification through the existing document service.

## Scope

- In scope:
  - define the state transition from AI suggestion to medically approved suggestion to explicit working-copy application;
  - enforce project/document/section/paragraph identity, accepted suggestion identity, current approval status and optimistic working-copy revision;
  - ensure application is explicit, idempotent, auditable and does not mutate the original DOCX;
  - preserve content-block structure and source locators while replacing only the approved selected text;
  - expose a clear editor/AI-rail action only after medical approval;
  - verify stale revision, wrong project/section, duplicate/absent selected text, repeated application and locked working-copy failures;
  - verify three real protocol projects without writing to the active runtime database.
- Out of scope:
  - DOCX round-trip, Word tracked changes/comments, electronic signature, export or regulatory submission;
  - automatic insertion on AI acceptance or approval;
  - broad redesign of the writing page, document-type expansion, or unrelated refactoring;
  - any clinical/regulatory claim derived by Hermes.

## Success Criteria

- A medically unapproved, rejected, returned, superseded or cross-project thread cannot change a working copy.
- A medically approved thread can be applied only by an explicit user action against the exact current working-copy revision.
- The selected text must still exist exactly once in the source-locator-bound block; otherwise the operation fails closed and records no partial write.
- A successful application creates one new immutable working-copy revision and audit trail containing the thread, suggestion, prior revision and resulting revision.
- Replaying the same business idempotency key returns the same result without a second revision; a different payload under the same key fails.
- The original parsed DOCX section remains unchanged.
- Frontend makes the boundary legible: approval does not apply text; application is available only when medically approved and requires a clean current working copy.
- Focused tests, production build, three-real-project API/browser interaction checks and desktop visual QC pass.

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
- Participants are read-only and advisory. They may inspect only the listed files and must not run tests, browse, edit, or access raw project documents.
- Do not weaken approval, CAS, source identity or audit requirements for convenience.
- Do not propose automatic application or replacement by free-text search across the whole document.

## Loop Log

- 2026-07-13 18:50:40: Conference initialized by `hermes_workflow_guard.py init-conference`.
