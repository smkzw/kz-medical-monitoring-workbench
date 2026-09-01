# Conference Context: medical_writing_revision_ui_20260708

Created: 2026-07-08 15:13:52
Objective: Wire 医学写作 rich editor revision UI to existing revision-thread backend with pending-medical-approval boundaries, Chinese clinical wording review, and browser QC
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- User objective: continue building the AI Medical Manager Workbench toward a commercializable product across all medical-related subsystems; this slice advances the 医学写作 subsystem.
- Existing approved scope: visible subsystems remain business names only; do not add lifecycle labels such as `第几环节` / `阶段`.
- Current local files for this slice:
  - `research/medical_writing_revision_ui_research_20260708.md`
  - `logs/subsystems/medical_writing_log.md`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/tests/medical_writing_manifest_qc.mjs`
  - `services/api/app/main.py`
  - `services/api/app/medical_writing.py`
  - `services/api/app/medical_writing_manifest.py`
  - `tests/test_medical_writing_revision_api.py`
  - `tests/test_medical_writing_manifest.py`
  - `context/medical_writing_revision_api_context.md`
  - `reviews/codex_medical_writing_revision_api_review.md`
  - `metrics/medical_writing_revision_api_metrics.md`
- Backend API already exists:
  - `GET /api/projects/{project_id}/revision-threads`
  - `POST /api/projects/{project_id}/revision-threads`
  - `POST /api/projects/{project_id}/revision-threads/{thread_id}/actions`
- Frontend already uses Tiptap 3 in `RichProtocolEditor`, but the AI revision rail is currently static demo content and does not call the revision endpoints.

## Scope

- In scope:
  - connect the 医学写作 page to the existing revision-thread backend;
  - support user-entered revision instruction, selected/current section text capture, thread list refresh, and accept/reject/request-rewrite actions;
  - make all AI suggestions visibly `待医学批准` / `待医学确认` and show the independent-AI gateway boundary honestly;
  - browser QC the submit/action workflow on desktop and mobile;
  - keep source/data and public UI free of local absolute paths and lifecycle-numbered subsystem names.
- Out of scope:
  - no real LLM connection in this slice;
  - no automatic formal protocol正文 overwrite when a suggestion is accepted;
  - no DOCX roundtrip/export, Word comments, tracked changes, or electronic signature;
  - no new standalone non-medical subsystem;
  - no change to TFL, Safety/PV, monitoring, eligibility, or approval-center APIs unless a direct regression is found.

## Success Criteria

- Static/contract tests prove the frontend calls the three revision endpoints and no longer presents only a static `AI 修订线程 #3` flow.
- Browser QC proves a user can open 医学写作, submit a revision instruction, see a returned suggestion, and perform at least one backend action without page overflow.
- UI copy clearly states accepted suggestions remain pending medical approval and do not auto-write formal正文.
- Existing backend revision API tests still pass.
- Frontend build and relevant regression tests pass.
- Logs record the implementation boundary, evidence, tests, pitfalls, and remaining commercialization gaps.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Original real project files under `/Users/smkzw/Documents/康哲项目资料` and `/Users/smkzw/Documents/朗来项目资料` are read-only unless copied into the workbench; do not delete, move, or cut originals.
- The deterministic backend stub must not be described as a configured production LLM. If the UI shows an AI run/provider status, it must say the independent provider is not configured.
- Chinese clinical-writing wording should be conservative: use `建议`, `候选`, `待医学批准`, `待医学确认`, and avoid `正式生成`, `自动定稿`, `可直接提交监管`.

## Loop Log

- 2026-07-08 15:13:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 15:18 CST: Codex filled source packet, scope, success criteria, and medical-writing risk boundaries after reviewing current code, tests, subsystem logs, and external research note.
