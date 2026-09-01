# R1 总体验收矩阵

日期：2026-08-10  
状态：`ACCEPTED_ISOLATED_R1_POC`  
范围：隔离 synthetic/offline POC；不包含产品、真实项目、真实 provider、临床/监管或商业化就绪。

## 1. 验收原则

- 要求权威是实施计划 v1.1 的 R1 步骤 1-13 及其“完成证据”；不以旧文件中的
  范围外 `OPEN` 无限扩张 R1。
- 代码/领域状态、浏览器视图和框架决策分层取证；静态界面不冒充已接入产品运行时。
- 历史 VETO/TODO 保留。当更晚的完整验收记录取代旧模板时，必须明示 superseded，
  不能删除或把旧 TODO 当作实现缺口。

## 2. R1 步骤 1-13 证据

| 步骤 | 当前证据 | 决定性锚点 | 候选结论 |
|---|---|---|---|
| 1. Graph IR | `domain.py`/`graph.py` 定义 node/edge/condition/work unit/checkpoint/retry/reuse/skip 与发布门；集成收口有7个真实工作单元 | `test_domain_store_graph.py` 图校验、顺序、恢复、重放、重试、迟到回调；`test_integrated_closure.py` 7/7 | PASS |
| 2. 最小 schema 与正交状态 | `MonitoringRun/ExecutionManifest/NodeRun/ArtifactEnvelope/AuditEvent` 与 analysis/evidence/review/output 独立迁移 | `test_domain_store_graph.py` 状态机、coverage/publication gate、内容寻址与审计链 | PASS |
| 3. 代表性 fixture | 一项目、N/N+1 两快照、AE/MH 阳性/阴性/反证/边界；报告含正文、表格、图形、脚注 | `fixtures.py`; `synthetic_report_fixture`; `test_ae_mh_vertical_slice.py`; `test_adapters_modes_report.py` | PASS |
| 4. audience-facing 纵切 | 同一 accepted N/N+1 链路贯通来源→facts→AE/MH 待核实风险→QC→看板→共享访视轴受试者医学旅程/受试者概览/历时轨迹→三分句 Query | `integrated_closure.py`; Slice 3 与 Slice 4 真实 Chromium/WebKit 证据；三个视图共用 `SubjectTemporalSpine` | PASS（隔离 POC） |
| 5. 候选图引擎 | 框架中立参照、LangGraph 1.2.10、Agent Framework 1.13.0 分别在独立 Python 3.12 环境验证；Temporal 有条件延后 | 两候选各 113 项已接受回归；`SPIKE_EVIDENCE.md`; `DEPENDENCY_DECISION.md`; Slice 2 Codex ACCEPT | PASS |
| 6. API + harness 公共合同 | `ExecutionProfile/CapabilityRequest` 冻结 binding/version/input hash/allowed tools/isolation/timeout；共享 raw-first/candidate-only/coverage 合同；`AttemptLifecycleObserver` 把一次 durable attempt 接到 application-owned work unit | `test_capability_runtime.py` 52 项 + `test_controller.py` 11 项；API 注入 transport + 真实本地子进程；Seatbelt 文件/网络/exec/环境负向证据；独立 ACCEPT | PASS（R1 最小合同） |
| 7. 真实 manifest 进度/播报 | 分母、revision、工作单元和受众中文投影都由 SQLite 台账+审计链推导；离页/刷新/重建不产生第二套进度 | `test_authoritative_progress.py`; `test_audience_progress.py`; `test_background_progress.py`; 真实中文进度页浏览器验收 | PASS |
| 8. 故障注入 | 模型不可用、partial/truncated、中断/续跑、artifact/审计/manifest 边界、重试、重复/迟到、损坏和 revision 隔离 | `test_failure_injection.py`; `test_capability_runtime.py`; `test_controller.py`; `test_integrated_closure.py` 的 raw/candidate 篡改阻断 | PASS |
| 9. 快照接受与风险身份 | Store-derived acceptance；identity ambiguous/merge/split/reopen/superseded/not_evaluable 不静默关闭 | `test_ae_mh_vertical_slice.py`; `test_failure_injection.py` 跨项目/错版本/伪造 proof 失败关闭 | PASS |
| 10. 三类 ModeContract | 日常、锁库前、锁库后—CFDI 前的 cutoff/source revision/carry-forward/output eligibility 分离 | `modes.py`; `test_adapters_modes_report.py` 包含切换、错 cutoff/source、缺失/歧义入口失败关闭 | PASS |
| 11. ClaimCoverageLedger | 正文/表格/图形/脚注原子主张、证据/截止日、批注锚点和全报告完成门 | `report_review.py`; `test_adapters_modes_report.py` 对 absent/partial/truncated/orphan/wrong-cutoff/无理由 not-evaluable 全部阻断 | PASS |
| 12. 候选比较 | 已比较复杂度、恢复、可观测性、单机打包、许可证、存储足迹与迁移/回滚；本阶段只观察测试耗时，未建立吞吐/时延基准，不把性能写成已证明 | `DEPENDENCY_DECISION.md`; `SPIKE_EVIDENCE.md`; `R1_ADAPTER_FAILURE_MATRIX.md` | PASS（定量性能带入 R7） |
| 13. 框架/持久化 ADR | SQLite 是唯一领域权威；LangGraph 仅为下一轮隔离验证首选；Agent Framework 保留参照；自有 GraphPort 是回滚路径 | `ADR-001`; `ADR-002`; Slice 2 独立 ACCEPT | PASS |

