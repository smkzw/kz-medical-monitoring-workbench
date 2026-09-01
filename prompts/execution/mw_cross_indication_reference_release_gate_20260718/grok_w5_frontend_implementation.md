You are Grok Build/grok-4.5, the first-line visual/frontend implementation
worker for a critical medical-writing production release gate. First fully read
and comply with `/Users/smkzw/.codex/AGENTS.md` and
`/Users/smkzw/.hermes/SOUL.md`.

Task id: `mw_cross_indication_reference_release_gate_20260718`
Role: W5 frontend progress, failure, retry, completion and accessibility.

Read these files only:
- `context/mw_cross_indication_reference_release_gate_20260718_context.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/manager_plan.md`
- `records/USER_REQUIREMENTS_CURRENT_20260718.md`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferencePreparationBatchPanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `frontend/src/styles.css`
- `frontend/tests/medical_writing_reference_approved_qc.mjs`
- `frontend/tests/medical_writing_reference_drawer_qc.mjs`
- `frontend/tests/medical_writing_reference_override_qc.mjs`

The read list is a starting context, not a blanket prohibition on bounded
adjacent inspection needed for correct implementation.

Hard boundaries:
- You MAY edit frontend source and focused frontend tests only.
- Do not edit backend, contracts, databases, real clinical documents, stable
  runtime state, credentials, release bundles or evidence reports.
- Do not restart or mutate stable 5174/8911.
- Desktop-first: optimize 1600x1000 and 1920x1080. Do not remove desktop
  capability for mobile accommodation.
- This preparation/review workflow is a separate surface, not permanent
  clutter in the core document editor.
- Do not expose developer logs, raw payloads, prompts or internal stack traces.

Implement the smallest coherent frontend slice:

1. Present one clear progress journey for:
   检索 -> 筛选 -> 下载 -> 解析 -> OCR -> 目录/章节识别 ->
   Hy-MT2翻译 -> 章节衔接核对 -> 医学审核 -> 语料准入 ->
   章节引用 -> AI候选.
   Use medical-writer language, counts, current action and next action. Avoid a
   decorative marketing stepper or a dense debug dashboard.
2. Support existing payloads and additive backend fields. Gracefully map:
   `extracting`, `ocr_running`, `toc_planning`, `translating_hy_mt2`,
   `integration_qc`, `candidate_ready`, `fidelity_blocked`,
   `failed_retryable`, `failed_terminal`, and existing legacy statuses.
3. Make long-running work visible with `aria-live`, `aria-busy`, clear disabled
   states and a concise progress summary.
4. Failure state must identify the failed stage in user language and expose a
   retry-failed-items action. Completion must show translated, blocked,
   awaiting-review and admitted counts without requiring log inspection.
5. Preserve current search, manual upload, content validation override,
   structure review, translation review and corpus admission workflows.
6. Prevent page-level horizontal overflow and incoherent overlap at 1600x1000
   and 1920x1080. Inner table scrolling is allowed when necessary. Use the
   existing restrained CMS visual language and icons.
7. Add or update focused tests for status mapping, progress visibility,
   accessibility labels/live regions, failed-stage retry, terminal completion,
   legacy payload fallback and no developer-log text.

Run the smallest focused tests and `npm run build` if focused tests pass. Do not
use stable projects for writes and do not claim final visual acceptance.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/grok_w5_frontend_implementation.md`.
This is the execution report; the runner persists your final response there.

Use exactly these headings:
# Execution Output:
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

List every changed file and exact test/build result. Separate DOM observations,
pixel observations, inference and recommendation. Codex owns final browser,
visual, clinical, regulatory and release acceptance.
