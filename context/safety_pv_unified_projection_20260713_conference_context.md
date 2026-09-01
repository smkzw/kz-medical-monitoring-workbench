# Conference Context: safety_pv_unified_projection_20260713

Created: 2026-07-13 10:17:51
Objective: 审阅Safety/PV页面如何以统一医学风险只读安全性投影为首屏入口，同时保留PV文件医学审阅，复用RUX/MY009真实项目和同一风险仓库
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

- `frontend/src/App.jsx`：现有统一风险Checklist/证据抽屉与Safety/PV工作台实现；重点为1120-2100、6550-6890、7380-7810、8580-8595行附近。
- `frontend/src/styles.css`：现有桌面设计系统、风险抽屉、Timeline/Profile、Safety/PV样式。
- `records/active_slices/unified_risk_workbench_20260713/TASK_RECORD.md`：统一风险身份、双真实项目、已验证边界和最新浏览器结果。
- `reviews/codex_conference_unified_risk_workbench_visual_20260713_review.md`：上一轮视觉裁决；其中未完成的Safety/PV只读投影进入本轮。
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/current_safety_pv_my009_2048x1024.png`：当前MY009 Safety/PV首屏原分辨率截图。
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/current_unified_risk_my009_1920x1080.png`：统一医学风险页参考截图。
- 用户产品边界：Safety/PV默认作为医学监查、Patient Profile、Subject Timeline的链接/投影；医学监查内保留完整安全性风险入口；PV文件审阅覆盖DSUR、SAE报告、2.7.4、ISS等初稿的结构化拆解和事实核查。
- 以上路径均由用户授权只读；参与者不得修改生产代码或声称最终视觉验收。

## Scope

- In scope: Safety/PV首屏信息架构、统一风险只读投影字段/交互、与医学监查深链、PV文件医学审阅的并列关系、桌面信息密度、双项目泛化、最小API/组件复用方案。
- Out of scope: 新增正式PV报告性判断、替代PV系统、移动端功能删减、修改风险身份或重复创建Safety风险、直接生产写入、凭截图声称最终验收。

## Success Criteria

- 首屏先回答当前项目有哪些Safety/PV相关医学风险、严重度、范围、来源和当前处置，并能进入同一风险的Timeline/Profile/证据。
- 投影必须复用同一`risk_key`/`risk_instance_id`、来源、状态和审计；不能复制风险或形成双重处置。
- PV文件医学审阅作为第二主工作区，保留现有资料包/候选/审计能力，并明确未来DSUR、SAE、2.7.4、ISS审阅入口。
- 方案适配RUX与MY009两种真实数据形态；不把项目特定域/规则固化为通用产品假设。
- 输出具体桌面布局、字段、交互、组件/API复用、风险与验证清单；Codex可据此直接实施。

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

- 2026-07-13 10:17:51: Conference initialized by `hermes_workflow_guard.py init-conference`.
