# Conference Context: medical_writing_visible_table_editor_20260714

Created: 2026-07-14 05:52:15
Objective: 复核医学写作工作台中研究流程表及其他方案表格的同步可见性、信息层级、桌面端可审阅性、表格选择定位与复杂宽表交互；基于三项目真实截图和DOM一致性报告提出可执行缺陷，Codex负责最终验收
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

- `records/active_slices/medical_writing_visible_table_editor_20260714/TASK_RECORD.md`: user requirement, implementation boundary, prior verification and pitfalls.
- `output/medical-writing-table-sync-qc/medical_writing_table_sync_qc.json`: 1600x1000 Chrome DOM/API parity report for RUX-03-002, CMS-D001 and MY008211A-PNH-3-01.
- `output/medical-writing-table-sync-qc/proj_rux_03_002_densest_table.png`: RUX densest real protocol table state.
- `output/medical-writing-table-sync-qc/proj_d001_densest_table.png`: D001 densest real protocol table state.
- `output/medical-writing-table-sync-qc/proj_my008_pnh_3_01_densest_table.png`: PNH densest real protocol table state.
- `frontend/src/App.jsx` and `frontend/src/styles.css`: current writing editor, table synchronization band and desktop layout implementation.
- Treat screenshots as rendered evidence and code/report as structural evidence. Do not infer interactions that are not represented by either source.

## Scope

- In scope: table title, actual table body, complete notes, source caption, row/column/note metrics, table picker, scroll linkage, AI cell-revision affordance, horizontal/vertical review ergonomics, information hierarchy, text overflow and desktop density.
- Out of scope: new routes, medical/regulatory correctness of protocol content, mobile adaptation, source document parsing, backend schema redesign, production edits by participants.

## Success Criteria

- Independently inspect all three full-resolution screenshots, not just thumbnails.
- Separate pixel-level observation, source/report evidence, inference and recommendation.
- Identify only actionable issues that remain after DOM parity passed; do not re-report missing-table defects contradicted by the report.
- Prioritize findings by likely impact on a medical manager reviewing or editing a wide protocol table.
- Preserve the user boundary: document editing and AI interaction remain the primary workspace; full-screen designer remains available for structural edits.
- Codex can map each accepted recommendation to a specific source/CSS change or consciously reject it with evidence.

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
- Desktop is the formal target. Do not recommend removing table columns, notes, evidence or editing functions to improve mobile behavior.
- Do not substitute cards, summaries or Markdown for the real table.

## Loop Log

- 2026-07-14 05:52:15: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14 05:55:00: Added three-project screenshots, DOM parity report, implementation source and task record as the bounded evidence packet.
