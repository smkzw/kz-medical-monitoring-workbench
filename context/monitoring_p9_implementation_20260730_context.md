# 医学监查 P9 总系统接入实施上下文

**目标：** 医学监查成为风险、证据、处置和未读的唯一业务写入者；总看板、收件箱、
Safety/PV、审批中心和其他子系统只通过稳定投影消费，不在读取路径重新计算或复制风险。

## Source of truth

1. `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` §13。
2. `docs/medical_monitoring_manual/医学监查子系统说明书.md` §39。
3. `context/monitoring_p9_integration_gap_20260729.md`。
4. 当前源码、测试和 8920/8921 真实运行态；历史报告不能替代运行态。

## 非协商边界

- 不修改、迁移、清理或重建医学写作拥有的工作副本、章节、版本、StudyDefinition、
  语料、来源文件和数据库。
- 总看板、收件箱、Safety/PV、审批中心和兼容 GET 都不得调用风险评估。
- 无持久化快照或快照过期时返回空/过期状态并提示显式运行，不得用“兼容”作为计算理由。
- 风险类别只读 P8 封闭类别字段；Safety/PV 只读显式附加布尔标记。
- 项目切换必须清除旧项目的 site/subject/risk/tab/filter/sort/page/snapshot。
- 夜间 00:00–08:30 不新启 aishuo 路由；已在切换前运行的 pass 不强杀。

## 当前任务拆分

| 切片 | 写入范围 | 状态 | 退出条件 |
|---|---|---|---|
| P8 assurance 收尾 | assurance 三文件、main 最小接线、测试 | 完成并加载运行态 | 真实 MedicalRiskRepository 只读 reader 已注入；主会场冲突组合通过 |
| P9-A 收件箱单一权威 | `workbench_inbox.py`、其测试 | 完成并加载运行态 | 无/过期/匹配快照均不调用 evaluate；运行库只读哈希验证通过 |
| P9-B 完整深链 | monitoring summary/router、模块合同测试 | 完成并加载运行态 | 全参数 round-trip、归属校验、替代实例重定向通过 |
| P9-C 总看板与兼容 GET | `main.py`、dashboard/risk index 测试 | 完成并加载运行态 | dashboard 和旧 GET monkeypatch evaluate 后仍可读，数量来自同一快照 |
| P9-D 共享来源内容投影 | 共享 Source Registry 兼容层及测试 | 完成并加载运行态 | 内容修订、模块绑定、模块解析修订分离，公开 DTO 不暴露 hash/path/text |
| P9-E 共享方案事实投影 | 新只读 adapter/route 及测试 | 完成并加载运行态 | 双模块只读确认事实、不可跨域写入；冲突与无证据事实关闭失败 |
| P9-F 前端与跨消费者验收 | 医学监查路由状态、总看板/Safety/审批文案、测试 | 完成 | 项目清场、抽屉关闭、未读、Safety/PV、Timeline/Profile 及桌面浏览器通过 |

## 已确认事实

- P8-B 源码/旧运行态验收通过；分类不依赖文本，URL 已保存完整列表状态。
- P9 只读审计中的 8 个陈旧静态测试失败已被后续 P8-B 测试迁移覆盖；主会场最新聚焦
  回归为 monitoring/integration `78 passed`、medical-writing consumer `23 passed`，
  前端四组状态测试与生产构建通过。
- V7 已全部进入终态并完成在线备份、完整性检查和隐私最小化 checkpoint；运行态已切换到
  当前源码。V7 仅作行为基线，未激活。
- V10 真实字段映射正在产品后台运行；不得在医学 QC 前自动确认或激活。

## P9 完成证据

1. 确定性单元/接口/并发/CAS/向后兼容测试。
2. monkeypatch 所有项目适配器 `evaluate_subject_risks` 为抛错后，总看板、收件箱、
   Safety/PV 和兼容 GET 仍成功且不写风险库。
3. API 重启后 OpenAPI、真实 RUX/MG-K10/MY009 运行态与持久化快照一致。
4. 1440x900、1728x1000 桌面浏览器验证深链、项目切换、未读和 Safety/PV。
5. 医学写作共享消费者与前端/后端关键回归通过，且运行库哈希/记录证明未发生 P9 越权写入。

## 2026-07-30 LOOP 1：只读权威收敛

