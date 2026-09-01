# Task Context: medical_monitoring_r1_audience_progress_20260809

Created: 2026-08-09 22:47:39
Objective: 在隔离 R1 POC 中将权威工作单元进度只读投影为资深医学监察员可直接理解的中文进度、当前工作与滚动动态，精确守恒完成数且不暴露后端身份、日志或内部状态标识
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py`
- 当前文件系统与已通过门禁的 R1 权威进度证据；不从旧会话记忆推断运行状态。

## Scope

- In scope: 在隔离 POC 新增只读投影模块和合成测试；从 `Store.structured_progress`
  及冻结 manifest 投影准确分母、阶段进度、当前工作、滚动动态和中文状态。
- In scope: 对界面值执行中文可读性与内部标识泄漏防护；重试只显示“继续处理”，
  不显示尝试编号或执行身份。
- Out of scope: 产品前端、医学写作子系统、8911 服务、真实 harness/provider/API/端点、
  真实研究项目、依赖安装、进度账本或运行时写路径修改。

## Success Criteria

- `completed`、`total`、百分比和各阶段计数与权威投影严格守恒；阻断/失败虽计入
  已处理分母，但在分类状态中单独如实显示。
- 当前工作和滚动动态只使用 manifest 冻结的中文 stage/label/临床 target 及受控模板，
  不透传运行 detail、execution identity、原始 event/status 或日志。
- 输出中不含 run/work-unit/node/attempt/provider/model/selector/hash/audit/backend 等内部身份，
  也不出现“正式事实”“候选信号”“只读xx”等非医学监查表达。
- pending/running/passed/reused/skipped/not-applicable/blocked/failed 与重试路径均有测试；
  非中文或包含内部标识的 audience label 必须 fail closed。
- 聚焦、权威进度相邻回归、R1 core、AE/MH audience、Patient Journey 分组回归通过；
  8911 保持无监听，产品与医学写作文件不改动。

## Risk Boundaries

- 允许写路径仅为 `poc/medical_monitoring_ai_native_r1/` 内的新投影模块/测试以及本任务的
  `context/`、`reviews/`、`metrics/` 和独立证据文件。
- 不修改已封存的权威 Store/Capability Runtime 合同；投影层无写能力、无外部副作用。
- 不启动 8911、服务或真实项目，不安装包，不改产品/医学写作源码。
- Codex 负责真实文件、测试和最终门禁；独立审阅者只有 veto/accept 权，不直接改写实现。

## Timeout Policy

- 本地聚焦检查先行；若进入独立审阅，沿用 guard 声明的长硬等待，不因延迟重派。
- 失败只依据确定的测试失败、证据不守恒、边界泄漏或终态审阅 veto。

## Loop Log

- 2026-08-09 22:47:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09 22:50: 冻结范围、成功标准与写边界；Patient Journey 刷新审阅门禁通过。
- 2026-08-09 23:15: 同一 Luna CLI compatibility 审阅会话复现中文紧邻协议、地址、
  路径及含中文 target 技术目录泄漏，VETO；仅修 audience 边界与聚焦测试。
- 2026-08-09 23:27: 同会话继续复现大小写/单字符 opaque scheme 漏检，VETO；改为
  通用 scheme 拦截并以临床缩写白名单保留 `ALT:轻度升高` 等中文医学表达。
- 2026-08-09 23:32: 同会话重跑 41 个边界 case、39 个只读/篡改 check、focused 68、
  adjacent 105，最终 ACCEPT，P0-P4=0；import-only Ruff 纠偏后再次 hash-bound ACCEPT。
- 2026-08-09 23:34: R1 core 259、AE/MH audience 18、Patient Journey 16 全绿，
  grouped 293；Ruff/compileall 通过，临时 bytecode cache 清理，8911 无监听。
