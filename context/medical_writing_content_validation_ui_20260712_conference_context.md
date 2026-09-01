# Conference Context: medical_writing_content_validation_ui_20260712

Created: 2026-07-12 22:49:32
Objective: 审阅医学写作证据面板中文件内容核验与显式确认交互，确保桌面端严谨、紧凑、无安全扫描残留且不弱化编辑器与AI主工作区
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

- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/styles.css`
- `records/visual_qc_20260710/medical_writing_proj_rux_03_002_desktop.png`（改动前同项目写作工作台）
- `records/visual_qc_20260712/medical_writing_reference/medical_writing_reference_content_validation_desktop.png`（当前1600x1000真实Chrome状态）
- `records/visual_qc_20260712/medical_writing_reference/medical_writing_reference_drawer_qc.json`
- `records/active_slices/medical_writing_competitor_corpus_20260712/TASK_RECORD.md`

## Scope

- In scope：AI rail内文件内容核验的信息层级、密度、术语区域、长URL/状态/override提示、滚动与编辑器主次关系；1600x1000桌面端。
- Out of scope：移动端、后端临床判断正确性、重构整体写作编辑器、直接插入正文、恢复安全扫描。

## Success Criteria

- 当前面板不遮挡或压缩编辑器/AI核心工作流，文档结构列保持可用。
- NCT、适应症、文件类型、来源、版本日期和核验状态可扫描比较，长值不溢出。
- mismatch/需确认状态可发现，显式确认有充分提醒但不形成重型弹窗流程。
- 页面不出现安全扫描、隔离区或药物安全性歧义。
- 输出具体到可验证的前端修改；Codex用真实Chrome和前后截图做最终判断。

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

## Loop Log

- 2026-07-12 22:49:32: Conference initialized by `hermes_workflow_guard.py init-conference`.
