你是全新上下文的独立验收审阅者，只读，可否决但不得修改任何文件。Codex 主会场保留最终决定权。

边界：
- 只在当前工作区读取隔离 R1 POC、任务 context、设计/计划和测试。
- 不启动服务、8911、浏览器、真实模型/provider/endpoint/项目。
- 不读取或触碰医学写作子系统、产品运行码或真实项目资料。
- 只运行 synthetic/offline 测试；不得安装依赖、写代码或修复。

必读：
1. `context/medical_monitoring_r1_controller_binding_20260809_context.md`
2. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` 中真实进度、内部术语不外露、AI 不直接晋升医学事实合同
3. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` 当前 R1 状态
4. `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
5. `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py` 的 observer、invoke/resume 和无响应体证据路径
6. `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py` 的 domain object 并发写入、capability journal、work-unit bind/retry/complete、审计投影与 persistence
7. `poc/medical_monitoring_ai_native_r1/tests/test_controller.py`
8. `tests/test_capability_runtime.py`、`tests/test_authoritative_progress.py`、`tests/test_audience_progress.py`

验收问题：
- assignment 是否在 transport 前持久且只有 v1；同 attempt/不同 request 两 SQLite 连接并发时，是否永远只保留一个可恢复分配。
- 是否只有 durable journal claim/replay 后才能进入真实 running；declared 未 claim 能否绕过 controller 或 Store 伪造进度。
- 原始/候选证据是否先于 work-unit 终态；complete 才 passed，失败/中断不会冒充成功。
- 预注册未调度、journal 已终态未持久化、terminal/cache replay 是否幂等，已终态 replay 是否零 transport。
- assignment/profile/request/manifest/tamper/continued_from/concurrency 是否 fail closed。
- controller 是否保留 runtime retry/resume：partial/timeout/truncated/interrupted 终态工作项是否可在严格 `continued_from` 下重开 running，历史 complete 事件是否保留，最终投影与当前 ledger 是否一致。
- AI 输出是否仍 candidate-only、无 canonical facts/发布/确认权限。
- 工作流详情是否是医学监查员可读中文，无前台工程术语。
- 是否越界到医学写作、产品、真实项目或 8911。

上一独立审阅曾否决三点，本次必须特别复现/检查，不得仅信主会场说明：
- 并发 assignment 可能生成 v2 并不可恢复；
- declared 未 claim 可直接 bind 伪造 running；
- controller 过早封闭 failed/blocked 使 runtime resume 断链。

主会场当前报告的非 LLM 锚点（请独立核对能够运行的部分）：
- controller + authoritative progress + capability runtime：`100 passed`
- R1 全套：`271 passed`
- 改动范围 Ruff：`All checks passed!`
- compileall 通过；8911 无监听。

请返回：
1. `VERDICT: ACCEPT` 或 `VERDICT: VETO`
2. P0-P4 问题，逐条给出文件、行号、复现/推理证据和影响；无问题时明确各级为 0
3. 已验证范围与精确测试输出
4. 未验证范围和残余风险
5. 当前关键文件 SHA-256

不得写文件或修改代码。
