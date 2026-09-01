# Conference Context: source_ledger_visual_qc_20260713

Created: 2026-07-13 03:37:21
Objective: 审阅医学经理工作台项目级来源台账的桌面信息架构、中文标签、状态与override交互，基于真实MY009和RUX截图提出可执行修正，不编辑生产文件
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

- `records/visual_qc_20260713/source_ledger/proj_my009_uc_1600x1000.png`
- `records/visual_qc_20260713/source_ledger/proj_rux_03_002_1920x1080.png`
- `records/visual_qc_20260713/source_ledger/source_ledger_qc.json`
- `frontend/src/App.jsx`：`SourceRegistryPage`、导航与状态标签实现。
- `frontend/src/styles.css`：`.source-ledger-*` 桌面布局。
- `frontend/AGENTS.md`：产品和文件内容校验边界。
- 旧系统视觉语言对照：`records/visual_qc_20260713/tfl_safety_source_admission/safety_my009_admission_before_1600.png`。

## Scope

- In scope: 桌面信息架构、中文标签、三轴状态、override门槛、历史版本入口、长标题、密度、对齐和跨项目一致性。
- Out of scope: 改代码、重新运行浏览器、改变医学/PV业务边界、移动端适配、恶意软件扫描。

## Success Criteria

- 分别审阅1600与1920真实截图，区分像素观察和代码推断。
- 找出会误导资深医学用户或影响高频操作的具体缺陷，给出可定位的修正建议。
- 确认warning/mismatch与已确认沿用不混淆，override门槛不弱化。
- 不引入本地路径/hash显示，不建议恢复安全扫描。

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

- 2026-07-13 03:37:21: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-13: Codex补齐最终截图、实现与QC指标来源；页面已通过1600/1920 Chrome检查，会议用于独立复核而非替代验收。
