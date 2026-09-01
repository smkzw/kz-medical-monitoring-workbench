# Conference Context: medical_writing_workspace_usability_20260715

Created: 2026-07-15 11:59:27
Objective: 重构医学写作工作台的桌面端信息架构、编辑器主路径、目录导航和AI证据交互，解决白屏、无法新建项目、信息过载和格式不保真
Task type: `visual_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Hermes `aishuo-gpt55 / gpt-5.5`. If either is unavailable, the runner tries OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Hermes `aishuo-gpt55 / gpt-5.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and OpenCode Go `deepseek-v4-flash`. If the OpenCode Go Flash role fails, the runner first switches to Reasonix `deepseek-v4-flash`, then tries OpenCode Go `qwen3.7-plus` and `mimo-v2.5`.
- Reasonix is used here only as the declared Flash fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_writing_workspace_usability_20260715/TASK_RECORD.md`: 用户最新六项纠正、运行态根因、当前 LOOP 和边界。
- `records/active_slices/medical_writing_workspace_usability_20260715/crash_probe/proj_ra_greenfield_sandbox.png`: 1920x1080 绿地写作台真实截图，包含三列挤压、空白编辑器和底部资料包。
- `records/active_slices/medical_writing_workspace_usability_20260715/crash_probe/proj_rux_03_002.png`: 1920x1080 原始 DOCX 写作台真实截图，包含表格正文、AI栏、151节点窄目录和底部资料包。
- `records/active_slices/medical_writing_workspace_usability_20260715/crash_probe/probe_report.json`: 三项目常驻端口浏览器探针结果。
- `frontend/src/App.jsx`: 当前写作主工作区、RichProtocolEditor、AI/证据栏、文档目录和底部 support zone。
- `frontend/src/styles.css`: 当前桌面布局和写作组件样式。
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`: 两阶段从零建项和方案摘要导入界面。
- `services/api/app/project_source_manifest.py`: 当前静态项目目录，解释为何不能新建项目。
- `services/api/app/medical_writing_document.py`: 原始 DOCX 解构合同与格式提取边界（如实际文件名不同，可在当前工作区内定位对应实现，但不得越出工作区）。

## Scope

- In scope: 医学写作桌面工作台信息架构；正文优先布局；可展开目录；子系统导航；新项目入口；竞品语料准备与主台证据候选边界；富文本格式可见性；逐按钮验收策略。
- Out of scope: 修改生产代码、运行浏览器/测试、医学或监管结论、重新设计其他子系统的业务内容、移动端功能裁剪。

## Success Criteria

- 形成可直接映射到现有组件和 CSS 的桌面信息架构，不给抽象营销式建议。
- 正文编辑区必须成为最大视觉和交互区域，目录与子系统导航不得常驻压缩正文。
- 主台右栏只保留 AI 交互和当前章节 3-5 个可直接采用的证据候选；检索/下载/解析/翻译/批量AI审核放到独立工作流。
- 明确哪些现有常驻卡片应移除、折叠或改为按需抽屉。
- 给出新建项目入口与从零/摘要导入两路径的最短可用链。
- 给出格式保真所需的前后端合同和浏览器/Word 验收点，而非只建议调整 CSS。

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

- 2026-07-15 11:59:27: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-15: Codex 重新读取全局 `/Users/smkzw/.codex/AGENTS.md`，本视觉会商按 aishuo MiniMax-M3 + aishuo-gpt55 GPT-5.5 无 chair 路由执行；Grok 4.5 作为非 Hermes 的额外单轮视角，不替代正式参与者。
# 2026-07-15 定向复核更新

本次复核仅评估最新实现，不得复述首次会商时已经失效的旧三栏、无新建项目、纯文本编辑器等观察。

- 最新真实桌面截图：`records/active_slices/medical_writing_workspace_usability_20260715/crash_probe_v5/proj_rux_03_002.png`。
- 最新全屏表格单元格点击截图：`records/active_slices/medical_writing_workspace_usability_20260715/crash_probe_v5/proj_rux_03_002_table_designer_cell_selected.png`。
- 最新几何/错误证据：`records/active_slices/medical_writing_workspace_usability_20260715/crash_probe_v5/probe_report.json`。
- 当前实现已满足：topbar 72px；6 个项目信息子项同一行且均 46px；侧栏收起 64px；Logo 元素位于品牌盒内；无 viewport overflow；全屏表格单元格可选；React/API 错误均为空。
- 定向复核问题：顶部状态和 Logo 是否仍有明显视觉层级/溢出问题；编辑器与 AI 候选区比例是否符合桌面医学写作；全屏表格的选中、工具栏、属性栏是否直观；是否存在会立即阻断用户的 P0 问题。
