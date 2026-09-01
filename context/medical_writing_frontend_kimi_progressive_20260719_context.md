# Task Context: medical_writing_frontend_kimi_progressive_20260719

Created: 2026-07-19 21:09:16
Objective: Kimi Code k3 独立审计医学写作工作流与前后端接口，建立隔离高保真桌面端设计 demo，并将可验证的小步 CSS/局部交互改进渐进并入生产前端
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-grok45+kimi-code-k3` / `mixed:Codex-led visual panel; Grok Build then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Global execution rules: `/Users/smkzw/.codex/AGENTS.md`.
- Project execution overlay: `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`.
- Stable workbench source: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend`.
- Stable backend/API contracts: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/services/api/app` and `/packages/contracts`.
- Current stable runtime: frontend `http://127.0.0.1:5174`, API `http://127.0.0.1:8911`.
- Isolated, fingerprint-matched audit runtime created after task start:
  - frontend `http://127.0.0.1:5176`
  - API `http://127.0.0.1:8912`
  - runtime data copy:
    `records/active_slices/medical_writing_frontend_kimi_progressive_20260719/isolated_runtime`
  - use this runtime for mutating browser tests; keep 5174/8911 untouched.
- Qoder anti-example only: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/records/qoder_full_system_audit_20260719/demo`, runtime `http://127.0.0.1:4321`.
- Kangzhe brand/color authority: `/Users/smkzw/Documents/康哲项目资料/模版/design.md`.
- Current medical-writing task state:
  - `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
  - `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/SOFT_PAUSE_RESUME.md`
  - `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md`
  - `records/active_slices/medical_writing_prelaunch_acceptance_20260717/SOFT_PAUSE_RESUME.md`
  - `records/active_slices/medical_writing_workspace_usability_20260715/TASK_RECORD.md`
- Existing frontend tests: `frontend/tests`.
- Existing rendered evidence: `frontend/tests/worker_02_evidence`, `records/visual_qc_*`, and current screenshots captured from the stable runtime.

## Scope

- In scope:
  - Kimi Code/k3, high reasoning, is the primary independent designer and execution manager for this slice.
  - Audit the complete system shell and medical-writing frontend through real desktop interaction.
  - Map visible functionality and interaction states to actual frontend source, backend endpoints, payloads, persistence, error handling, and long-running progress states.
  - Build an independent runnable Kimi demo in an isolated new directory.
  - Use Qoder demo only as a negative comparator, never as a starting point.
  - Produce design specification, interaction specification, backend/interface map, gap analysis, implementation guide, and browser/visual evidence.
  - After Codex review, progressively merge only small, reversible CSS/local-interaction improvements into the existing frontend.
- Out of scope:
  - Replacing the current frontend architecture or rewriting the workbench.
  - Stopping or replacing stable services on ports 5174/8911.
  - Modifying DOCX backend files currently owned by the main task:
    - `services/api/app/medical_writing_document_exporter.py`
    - `services/api/app/medical_writing_protocol_template.py`
    - `services/api/app/medical_writing_greenfield.py`
    - their tests.
  - Treating model output, source inspection, a narrow viewport, or a synthetic demo as final product acceptance.

## Success Criteria

1. Kimi route evidence records provider/model `kimi-code/k3`, high reasoning, session id, source list, pass count, tools used, and any failure/fallback.
2. Stable runtime is tested as a lazy but senior medical writer would use it: new project, import and greenfield flows, framing/PICOS, competitor corpus, AI candidates, evidence, references/citations, document and table editing, full-screen/default editing, save/revision, export, loading/error/empty/offline/conflict states.
3. Every visible control is classified as working, partially working, blocked by prerequisite, misleading, redundant, or missing; its API/implementation dependency is named.
4. A Kimi-owned, runnable desktop-first demo exists outside production source and has been iterated using browser screenshots and real interactions at 1440x900, 1920x1080, 2048x1024, and 2560x1440 where feasible.
5. The demo uses Kangzhe color and brand primitives from `design.md` but is not constrained by unrelated HTML-PPT fixed-layout rules.
6. Reports explain exact CSS/component/interface implementation, not just visual intent.
7. Production integration is incremental and does not overwrite unrelated user changes. Before each integration slice, the touched frontend files are copied to a task backup and their hashes recorded.
8. Existing relevant frontend tests and `npm run build` pass after each integration slice. Real-browser desktop interaction and visual QC show no new overflow, overlap, white-screen, editor, table-editor, or full-screen regression.
9. Stable services remain available throughout the task.
10. The baseline F001 timeout is not accepted as proof of an Enter or
    persistence defect. Acceptance must capture the post-refresh URL,
    runtime-readiness result, visible page text/error, working-copy API
    response, and persisted database row in the isolated runtime. Provide a
    factual `Enter -> save -> refresh -> frontend/backend restart -> reread`
    chain, and distinguish locator drift or load races from product
    persistence defects. Updating a test locator alone is not product proof.
11. Classify the truncated project-code cell and excessive blank workspace as
    visual/layout P2 findings. Classify a post-search PICOS flow that still
    offers only blank or unselected static choices, without AI recommendation,
    preselection, or rationale, as a product-logic P1 finding. Audit every
    remaining PICOS group for the same pattern and distinguish absent backend
    proposals, undisplayed proposals, non-preselected proposals, and missing
    traceable rationale. CSS alone cannot close this P1.
12. Enter/new-paragraph support is now an accepted product P1. The frontend
    rich-text-to-source-block mapper must preserve every imported block's
    `block_id`, `source_locator`, and `source_kind`, while assigning stable,
    auditable identity/order/source semantics to user-created paragraphs.
    Prove the fixed Enter path through UI, API, SQLite, refresh, and full
    isolated frontend/backend restart. Do not close it by removing the block
    count guard or permitting untraceable replacement.
13. Do not close F001 by merely removing the `!isGreenfieldAuthoring` guard and
    reusing `foldExtraEditorNodesIntoBlocks`. That positional helper folds all
    extras into the final foldable source block and can misbind a paragraph
    created in the middle of a section. Capture TipTap JSON and
    `sourceBlockId` order before/after Enter, rebuild by stable identity plus
    adjacent anchors, and test both mid-section and end-section Enter. Assert
    that neighboring canonical block IDs/locators and table/image identities
    do not drift.
14. Evaluate a high-priority custom Enter command against the actual installed
    TipTap schema (core/StarterKit 3.27.4; `@tiptap/pm` 3.27.2). At a cursor
    inside `sourceBlock > paragraph/heading`, prove
    whether a depth-1 transaction split or the equivalent splitBlock command
    keeps the new paragraph in the same sourceBlock. Do not copy a generic
    ProseMirror example without `canSplit`/transaction evidence from this
    schema. Stable-ID mapping remains mandatory even if command-level
    containment succeeds.
15. AI revision has two distinct contracts. A real user selection is a
    rewrite target. A section with no body text is a drafting target and must
    send empty selected text plus StudyDefinition, PICOS, approved corpus and
    section semantics to produce 3-5 substantive body candidates. A heading
    must never be silently substituted as selected body text. Fake/disabled
    providers may prove routing and payload shape only, never medical-writing
    quality.
16. Competitor search completion alone is not an AI-first PICOS result. The
    current backend only persists a search snapshot and the current frontend
    only renders five hard-coded archetypes. Closing this P1 requires a
    traceable proposal contract, recommendation generation from the project
    definition and triaged corpus, prefilled values, visible rationale/source
    links and user edit/override; visual preselection without backend
    proposals is not acceptance.
17. Runtime evidence must keep provider quality separate from UI mechanics.
    Isolated API 8912 currently reports independent AI unconfigured/not ready,
    so screenshots s22-s27 are substitute-output evidence only. Stable API
    8911 reports the production DeepSeek provider ready but has an older build
    fingerprint. Medical candidate quality remains unverified until a separate
    runtime has both the current source fingerprint and the configured
    production AI provider.

## Risk Boundaries

- Kimi stages 1-3 may write only under:
  - `records/active_slices/medical_writing_frontend_kimi_progressive_20260719/`
  - `records/active_slices/medical_writing_frontend_kimi_progressive_20260719/kimi_demo/`
  - task-specific screenshots/logs under the same directory.
- Do not write to production frontend until Codex reviews the Kimi demo and issues a same-session stage-4 continuation.
- Stage 4 may write only frontend files explicitly listed by Codex after a backup and baseline test run.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Use fake or disposable test data for mutating flow tests. Do not alter real clinical source files.
- Do not stop stable 5174/8911 or the Qoder comparison runtime on 4321.
- Do not claim the Qoder demo is the current product.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-19 21:09:16: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-19: User delegated a four-stage Kimi-led frontend design and progressive-integration slice. Stable runtime, Qoder anti-example, production write boundaries, and prohibited DOCX files were fixed in this contract.
- 2026-07-19: Baseline found 5174 embeds an older backend build fingerprint while the main task continues changing backend source. Created isolated 8912/5176 with a copied runtime store; backend and frontend fingerprint both `api-948922e9f1f3881e`. `medical_writing_runtime_readiness_qc.mjs` passed on the isolated runtime with no console errors.
- 2026-07-19: User clarified that F001 only timed out while waiting 20 seconds
  for the editor heading after refresh. Added the required runtime/API/database
  persistence evidence chain; no failure classification will be made from
  that timeout alone.
- 2026-07-19: User reviewed `s14_after_step1_commit_1920.png`. Added P1 product
  acceptance for AI-first PICOS proposal/prefill/rationale after a successful
  454-study/220-document search, plus P2 findings for project-code truncation
  and low information density.
- 2026-07-19: F001 was decomposed with direct runtime/API/SQLite evidence.
  Enter creates a visible paragraph but save is blocked because editor/source
  block counts diverge (56 vs 54). An in-block edit persisted from revision 2
  to 3 and survived API/database reread plus a full isolated frontend/backend
  restart. A plain page refresh resets URL `/` to the default project
  dashboard, explaining the old title wait timeout. A possible cursor-to-block
  mapping mismatch remains pending real mouse-click confirmation.
- 2026-07-19: User accepted the Enter block-count mismatch as a real P1 and
  required a source-preserving new-paragraph mapping fix with full persistence
  evidence. AI-first PICOS/framing after competitor retrieval remains a
  separate P1 and cannot be addressed as a styling issue.
- 2026-07-19: User prohibited the positional end-fold shortcut for imported
  documents. F001 acceptance now requires stable-ID/adjacent-anchor mapping and
  mid/end Enter tests with TipTap JSON plus source identity evidence.
- 2026-07-19: Source review confirmed `sourceBlock` is an isolating `block+`
  container and the current mapper is positional. Added actual-schema
  split-command validation before implementation.
- 2026-07-19: Traced AI-first PICOS to a missing backend recommendation
  contract, not a hidden frontend rendering bug. Traced title-only AI
  candidates to editor initialization falling back from absent body text to a
  heading as `selected_text`.
- 2026-07-19: Marked s22-s27 as UI/substitute-provider evidence only. Current
  isolated 8912 has no independent AI configured; configured 8911 is an older
  build and cannot be used as current-source quality acceptance.
- 2026-07-19: The current installed TipTap minimal schema probe passed
  depth-1 splitting
  at both paragraph middle and end while preserving the current and following
  sourceBlock IDs. Real-workbench selection ancestry and before/after JSON
  still require capture before implementation acceptance.
