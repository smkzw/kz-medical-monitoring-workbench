# 医学监查 R4 阶段总体关闭任务上下文

日期：2026-08-18  
状态：`ACCEPT_R4_STAGE`  
任务：只读审计 D01–D10 的合成/离线风险子图阶段是否满足 System Design v1.1 与 R0–R8 计划的 R4 完成门；仅在独立审阅接受后解锁 R5。

## 来源权威

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
3. `context/medical_monitoring_r4_d10_runtime_final_acceptance_pause_20260818.md`
4. D01–D10 的冻结合同、最终 acceptance records、当前 R4 源码/测试、generator/oracle/registry 与 immutable anchors。
5. 当前文件系统、实际测试输出和端口状态优先于历史摘要。

## 关闭门

- D01–D10 每域适用性、输入、来源、时间边界、阳性/阴性/边界/反证、`not_applicable/not_evaluable` 与误报/漏报合同可定位。
- AE/MH、CM、IP、方案/潜在 PD、访视、疗效、实验室/检查、多表逻辑、中心模式、项目/跨中心聚合均有可追溯事实/风险/反证/Query 或明确不适用语义。
- ensemble size 1/N、隔离分析、evidence verifier/adjudication、基座 gap search 与高风险不隐藏语义闭合。
- Query 保持“依据＋发现＋行动项”；PD 仅作为待核实线索，不建立发送/回复/关闭工作流。
- 风险 identity、merge/split/reopen、`identity_ambiguous`、`superseded/not_evaluable` 与高风险自动关闭边界不被跨域投影破坏。
- 决策路径不得读取 oracle、case-id/index、mutation class 或 synthetic sentinel；replay/order/mutation/hidden/negative 证据有效。
- D01–D10 公共导出、相邻传播路径、完整 R4 回归、Ruff/compile、冻结 SHA/anchor 与 8911 停止均通过。
- 独立 verifier 只能返回 `ACCEPT_R4_STAGE` 或 `REVISE_R4_STAGE`；任何真实 P0–P4 均阻断关闭。

## 边界

- 只审计/必要时最小修复 `poc/medical_monitoring_ai_native_r4` 及本任务记录；不得修改产品源码或医学写作子系统。
- 不启动 8911、服务、浏览器，不运行五个真实项目，不调用真实医学分析模型。
- 不进入 R5/UI，不做系统安全设计或测试。
- 本阶段接受只代表 synthetic/offline R4 风险子图，不代表产品、真实项目、R5、生产或商业化完成。

## 路由与等待

- 按最新全局规则使用隔离 `Codex subAgent/codex/gpt-5.6-sol:high` 做 stage review；Codex 主会场保留最终接受权。
- 单次长等待上限 120 分钟；慢响应不触发重派，同一 session 仅在明确可操作缺口时补发。

## LOOP

- Objective：获得可审计的 R4 阶段接受或精确退回清单。
- Hypothesis：D01–D10 已分别接受，但阶段级跨域与完成门仍需从当前文件系统独立重建。
- Action：主会场结构/测试审计＋隔离 Sol 阶段审阅。
- Observation：测试、静态追踪、SHA、anchor、端口和独立 verdict。
- Decision：`ACCEPT_R4_STAGE` 才更新计划并进入 R5；否则按传播路径最小修复并在同一 reviewer session 复验。
- Record：本文件、主计划、review 与最终 acceptance/pause record。

## 最终观察与决定

- 初次独立审阅返回 `REVISE_R4_STAGE`，定位四类阶段阻断：共享参考基线/多模型闭环缺失、D06 合成哨兵/固定样本分流、公共 coverage matrix 冻结漂移、Ruff 与 D07 旧 pin。
- 五项修复工作和三轮同会话负向探针复验后，独立 verifier 对稳定快照返回 `ACCEPT_R4_STAGE`，无 P0–P4。
- 决定性门禁：ensemble `116 passed`，D06 `920 passed`，D08–D10 相邻 `177 passed`，D07–D10 artifact `385 passed`，全 R4 `4396 passed`；Ruff、94 个源文件内存编译、D06/D07/D09/D10 generator/oracle/authority/verifier 检查、18 个冻结 JSON SHA 均通过。
- coverage matrix 显式勘误并重冻结为 SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`；D07 接受 pin 为 `e0e244d03d06a30127daeb71769733439e8620d62722b78074eb2e2068a3f4e9`。
- 8911 无监听。R4 接受范围仅为 synthetic/offline 风险 Agent 子图；R5、UI、真实项目/模型、产品、生产、正式临床结论与医学写作仍未接受。
- 下一安全动作：先冻结 R5 用户任务、信息架构、聚合口径、Journey 交互与视觉验收合同，再实施面向用户的最小纵切；在合同要求真实浏览器前继续保持 8911 停止。

外部发现决定：本轮不重新搜索架构方案；设计 v1.1 已完成外部研究，当前问题是对不变合同和本地实现做阶段验收，新增搜索不会改变关闭门。
