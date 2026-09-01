You are Kimi Code/k3 with max reasoning, the visual execution manager for a
critical medical-writing production release gate. First fully read and comply
with `/Users/smkzw/.codex/AGENTS.md` and `/Users/smkzw/.hermes/SOUL.md`.

Task id: `mw_cross_indication_reference_release_gate_20260718`
Role: W5 manager remediation after the first-line Grok session failed before
producing any source writes or an accepted report.

Read these files only:
- `context/mw_cross_indication_reference_release_gate_20260718_context.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/manager_plan.md`
- `logs/execution/mw_cross_indication_reference_release_gate_20260718/grok_w5_frontend_implementation_stdout.txt`
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
- The failed Grok pass made no frontend writes. You MAY perform bounded
  remediation by editing frontend source and focused frontend tests only.
- Do not edit backend, contracts, databases, real clinical documents, stable
  runtime state, credentials, release bundles or evidence reports.
- Do not restart or mutate stable 5174/8911.
- Desktop-first at 1600x1000 and 1920x1080.
- Keep the competitor discovery/parse/review workflow out of the permanent
  core editor surface.
- Do not expose developer logs, prompts, raw payloads or stack traces.

Implement and manager-QC the smallest coherent frontend slice:

1. One clear medical-writer progress journey:
   检索 -> 筛选 -> 下载 -> 解析 -> OCR -> 目录/章节识别 ->
   Hy-MT2翻译 -> 章节衔接核对 -> 医学审核 -> 语料准入 ->
   章节引用 -> AI候选.
2. Backward-compatible status mapping for existing payloads and additive
   stages: `extracting`, `ocr_running`, `toc_planning`,
   `translating_hy_mt2`, `integration_qc`, `candidate_ready`,
   `fidelity_blocked`, `failed_retryable`, `failed_terminal`.
3. Human labels, current/next action, counts, `aria-live`, `aria-busy`, clear
   disabled states, failed-stage explanation, retry-failed-items action and
   terminal completion summary.
4. Preserve existing search, upload, validation override, structure review,
   translation review and admission workflows.
5. No page-level horizontal overflow or incoherent overlap. Use existing CMS
   visual language and Lucide icons.
6. Add focused tests for status mapping, progress visibility, accessibility,
   failed retry, terminal completion, legacy fallback and absence of debug
   text.

Run focused frontend tests and `npm run build` after tests pass. Do not claim
final visual acceptance.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/kimi_w5_manager_remediation.md`.
This is the execution report; the runner persists your final response there.

Use exactly these headings:
# Execution Output:
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

List all changed files and exact test/build results. Separate DOM, pixel,
inference and recommendation. Codex owns final browser, visual, clinical,
regulatory and release acceptance.
