# Conference Context: mw_ai_first_authoring_redesign_20260718

Created: 2026-07-18 21:10:14
Objective: 审议医学写作AI前置撰写器重构合同：极简建项、证据化AI预填、正交研究设计、I期复合研究、IB利用、用户采用即确认及人因易用性硬门
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/RESEARCH_AND_IMPLEMENTATION_CONTRACT.md`
- `records/visual_qc_20260715/medical_writing_draft_applicability/qc_report.json`
- `frontend/src/components/medical-writing/MedicalWritingNewProjectDialog.jsx`
- `frontend/src/components/medical-writing/MedicalWritingAuthoringJourney.jsx`
- `services/api/app/medical_writing_journey.py`
- `services/api/app/writing_study_definition.py`
- `services/api/app/project_source_manifest.py`
- `services/api/app/main.py` 中医学写作项目、PICOS、候选和审批相关路由
- `frontend/src/App.jsx` 中医学写作建项、framing、PICOS、候选采用和审批状态
- 本会商只读；用户已授权读取本地真实方案/IB，但参与者不得把机密内容复制到
  外部查询、报告或提示词。研究合同中的本地路径和抽象观察足够时不再打开原文。

## Scope

- In scope:
  - 极简双入口建项和跨步骤已知事实继承；
  - 竞品调研、摘要、IB和语料驱动的字段级AI预填；
  - 正交研究设计字段和“其他自然语言 -> AI结构化”；
  - 完整PICOS建议包及证据/冲突/置信呈现；
  - I期多研究部分的分类、组合依赖、SoA/终点/安全性/停止标准投影；
  - IB解析、版本、项目事实、章节引用和变更影响；
  - `AI suggested -> user confirmed`，用户采用后不再重复医学批准；
  - 人因易用性、零耐心医学经理和真实项目验收合同；
  - 现有系统到目标状态的最小兼容迁移序列。
- Out of scope:
  - 本轮不修改生产代码、数据库、端口、真实项目或临床文件；
  - 不设计未来电子签名、药政发布或多角色医学总监审批的完整实现；
  - 不替代当前正在独立执行的翻译对齐V11主线；
  - 不把外部商业平台或付费组件引入生产依赖。

## Success Criteria

1. 从医学经理真实任务出发，明确哪些步骤必须删除、自动化、延后或保留。
2. 对研究合同逐条提出接受、修订或拒绝意见，不能只做摘要。
3. 给出可实现的数据状态机、API/job边界和桌面交互，不把AI预填简化成
   静态默认值或新的大表单。
4. I期分类和组合规则同时覆盖科学、操作和文档投影；指出不应默认合并的研究。
5. IB利用有项目事实边界、版本影响、冲突和数据出域风险控制。
6. 用户采用即确认，清除当前初版重复的“待医学批准”，同时不丢失审计。
7. 建立可量化的人因门：必填数、原创字数、点击数、重复确认、首个可用草稿
   时间和流程跳转；解释为什么此前多模型测试未发现这些问题。
8. 形成不推翻现有系统的实施分片、回归测试矩阵和明确的剩余决策。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-18 21:10:14: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-18 21:14: Source, scope, risk and success criteria populated from the
  user requirement ledger and independent research contract.
