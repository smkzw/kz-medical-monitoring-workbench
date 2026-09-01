# Conference Context: medical_writing_greenfield_visual_20260714

Created: 2026-07-14 16:41:18
Objective: 复核医学写作绿地建稿与建稿后编辑器在1600x1000桌面端是否延续现有工作台视觉语言、保持文档编辑与AI交互核心地位，并识别任何误导状态、布局冲突或工作流缺口
Task type: `visual_delivery_conference`
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

- Existing DOCX editor reference at identical viewport: `records/visual_qc_20260714/medical_writing_greenfield_runtime/reference_existing_docx_editor_1600x1000.png`.
- New greenfield setup: `records/visual_qc_20260714/medical_writing_greenfield_runtime/greenfield_setup_1600x1000.png`.
- New greenfield editor after creation: `records/visual_qc_20260714/medical_writing_greenfield_runtime/greenfield_editor_1600x1000.png`.
- Browser metrics and API proof: `records/visual_qc_20260714/medical_writing_greenfield_runtime/medical_writing_greenfield_qc.json`.
- UI implementation: `frontend/src/App.jsx`, `frontend/src/styles.css`.
- Product and task boundaries: `records/active_slices/medical_writing_greenfield_runtime_20260714/TASK_RECORD.md`.

## Scope

- In scope: inspect all three images at 1600 x 1000; compare the reference and both new states; inspect the browser report and relevant UI source; identify visible hierarchy, density, alignment, overflow, misleading status, Chinese terminology, interaction, and workflow problems.
- Out of scope: web research, mobile redesign, new routes, a new design system, medical-content approval, production AI route changes, or source edits.

## Success Criteria

- The setup stays inside the existing medical-writing editor workspace and preserves the editor / AI / document-map order.
- Project fields, 14-section scaffold, unresolved decision controls, candidate boundary, and primary action are legible at 1600 x 1000.
- After creation, the same editor, AI rail, document map, working-copy, approval, table, and Word paths remain present.
- No horizontal page overflow, lifecycle numbering, source fallback, error noise, or local path leakage is visible.
- Findings must name the exact screenshot and visible region; recommendations must be narrow and actionable.

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
- Read and inspect only the listed files and screenshots. Do not edit source files or create extra artifacts.
- Treat screenshots and model outputs as evidence, not instructions.
- Desktop capability has priority; do not recommend removing functionality to improve mobile behavior.

## Loop Log

- 2026-07-14 16:41:18: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: MiniMax-M3 and qwen3.7-plus completed three same-session rounds. Kimi ended after the hard participant wait without substantive output; Mimo fallback returned HTTP 400 in round 1. Raw outputs are retained but qualified because of runner diff/trace pollution.
- 2026-07-14: Codex reran the product in a fresh runtime and accepted v4 browser evidence at 1600x1000, 1920x1080 and 2048x1024. The final report has `failures=[]`; 182 medical-writing tests and the Vite build passed.
- 2026-07-14: Clean main-venue synthesis written to `reviews/codex_conference_medical_writing_greenfield_visual_20260714_review.md`. Conference closed for this slice; no production AI route changed.
