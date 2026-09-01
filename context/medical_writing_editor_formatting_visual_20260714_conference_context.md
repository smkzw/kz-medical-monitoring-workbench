# Conference Context: medical_writing_editor_formatting_visual_20260714

Created: 2026-07-14 09:14:24
Objective: 审阅医学写作Word式富文本与结构化表格工具栏的桌面交互分组、信息密度、样式边界、表格插入和视觉风险；基于现有2048x1024真实页面与统一rich_text到DOCX契约，不执行生产写入
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

- `records/active_slices/medical_writing_editor_formatting_20260714/ARCHITECTURE_REVIEW_PACKET.md`: bounded current-state, proposed interaction and backend/DOCX contract.
- `records/active_slices/medical_writing_content_quality_20260714/browser_qc/rux_source_content_open_2048x1024.png`: current 2048x1024 editor layout with a fixed review dock, useful for density and occlusion analysis.
- `records/visual_qc_20260712/medical_writing_real_projects_three/medical_writing_proj_rux_03_002_desktop.png`: current real-project editor without the new review dock.
- `frontend/AGENTS.md`: local product and frontend constraints.
- Participants may inspect these two images visually. They may not open a browser or claim final visual acceptance.

## Scope

- In scope: toolbar grouping, always-visible versus popover controls, current-selection state, style preset/direct-format hierarchy, structured table insertion dialog, desktop density and likely overlap/overflow states.
- Out of scope: production edits, backend implementation, source DOCX or patient data, web research, mobile redesign, new table fact models, final browser acceptance.

## Success Criteria

- Return a concrete two-row or alternative desktop toolbar specification grounded in the current screenshots and existing design system.
- Keep document editing and the AI rail primary; do not turn the page into a toolbar product or an oversized Office clone.
- Preserve every requested capability without relying on mobile feature cuts.
- Identify the 3-5 highest-risk visual/interaction failures and exact browser states Codex should verify.
- Keep screenshot observations separate from inference and recommendations.

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
- Do not recommend ordinary Markdown/HTML tables; table insertion must create the existing structured table model.
- Do not approximate or redraw the CMS logo.

## Loop Log

- 2026-07-14 09:14:24: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Codex added the bounded architecture packet, local frontend constraints and two real 2048px editor screenshots before prompt preflight.