## 3. 2026-08-10 当前复验

- R1 core：`327 passed in 11.23s`。
- AE/MH audience workbench：数据合同 `12 passed in 0.41s`，浏览器 `7 passed in 29.09s`，合计 `19 passed`。
- Patient Journey：数据合同 `10 passed in 0.04s`，浏览器 `7 passed in 21.51s`，合计 `17 passed`。
- Audience workbench browser matrix：Chromium/WebKit × 4 视口，`overall_pass=true`，`defects=[]`。
- Patient Journey browser matrix：Chromium/WebKit × 3 视口，`overall_pass=true`，`defects=[]`。
- 两个前端 `app.js` 均通过 `node --check`；Python `compileall` 通过。当前环境无 `ruff`
  可执行文件，本次未重复 Ruff；集成收口冻结验收已有 Ruff 通过证据。
- `lsof -nP -iTCP:8911 -sTCP:LISTEN` 无输出；8911 保持停止。
- Codex 重新打开实际截图后发现并纠正了会商漏检的观众语言缺陷：移除“只读”“正式事实”
  “候选信号”“漏报候选”“时间脊事件”及 `Profile/Timeline` 等内部或半中半英表达；新增源资源与
  浏览器双门，更新后的 Chromium 截图经人工复核。
- Pi/Qwen fresh-context 全量反证后 `ACCEPT`，并指出步骤 12 的性能表述过度；Grok 同会话第 3 轮
  在无工具条件下给出范围受限的 `ACCEPT`，不能替代主会场实测。Capability Runtime 另由隔离
  reviewer 对最终稳定哈希复验。
- 补充 verifier 随后发现 `AttemptLifecycleObserver` 虽在模块 `__all__` 中，却未由 `mm_r1`
  根包导出。主会场补齐这一处公共 API 并新增合同测试；capability/controller/closure 及全 core
  均重新通过，旧 reviewer SHA 因有意修复而作废，新快照重新冻结后才接受。

## 4. 阶段归属与残余边界

下列事项不被消失，但不是 R1 实施计划的完成门：

- ensemble 1/N、多模型归并与独立 adjudication binding：R4 步骤 10。
- 禁用药 PD、入排、其他 PD、IP、疗效/安全性趋势等其余风险域：R3-R5；R1 只要求
  AE/MH 端到端纵切和多域事件/风险可视化合同。
- API/provider-native 工具调用策略、真实 provider/harness 兼容、token/费用投影：产品接入
  阶段；R1 已证明不选模型、冻结 allowed-tools/identity 和 harness 合成强制边界。
- 签名 App Sandbox helper/VM、真实 OS 断电/恶意 `setsid` 逃逸、多机灾备、生产迁移：R2/R7
  的架构与产品门；当前已弃用 Seatbelt 只能称为当前 macOS synthetic POC 证据。
- 静态 UI fixture 未与 Store 产品运行时接线：R5/R7 门；R1 有同源领域生成、真实浏览器
  交互和集成运行链证据，不冒充产品接线。
- 浏览器 `qc_summary.json` 由测试过程生成，当前决定性锚点是实际 pytest 通过与 Codex 重新
  查看截图；R2 起应为 QC 摘要补 generator identity/content hash，避免把可重写摘要当独立证明。
- 框架 spike 的一次性 Python 3.12 环境已清理；需要复跑时须从 `dependency-pins.json` 重建，
  历史 113+113 结果不冒充本轮重新执行。
- 吞吐、时延、长任务和资源占用的量化基准尚未建立，按计划在 R7 步骤 10 完成。

## 5. 最终决定

R1 步骤 1-13 作为 **synthetic/offline 隔离 POC** 已接受，允许开始 R2 的隔离领域内核、审计与
迁移底座。该决定不等于产品接线、真实 provider/harness、真实项目、临床/监管或商业化就绪；
上述残余必须原样带入 R2-R7。产品源码、医学写作子系统、五个真实项目和 8911 继续冻结。
