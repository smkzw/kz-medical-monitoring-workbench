# 医学监查 AI 原生重构实施计划 v1.1

**状态**：`R8_G6_CONTRACT_FROZEN_READY_FOR_GOVERNED_IMPLEMENTATION`  
**前置设计**：`reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（文内版本 v1.1，路径保留作恢复锚点）  
**当前约束**：医学写作子系统继续保护；8911/5174/8984 停止；G7 前不访问五个真实项目，G8 前真实项目语义不进入模型，G6 前不启动产品浏览器；旧 P10/B6/真实 LOOP 不恢复

**当前恢复锚点（2026-08-31）**：R8 G6 synthetic `ego(lite)` 受众验收合同已独立接受，权威记录为 `context/medical_monitoring_r8_gate6_contract_acceptance_record_20260831.md`。四轮同会话审阅冻结 actual app 入口、可证伪执行闭集、九场景生命周期、Path A 双通道 presented、九终态×四能力、六类失效导航、十三项应用内 §15.4 任务、1920–4K 数值视觉门、Journey/流向 oracle 和双独立 reviewer 顺序，最终 P0-P4 全零。下一步进入 governed G6 实施；只有受控 synthetic app/browser 可启动，仍不访问真实项目、不调用真实模型/harness、不修改医学写作，G6 接受前不进入 G7。

**当前恢复锚点（2026-08-18）**：R4 D01–D10 synthetic/offline 风险 Agent 子图已完成阶段总体关闭，独立 fresh-context verifier 对稳定快照返回 `ACCEPT_R4_STAGE`，无 P0–P4。最终门禁：ensemble `116 passed`、D06 `920 passed`、D08–D10 adjacent `177 passed`、D07–D10 artifact `385 passed`、全 R4 `4396 passed`，Ruff、94 文件内存编译、四域 generator/oracle/authority/verifier、18 个冻结 JSON SHA 与 8911 停止全部通过。权威记录为 `context/medical_monitoring_r4_stage_closure_acceptance_record_20260818.md`。当前已解锁 R5 合同与实现：先冻结风险驾驶舱、中心图谱、Subject Workspace/Patient Journey 的用户任务、数据口径、交互和视觉验收合同，再实施 audience-facing 最小纵切。真实项目/模型、生产和医学写作仍受保护；8911 在真实浏览器验收前保持停止。

## 1. 宏观目标

以“可恢复的研究级 Monitoring Run”为中心，把现有 Profile、Timeline、AE/MH 漏报、风险、mapping、batch、规则、AI、审计与报告能力迁移到一个框架中立、证据优先的 Graph 内核，最终在全部五个真实项目上达到双角色连续两轮零 P0-P4。

采用渐进式迁移，不做大爆炸重写：先建立领域权威和隔离纵切，再通过 adapter/双读验证保留现有有效资产，最后切换投影和用户入口。

## 2. 全局实施原则

1. **旧系统是迁移来源，不是新架构控制平面。**
2. **领域合同先于框架。** POC 不能把框架 session/message 写入业务 schema。
3. **来源只读。** 五个真实项目原始文件永不被系统测试修改。
4. **每阶段有非 LLM 锚点。** schema、hash、测试、真实文件、渲染界面或恢复日志至少一项。
5. **独立 QC 拥有阶段完成。** 开发节点不能自我宣布完成。
6. **修复按传播路径回归。** 不再堆叠与真实用户价值无关的微合同 LOOP。
7. **看板运行证据优先。** UI/文档输出必须在真实 audience-facing runtime 验证。
8. **8911 仅在明确实施阶段和隔离运行合同下启动。**
9. **工程语言与用户语言分层。** 领域对象、状态机和字段名可在内部合同中使用，但监察员界面只能显示具体医学问题、风险等级、支持/排除依据和数据来源；不得把源数据记录称为“正式事实”，不得把一般待核实线索称为“候选信号”。
10. **临床域不能被记录状态取代。** 事件与风险至少按 AE、MH、CM、IP给药、实验室/检查、住院/操作等域分别编码；风险等级另行显示，并以自动化浏览器门防止退化回通用“事项/风险”图例。

## 3. 里程碑总览

| 里程碑 | 结果 | 主要验收 |
|---|---|---|
| M0 | System Design v1.1 批准 | 会商问题闭环、状态/覆盖/验收合同冻结、用户批准、ADR backlog |
| M1 | Graph/存储/恢复 POC | 中断、重启、幂等、checkpoint、artifact 可重放 |
| M2 | 领域内核与旧资产 adapter | facts/risk/run/audit 单一权威；双读一致 |
| M3 | 通用资料/数据智能 | 三类以上项目结构不靠硬编码接入 |
| M4 | 风险子图与多模型机制 | 核心域、AE/MH 漏报、裁决、Query 可追溯 |
| M5 | 项目/中心/Subject Workspace | 风险到来源一跳；Profile/Timeline 共轴同步 |
| M6 | 外部报告与模式输出 | 报告三件套、三模式组合输出一致 |
| M7 | 三模式与本地应用恢复 | 日常/锁库前/核查前贯通；备份迁移可用 |
| M8 | 五项目严格完成 | 双角色连续两轮零开放 P0-P4 |

## 4. 阶段 R0：设计、会商与批准

### 目标

锁定框架中立设计、迁移策略、验收合同和 POC 问题，不修改产品实现。

### 步骤

1. 合并 D1-D39 为 System Design v1，并在独立会商后修订为 v1.1。
2. 建立领域对象、状态图、Agent cards、Artifact Envelope、UI 信息架构和完成门。
3. 运行独立架构会商，重点挑战复杂度、状态权威、单机可行性、AI adapter、恢复、审计和五项目验收成本。
4. 对会商问题分类：必须修订、POC 验证、实施期观察、拒绝并说明。
5. 形成 Design v1.1、ADR backlog 和用户批准包；批准前冻结：正交发布状态、快照接受链、节点副作用、风险身份、Adapter/coverage、三模式合同与 P0-P4 判定合同。
6. 用户明确批准后才进入 R1。

### 完成证据

- 已批准 System Design v1.1；
- 会商报告与问题处置表；
- POC success/failure criteria；
- 保护路径与回滚边界；
- 仍保持产品源码、8911 和真实项目冻结。

## 5. 阶段 R1：框架中立领域图与隔离 POC

### 目标

用最小非真实/隔离数据证明状态权威、artifact/coverage、恢复、进度、三模式和用户配置 AI adapter 可行，并完成一个 audience-facing AE/MH 纵切，再决定框架。

### 步骤

1. 定义 graph IR：node、edge、condition、work unit、checkpoint、retry、skip/reuse、publication gate。
2. 定义 `MonitoringRun/ExecutionManifest/NodeRun/ArtifactEnvelope/AuditEvent` 最小 schema，以及 analysis/evidence/review/output 正交状态。
3. 构造不含真实项目内容的代表性 fixture：一个项目、两个快照、AE/MH 完整风险域、一个含正文/表格/图形/脚注的报告。
4. 实现同一 audience-facing 纵切：来源 → 快照接受/mapping → facts → AE/MH 候选/反证 → QC/coverage → 风险驾驶舱 → 共享访视轴的受试者医学旅程（含 Profile/Timeline 同步子视图与风险标记）→ Query 草稿。
5. 分别验证候选图引擎；必要时验证 Temporal 的跨重启活动，但不得先承诺引入服务。
6. 实现 API adapter 与至少一个 harness adapter 的最小公共合同：binding/version、输入哈希、工具权限、隔离上下文、启动、状态、原始输出、complete/partial/truncated、coverage、取消、恢复/继续、超时和审计。
7. 实现真实 manifest 进度和结构化工作播报。
8. 注入故障：模型不可用、截断/部分输出、进程中断、artifact/审计/manifest 提交边界崩溃、节点重试、重复提交、迟到回调、artifact 损坏和 manifest revision。
9. 验证 snapshot acceptance、identity ambiguous、风险 merge/split/reopen、规则/范围变化导致 superseded/not_evaluable，而非错误 auto-close。
10. 用日常/锁库前/锁库后—CFDI 前三个最小 ModeContract 验证 cutoff、修订、carry-forward 和输出资格不会静默串用。
11. 验证报告 ClaimCoverageLedger、批注锚点和 coverage 不足时不声明全报告完成。
12. 比较开发复杂度、恢复、可观察性、单机打包、许可证、存储、性能与迁移成本。
13. 形成框架与持久化 ADR；失败候选保留证据，不强行采用。

### 完成证据

- 可重复 POC；
- schema 与状态迁移测试；
- 中断/重启/幂等/重放日志；
- AE/MH 医学纵切的阳性、阴性、边界、反证与 coverage 证据；
- 合成名义/实际/非计划访视、访视间事件、日期待定和风险锚点的“受试者医学旅程”交互证据；
- Adapter 正常/部分/截断/失败/恢复矩阵；
- 三模式最小状态机与报告 claim coverage 证据；
- 真实进度逐项对账；
- 框架/存储/回滚 ADR；
- 独立 reviewer 接受。

## 6. 阶段 R2：领域内核、审计与迁移底座

### 目标

建立单一 Run、来源、事实、风险、裁决和审计权威，使旧服务只能通过 adapter 接入。

### 步骤

1. 实现 StudyProject、SourceRevision、ListingSnapshot 和内容寻址 artifact store。
2. 实现 KnowledgePack、RuleActivation、Mapping/Facts 版本合同。
3. 实现 SnapshotAcceptance、source coverage、mapping/record identity 与 baseline eligibility 状态链。
4. 实现 RiskCandidate、RiskInstance、RiskTransition、AdjudicationRecord，以及稳定风险身份、merge/split、identity_ambiguous、superseded/not_evaluable。
5. 实现双基线、三类 ModeContract 与 full/incremental 快照 diff。
6. 实现项目级 tamper-evident 业务审计和验证工具；技术日志分离。
7. 实现 checkpoint、原子 artifact/state/audit 提交、幂等 side-effect gate 和 publication gate。
8. 为现有 batch、mapping、rule、risk、Profile/Timeline 服务建立只读/写入 adapter。
9. 建立旧/新双读比对，证明同一来源/事实/风险的身份映射。
10. 明确旧数据库表冻结、迁移、回滚和删除禁区；当前阶段不删除旧状态。
11. 对共享合同运行单元、属性、迁移、并发与失败测试。

### 完成证据

- 单一 schema registry；
- 双读差异报告；
- 审计链重建/篡改检测；
- 迁移与回滚演练；
- 无真实项目写入；
- 独立 QC 接受。

## 7. 阶段 R3：Study Intelligence 与异构 listing

### 目标

让项目资料、适应症、药物和 listing 结构被智能识别，消除 RUX/MGK10/MY009 硬编码成为公共内核的风险。

### 步骤

1. 资料分类、版本、有效时间和范围识别。
2. 方案/修订、IB/RSI、项目计划与外部证据结构化抽取。
3. 建立四层知识、claim authority matrix 和 source conflict/resolution。
4. 实现 listing workbook/table/field 结构画像与稳定 record identity。
5. 实现语义 mapping 候选、置信度、字段依赖与用户少量确认。
6. 实现日期、单位、编码、部分日期、重复记录和缺失语义。
7. 实现 snapshot diff 与临床影响传播。
8. 实现自然语言规则拆解、模拟、激活和三类 evaluation scope。
9. 用隔离副本逐步读取三种以上项目结构进行只读结构验证，不运行完整医学分析。
10. 对项目 adapter 与公共内核做反过拟合审查。
11. 增加 baseline-free/hidden challenge cases，对比基座可见/隐藏时的遗漏、误报与锚定偏差；一致性不得提升为医学真值。

### 完成证据

- Knowledge Pack 与 source conflict fixtures；
- 三种以上 listing 结构盲测；
- mapping/日期/单位/identity 质量报告；
- 无项目绝对路径或项目名硬编码进入公共规则；
- 独立医学/工程 QC。

## 8. 阶段 R4：风险 Agent 子图与多模型分析

### 目标

覆盖核心风险域，统一证据、分级、反证、生命周期、多模型和 Query。

### 步骤

1. 定义每个风险域 coverage matrix：适用前提、必需输入、来源权威、时间边界、阳性/阴性/边界/反证、not applicable/not evaluable、误报/漏报和医学裁决。
2. 实现 AE/MH 事实一致性、严重性和漏报候选。
3. 实现 CM/IP 暴露、适应证、禁限用药、依从性和处置关系。
4. 实现方案/访视/潜在 PD/Query 风险；PD 只进入 Query 核实。
5. 实现疗效终点、个体趋势、异常改善/恶化与缺失解释。
6. 实现安全/实验室/检查、基线/给药/处置关系和严重事件线索。
7. 实现多表交叉、时间逻辑和数据质量风险。
8. 实现中心重复模式和项目安全/疗效信号聚合。
9. 实现 reference baseline 核验与 baseline gap search。
10. 实现 ensemble size 1/N、隔离并行、归并、evidence verifier 与 adjudication binding。
11. 实现三段式 Query 草稿、导出和不跟踪外部回复边界。
12. 实现低/中自动关闭、高风险门与重开身份。
13. 为每域建立 reference cases、反证、边界、hidden cases 和误报/漏报分类；候选、事实、正式结论分别计量。

### 完成证据

- 每域事实/风险/反证/Query 可追溯；
- AE/MH 候选不污染正式事实计数；
- ensemble 1/N 语义正确；
- 高风险不被多数票/裁决静默隐藏；
- 跨域相邻回归；
- 独立 QC 接受。

### 当前实施进度（2026-08-14）

- D01 AE/MH、D02 CM、D03 IP、D04 方案/潜在 PD 与 D05 访视/评估/样本时序的
  合成/离线纵切均已完成独立验收。
- D05 权威验收记录为
  `context/medical_monitoring_r4_d05_implementation_acceptance_record_20260812.md`；
  最终门禁为 D05 `342 passed`、R4 `1327 passed`、R2 `598 passed`、
  R3 `339 passed`，独立 Luna 复审 `ACCEPT`。
- D06 v1.16 初始实现被独立审阅拒绝：存在 expected/manifest 循环注入、
  106/191 同输入异 trace 及多项硬编码/失败吞没问题；该实现从未被接受。
- D06 疗效终点/评估/趋势合同 v1.18 已完成原独立 Luna 会话的语义接受与
  冻结元数据复核；冻结文件 SHA-256 为
  `460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb`，
  接受记录为 `context/medical_monitoring_r4_d06_contract_acceptance_record_20260813.md`。
- D06 v1.18 合成/离线实现已完成独立验收。权威记录为
  `context/medical_monitoring_r4_d06_implementation_acceptance_record_20260813.md`；
  最终门禁为 raw oracle/DSL `219/219`、mutation `119 passed`、D06
  `912 passed`、R4 `2239 passed`、R2/R3/R1 `598/339/327 passed`，原 Luna
  verifier session `019ff7e2-f2ef-71a0-9c84-fa5e303cad24` 最终
  `VERDICT: ACCEPT`、无 P0-P4。该结论不等于 R4 总体、R5 UI、真实项目、
  产品或生产接受。下一步按 R4 顺序先冻结 D07 临床安全性/实验室/检查纵切合同，
  再做合成/离线实现；继续保持 8911 停止、不运行真实项目、不触碰医学写作，
  不扩展系统安全设计/测试。
- D07 临床安全性、实验室、检查、中文 Query 与 renderer-neutral Journey 合成/离线纵切已完成独立验收。权威记录为 `context/medical_monitoring_r4_d07_runtime_acceptance_record_20260814.md`；最终门禁为 challenge matrix `303 passed`、R4 `3657 passed`、R1/R2/R3 `327/598/339 passed`、generator 三项与 Ruff 全部通过，8911 停止。原 Luna verifier session `019ffdb2-3613-7872-aa8e-47fcbaee88ad` 最终返回 `ACCEPT_D07_RUNTIME`。该结论不等于 R4 总体、R5 UI、真实项目、真实模型、产品或医学写作接受。下一步按顺序先冻结 D08“多表医学逻辑与数据质量”合同，再实施 synthetic/offline D08。
- D08 多表医学逻辑与数据质量 synthetic/offline 纵切已完成独立验收。权威记录为 `context/medical_monitoring_r4_d08_runtime_final_acceptance_20260814.md`；最终门禁为 D08 `186 passed`、全 R4 `3843 passed`、R1-R3 `1264 passed`、generator `54 passed`、Ruff/compile 通过，8911 停止。原 Luna verifier session `019fff98-9f85-7ec2-ba80-63be3ef6ab1e` 最终返回 `ACCEPT_D08_RUNTIME`，当前范围无剩余 P0-P4。该结论不等于 R4 总体、D09/D10、R5 UI、真实项目/模型、产品、生产或医学写作接受；下一步只解锁 D09“中心重复模式与系统性风险”合同冻结。
- 2026-08-14：R4-D09 中心重复模式与系统性风险合同已冻结为 `FROZEN_R4_D09_CONTRACT_V0_5`，合同 SHA `9d20b994...907e40`。Pi/CMS-SMK 与 Grok Build 原会话完成多轮挑战，独立 Codex Luna/max CLI compatibility session `01a0004e-3fb6-7b30-a552-95edd8d9932a` 经 v0.3/v0.4 `REVISE` 后对 v0.5 返回 `ACCEPT_D09_CONTRACT`；8911 停止。权威记录为 `context/medical_monitoring_r4_d09_contract_acceptance_record_20260814.md`。该结论不等于 artifact/runtime、D10、R5 UI、真实项目或产品接受；下一安全动作仅为构建并独立冻结 D09 179-case 以上 synthetic/offline catalog/oracle/registry/generator。
- 2026-08-14：D09 artifact 构建已完成 Worker 01 catalog/quota/provisional registry 与 Worker 02 independent oracle/resolved registry，并通过 Codex 聚焦静态检查；权威暂停记录为 `context/medical_monitoring_r4_d09_artifact_oracle_pause_20260814.md`。artifact freeze **尚未接受**：Worker 03 非 LLM 冻结测试与独立 Luna freeze review 未开始；Worker 01 generator 的 unresolved registry 与当前 resolved registry 存在预期的 staged `--check` mismatch，必须在 Worker 03 首先闭合。8911 停止；下一安全动作仅为重新核对 SHA 后启动 Worker 03。
- 2026-08-15：R4-D09 179-case synthetic/offline artifact freeze 已完成并经独立 Luna/max 验收。Worker 03 同会话闭合了 resolved registry 两阶段校验、oracle 隐藏语义标签/跳过、全 179 例处置与计数独立重建、generator hash 篡改门及 CASE-047 D08 成员风险类型白名单缺陷；生成器真实校验路径已对未列明风险类型 fail-closed。最终门禁为 D09 `96 passed`、D08 相邻 `54 passed`、两套 D09 generator check、compile、固定 SHA 与 8911 停止；同一独立 verifier session 先 `REVISE_D09_ARTIFACTS`、修复后返回 `ACCEPT_D09_ARTIFACTS`。权威记录为 `context/medical_monitoring_r4_d09_artifact_freeze_acceptance_record_20260815.md`。该结论不等于 D09 runtime、D10、R4 总体、R5 UI、真实项目/模型、产品或医学写作接受；下一安全动作只解锁 D09 synthetic/offline runtime 规划与实施。
- 2026-08-15 后续 runtime 审计发现上述 artifact ACCEPT 的新证据缺口：首版 D09 evaluator 只有直接按 `mutation_context.mutation_class`、`SYN-*` 哨兵值和合成 revision hash 约定分支才能实现 179/179 parity，属测试意图泄漏。清除全部这些决策耦合后，当前冻结 catalog 只有 151/179 例可由领域事实完整重建，28 例缺失显式的 authority/method/statistical expansion/query redundancy/lifecycle prior-state/site identity/source resolution/producer verification 事实。权威纠偏记录为 `context/medical_monitoring_r4_d09_runtime_worker01_overfit_correction_20260815.md`。原 ACCEPT 作为历史证据保留，但不再解锁 Worker 02/D09 runtime；当前先由原独立 Luna 验收会话裁决 artifact schema 是否必须重开及最小显式事实补丁。
- 2026-08-16：D09 Worker01/artifact 的 fact-completeness 纠偏已由原 Luna
  会话接受；其后 Worker02 projection 经两次同会话执行纠偏和 Codex 三项
  最小闭环修复，独立 Luna verifier 最终返回
  `ACCEPT_D09_WORKER02_PROJECTION`。接受快照、65 条 Query 的 PD 双门控、
  hidden audience 隔离、锚点/证据/R2 防篡改与 revision 顺序稳定证据见
  `context/medical_monitoring_r4_d09_worker02_projection_acceptance_20260816.md`。
  Worker03 现已解锁，仅执行 public exports、mutation/anti-overfit/replay/
  closure 与全量回归；8911、真实项目、产品/UI、D10 和医学写作继续冻结。
- 2026-08-16：D09 Worker03 closure 与最终 runtime 纠偏已完成；同一独立
  verifier 节点连续退回并复测 Query 精确绑定、伪造结果、owner/token/action、
  evaluation identity、已知/未知工程引用和 Unicode 绕过，最终对固定 SHA 返回
  `ACCEPT_D09_RUNTIME`。最终门禁为 D09 `243 passed + 33 subtests`、D07/D08
  `1604 passed`、全 R4 `4086 passed + 33 subtests`、R1/R2/R3
  `327/598/339 passed`、artifact `99 passed`、两套 generator check、Ruff/
  compile/import 与 8911 停止。权威记录为
  `context/medical_monitoring_r4_d09_runtime_final_acceptance_20260816.md`。
  该接受不等于 D10、R4 总体、R5/UI、真实项目/模型、产品、生产或医学写作；
  下一步只解锁 D10 项目/跨中心聚合合同与挑战矩阵，runtime 继续锁定。
- 2026-08-16：R4-D10 项目/跨中心安全与疗效信号聚合合同已冻结为
  `FROZEN_R4_D10_CONTRACT_V0_6`，合同 SHA
  `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`。
  同一隔离 Luna/max verifier session 对 v0.1-v0.5 连续返回 revise，逐层关闭
  owner/legal matrix、身份/分母/可比性、baseline/change、R2、盲态可见性、
  Query/投影、多模型与 cutoff/deep-link 传播缺口，最终对固定 v0.6 返回
  `ACCEPT_D10_DRAFT_FOR_REVISION_FREEZE`。Codex 静态复核确认 21 个核心合同对象、
  312 个互斥 primary case 配额、mandatory-attack 子配额、固定 SHA、prompt
  preflight 与 8911 停止。权威记录为
  `context/medical_monitoring_r4_d10_contract_acceptance_record_20260816.md`。
  该接受不等于 D10 artifact/runtime、R4 总体、R5/UI、真实项目/模型、产品、
  生产、正式临床结论或医学写作；当前按用户指令无损暂停。恢复后下一安全动作
  仅为构建并独立冻结 D10 synthetic/offline catalog、oracle、registry、generator
  与 quota manifest，runtime 继续锁定，8911 必须保持停止。
- 2026-08-17：R4-D10 312-case synthetic/offline artifact 已完成五门纠偏并经
  全新隔离 Luna/max verifier 独立验收，最终结论 `ACCEPT_D10_ARTIFACTS`。
  最终门禁为 D10 `106 tests`、D09 `99 tests`、三项 generator check、独立
  verifier `0 problems / 0 cases failing`、外部 `uchg` raw-SHA 锚点与 8911
  停止。权威记录为
  `context/medical_monitoring_r4_d10_artifact_freeze_acceptance_record_20260817.md`。
  该接受不等于 D10 runtime、R4 总体、R5/UI、真实项目/模型、产品、生产、
  正式临床结论或医学写作；下一安全动作仅为在 `poc/medical_monitoring_ai_native_r4`
  规划并实施 D10 synthetic/offline runtime，且决策路径不得读取 oracle、case-id/index、
  mutation class 或合成哨兵。

## 9. 阶段 R5：风险驾驶舱、中心图谱与 Subject Workspace

### 目标

把复杂风险转换成资深医学监察员可快速浏览、比较和定位来源的桌面工作面。

### 步骤

1. 实现项目级“变化优先＋当前全量”风险驾驶舱。
2. 实现全部中高风险、低风险折叠、筛选、风险簇与热点。
3. 实现中心风险热图、重复模式、受试者热点和统计/目录切换。
4. 实现绝对量＋标准化率、分母展开、not evaluable 与小样本提示。
5. 实现分栏 Risk Inspector 与基座/多模型/裁决/证据/来源对照。
6. 实现统一 Subject Workspace、共享身份栏和默认“受试者医学旅程”；完整 Profile/Timeline 分别保留为同步的“指标趋势/事件明细”子视图。
7. 实现 Subject Temporal Spine、实际日期主轴、研究日切换、阶段带和名义/实际/非计划访视轴；部分/冲突/缺失日期独立表达。
8. 实现 AE、MH、CM、IP 给药、检验与检查、住院与操作、症状与疗效、方案符合性八类自适应可折叠轨道及点/区间事件；补齐 AE/MH 漏报、禁用药、入排、访视/给药/样本/评估 PD 与 Query 依据。
9. 实现 Journey/Profile/Timeline 共享时间刷选、缩放、选择、交叉高亮、深链接和返回上下文恢复。
10. 实现风险在事件/区间/访视处的空间锚定；中高风险全部优先显示，重叠聚类，各临床域、风险类型与等级用形状＋域名短标签＋文字直接表达，不只靠颜色；前台禁止“已记录事项”“正式事实”“候选信号”“通用风险点”。
11. 实现 AE/MH 漏报多投影、“原疑似漏报—后续已补录记录”匹配历史，以及风险标记—正反证—原始 listing—方案/IB—Query 双向联动；身份不一致 fail-closed。
12. 建立桌面优先视觉系统、图例、密度、语义缩放、色彩、可访问性和窄屏降级。
13. 真实浏览器逐页视觉/交互 QC，不以组件测试替代。

### 完成证据

- 风险到来源定位成功率；
- Journey/Profile/Timeline 同一访视轴、时间窗、选择与风险锚点一致性；
- 项目/中心/受试者聚合数字可重建；
- 真实用户任务时长、点击数和视觉评分；
- audience-facing screenshots/Playwright evidence；
- 独立视觉/医学 QC。

### 当前实施进度（2026-08-18）

- R5 S0 总合同已冻结并独立接受；S1 R4→R5 authority adapter 已完成并接受。
- R5 S2 第一条 synthetic/offline、renderer-neutral 薄纵切已完成并由原独立
  reviewer 在 `REVISE_R5_S2` 后复验接受。该片闭合项目风险→中心→Inspector→
  Subject Workspace/实际日期锚点→精确来源，包含两名隔离 worker、可见分歧、
  独立裁决与 packet-only ModelEvidence；外部个体成员替换、ModelEvidence 身份/
  哈希篡改、来源类型漂移和分析窗漂移均 fail-closed。
- 最终门禁：R5 普通/优化均 `427 passed + 15 subtests`，R4 全量
  `4396 passed + 11258 subtests`，前置 generator/verifier 普通/优化及 13 个
  tamper probes、Ruff、compile、只读 SHA 与 8911 停止全部通过。权威记录为
  `context/medical_monitoring_r5_s2_acceptance_record_20260818.md`。
- 该接受不等于 UI/浏览器、真实项目/模型、临床事实、产品/生产或 S3-S8；
  下一步进入 S3 项目驾驶舱与中心图谱合同/实现，8911 在 S7 前保持停止。
- 2026-08-26 续接状态：S3 项目驾驶舱/中心图谱、S4 Risk Inspector/
  ensemble 以及 S5 public-authority producer 前置链均已有独立接受记录；
  S5 Subject Workspace / Patient Journey renderer-neutral runtime v0.1 已以
  `ACCEPT_R5_S5_SUBJECT_WORKSPACE_RUNTIME_V0_1` 接受。S5 最终门禁为
  focused normal/`-O`/`-OO` 各 `349 passed`、public-authority 相邻回归
  `68 passed + 15 subtests`、250/250 mutation/oracle、36 条 S5 真运行、
  10/10 public graph replay、10/10 owned 与 51/51 frozen hash、8911 停止；
  权威记录为
  `context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_acceptance_record_20260826.md`。
  该接受不等于前端/浏览器、真实项目/模型、临床事实、产品/生产、security
  或医学写作接受。下一步按阶段合同进入 S6：先冻结深链、返回上下文、密度/
  语义缩放、键盘/非颜色编码与高密度性能语料合同，再实施离线 runtime；
  8911 继续停止，S7 才允许产品最小接入和真实浏览器验收。
- 2026-08-27 续接状态：S6 深链/返回/密度/键盘与非颜色合同和 runtime、S7
  产品最小接入 runtime 均已有独立接受记录；S7 当前用户可见核心已在 1440×900
  与 1600×1000 真实 Playwright 下完成两套独立复核。MiniMax-M3 与 Gemini 3.7
  Flash 对修订后 9 个决定性场景各执行 18 次并返回 `P0-P4=0`，Codex 复核最新
  截图与 `22 passed`、route 28、adapter 41、产品合同及 production build。权威记录为
  `context/medical_monitoring_r5_s7_browser_visual_acceptance_record_20260827.md`。
  CodeBuddy/HY3 原会话最终重放在 B10 后因供应方 429 中断。Codex 自有 runner
  已随后冻结最终 26 行 identity/network/7 次冷暖性能测量包：26/26 行通过，
  cold p95 969.56 ms、warm p95 953.22 ms、交互 p95 44.60 ms、FPS p05 107.53，
  140 个网络记录全部为 GET 且 0 失败/0 外部请求。R5-S7 总关闭标记现仅等待
  HY3 原会话最终重放；可并行冻结 R6 合同，但 R6 runtime 实现须等待该单一门关闭。
- 2026-08-27 R6 合同续接：外部报告审阅、ClaimCoverageLedger、反向遗漏、稳定
  claim/issue identity、三件套、三模式和输出门的 prose、machine contract 与 86 行
  metadata-oracle 挑战矩阵已在独立执行与同 session 多轮会商后，以
  `ACCEPT_R6_CONTRACT_V0_1_FOR_SYNTHETIC_OFFLINE_PLANNING` 接受。权威记录为
  `context/medical_monitoring_r6_contract_acceptance_record_20260827.md`。该接受只解除
  R6 合同规划门，不等于 runtime、产品、真实项目/报告或格式渲染接受；R6 runtime
  仍须等待上述 R5-S7 HY3 原会话重放关闭，8911/5174 继续停止，医学写作子系统保持不变。
  当前 `validate-conference` 对 Cursor 必选标记与 live route 输出不一致，已作为治理
  工具缺口记录；不得用伪造席位或补词绕过，也不改变本合同内容裁决。

## 10. 阶段 R6：外部报告审阅与模式化输出

### 目标

完成报告主张核查、三件套与三种监查模式输出。

### 步骤

1. 报告结构/claim 提取和版本/截止身份。
2. claim—事实—风险—Profile/Timeline—前次报告逐条核查。
3. 遗漏、过度/不足、错误截止和内部矛盾检测。
4. report review matrix 与稳定 issue identity。
5. ClaimCoverageLedger 覆盖正文、表格、图形、脚注、分母与 cutoff；未提取单元明确 no_claim/not_evaluable。
6. 格式感知批注副本；不可原位批注时生成旁注副本并准确声明，验证 issue 锚点。
7. 可选清洁修订稿、DRAFT 身份和未决冲突安全表述。
8. 修订报告重新上传后的 issue 解决状态比较。
9. 日常增量摘要与受影响 Query。
10. 锁库前全量风险、修订影响和检查包。
11. 锁库后—CFDI 前全量报告、中心/个例材料与 checklist。
12. DOCX/PDF/HTML 输出的内容、格式、身份、coverage、哈希和来源 QC。

### 完成证据

- 主张矩阵与来源定位；
- 页/表/图/脚注 claim coverage 对账；
- 原件/批注/清洁稿身份不混淆；
- 输出间数字/风险一致；
- 修订前后 issue diff；
- 渲染/格式保真 evidence；
- 独立医学/文档 QC。

### 当前实施进度（2026-08-28）

- R6 v0.1 合同第一条 synthetic/offline 机器可执行纵切已接受，权威记录为
  `context/medical_monitoring_r6_runtime_slice_01_acceptance_record_20260827.md`。
  最终门禁为 `243 passed`、86/86 单变异 oracle、18 个正向行无阻断、
  816/816 跨 category 诊断保持、normal/`-O`/`-OO` × 3 hash seeds 全通过，
  frozen input 与医学写作 542 文件聚合 SHA 不变，8911/5174 停止。
- 本接受只覆盖 contract loader、fixture catalog、validator dispatcher 和 evidence
  receipt，不等于报告对象 runtime、产品、真实报告/项目、格式渲染或 R6 总体。
  第二纵切已继续完成并接受。
- R6 第二纵切以 `ACCEPT_R6_RUNTIME_SLICE_02_SYNTHETIC_OFFLINE` 接受，
  权威记录为
  `context/medical_monitoring_r6_runtime_slice_02_acceptance_record_20260827.md`。
  最终门禁为 focused `63 passed`、full `306 passed`、9 个 optimizer/hash
  单元各 `63 passed`、86/86 oracle、医学写作 542 文件聚合 SHA 不变、
  8911/5174 停止，execution audit 与 conference review-gate 通过。
- 该接受只包括 synthetic/offline 的不可变 report source、对象多对多、
  expected review surface/反向遗漏和 ClaimCoverageLedger 双门；不等于
  产品、真实报告/项目、三件套或格式渲染接受。
- R6 第三纵切已以 `ACCEPT_R6_RUNTIME_SLICE_03_SYNTHETIC_OFFLINE` 接受，
  权威记录为
  `context/medical_monitoring_r6_runtime_slice_03_acceptance_record_20260828.md`。
  最终门禁为 focused `71 passed`、full `377 passed`、9 个 optimizer/hash
  单元各 `71 passed`、医学写作 542 文件聚合 SHA 不变、8911/5174 停止，
  execution/conference/Codex review 证据闭环。
- 该接受仅包括 canonical JSON 的三件共享身份、sidecar annotation/anchor map、
  可选 DRAFT、IssueTransition/revision diff；不等于产品、真实报告/项目、医学结论、
  DOCX/PDF/HTML 解析渲染、前端或 R6 总体接受。
- R6 第四纵切已以 `ACCEPT_R6_RUNTIME_SLICE_04_SYNTHETIC_OFFLINE` 接受，
  权威记录为
  `context/medical_monitoring_r6_runtime_slice_04_acceptance_record_20260828.md`。
  最终门禁为 focused `96 passed`、full `473 passed`、9 个 optimizer/hash
  单元各 `96 passed`、医学写作 542 文件聚合 SHA 不变、8911/5174 停止；
  初轮会商发现的 D1-D7 与畸形输入失败开放均经修订并在原 session 复核关闭。
- 该接受只包括 synthetic/offline 三模式 ModeContract、Run gate、通用 ModeOutput、
  daily 四输出与结构化 Query 草稿；不等于产品、真实项目/报告、医学结论、Query
  外发、PD 工作流、pre_lock/post_lock 深层输出或 Agent Harness 接入。
- R6 第五纵切已以 `ACCEPT_R6_RUNTIME_SLICE_05_SYNTHETIC_OFFLINE` 接受，权威记录为
  `context/medical_monitoring_r6_runtime_slice_05_acceptance_record_20260828.md`。
  最终门禁为 focused `204 passed`、full `581 passed`、9 个 optimizer/hash 单元各
  `204 passed`；初轮 worker 证据未直接接受，独立会商发现的 D1-D6 及后续包级
  workflow/count/PD-alias 缺口均由 Codex 修订并在原 Pi/Grok sessions 复核关闭。
- 该接受仅覆盖 synthetic/offline pre_lock 四输出及其 authority、身份、数字、证据、
  生命周期与确定性边界；不等于产品、真实项目/报告、医学结论、Query/PD 工作流、
  post_lock 深层输出或 Agent Harness 接入。
- R6 第六纵切已以 `ACCEPT_R6_RUNTIME_SLICE_06_SYNTHETIC_OFFLINE` 接受，权威记录为
  `context/medical_monitoring_r6_runtime_slice_06_acceptance_record_20260828.md`。
  最终门禁为 focused `351 passed`、full `728 passed`、9 个 optimizer/hash 单元各
  `351 passed`；独立 Pi/Grok 三轮同会话复核最终均为 `accept_limited`。初轮和次轮
  发现的跨输出对账、嵌套身份、draft/PD/overwrite 及 envelope 身份失败开放均已关闭。
- 该接受仅覆盖 synthetic/offline post_lock_pre_cfdi 四输出及其固定总量、锁定身份、
  Profile/Timeline 入口和项目/中心/受试者/checklist 对账；不等于产品、真实项目/报告、
  医学结论、文档渲染、Query/PD/签署/外发、Agent Harness 或 R6 总体接受。
- R6 第七纵切已以
  `ACCEPT_R6_RUNTIME_SLICE_07_AGENT_HARNESS_ADAPTER_LIMITED` 接受，权威记录为
  `context/medical_monitoring_r6_runtime_slice_07_agent_harness_acceptance_record_20260828.md`。
  最终门禁为 focused `35 passed`、full `763 passed`、9 个 optimizer/hash 单元通过；
  修订后的真实合成 OMP smoke 已分别证明 MTPLX medium 默认配置和 DeepSeek V4 Flash
  max 显式配置可调用、可解析、覆盖完整且无 fallback。execution audit、conference
  review-gate 与 conference validation 均通过。
- 该接受仅覆盖独立 ExecutionProfile/Agent Harness adapter 的身份冻结、catalog/preflight、
  argv、调用、receipt 与覆盖失败关闭；不等于产品接线、长任务继续/恢复/取消、医学质量、
  真实项目、R6 总体或 R7 接受。下一步进入 R7 的最小产品接线纵切：先冻结
  ExecutionProfile 持久化/API 与运行入口合同，使模型配置仍只存在于 harness 层，并保持
  医学业务对象、医学写作子系统、真实项目和前端视觉面在该合同冻结阶段不变。

## 11. 阶段 R7：三模式贯通、本地产品化与恢复

### 目标

让日常、锁库前、核查前三种模式在同一内核中稳定运行，并形成无需手工管理服务的本地应用。

### 步骤

1. 打通三模式 common core 与专属子图。
2. 验证数据基线、医学决定版本、模式输出和跨 Run carry-forward。
3. 实现应用封装的启动/停止、后台任务和本地通知。
4. 实现用户 ExecutionProfile UI、API 凭据安全引用和 harness preflight。
5. 实现真实节点进度、manifest revision 和结构化工作播报。
6. 实现进程/设备中断、模型/harness 故障、恢复和重试。
7. 实现项目备份、恢复、迁移、升级和回滚。
8. 实现项目审计链验证与技术日志轮转。
9. 建立安装、首次启动、升级和卸载数据处置说明。
10. 对性能、存储、调用和长任务稳定性做分级基准。

### Agent Harness 路由约束（2026-08-28 用户确认）

- 内置 Agent Harness 默认目标：
  `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`。
- 同一 adapter 公共合同必须保留并真实验证
  `deepseek/DeepSeek V4 flash:max` 的接入与应用能力。
- 模型选择、健康检查、调用、工具权限、原始输出、partial/truncated、取消、恢复和
  审计必须走 ExecutionProfile/harness adapter，不写死在 R6 业务对象中。
- R6 slice-07 已完成该独立 adapter 的受限接入验收；产品持久化/API、运行入口、后台长任务、
  中断恢复与用户界面仍属于 R7 后续纵切。R6 slice-03/04 的 offline JSON receipt 仍不声称
  模型接入完成。

### 当前实施进度（2026-08-28）

- R7 slice-01 已以 `ACCEPT_R7_SLICE_01_EXECUTION_PROFILE_RUN_BINDING_LIMITED`
  受限接受。权威记录为
  `context/medical_monitoring_r7_slice_01_execution_profile_run_binding_acceptance_record_20260828.md`。
- 已完成四层 ExecutionProfile 的标准库 SQLite 版本化持久化，以及 Monitoring Run 对
  已冻结 R6 harness profile 身份的不可变绑定；门禁为 R7 `56 passed`、相邻 R6
  `763 passed`、9 单元确定性向量通过、独立同会话缺陷修订后 `accept_limited`。
- 该接受不包括产品 API/UI、后台执行、继续/恢复/取消、真实项目、医学质量、Patient
  Journey、R7 总体或 R8。
- R7 slice-02 已受限接受，权威记录为
  `context/medical_monitoring_r7_slice_02_product_api_run_entry_acceptance_record_20260828.md`。
  隔离 API/运行入口实现显式引导、四层配置、默认 MTPLX medium、显式 DeepSeek max、
  三模式身份字段与全量/增量重放/冲突；最终门禁为 focused `37 passed`、R7
  `93 passed`、相邻 R6 `763 passed`，独立会商发现的名称选择、中文错误、应用工厂、
  工作区路径和引导重放缺口均已纠偏。
- 该接受仍不包括产品 `main.py` 挂载、后台执行、真实模型、真实项目、UI 或 R7 总体。
  下一纵切先冻结产品挂载/迁移合同，明确工作区目录、项目作用域、每请求连接生命周期与
  中文错误处理，再做受控接线；不得直接启动 8911/5174。
- R7 slice-03 产品挂载已完成受限接受，权威记录为
  `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`。
  最终门禁为产品聚焦 `15 passed`、R7 `93 passed`、相邻 R6 `763 passed`、相邻产品路由
  `132 passed`，并完成 canonical 项目作用域、双库就绪、每请求连接生命周期、R7 局部中文
  错误和稳定产品错误映射纠偏；8911/5174 停止，医学写作边界不变。
- 该接受不包括后台执行、精确进度、继续/恢复/取消、真实模型、真实项目、前端或 R7 总体。
  R7 阶段复盘与后续顺序见
  `context/medical_monitoring_r7_phase_review_and_slice04_plan_20260828.md`。下一纵切为
  Slice-04：先冻结并独立会商持久化 Run 进度事实面合同，再以 synthetic/offline 方式复用
  R1 manifest、work-unit ledger 和中文受众投影；不得提前启动后台线程、服务或模型。
- 2026-08-28 新增项目/中心默认页“受试者阶段流向”看板与下方表格要求，详见
  `context/medical_monitoring_subject_flow_dashboard_requirement_20260828.md`。该要求进入后续
  产品 UI 纵切，并使用 ego(lite) 做实际浏览器验收，不挤入 Slice-04 后台事实面范围。
- R7 slice-04 持久化运行进度事实面已完成有限验收，权威记录为
  `context/medical_monitoring_r7_slice_04_durable_progress_acceptance_record_20260828.md`。
  最终门禁为聚焦 `38 passed`、R7 `108 passed`、R1 `327 passed`、R6 `763 passed`，
  compileall 69 文件，8911/5174 停止，医学写作 542 文件聚合哈希不变。独立会商发现并关闭
  产品创建允许内部哈希式截止点、但进度层拒绝展示的跨切片陷阱，同时补齐产品级回退/冻结
  与 R1 幂等冲突回归。
- Slice-04 接受不包括后台执行、进程所有权、checkpoint/恢复、真实模型/项目、前端或 R7
  总体。下一纵切为 Slice-05：先冻结后台执行与可恢复状态机合同，明确原子领取、唯一所有者、
  崩溃重建、继续/重试/取消及一致受众快照，再实施 synthetic/offline 纵切。
- R7 slice-05 后台执行与中断恢复已完成有限验收，权威记录为
  `context/medical_monitoring_r7_slice_05_background_recovery_acceptance_record_20260828.md`。
  最终门禁为 focused runtime/determinism `47 passed`、产品 `28 passed`、R7
  `125 passed`、R1 core `327 passed`、R6 功能 `758 passed`（5 个旧缓存计数断言
  deselected）、compileall 70，8911/5174 停止。独立会商复现并关闭了过期租约停止回滚、
  最后单元错误提示继续等状态机缺陷；合同勘误明确进度页只可持久化过期中断，绝不自动继续。
- Slice-05 不包括 R7 总体、真实模型/项目、真实 retry/continuation、两进程 kill-9、
  exactly-once、服务、前端或视觉验收。下一纵切为 Slice-06：先冻结真实模型 capability
  attempt 的 owner/lease、失败分类、有限 retry、同 session continuation 与恢复合同，再做
  隔离实现；不得提前启动 8911/5174 或运行真实项目。
- R7 slice-06 harness 调用、有限重试与恢复已完成 synthetic 范围的受限验收，权威记录为
  `context/medical_monitoring_r7_slice_06_harness_live_acceptance_record_20260828.md`。
  离线故障/并发/租约/泄漏门禁通过后，新受治理 timeout=300 执行包按串行闸门真实完成
  MTPLX medium 与显式 DeepSeek V4 Flash max 各一个 synthetic 单元；两者均一次 attempt、
  terminal complete、解析与覆盖完整、无 fallback。当前 R7+产品路由 `192 passed`，
  compileall 通过，R1/R6 哈希不变，8911/5174 停止。
- 该接受不包括真实项目、产品服务、前端/浏览器、医学质量、医学写作、R7 总体或 R8。
  Slice-06 复盘与下一纵切见
  `context/medical_monitoring_r7_slice_06_review_and_slice07_plan_20260828.md`。下一步为
  Slice-07 用户界面：先冻结真实进度、后台离页、恢复入口和中文体验合同，再做最小产品
  接线与 ego(lite) 验收；项目/中心流向看板作为后续独立 UI 子切片，不与当前 harness 结论
  混合验收。
- R7 Slice-07A 真实进度界面已完成 synthetic 范围受限验收，权威记录为
  `context/medical_monitoring_r7_slice07a_progress_ui_acceptance_record_20260828.md`。
  Codex 独立门禁为 R7+产品路由 `195 passed`、医学监查前端 `49/49` test files、
  隔离夹具 `16 passed`、Vite build 与 ego(lite) live 复核通过；七态、真实
  manifest/work-unit 数字、当前工作、刷新恢复及停止确认已接入。该接受仍不包括真实项目、
  独立视觉会商对最终 v2 失败态层级给出 `accept_limited`；医学监察员首屏无权动作、
  失败 100% 完成错觉及 R5 不可用占位均已关闭。该接受仍不包括真实项目、
  医学质量、三模式端到端、Patient Journey、项目/中心流向看板、R7 总体或 R8。下一步为
  Slice-07B：冻结并实现项目/中心受试者阶段流向 Sankey 与下方表格同源双向对账。
- R7 Slice-07B 受试者阶段流向看板已完成 synthetic 范围受限验收，权威记录为
  `context/medical_monitoring_r7_slice07b_subject_flow_acceptance_record_20260829.md`。项目/中心
  默认页使用同一守恒 `subject_flow` 投影生成横向主流程、关键分支、中高风险与逐例明细；
  节点/连线筛选及 Patient Journey 跳转通过 ego(lite) 实际复核。最终门禁为 focused Python
  `69 passed`、全部 49 个医学监查 Node 测试文件通过、Subject Flow render `99 checks`、
  Vite build 与独立视觉会商通过；8911 和五个真实项目未启动。
- 该接受不证明真实项目阶段解析、医学正确性、三模式产品闭环、R7 总体或 R8。下一纵切为
  Slice-07C：先冻结“运行入口—后台进度—结果看板—Patient Journey”的三模式端到端合同，
  再用 synthetic 全量/定期增量/锁库修订增量矩阵完成最小产品闭环和 ego(lite) 验收。
- R7 Slice-07C 总合同已冻结为
  `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_2_20260829.md`；
  其中 Slice-07C-1 已完成 synthetic 范围受限验收，权威记录为
  `context/medical_monitoring_r7_slice07c1_setup_diff_rules_acceptance_record_20260829.md`。
  三模式 options、同项目同模式已发布基线、规范化业务键差异、项目级自然语言特殊关注规则版本
  和模板生成 work-unit 已接入产品路由。最终门禁为 R7 `170 passed`、产品路由 `37 passed`、
  编译/JSON/执行审计及独立会商通过；8911/5174 和真实项目保持停止。
- Slice-07C-1 不包括 prepare-and-start、结果发布或前端。下一子切为 Slice-07C-2：服务端接受
  模式、完整当前快照、可选同模式已发布基线和已确认规则公开 token，解析并冻结具体版本，
  原子生成 manifest、创建/绑定运行并接入现有后台进度。先补多候选锁库前基线选择测试，并
  明确规则仓库连接回收、SQLite `busy_timeout` 和多 worker 写入边界。
- R7 Slice-07C-2 已完成 synthetic 范围受限验收，权威记录为
  `context/medical_monitoring_r7_slice07c2_prepare_start_acceptance_record_20260829.md`。服务端
  已完成 token 解析、manifest 冻结、原子运行保留、绑定/准备/启动、同 key 重放/冲突、
  reservation-only 中断愈合和 runtime-backed 有界中文历史；医学监察员角色可启动，结果入口
  仍关闭。最终门禁为产品路由 `43 passed`、R7 `181 passed`、compileall、执行审计与三轮同
  session 独立会商通过；8911/5174 和真实项目保持停止。
- Slice-07C-2 不包括结果发布、结果入口、前端、真实项目/模型或医学质量。下一子切为
  Slice-07C-3：冻结并实现 run-keyed 原子 `ResultPublication`、有界 progress 扩展和 R5
  authority packet/result-entry；只有发布事实完整且一致时才开放结果入口。
- R7 Slice-07C-3 结果发布合同已冻结接受，权威记录为
  `context/medical_monitoring_r7_slice07c3_result_publication_contract_acceptance_record_20260829.md`。
  合同钉死 R5-owned S4→产品 authority bridge、双 manifest、冻结身份指纹、publication 状态机、
  registry v2 additive migration、R6 receipt/site/member 门禁、原子 finalize 及精确 result-entry DTO。
- R7 Slice-07C-3 实现已完成 synthetic/offline 范围受限验收，权威记录为
  `context/medical_monitoring_r7_slice07c3_result_publication_acceptance_record_20260829.md`。R5-owned typed
  assembler/bridge、registry v2、双 manifest/receipt/site/member 门禁、原子 finalize、有界 progress 与
  精确 result-entry 已贯通；最终门禁为产品 07C-3 `7 passed`、registry `22 passed`、R5 bridge+S4
  `179 passed`、combined `249 passed in 32.36s`，compileall、同 ID execution/conference 审计和停止端口
  均通过。独立会商 Round 1 的 6 个 P2 已全部关闭，Round 2 及同 ID 登记复核均为 `ACCEPT`。
- Slice-07C-3 不包括前端、真实项目/模型或医学质量。下一子切为 07C-4：用中文原生向导贯通模式/
  快照/基线/特殊关注规则、主按钮、后台离页恢复、历史、精确进度、结果看板和 Patient Journey；
  使用 synthetic 数据及 ego(lite) 完成宽屏、交互、离页恢复和失败关闭验收，继续保持 8911 与真实项目停止。
- R7 Slice-07C-4 已完成 synthetic/offline 中文产品闭环与 ego(lite) 视觉受限验收，权威记录为
  `context/medical_monitoring_r7_slice07c4_visual_acceptance_record_20260829.md`。三模式向导、后台进度、
  历史/结果入口、项目/中心流向、受试者访视轴与来源下钻已在 1280/1440/1920 复核；最终门禁为
  52 个医学监查 Node 测试文件、相邻 Python `129 passed`、fixture `15 passed`、frontend envelope
  `13/13`、Vite/compileall 及独立视觉会商通过。
- R7 阶段复盘确定 Slice-08 为三模式跨 Run 决定连续性，合同已冻结为
  `FROZEN_ACCEPTED_R7_SLICE_08_CONTRACT_V0_2`，权威记录为
  `context/medical_monitoring_r7_slice08_contract_acceptance_record_20260829.md`。
- R7 Slice-08A continuity synthetic/offline foundation 已接受，权威记录为
  `context/medical_monitoring_r7_slice08a_continuity_acceptance_record_20260829.md`。实现 R2 唯一生命周期
  上的 R7 只读变化投影、缺行不关闭、逐对象处置、三模式基线、registry v3 additive migration 与
  ResultPublication 同事务 CAS。最终门禁为聚焦/相邻 `63 passed`、R7 `220 passed`、产品医学监查
  `256 passed`、9-cell 每格 `24 passed`，执行审计及独立会商通过。
- Slice-08A 不含真实 R5/R6 authority 或 artifact 字节/member-set 复核。下一子切为 Slice-08B：先冻结
  窄合同，再接入真实 R5 authority identity、R6 ModeOutput 子项抽取和 publication 成员/字节 SHA-256
  校验；继续保持 UI、服务、真实项目与医学写作不变。后续 UI/可视化切片同时受
  `context/medical_monitoring_visual_polish_acceptance_requirement_20260829.md` 约束。
- R7 Slice-08B 权威与产物桥接已接受为
  `FROZEN_ACCEPTED_R7_SLICE_08B_IMPLEMENTATION`，权威记录为
  `context/medical_monitoring_r7_slice08b_authority_artifact_bridge_acceptance_record_20260829.md`。实现只复用
  R5 typed authority、R6 冻结 ModeOutput/validator 和 R1 真实 ArtifactEnvelope，完成四输出/五类原子项、
  publication 四成员闭包、真实字节与摘要复核、LaunchRegistry v4 CAS 以及最小产品接线。最终门禁为
  聚焦 `74 passed`、产品路由 `61 passed`、全 R7+产品 `320 passed`，核心 74 项九格确定性矩阵及 R1
  相邻 `56 passed`；独立三轮会商最终 `ACCEPT`，8911/5174 停止。
- 该接受不等于中文跨轮 UI、视觉、三模式综合回归、真实项目/模型医学质量、R7 总体或 R8。R5 readonly
  hash 与 R6 医学写作聚合计数的旧基线漂移来自本 Slice 未修改的并行边界，保持显式未解决状态。
  下一子切为 Slice-08C：先冻结中文跨轮连续性投影/交互合同，再接入 08B 事实并以 synthetic 数据在
  ego(lite) 1280/1440/1920 完成项目→中心→风险→Patient Journey→来源的身份、信息层级与视觉验收；
  完成前不得进入 08D，真实项目、服务和医学写作保持不变。
- R7 Slice-08C 中文连续性投影与视觉交互合同已冻结为
  `FROZEN_ACCEPTED_R7_SLICE_08C_CONTRACT_V0_2`，权威记录为
  `context/medical_monitoring_r7_slice08c_contract_acceptance_record_20260829.md`。合同冻结独立 continuity
  公开端点、九项计数与五值关注提示闭集、七类风险变化等级显示、同身份下钻、访视轴 Patient Journey、
  overlay/push 详情抽屉和三视口 ego(lite) 验收。下一步按 08C-1→08C-4 连续实施；合同接受不等于功能或视觉完成。
- R7 Slice-08C-1 continuity 公开端点与 08C-2 项目/中心前端纵切已分别完成 synthetic/offline 受限接受，权威记录为
  `context/medical_monitoring_r7_slice08c1_continuity_endpoint_acceptance_record_20260829.md` 与
  `context/medical_monitoring_r7_slice08c2_frontend_vertical_acceptance_record_20260829.md`。两者建立公开身份、严格校验、项目/中心本轮变化和同身份下钻，但不等于 Patient Journey 抽屉或视觉接受。
- R7 Slice-08C-3 Patient Journey 变化标记与详情抽屉已完成 synthetic/offline 接受，状态
  `ACCEPT_R7_SLICE_08C3_SYNTHETIC_OFFLINE`，权威记录为
  `context/medical_monitoring_r7_slice08c3_implementation_acceptance_record_20260830.md`。最终树保持唯一横向访视轴，完成七类变化、八域中文标签、同身份 event/risk 绑定、overlay/push 详情抽屉、精确行切换、路由关闭与 legacy R5 隔离；门禁为 R5/R7 `23/23`、医学监查全量 `61/61` test files、Vite `1981 modules`，三轮同 session 独立代码会商 P2 `2→1→0` 后 `ACCEPT`。8911/5174 停止，医学写作保护面任务时段内无新 mtime。
- 08C-3 不接受真实 DOM 焦点/滚动锁、实际 resize、1280 overlay、1440/1920 push、整页无横溢、视觉高级感或真实项目/模型医学质量。下一步进入 08C-4：先冻结 ego(lite) 三视口运行时/视觉验收合同和参考图并列比较方法，再进行隔离服务、视觉执行、专项修订和独立视觉会商；完成前不进入 08D。
- R7 Slice-08C-4 已完成 synthetic/offline 桌面运行时视觉受限验收，状态
  `ACCEPT_R7_SLICE_08C4_SYNTHETIC_VISUAL_LIMITED`，权威记录为
  `context/medical_monitoring_r7_slice08c4_visual_acceptance_record_20260830.md`。最终生产视觉边界按用户确认固定为 1920×1080 至 4K；1280/1440 仅保留韧性证据。十轮执行纠偏与八轮同 session 独立视觉会商关闭表格/轨道/中文断词/卡片折叠及 1920 半行裁切，最终 P0-P4 全零。门禁仍包括 R5/R7 `23/23`、医学监查前端 `61/61` test files、Vite `1981 modules` 与 8911/5174/8984 停止。
- 08C-4 不等于真实项目/模型医学质量、R7 总体、R8、生产或商业化。阶段复盘和 08D 计划见
  `context/medical_monitoring_r7_phase_review_after_slice08c4_and_slice08d_plan_20260830.md`。下一步进入 08D 三模式 synthetic 综合回归；不得新增 UI 或窄屏义务，不得运行五个真实项目、启动 8911/5174 或修改医学写作。
- R7 Slice-08D 三模式综合回归合同已冻结为 v0.1 + v0.2 纠偏附录，接受状态
  `ACCEPT_R7_SLICE_08D_CONTRACT_V0_2`，权威记录为
  `context/medical_monitoring_r7_slice08d_contract_acceptance_record_20260830.md`。实施必须完成 20 格业务场景、15 格 hash/优化级别确定性、输入侧独立 oracle、全故障钩子、SQLite 重开/CAS/迟到回调恢复和固定相邻回归；08D 不重复 08C 视觉验收，不运行真实项目/模型，不启动 8911/5174，不修改医学写作。
- R7 Slice-08D 实现已完成 synthetic/offline 接受，状态 `ACCEPT_R7_SLICE_08D`，权威记录为
  `context/medical_monitoring_r7_slice08d_implementation_acceptance_record_20260830.md`。20 格场景、两个 15 格确定性探针、31 个当前源码故障钩子、SQLite 重开、CAS/重放/迟到回调、公开中文和固定相邻回归均闭合；Codex 复跑 911 个 Python 测试零失败，独立会商 P0-P4 全零。
- Slice-08 总体 synthetic/offline 决定为 `ACCEPT_R7_SLICE_08_SYNTHETIC_OFFLINE`，复盘与 Slice-09 分解见
  `context/medical_monitoring_r7_slice08_overall_review_and_slice09_plan_20260830.md`。下一步冻结 09A 项目级备份/恢复/导出导入合同；不得直接跳到 R8，也不得把 synthetic/offline 接受外推到真实项目/模型、生产或商业化。
- R7 Slice-09A 项目备份、恢复、导出与导入合同已冻结为 v0.1 + v0.2 + v0.3，状态
  `FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3`，权威记录为
  `context/medical_monitoring_r7_slice09a_contract_acceptance_record_20260830.md`。合同固定 deterministic `.mmbackup`、项目维护门、根级操作账本、工件闭包、原子切换/回滚、同值重放、旧包显式确认和中文进度 DTO。下一步进入 governed 09A implementation；合同接受不等于实现、Slice-09、R7 或 R8 完成。
- R7 Slice-09A 实现已完成 synthetic/offline 接受，状态
  `ACCEPT_R7_SLICE_09A_SYNTHETIC_OFFLINE`，权威记录为
  `context/medical_monitoring_r7_slice09a_implementation_acceptance_record_20260830.md`。当前门禁为聚焦 5、R7+产品 511、相邻 R1 327、compileall、哈希清单、execution audit、conference validate 与两轮同 session 独立会商 P0-P4 全零。8911/5174 保持停止，未运行真实项目/模型或修改医学写作。下一步进入 09B schema 迁移、升级与回滚合同；09A 接受不等于 Slice-09、R7 或 R8 完成。
- R7 Slice-09B 项目格式升级、兼容与恢复合同已冻结为 v0.1 + v0.2，状态
  `ACCEPT_R7_SLICE_09B_CONTRACT_V0_2`，权威记录为
  `context/medical_monitoring_r7_slice09b_contract_acceptance_record_20260830.md`。合同固定普通 constructor current-only、旧项目先只读识别、09A 同源恢复点、sibling staging、marker-last、目录级切换/恢复、三入口崩溃恢复和中文产品 DTO；同 session 两轮会商最终 P0-P4 全零。下一步进入 governed 09B implementation；合同接受不等于实现、Slice-09、R7 或 R8 完成。

### 完成证据

- 三模式状态图与输出贯通；
- 无手工端口/数据库管理；
- 失败注入和恢复录像/日志；
- 备份/迁移/回滚演练；
- 审计链验证；
- 性能基线与已知容量边界。

## 12. 阶段 R8：五个真实项目严格验收

### 目标

在全部五个真实项目上证明泛化、医学质量、数据/身份安全、视觉可用、报告输出和恢复能力，达到双角色连续两轮零开放 P0-P4。

### 项目矩阵

| 项目 | 主要验收价值 |
|---|---|
| MG-K10-SAR | Profile/Timeline/漏报/checklist/风险成熟基座无损与新增风险 |
| 芦可替尼 AD | 第二成熟基座、不同研究/药物/界面内容回归 |
| MY008-3-02 | 从原始资料完整构建、PNH/同类研究特异性 |
| MY008-3-01 | 同类项目差异、身份隔离和不可硬编码复用 |
| MY009-UC-2-01 | UC、小数据、异构 listing、not evaluable 与小样本语义 |

### 步骤

1. 建立每项目只读输入清单、来源版本、真实双快照/报告可用性。
2. 为每项目固定 ExecutionProfile、测试角色、Run 模式、输出隔离目录，以及 R0 已冻结的 task coverage matrix、gold/negative/boundary/hidden cases、缺失输入规则与 P0-P4 判定。
3. 每项目至少一次真实全量 Run；真实兼容双快照存在时追加真实增量。
4. 工程师角色验证导入、执行、进度、失败恢复、审计、备份、迁移、导出和性能。
5. 资深医学监察员角色必须用 Playwright 真实 UI 从零完成风险、中心、Subject Workspace、漏报、来源和报告任务。
6. 评价基座召回、证据支持的新增发现、基座错误/过时、误报/漏报和分级。
7. 评价中文、信息密度、图表逻辑、美学、交互路径和数据定位。
8. 每轮 prompt/任务路径不同但 coverage 等价；角色会话相互独立。
9. `not_applicable/not_evaluable/非问题` 必须有来源、规则、医学裁决和复验证据，不得通过缩小 coverage 制造通过。
10. 对缺陷执行证据复核、修复、传播分析和受影响回归；修复重置 clean streak。
11. 每项目×角色连续两轮零开放 P0-P4。
12. 汇总五项目 coverage matrix、性能 SLO、已验证边界与使用说明。

### 完成证据

- 五项目输入/输出/Run/ExecutionProfile manifest；
- 两角色两轮 Playwright/工程证据；
- 医学基座与新增风险对照；
- 零开放 P0-P4 缺陷账本；
- 性能、恢复、审计、备份和迁移报告；
- 用户可用的本地版本与回滚包；
- 不生成商业化/法规认证声明。

## 13. 测试与证据策略

### 13.1 分层验证

1. schema/属性/状态机单元测试；
2. 数据结构、mapping、diff、时间和聚合合同测试；
3. Graph 节点、checkpoint、幂等、恢复与失败注入；
4. 风险域 reference/negative/boundary cases；
5. baseline-free/hidden challenge 与 coverage completeness；
6. 跨域与跨层 projection consistency；
7. 文档输出和渲染保真；
8. Playwright audience-facing E2E；
9. 五项目医学与工程验收。

### 13.2 缺陷传播

每个缺陷绑定原因、受影响合同、消费者、修复、最小决定性测试和相邻回归。禁止以增加无关 hash/shape 微合同替代真实医学/用户证据。

### 13.3 P0-P4 clean streak

P0-P4 语义、角色任务、coverage matrix、gold/negative/boundary/hidden cases、缺失输入规则、`not_applicable/not_evaluable` 和非问题关闭证据在 R0 冻结；R8 前只能补充案例，不能改变通过语义。任何真实缺陷修复后，受影响项目/角色/模式/共享消费者的连续通过轮次重新计算。非问题关闭必须保留裁决和复验证据。

## 14. 迁移与回滚

1. 新内核使用隔离 namespace/schema/artifact 目录。
2. 旧服务先只读 adapter，再双读比对，最后才允许新写路径。
3. 旧 Profile/Timeline/漏报输出作为 reference baseline，不直接复制为新权威。
4. 每次切换有 feature gate、数据备份、投影比对和回滚点。
5. 未通过阶段 QC 时，用户入口保持旧稳定版本或明确不可用，不半切换。
6. 旧状态只在新系统通过五项目验收且用户另行批准后考虑归档；本计划不授权删除。

## 15. 用户决策点

设计批准后，普通实现机制不再逐步打断用户。仅以下重大分叉需要用户选择：

- POC 证据显示推荐框架需引入显著新服务/运维成本；
- 现有项目资料版本或基座权威存在无法从文件判断的实质冲突；
- 某功能目标与“看板为主、非待办系统”产生不可兼容分叉；
- 真实项目缺少关键来源，使医学结论路线发生实质变化；
- 需要扩大到多人/商业/受监管签名或外部系统写入。

## 16. 当前恢复点

- D1–D39、System Design v1.1 与本计划 v1.1 已批准。R1 合成/离线 POC、R2 领域内核和 R3 合成 Study Intelligence 内核均有冻结接受记录；它们不等于产品完成。
- R3 真实项目只读结构盲测已接受：5 个隔离 XLSX、289 张表；任务内 `81 passed`、冻结 R3 `339 passed`、F1–F7 全 PASS、11 个 JSON 双遍字节一致。
- 当前冻结锚点：R1 full tree `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；R2 Python `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`；R3 root-relative Python `418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d`。
- 五个真实源文件任务后 SHA/字节数未变；隔离副本 `0440`；无 cache；8911 停止；产品源码和并行医学写作子系统未改。
- R3 自然语言规则→结构化 RuleDraft/Simulation/Activation 的模型无关隔离纵切已完成并独立接受：最终 13 文件摘要 `8130880453d935fdd9490c19519a564a6257c8ebb51d2f53a18fd4382e20426c`；规则包 `247 passed`、冻结 R3 `339 passed`；三种中文范围建议和用户明确激活边界通过审查。该接受不等于 R3 总体或产品完成。
- R4 coverage matrix 与共同风险合同已冻结为 `FROZEN_R4_CONTRACT_V1`（`6bb9f73a...2705`）；R4-D01 AE/MH 与 R4-D02 CM 两个合成/离线纵切均已完成独立验收。D02 当前接受快照为：R4 `457 passed`、D01 基线 `224 passed`、共享方案合同 `39 passed`、D02 单元 `76 passed`、D02 投影 `63 passed`、D02 挑战矩阵 `55 passed`、冻结 R2 `598 passed`、冻结 R3 `339 passed`；Ruff、compileall、公共导入/对象身份和 8911 停止检查均通过。其范围不等于产品、真实项目或 R4 总体完成。
- R4-D03 输入/治疗角色/计划与实际暴露/依从性分母/允许调整/跨域处置证据/边界/输出合同已冻结为 `FROZEN_R4_D03_CONTRACT_V1`（`reviews/medical_monitoring_r4_d03_ip_slice_contract_v1_20260811.md`，初始 SHA-256 `859b9fd3...339c`）。下一安全动作是在重新核对当前文件快照后，复用已接受的 coverage、identity、lifecycle、Query/journey 公共合同实现 D03 合成纵切；不得直接跳到 D04。随后才依次扩展 PD/方案、访视、疗效、实验室/检查、多表逻辑、中心/项目聚合、多模型归并和 Query；继续保持 8911 停止、不运行五项目完整医学分析、不修改产品或医学写作子系统，不扩展系统安全设计/测试。
- 2026-08-12：R4-D03 合成/离线纵切完成独立验收。最终合同为 `FROZEN_R4_D03_CONTRACT_V1_1`，合同 SHA `fa62e229...76de9`；门禁为 AssignmentBinding 12、R4 681、R2 598、R3 339、Ruff/compileall/确定性 payload/8911 停止全部通过。最终独立 verifier session `019ff190-22aa-7f51-9de1-f5863f67ab6a` 为 `ACCEPT`。该结论不等于 R4 总体、R5 UI、真实项目或产品接受。下一安全动作是先冻结 R4-D04“入排、方案要求与潜在 PD”纵切合同，再实施合成/离线 D04；PD 仅生成待核实风险与三段式 Query，不建立提交/关闭工作流。继续保持 8911 停止、不运行真实项目、不触碰医学写作。
- 2026-08-12：R4-D04 v2 合成/离线纵切完成执行经理、医学方案语义席、工程确定性席与 Codex 四重接受。权威记录为 `context/medical_monitoring_r4_d04_implementation_acceptance_record_20260812.md`；门禁为 R4/R2/R3 `985/598/339 passed`、Ruff/compileall、83 行挑战矩阵、确定性金样、前后冻结哈希与 8911 停止。v1 的错误方案修订适用性已作为被拒绝证据保留，不得冒充接受。下一安全动作按 R4 顺序进入 D05“访视、评估、样本与时序符合性”：先冻结 coverage/owner/identity/expected-set/Journey 合同，再实施合成/离线纵切；继续不运行真实项目、不启动 8911、不触碰 R5 UI 或医学写作。
- 2026-08-12：R4-D05“访视、评估、样本与时序符合性”合同已冻结为 `FROZEN_R4_D05_CONTRACT_V1_2`。独立接受临床/算法语义 SHA 为 `7d20dadd...c4fa`；实现前文件系统检查发现 v1.1 误写 R1 实现路径，同一 Luna session 进一步以 `ACCEPT_PATH_ERRATUM` 接受 R4 路径勘误 SHA `0c7eb9d5...c265`；最终冻结 SHA 为 `23172cac...921c`。该 session 经 `REVISE → REVISE → ACCEPT → ACCEPT_PATH_ERRATUM` 关闭链式 anchor、双 cutoff、gate、bundle、活动双向 ledger、Query 入组情境、typed producer anchor、priority precedence 和实现目录边界。权威记录为 `context/medical_monitoring_r4_d05_contract_acceptance_record_20260812.md`。下一安全动作是按 116 行挑战矩阵在 `poc/medical_monitoring_ai_native_r4` 实施合成/离线 D05 纵切并完成 D01-D04/R2/R3 相邻回归；仍不运行真实项目、不启动 8911、不触碰 R5 UI、产品服务或医学写作，不扩展系统安全设计/测试。
- 2026-08-12：R4-D05 实施已完成 worker_01/02 局部接受并按用户指令暂停。当前接受对象/合同/评价器/测试 SHA 为 `00ecf4b5...e4daff`、`8e4fc830...8942e`、`bf6fdc04...47c1f`、`fcaa4489...c2569`；D05 聚焦 `247 passed`、完整 R4 `1232 passed`。已纠正稳定 bundle 身份、typed anchor 全维缺失 fail-closed、open gate 阻断医学完整性以及处置记录不得单独触发已入组/PD 措辞。权威暂停记录为 `context/medical_monitoring_r4_d05_implementation_pause_20260812.md`。worker_03/04、116 行矩阵、Journey 投影、R2/R3 相邻回归、manager 与独立总体接受均未执行；恢复时先只读复核哈希与 8911 停止，再从 worker_03 串行继续。
- 2026-08-13：R4-D06 疗效终点、评估、基线、个体趋势、Query 与 renderer-neutral Patient Journey 合成/离线纵切完成独立验收。冻结合同 SHA 为 `460aba75...c8baeb`；最终实现门禁为 raw oracle/DSL `219/219`、mutation `119`、D06 `912`、R4 `2239`、R2/R3/R1 `598/339/327 passed`，generator/Ruff/compile/export/8911/cache 均通过。原独立 verifier session `019ff7e2-f2ef-71a0-9c84-fa5e303cad24` 在六次 follow-up 后对最终不可变快照给出 `VERDICT: ACCEPT`、无 P0-P4。权威记录为 `context/medical_monitoring_r4_d06_implementation_acceptance_record_20260813.md`。下一安全动作是先冻结 R4-D07 临床安全性/实验室/检查纵切合同，再实施合成/离线 D07；不启动 8911、不运行真实项目、不触碰 R5 UI 或医学写作，不扩展系统安全设计/测试。
- 2026-08-13：R4-D07 v0.4 临床安全性、实验室与检查纵切语义合同及 144 条 synthetic/offline 验证工件完成独立冻结接受。冻结锚点为合同 `0b1f42c...0fe84`/semantic `6facbaed...b02a`、catalog `419f2a06...ee4cd`、oracle `6ef89feb...60a8`、registry `01f036f2...e9ca`；门禁为 `--check-inputs/--check-refs/--check`、4,732 reference leaves/7,605 resolved/0 failing、focused `125 passed`、确定性重建与 8911 停止。fresh Luna session `019ffb6f-02a8-7ee3-86ef-b1790585f6e5` 经 `REVISE → ACCEPT_D07_ARTIFACT_FREEZE` 关闭 case-017、引用闭合与 wrong-run 变异。权威记录为 `context/medical_monitoring_r4_d07_artifact_freeze_acceptance_record_20260813.md`。下一安全动作是在 R4 POC 内实现 D07 runtime，仍不运行真实项目、不启动 8911、不触碰产品/R5 UI 或医学写作。
- 2026-08-29：R7 Slice-07C-4 synthetic/offline 中文产品闭环与 1280/1440/1920 ego(lite) 视觉验收完成，状态 `ACCEPT_R7_SLICE_07C4_SYNTHETIC_VISUAL_LIMITED`。权威记录为 `context/medical_monitoring_r7_slice07c4_visual_acceptance_record_20260829.md`。最终门禁为医学监查前端 52 个 test 文件全通过、后端相邻 `129 passed`、夹具 `15 passed`、真实前端信封 `13/13`、Vite/compileall、独立 Gemini visual conference 和 8978/8911/5174 停止。该接受不等于真实项目/模型医学质量、R7 总体或 R8；下一安全动作是先进行 R7 大阶段复盘并冻结下一 bounded contract，不得直接运行五个真实项目或跳到 R8。
- 2026-08-30：R7 Slice-08C-3 synthetic/offline Patient Journey 变化与详情抽屉完成接受，状态 `ACCEPT_R7_SLICE_08C3_SYNTHETIC_OFFLINE`。权威记录为 `context/medical_monitoring_r7_slice08c3_implementation_acceptance_record_20260830.md`。下一安全动作是 08C-4 ego(lite) 三视口运行时/视觉专项验收；不得以离线测试替代真实 DOM、视觉或焦点接受。
- 2026-08-30：R7 Slice-08C-4 synthetic/offline 桌面运行时视觉完成受限接受，状态 `ACCEPT_R7_SLICE_08C4_SYNTHETIC_VISUAL_LIMITED`。权威记录为 `context/medical_monitoring_r7_slice08c4_visual_acceptance_record_20260830.md`。当前生产验收边界为 1920×1080 至 4K，1280/1440 仅作韧性证据；最终视觉会商 P0-P4 为 0。下一安全动作是按冻结 Slice-08 v0.2 合同启动 08D 三模式综合回归，不新增 UI、不运行真实项目/模型、不启动 8911/5174、不修改医学写作。
- 2026-08-30：R7 Slice-08D 三模式综合回归合同完成同会话独立纠偏并冻结，状态 `ACCEPT_R7_SLICE_08D_CONTRACT_V0_2`。完整合同由 `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md` 与 v0.2 附录合并构成；会商 P0-P4 为 0。下一安全动作是启动 08D governed execution；合同接受不等于实现完成。
- 2026-08-30：R7 Slice-08D synthetic/offline 综合回归实现接受，状态 `ACCEPT_R7_SLICE_08D`；随后完成 Slice-08 总体复盘并接受跨轮决定连续性 synthetic/offline 闭包。下一安全动作是 Slice-09A 项目级备份/恢复/导出导入合同冻结。
- 2026-08-30：R7 Slice-09A 项目级备份/恢复/导出导入合同经同会话三轮独立纠偏冻结为 `FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3`，最终 P0-P4 全零。下一安全动作是 governed 09A implementation；继续保持 synthetic/offline、8911/5174 停止、真实项目/模型与医学写作不触碰。
- 2026-08-30：R7 Slice-09A synthetic/offline 实现完成接受，状态 `ACCEPT_R7_SLICE_09A_SYNTHETIC_OFFLINE`；当前源码经 511 项 R7+产品、327 项 R1 相邻回归、compileall、执行审计和同会话独立会商验证，P0-P4 全零。下一安全动作是冻结 09B schema 迁移、升级与回滚合同。
- 2026-08-30：R7 Slice-09B schema 迁移、升级、兼容与恢复合同经两轮同 session 独立会商冻结为 `FROZEN_R7_SLICE_09B_SCHEMA_MIGRATION_CONTRACT_V0_2`，最终 P0-P4 全零。下一安全动作是 governed 09B implementation；先做只读 schema inspector/fixture，再做 staged-only migration、产品 DTO 与完整回归，继续保持 8911/5174、真实项目/模型、视觉页面和医学写作停止边界。
- 2026-08-30：R7 Slice-09B synthetic/offline 实现完成接受，状态 `ACCEPT_R7_SLICE_09B_SYNTHETIC_OFFLINE`。权威记录为 `context/medical_monitoring_r7_slice09b_implementation_acceptance_record_20260830.md`；最终门禁为 R7+产品 `566 passed`、R1 `327 passed`、09A adversarial `69 passed`、live-verifying 六入口、15/15 确定性矩阵、compileall、execution audit、conference validate 与同 session 三轮独立会商 P0-P4 全零。下一安全动作是先冻结 Slice-09C business audit、日志轮转/保留、容量与故障可观测性合同，再实施；09B 接受不等于真实项目、可视页面、Slice-09/R7/R8 或产品接受。
- 2026-08-30：R7 Slice-09C 业务审计核验与技术日志轮转合同经三项只读执行审计和同 session 两轮独立会商，冻结为 `FROZEN_R7_SLICE_09C_BUSINESS_AUDIT_LOG_ROTATION_CONTRACT_V0_2`，合同 SHA `834da09d...6de`，最终 `P0=P1=P2=P3=P4=0`。权威记录为 `context/medical_monitoring_r7_slice09c_contract_acceptance_record_20260830.md`。下一安全动作是按冻结合同实施 root project audit ledger、只读 verifier、09A/09B 边界/三入口恢复接线和 bounded technical logs，再做 synthetic 故障注入、确定性与相邻回归；合同接受不等于实现、09D、Slice-09/R7/R8、真实项目/模型、浏览器视觉或医学写作接受。
- 2026-08-30：R7 Slice-09C synthetic/offline 实现完成接受，状态 `ACCEPT_R7_SLICE_09C_SYNTHETIC_OFFLINE`。权威记录为 `context/medical_monitoring_r7_slice09c_implementation_acceptance_record_20260830.md`；门禁为聚焦 `37 passed`、09C 确定性 `15 passed`、全 R7 `526 passed`、R1 `327 passed`、compile、三端口停止与同 session 两轮独立会商最终 P0-P4 全零。下一步先冻结 09D 容量/性能/长运行恢复合同；09C 接受不等于真实项目/模型、视觉、Slice-09/R7/R8 或产品接受。
- 09D 及后续真实资料门禁新增反过拟合约束：研究方案、IB 与 data listing 只用于验证通用结构识别、规则解构和证据追溯，不得把特定疾病、药物、评分量表、风险模式、列名或表格布局写入业务内核。listing 解构、药物/疾病信息提取必须由医学监查子系统内置的独立 harness/LLM 在隔离上下文中完成；Codex 只负责提示框架、结构化输出合同、确定性校验、覆盖矩阵与失败边界，不代替模型生成医学解构结果。验收至少包含跨项目异构列名/表结构、未知疾病/药物、缺失或冲突资料、同义表达和对抗性格式，任何靠项目专有常量通过的实现均判定失败。
- 2026-08-31：R7 Slice-09D 性能、容量与长任务恢复合同经三项只读执行审阅和同 session 四轮独立会商冻结为 `FROZEN_ACCEPTED_R7_SLICE_09D_CONTRACT_V0_2`，SHA `9026dae9...a34f`，最终 P0-P4 全零。权威记录为 `context/medical_monitoring_r7_slice09d_contract_acceptance_record_20260831.md`。下一步先冻结 generator/oracle/measurement/fault artifacts，再实施 synthetic/offline 09D；合同接受不等于实现、Slice-09/R7/R8、真实项目/模型或产品接受。
- 2026-08-31：R7 Slice-09D 已接受恢复与有界实现检查点 `ACCEPT_R7_SLICE_09D_RECOVERY_AND_BOUNDED_IMPLEMENTATION_CHECKPOINT`。§5 为 18 个语义场景+82 个源码枚举 hooks 共 100/100 observed pass；artifact `40 passed`、R1 `327 passed`、R7 `526 passed`、聚焦 `42 passed`、执行审计与三端口停止均通过。权威记录为 `context/medical_monitoring_r7_slice09d_recovery_bounded_checkpoint_20260831.md`。§3/§4 仍开放：当前 4-cell/196-record `synthetic_fixture_io` proof 为 `inconclusive_environment_drift`，不得作为 09A–09C accepted seam 或产品容量；下一步实现 accepted-seam measurement adapter，再运行冻结 30-cell/确认/相邻边界。
- 2026-08-31：R7 Slice-09D synthetic/offline 性能、容量、确定性与恢复实现完成接受，状态 `ACCEPT_R7_SLICE_09D_SYNTHETIC_OFFLINE_CAPACITY_RECOVERY`。权威记录为 `context/medical_monitoring_r7_slice09d_implementation_acceptance_record_20260831.md`；v4 为唯一可接受 full-run，30 cells、2450 raw、225/225 determinism 全绿，artifact `56 passed`、相邻 R1+R7 `853 passed`，独立会商最终 P0-P4 全零。容量结论仅限记录工作站/source-copy/frozen corpus，不构成产品容量、SLO 或支持范围。下一动作先完成 Slice-09/R7 总体复盘并冻结 R8 source-admission/反过拟合合同；合同接受前不得读取五个真实项目或启动真实模型、浏览器、8911。
- 2026-08-31：R7 Slice-09E 本地分发与数据处置壳层完成窄范围接受，状态 `ACCEPT_R7_SLICE_09E_LOCAL_DISTRIBUTION_SYNTHETIC_OFFLINE`，权威记录为 `context/medical_monitoring_r7_slice09e_implementation_acceptance_record_20260831.md`。最终焦点 `45 passed`、Ruff/compileall、execution audit、双轮同 session 独立会商和 review gate 通过；它不是真实安装包或运行就绪证明。
- 2026-08-31：R7 十项阶段复核完成，状态 `ACCEPT_R7_SYNTHETIC_OFFLINE_ENGINEERING_BASELINE`，权威记录为 `context/medical_monitoring_r7_phase_acceptance_record_20260831.md`。本接受只关闭工程合成离线基线；离页通知、完整一键桌面应用与 System Design §15.4 真实验证转为 R8-0 硬门。R8-0 source-admission、anti-overfit、harness responsibility、real-app/notification 和真实备份迁移合同全部冻结前，不得读取五个真实项目或调用真实模型/浏览器。
- 2026-08-31：R8-0 联合准入合同经三项 governed execution、execution audit 与同 session 三轮 fresh-context 会商冻结为 `CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`，最终 SHA `19a855bf...e344e74`，权威记录为 `context/medical_monitoring_r8_gate0_contract_acceptance_record_20260831.md`。本接受只关闭合同文本，不等于 R8-0 readiness 或任何真实验证。下一安全动作仅为 G2 `RUNTIME_LAUNCH_READY_SYNTHETIC`：实现 canonical digest/manifest replay、目标 macOS synthetic source-access profile 和 synthetic runtime/一键入口；G7 前禁止读取真实项目，G8 前禁止真实项目语义进入模型，G6 前禁止产品浏览器。
- 2026-08-31：R8 G2 `RUNTIME_LAUNCH_READY_SYNTHETIC` 完成接受，状态 `ACCEPT_R8_G2_SYNTHETIC_RUNTIME`，权威记录为 `context/medical_monitoring_r8_gate2_synthetic_runtime_acceptance_record_20260831.md`。最终门禁为 `91 passed`、共享 canonical、manifest/source-access digest 桥接、独立 lifecycle replay、目标 macOS 临时 filesystem shadow-root、发布清单 16 文件、execution/conference review gate 与三端口停止；同一独立 Minimax session 第二轮确认无剩余 P0/P1。该接受不等于真实项目、真实模型、产品浏览器、医学质量或产品接受。下一安全动作只解锁 G3 通知路径决定与合同冻结；继续保持 G4-G8 顺序和全部真实边界。
- 2026-08-31：R8 G3 `NOTIFICATION_DECISION_LOCKED` 冻结并接受，权威记录为 `context/medical_monitoring_r8_gate3_notification_decision_acceptance_record_20260831.md`。合同选择 G0 Path A，冻结三元身份+终态 revision、原始终态、双通道一致、四类能力状态、点击无启动副作用、十三项 §15.4 清单和 G6 synthetic binding 门。同一 `Pi/cms-router/minimax-m3:xhigh` session 三轮终审返回 `ACCEPT_G3_CONTRACT_V0_3`，P0-P4 全零，无 fallback。仅解锁 G4 synthetic/offline 实施；G5-G8 保持关闭。
- 2026-08-31：R8 G4 synthetic/offline 通知 seam 与 System Design §15.4 十三项程序完成接受，状态 `ACCEPT_R8_G4_SYNTHETIC_15_4_PROCEDURE_READY`，权威记录为 `context/medical_monitoring_r8_gate4_synthetic_15_4_acceptance_record_20260831.md`。最终门禁为聚焦 `67 passed`、G2/R7 相邻 `196 passed`、9/9 确定性同 digest、发布 manifest 19 文件、三端口停止与医学写作边界不变；独立 `Pi/cms-router/minimax-m3:xhigh` 会商无 P0/P1，两类 review gate 均通过。该接受只证明程序准备，不等于真实通知、真实 §15.4、真实项目/模型/浏览器、G5/G6 或 R8 总体。下一安全动作仅为 G5 `PRE_REAL_INDEPENDENT_ACCEPTED` 联合门审阅；G6-G8 继续关闭。
- 2026-08-31：G5 第 1 轮独立审阅以两项 P1 推翻 G4 当前接受继承：终态 revision/跳转目标未绑定当前对象，发布清单非自包含运行闭包。当前已按最小边界完成纠偏并通过 G4 `73 passed`、相邻 `210 passed`、9/9 确定性与仅发布文件隔离副本十三项运行；状态为候选待同一独立会话复核，G6 继续锁定。
- 2026-08-31：R8 G5 同一独立会话第 2 轮确认两项 P1 均关闭，最终 `P0=P1=P2=P3=P4=0`，状态 `PRE_REAL_INDEPENDENT_ACCEPTED`。权威记录为 `context/medical_monitoring_r8_gate5_pre_real_independent_acceptance_record_20260831.md`。仅解锁 G6 synthetic `ego(lite)` 受众验收合同冻结；不解锁应用/浏览器启动、真实项目/模型/harness、真实通知/§15.4、医学质量或 R8 总体。
- 2026-08-31：R8 G6 synthetic `ego(lite)` 受众验收合同经同一 fresh reviewer 四轮纠偏独立接受，状态 `G6_CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`，权威记录为 `context/medical_monitoring_r8_gate6_contract_acceptance_record_20260831.md`。只解锁 governed G6 actual-app synthetic 实施；真实项目、真实模型/harness、G7 及医学写作继续关闭。