- 总看板的 RUX、MY009 项目特例不再遍历受试者或调用风险规则；先读取统一项目
  manifest，再仅以 `MedicalRiskRepository` 当前持久化快照覆盖医学监查风险数量、
  待处置数量、严重程度分布与最近风险。
- 旧兼容 `GET /monitoring/risks` 已降级为统一风险快照投影的只读代理。无快照时返回
  `persisted_snapshot_empty`，不再瞬时计算、不再保存快照；显式 POST run 仍是唯一
  风险计算入口。
- 风险索引回归已改为将适配器 `evaluate_subject_risks` 强制设为抛错，再验证总看板和
  兼容 GET 仍成功。主会场冲突组合：
  - risk index + module contract + inbox + risk repository：`65 passed`；
  - assurance + daily run + source projection：`35 passed`。
- 新增 `/api/projects/{project_id}/source-contents` 只读共享内容投影。内容身份、
  内容修订、模块绑定和模块解析修订彼此分离；公开响应不含内容哈希、存储键、本地路径
  或原始全文。单元/API 接线组合 `12 passed`。
- 新增 `/api/projects/{project_id}/shared-protocol-facts`。投影仅接受已有确认动作身份、
  完整来源条目、来源修订和 locator 的事实；候选、草稿、冲突、无来源、未知和已替代
  修订不跨模块。医学写作无证据的绿色字段仍返回空，dashboard 不消费医学监查运行规则。
  主会场与两侧事实拥有者冲突组合 `78 passed`，语法编译通过。
- V7 队列终态后已创建
  `runs/acceptance/monitoring_v7_cutover_checkpoint_20260730/`，5 个 SQLite 在线备份
  均通过 `PRAGMA integrity_check`，manifest SHA-256 复算一致；运行态随后完成切换。

## 2026-07-30 LOOP 2：运行态与桌面端冲突验收

- 医学监查/来源/风险/收件箱/assurance 相关全量后端回归：
  `766 passed, 18 warnings`。warnings 仅为 FastAPI 生命周期弃用提示和真实 Excel
  页眉页脚/默认样式解析提示，不改变 listing 行数据或风险合同。
- 前端医学监查 API、模型、Checklist、路由状态测试共 `179 passed`；医学监查/Safety/
  统一风险工作台/模块合同在导航深链及批次工作区互斥修复后 `56 passed`；Vite 生产构建成功
  （1903 modules）。
- 主会场发现并修复证据抽屉关闭后的内存路由残留：清除 `risk_key`、
  `risk_instance_id`、`evidence_tab` 后重新规范化，`view=evidence` 必须回落为
  `view=checklist`，同时保留范围、筛选、排序、分页和快照。
- 主会场进一步复现从 Patient Profile 点击侧栏“医学监查”后主页面已切回 Checklist、
  URL 却仍为 `view=profile` 的深链不一致；医学监查主页面现在固定序列化为
  `view=checklist`，刷新不再跳回 Profile。
- 从风险证据抽屉打开“上传新批次”时现在先关闭风险抽屉，再显示批次工作区；两个
  高优先级任务不再叠加，风险聚焦参数也会同步从 URL 清除。
- 真实运行态 API 已验证：
  - dashboard、旧 GET、收件箱和 current snapshot 读取不改变风险库哈希/大小/mtime；
  - `/source-contents` 与 `/shared-protocol-facts` 已加载；
  - P8 assurance 与 diagnostic 路由已加载；
  - RUX 共享方案事实仅投影具备确认身份和来源定位的医学写作事实，不用监查规则填充。
- 真实桌面浏览器覆盖 MY009 与 RUX：
  - 项目切换清除旧项目 site/subject/risk/tab/filter/sort/page/snapshot；
  - 点击风险自动写入“已读”，关闭证据工作区后 URL 与内存状态均回到 Checklist；
  - 原始数据、方案原文、系统规则先呈现源信息，定位信息作为次级溯源；
  - Subject Timeline 按访视轴展示 AE、试验药物、非试验用合并用药、病史和实验室泳道；
  - Patient Profile 展示疗效/安全性趋势、基线规则、PD/Query 和来源事件；
  - Safety/PV 仅投影同一风险编号、来源、状态和审计，不拥有风险处置。
- P9 退出条件已满足。P10 将针对真实增量批次、重复源记录、全流程处置/确认和重启恢复
  继续验证，不把 P9 确定性通过外推为 P10 已完成。
