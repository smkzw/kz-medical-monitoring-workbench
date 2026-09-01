# 医学监查 P9 总系统接入只读冲突审计

**审计日期：** 2026-07-29  
**审计性质：** 只读冲突审计，不实施接线、不修改产品代码、不触碰医学写作拥有的数据或文件  
**适用基线：** 当前工作区源码、当前本地运行态、P8 新风险分类合同、医学监查说明书 §39、P9 分阶段实施与 LOOP 计划  
**唯一审计产物：** `context/monitoring_p9_integration_gap_20260729.md`

## 1. 结论

P9 尚不满足总系统接入条件。当前已有可复用的医学监查模块摘要、持久化风险快照、显式未读、审批、Safety/PV 只读投影和前端路由状态能力，但存在 4 个接入阻断项：

1. **总看板仍存在第二套风险计算链。** `/dashboard` 对 RUX/MY009 项目直接调用项目适配器重新评估风险，既未投影医学监查当前快照，也与模块摘要数量不一致。
2. **P8 新风险分类合同已进入源码，但当前 API 运行态未完整加载。** 源码已有 `/risk-taxonomy` 和七类筛选参数；当前端口的 OpenAPI 与响应仍是旧合同，`/risk-taxonomy` 返回 404。
3. **共享 Source Registry 与共享方案事实尚未形成总系统级单一内容版本和消费者投影。** 当前来源登记仍以模块为身份的一部分；医学写作与医学监查分别维护方案事实，没有共享只读消费者接口。
4. **深链只完成了前端参数保存，尚未形成后端校验、替代风险重定向、跨项目清场和关闭后状态恢复的完整合同。**

未读不会因刷新或再次进入自动消失；Safety/PV 风险区域目前确为医学监查风险的只读投影，没有建立第二套 Safety 风险库。二者不是当前阻断项，但均有显示与边界细节需要在 P9 接线时补齐。

## 2. 状态口径

| 标记 | 含义 |
|---|---|
| **I 已实现** | 源码存在，当前运行态也能观察到目标行为 |
| **S 源码已有、运行态未加载** | 源码合同已存在，但当前端口仍加载旧代码或旧 OpenAPI |
| **M 缺失** | 目标合同、接口或消费者尚不存在 |
| **C 冲突** | 已有实现会形成第二数据权威、错误写入边界或相互矛盾的行为 |

## 3. 审计边界与来源

### 3.1 已读取的主合同

- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`：P9 总系统接入目标、退出条件。
- `docs/medical_monitoring_manual/医学监查子系统说明书.md`：§39 单一项目身份、共享来源、共享方案事实、风险单一权威、跨模块只读消费、深链和兼容边界。
- `context/monitoring_p8a_backend_context.md`
- `records/handoffs/monitoring_p8a_backend_handoff_20260729.md`
- `reviews/codex_monitoring-p8a-backend_review.md`
- `services/api/app/medical_monitoring_risk_taxonomy.py`：P8 风险分类合同。

### 3.2 审计限制

- 未修改、迁移或重新生成任何产品代码、数据库、运行态数据、医学写作资料或医学写作工作副本。
- 未重启 API 或前端服务，因此“运行态未加载”只作事实记录，不在本轮修复。
- 未执行会创建工作流记录的执行/会商初始化，避免违反“只创建一个报告文件”的硬约束。

### 3.3 明确未核实项

- 未重启后端，因此未核实“重启后 P8 新源码能否无错误加载”；目前只确认源码与当前 OpenAPI/响应不一致。
- 未进行新的浏览器真人点击 E2E；深链、抽屉关闭、项目切换和 Safety/PV 交互结论来自当前源码、既有测试及只读 API 观察。
- 未打开、读取或校验医学写作拥有的业务数据和文档；“当前无跨模块消费者”是基于消费者代码、路由和测试搜索，不代表对医学写作数据内容作过检查。
- 未实际实施共享来源修订、共享方案事实投影或兼容迁移，因此其数据迁移成本、历史记录碰撞数和性能只列为待实施验证项。
- 未核实生产式多用户并发下未读、审批与快照写入的事务行为；本轮只核对单机当前实现和现有测试合同。

## 4. 真实消费者与当前接口总表

| 消费者 | 当前代码、路由或组件 | 当前数据权威 | 状态 | 主要差距 |
|---|---|---|---|---|
| 医学监查模块摘要 | `medical_monitoring_router.py`：`GET /api/projects/{project_id}/modules/medical-monitoring/summary`；`medical_monitoring_summary.py` | 医学监查风险仓库、处置仓库、未读仓库 | **I** | 摘要本身可用，但尚未成为总看板唯一风险投影 |
| 医学监查当前风险快照 | `GET .../risk-snapshots/current`；`MedicalMonitoringSummaryService.current_risk_snapshot` | 持久化风险快照 | **S** | 新七筛选/排序/固定快照源码已存在，当前运行态仍为旧合同 |
| P8 风险分类目录 | `GET .../risk-taxonomy`；`medical_monitoring_risk_taxonomy.py` | `medical-monitoring-risk-taxonomy-v1` | **S** | 当前端口返回 404，说明 API 未加载新路由 |
| 项目总看板 | `main.py`：`GET /api/projects/{project_id}/dashboard`；`_rux_dashboard_summary`、`_my009_dashboard_summary`；前端 `App.jsx` 总览页 | 项目适配器即时评估 + 部分静态摘要 | **C** | 存在第二套风险；风险数量、时间戳与模块快照不一致 |
| 工作台收件箱 | `workbench_inbox.py`：`GET /workbench-inbox`；`_monitoring_risk_items` | 优先当前快照，条件不满足时回退即时评估 | **C** | 仍可能绕过持久化快照重新计算风险 |
| 医学监查风险列表 | `MedicalMonitoringRiskChecklist.jsx`、`medicalMonitoringApi.mjs` | 当前风险快照接口 | **S** | 新组件已迁移，旧静态合同测试未同步；运行态后端仍旧 |
| 未读 | `WorkbenchInboxService.inbox`、`MARK_READ`；前端风险点击和总览点击 | `WorkbenchInboxStore` 的 actor + source_version 读状态 | **I** | 不会自动消失；但顶部“未读决策”只统计“未读且需行动”，不是全部未读 |
| 审批中心 | `main.py` 审批路由；`ApprovalPage`；医学监查处置提交审批 | 审批仓库；审批中心为审批决策唯一写入者 | **I/C** | RUX/MY009 看板审批统计未按 target module 分配；前端标题硬编码 RUX |
| Safety/PV 风险入口 | `SafetyRiskProjection`；`fetchCompleteMonitoringRiskIndex(... safetyPvOnly:true)` | 医学监查当前快照中的 `safety_pv_flag` | **I** | 风险是只读投影；嵌入表格目前无交互式筛选/排序参数 |
| Safety/PV 文件审阅 | Safety review manifest/review/handoff API 和页面 | Safety 文档审阅仓库 | **I** | 与风险投影边界清楚；不得反向写医学监查风险 |
| 共享项目身份 | `project_source_manifest.py`；`GET /api/projects`、`/source-manifest`、`/module-catalog` | canonical project ID + alias | **I** | 前端项目切换未完整清空医学监查路由状态 |
| Source Registry | `source_intake.py`；`GET/POST /api/projects/{project_id}/sources` | 模块化 Source Registry JSONL/仓库 | **C/M** | 来源 ID 和 current slot 含 module；缺少共享内容修订与独立模块绑定接口 |
| 医学监查方案事实 | `monitoring_protocol_rule_repository.py`；医学监查 protocol facts 路由 | 医学监查自有事实表 | **I** | 仅模块内可用 |
| 医学写作方案事实 | `medical_writing_authoring_journey.py`、`medical_writing_study_schema.py` | 医学写作自有 StudyDefinition/版本事实 | **I** | 无总系统共享只读事实投影 |
| 医学写作消费者 | 医学写作 API、前端和 freeze 测试 | 医学写作自有仓库 | **M** | 尚无对医学监查确认事实/风险摘要的只读消费；也无反向共享事实接口 |
| 医学监查深链 | `medicalMonitoringRouteState.mjs`；`GET .../deep-link` | 前端 URL 状态 + 后端基础规范化 | **I/M** | 基础参数已实现；完整验证、替代风险重定向、跨项目清场、关闭恢复缺失 |
| 旧医学监查风险路由 | `main.py`：`GET /api/projects/{project_id}/monitoring/risks` | 可即时评估并持久化快照 | **C** | 与新只读快照接口并存，仍可成为第二条读取即计算路径 |

## 5. 关键冲突与证据

### 5.1 总看板存在第二套风险

**结论：确认存在。**

- `services/api/app/main.py`
  - `_rux_dashboard_summary`（约 2094–2159 行）逐受试者调用 `rux_monitoring_service.evaluate_subject_risks`。
  - `_my009_dashboard_summary`（约 2162–2212 行）逐受试者调用 `my009_monitoring_service.evaluate_subject_risks`。
  - `GET /api/projects/{project_id}/dashboard`（约 3149–3162 行）直接分派到上述实现。
- `frontend/src/App.jsx` 的项目总览仍消费 `/dashboard`，没有消费医学监查模块摘要。
- 只读运行态核对：
  - 医学监查模块摘要返回 **16** 个开放风险。
  - 同一项目 `/dashboard` 返回 **4** 个开放风险，并带即时生成的更新时间。

这不是展示口径差异，而是两个计算来源并存。P9 必须把总看板降为医学监查持久化快照的摘要消费者，不得在 GET 看板时重新评估。

### 5.2 收件箱仍保留风险回退计算

- `services/api/app/workbench_inbox.py` 的 `_monitoring_risk_items`（约 645–765 行）只有在快照版本完全匹配时才使用当前快照。
- 当来源、规则或引擎版本不匹配时，约 675–689 行回退到 `adapter.evaluate_subject_risks`。
- `MedicalMonitoringSummaryService` 生成 work-item 投影时调用该服务，因此“摘要绝不经过 inbox builder 计算”的边界尚不彻底。

P9 最小接线应将风险 work item 改为**仓库投影**：没有合格当前快照时返回空投影和“需要显式运行”的状态，不得在只读 GET 中计算。

### 5.3 未读不会因再次进入自动消失

**结论：当前语义正确。**

- `WorkbenchInboxService.inbox` 以 `read_versions[item_id] != source_version` 判断未读。
- 只有显式 `MARK_READ` 动作更新已读版本，并校验 `expected_source_version`。
- 前端只在用户点击具体总览项或风险项时调用已读动作；页面进入、刷新和项目再次打开均未调用。
- 连续两次只读请求得到相同 `unread_count=54`，项目再次读取不会自动清空。

需要注意两项非阻断差异：

1. AppShell 的“未读决策”是“未读且需要行动”的子集，不等于模块全部未读。
2. 总看板尚未显示医学监查模块摘要中的未读数；接线后应明确“全部未读”和“待决策未读”的标签，禁止混用。

### 5.4 Safety/PV 是否只读投影

**结论：风险部分是只读投影；文件审阅是独立写域。**

- `SafetyRiskProjection` 通过 `fetchCompleteMonitoringRiskIndex(..., { safetyPvOnly: true })` 分页读取医学监查当前风险快照。
- 过滤条件仅使用显式 `risk.safety_pv_flag === true`，没有基于标题或理由推断。
- Safety/PV 页面没有医学监查风险处置写入动作；点击风险深链回医学监查处理。
- Safety/PV 文件审阅的 review/action/handoff 写入自身文档审阅仓库，不写医学监查风险仓库。
- `safety_monitoring_collaboration_handoffs` 也是由医学监查处置和工作项派生，不另建风险。

现有细节差距：Safety/PV 内嵌风险表没有向复用 checklist 传入 `onQueryChange`，因此当前为完整读取后的静态只读表，不提供该页内筛选、排序和分页交互。这不改变单一风险权威，但应在 P9 产品验收中明确是否需要同源只读筛选。

### 5.5 当前 P8 新合同未进入运行态

源码中：

- `medical_monitoring_router.py` 已声明 `/risk-taxonomy`。
- `medical_monitoring_summary.py` 已声明 P8 七类筛选、排序和固定快照参数。
- `medical_monitoring_risk_taxonomy.py` 已声明 18 个闭合类别、明确确定性/AI 分类、Safety/PV 叠加标记，以及 CM 与 EX/EC/DA/IP 边界。

当前端口中：

- `/risk-taxonomy` 返回 404。
- OpenAPI 中 `/risk-snapshots/current` 仍只有旧参数：`category`、`severity`、`status` 等，不含完整 P8 七筛选和固定快照合同。

状态必须标记为 **S 源码已有、运行态未加载**，不得作为 P9 已实现能力验收。

## 6. 深链恢复矩阵

| 状态 | 前端 URL 编解码 | 后端 `/deep-link` | 当前恢复行为 | 差距 |
|---|---:|---:|---|---|
| `project_id` | 已支持 | 已支持 | 可进入指定项目 | 项目切换时旧模块状态未完整清空 |
| `scope` | 已支持 | 已支持 | 可恢复 trial/site/subject | 缺少后端对象关系校验 |
| `site_id` | 已支持 | 已支持 | 可恢复中心范围 | 未验证中心属于项目 |
| `subject_id` | 已支持 | 已支持 | 可恢复受试者范围 | 未验证受试者属于中心/项目 |
| `risk_instance_id` / `risk_key` | 已支持 | 已支持 | 可按实例补取焦点风险 | 已替代/已重算风险没有跳转到当前实例 |
| `tab` / `evidence_tab` | 已支持 | **缺失** | 前端可本地恢复证据页签 | 后端返回的 canonical href 丢失该状态 |
| 七类 `filter` | 已支持 | **缺失** | 前端可恢复并传给快照 API | 后端不校验枚举和值 |
| `sort` | 已支持 | **缺失** | 前端可恢复 | 后端不校验字段/方向 |
| `page` / `page_size` | 已支持 | **缺失** | 前端可恢复 | 后端不校验边界和快照总页数 |
| `risk_snapshot_id` | 已支持 | **缺失** | 前端可恢复固定快照 | 后端不验证快照存在及归属 |
| 滚动位置 | **缺失** | 不适用 | 关闭证据抽屉不恢复原滚动锚点 | 需局部保存和恢复 |
| 关闭风险抽屉 | 部分 | 不适用 | 仅关闭 UI | URL 仍保留 risk/tab；刷新后会再次打开 |
| 浏览器前进/后退 | 部分 | 不适用 | 有 `popstate` 监听 | 交互使用 `replaceState`，没有逐步历史 |

特别核对结果：

- 前端已经保存 `scope/site/subject/risk/tab/filter/sort/page/snapshot`，不是全部缺失。
- 后端只规范化基础 scope/site/subject/risk/view/batch，额外参数在当前运行态被静默丢弃。
- 前端没有先调用后端深链校验再恢复对象。
- 当前风险实例不存在时，没有用 `risk_key + 当前快照` 查找替代实例并重定向。
- 关闭风险详情不会清除 URL 中的风险焦点，也没有恢复滚动位置。
- 切换项目只更新项目/页面，医学监查筛选、页码、快照和风险焦点可能带入新项目。

## 7. Source Registry 与方案事实差距

### 7.1 Source Registry

当前 `SourceRegistryEntry` 含 `module`，来源 ID token 也含 module；`main.py` 的 current slot 使用 `(module, source_kind)`。同一物理文件被两个模块使用时，会成为两条模块化登记，而不是：

1. 一个共享 `source_content_id`；
2. 一个不可变 `source_content_revision`；
3. 多个独立 `module_binding`；
4. 各模块自己的 `parse_revision` 和确认状态。

目前也没有通用 `POST /sources/{source_id}/bindings`。`GET /sources` 不支持 module 查询，前端采用客户端过滤。P9 所要求的“来源内容修订共享、解析修订和模块绑定分离”尚未实现。

### 7.2 方案事实

- 医学监查 `monitoring_protocol_facts` 表已保存来源条目、定位、原文和修订，并支持采纳/确认。
- 医学写作有独立的 StudyDefinition、版本和事实结构。
- 未发现总系统级 `/protocol-facts?consumer=...` 或等价共享投影。
- 未发现医学监查读取医学写作已确认事实、或医学写作读取医学监查已确认事实/风险摘要的生产消费者。

因此现状是两个合法的模块内事实仓库，但缺少共享只读视图。P9 不应合并两库，更不能让任一模块直接更新另一模块记录；应新增总系统只读投影和消费者绑定。

## 8. 写入所有权

| 数据对象 | 唯一写入所有者 | 允许的其他模块行为 | 禁止行为 |
|---|---|---|---|
| canonical project ID / alias | 共享项目服务 | 只读解析和选择 | 模块自建另一套项目 ID |
| 来源二进制/内容修订 | 目标态：共享 Source Registry | 各模块建立绑定、产生自己的解析修订 | 每个模块复制成另一份“共享原件” |
| 模块来源绑定/解析修订 | 各消费模块 | 只读查看其他模块确认的共享内容 | 覆盖其他模块解析或确认状态 |
| 医学监查风险、快照、分类 | 医学监查风险仓库 | 总看板、Safety/PV、医学写作只读投影 | 看板、收件箱或 Safety/PV 重新计算/另存风险 |
| 医学监查风险处置 | 医学监查处置仓库 | 审批中心读取并回写审批结果 | Safety/PV 或总看板直接处置 |
| 未读状态 | Workbench Inbox 读状态仓库 | 显式点击后调用 `MARK_READ` | 页面进入/刷新自动标已读 |
| 审批申请 | 业务模块按项目策略创建 | 审批中心读取 | 未配置审批策略时强制创建 |
| 审批决定 | 审批中心 | 业务模块只读结果 | 业务页面伪造审批结果 |
| Safety/PV 文件审阅 | Safety/PV 文档审阅仓库 | 医学监查只读查看必要结果 | 写入医学监查风险权威 |
| 医学监查方案事实 | 医学监查事实仓库 | 共享层投影已确认事实 | 直接写医学写作 StudyDefinition |
| 医学写作章节、版本、工作副本、StudyDefinition | 医学写作子系统 | 其他模块只读消费经批准投影 | 医学监查/P9 迁移、改写或触碰其文件与数据 |

## 9. 最小接线方案

以下是后续 P9 的最小变更集合，不在本轮实施。

### 9.1 风险单一权威

1. 在 `services/api/app/main.py` 的 `/dashboard` 组装层调用 `MedicalMonitoringSummaryService.module_summary`，只投影开放风险数、严重度分布、未读数和更新时间。
2. 删除或封闭 `_rux_dashboard_summary`、`_my009_dashboard_summary` 中 GET 路径对 `evaluate_subject_risks` 的调用；项目特殊信息可保留，但风险字段必须来自模块摘要。
3. 将 `WorkbenchInboxService._monitoring_risk_items` 改为仅从持久化当前快照投影。快照不存在或版本不匹配时返回空风险工作项和“需要显式运行”的机器状态，不自动评估。
4. 将旧 `GET /monitoring/risks` 改为读取当前快照的兼容代理，或返回明确迁移状态；风险计算只允许经 `POST .../runs` 显式命令触发。
5. 前端总览继续消费 `/dashboard` 亦可，但后端 dashboard 必须已经是模块摘要投影；禁止前端拼第二套风险。

### 9.2 共享来源

1. 在现有 Source Registry 前增加兼容层：`source_content` 与 `source_content_revision` 为共享身份，module 不再参与内容 ID。
2. 新增独立 `source_module_binding`，包含 module、用途、parse revision、确认状态。
3. 保留旧 source entry ID 作为 alias，先添加可选字段，不破坏医学写作现有请求/响应。
4. 新增只读绑定查询和显式绑定命令；禁止通过读取接口自动创建绑定。

### 9.3 共享方案事实

1. 建立共享只读 DTO：`fact_id`、`project_id`、`fact_type`、`value`、`source_id`、`source_revision`、`locator`、`confirmed_by_module`、`confirmed_revision`、`consumer`。
2. 医学监查和医学写作各自提供 adapter，不迁移、不合并原表。
3. 建议接口：
   - `GET /api/v1/projects/{project_id}/protocol-facts?consumer=medical-monitoring`
   - `GET /api/v1/projects/{project_id}/protocol-facts?consumer=medical-writing`
4. 跨模块只允许读取确认版本；候选、草稿和模块内推理不自动外溢。

### 9.4 深链

1. 扩展 `medical_monitoring_router.py` 的 `/deep-link` 参数和返回 DTO，覆盖 tab、七筛选、sort、page/page_size、snapshot。
2. 服务端校验 project/site/subject/risk/snapshot 归属关系，并返回 canonical URL。
3. 若 `risk_instance_id` 已被新快照替代，按稳定 `risk_key` 返回当前实例和 redirect reason。
4. 前端进入医学监查前调用验证接口；项目切换时清空 scope 以下的 site/subject/risk/tab/filter/sort/page/snapshot 状态。
5. 关闭证据抽屉时清除 risk/tab URL 参数，保留筛选、排序、页码、快照，并恢复列表滚动锚点。

### 9.5 审批与 Safety/PV

1. RUX/MY009 总看板审批数改为按 approval target module 聚合，不得全部记入医学监查。
2. 将 `ApprovalPage` 的“RUX内部Query草稿审批”等项目硬编码改为通用医学监查处置文案。
3. 保持“只有项目策略 `internal_approval_required=true` 才创建审批”的现有边界。
4. Safety/PV 保持 `safety_pv_flag` 只读投影；如增加筛选/排序，只复用医学监查快照查询，不增加风险写入接口。

## 10. 兼容策略

1. **增量兼容：** 新接口和字段先以 optional 方式加入；不修改医学写作现有数据结构和文件。
2. **单一风险 ID：** 保留旧 `risk_key`，新增或沿用 `risk_instance_id`；被替代实例通过显式映射重定向，不复制风险。
3. **无快照不计算：** 兼容读取只能返回空、旧快照或明确状态，不能以“兼容”为由触发评估。
4. **分类兼容：** 旧 category 无法映射时进入显式 `unknown/unclassified` 迁移状态；禁止根据标题、理由或展示文本推断 P8 类别。
5. **项目 alias：** 接口入口可接受 alias，但持久化和深链 canonical URL 统一使用 canonical project ID。
6. **来源兼容：** 旧 module-scoped source entry 通过 alias 映射到共享内容修订；旧记录不原地重写。
7. **医学写作保护：** 只添加消费者投影和回归测试，不移动、不改写、不重建医学写作工作副本、章节版本、StudyDefinition 或来源文件。

## 11. 测试矩阵

### 11.1 当前已运行的只读回归

执行范围：

- `tests/test_medical_monitoring_module_contract.py`
- `tests/test_medical_monitoring_risk_taxonomy.py`
- `tests/test_frontend_monitoring_contract.py`
- `tests/test_frontend_unified_risk_workbench_contract.py`
- `tests/test_frontend_safety_projection_contract.py`
- `tests/test_project_source_manifest.py`
- `tests/test_source_manifest_dashboard_approval_overlay.py`
- `tests/test_approval_center.py`
- `tests/test_monitoring_approval_source_gate.py`
- `tests/test_safety_pv_review_workbench.py`
- `tests/test_safety_pv_sqlite_workflow.py`

结果：**85 passed，8 failed，10 warnings**。

8 个失败集中在旧的前端静态源码断言：

- 2 个仍要求映射/demo 逻辑位于 `App.jsx`。
- 4 个仍要求旧 `RiskChecklistTable` 和旧分类推断/字符串布局。
- 2 个仍要求旧 Safety 投影函数签名和单体表格。

当前实现已迁移到：

- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`

因此这些失败首先是**测试合同陈旧**，但 P8-B 和 assurance review 仍是 TODO，不能据此宣布前端已验收。

### 11.2 P9 必须新增或修订的测试

| 测试目标 | 建议定位 | 必须证明 |
|---|---|---|
| 总看板不计算风险 | 新增 `tests/test_monitoring_dashboard_projection.py` | monkeypatch 所有 `evaluate_subject_risks` 为抛错，GET dashboard 仍成功且数量等于模块摘要 |
| 收件箱不回退计算 | 新增 `tests/test_monitoring_inbox_projection_only.py` | 无匹配快照时不调用 adapter，仅返回空投影/显式状态 |
| 旧风险 GET 兼容 | 扩展模块合同测试 | GET 不计算；POST run 才可生成新快照 |
| P8 运行态合同 | 扩展 `test_medical_monitoring_module_contract.py` | `/risk-taxonomy`、七筛选、排序、snapshot 均进入 OpenAPI 和真实响应 |
| 未读不自动消失 | 新增 API + 浏览器测试 | 刷新、重新进入、切换 tab 不改变未读；点击具体项目后才改变 |
| 总未读与待决策未读 | 前端合同 + E2E | 两类数字与标签不混淆 |
| Safety/PV 只读 | 修订 `test_frontend_safety_projection_contract.py` | 只读 current snapshot、只用显式 flag、无风险写入动作 |
| 审批按 target 聚合 | 扩展 `test_source_manifest_dashboard_approval_overlay.py` | 混合审批不会全部计入医学监查 |
| 审批文案跨项目 | 前端 E2E | 非 RUX 项目无 RUX 文案 |
| 项目切换清场 | 新增路由状态单测 + Playwright | 切换项目后 site/subject/risk/tab/filter/sort/page/snapshot 全部重置 |
| 完整深链恢复 | 路由状态单测 + API + Playwright | scope/site/subject/risk/tab/filter/sort/page/snapshot 全量恢复 |
| 替代风险重定向 | API 测试 | 旧实例跳到相同 risk_key 的当前实例，并给出原因 |
| 关闭抽屉恢复 | Playwright | 清 risk/tab，保留查询状态，恢复滚动 |
| 共享来源修订 | Source Registry 单测 | 同一内容一个 revision、多个 module binding，互不覆盖 parse revision |
| 共享方案事实 | 新增 consumer projection 测试 | 双方只读确认事实，无法跨模块写入 |
| 医学写作回归 | 现有 medical-writing 全量相关测试 | P9 optional 字段/投影不改变写作请求、版本、导出和 freeze |

## 12. 禁止触碰面

P9 实施和测试必须持续禁止：

1. 修改、迁移、重写或清理医学写作拥有的数据库、JSON/JSONL、文档、语料库、工作副本、导出物和项目数据。
2. 让医学监查写入医学写作章节、版本、StudyDefinition、来源确认或文档状态。
3. 让医学写作写入医学监查风险、快照、分类、处置或未读仓库。
4. 在总看板、收件箱、Safety/PV、审批中心或 GET 兼容路由中重新计算风险。
5. 根据风险标题、理由、标签文案推断 P8 风险类别或 Safety/PV 属性。
6. 将 CM 与试验药物变更混用；EX/EC/DA/IP 等试验药物暴露、调整、中断必须保持独立数据域。
7. 在项目切换失败时静默落到其他项目，或在深链对象不存在时静默展示第一个受试者。
8. 用“兼容迁移”覆盖旧记录；所有迁移必须可追踪、可回退并保留原始 ID alias。
9. 将日志、技术状态、来源版本警告常驻到医学经理主要操作界面；只展示影响当前决策的简洁信息。

## 13. P9 接入退出门

只有以下条件全部满足，才能宣布 P9 总系统接入完成：

- [ ] 当前运行态已加载 P8 风险分类、七筛选、排序和固定快照合同。
- [ ] 总看板风险数与医学监查模块摘要来自同一持久化快照。
- [ ] 总看板、收件箱、Safety/PV 和旧 GET 路由均无法触发风险评估。
- [ ] 未读只在显式打开具体项后改变，再次进入不自动消失。
- [ ] Safety/PV 风险只读投影，无第二风险仓库。
- [ ] canonical project ID 在所有消费者一致，切换项目清空模块局部状态。
- [ ] 深链可恢复并校验 scope/site/subject/risk/tab/filter/sort/page/snapshot。
- [ ] 旧风险实例可定向到当前实例；关闭详情保留列表状态并恢复滚动。
- [ ] Source Registry 已区分共享内容修订、模块绑定和模块解析修订。
- [ ] 方案事实通过共享只读消费者投影交换，双方不能跨域写入。
- [ ] 审批数量按 target module 聚合，项目文案无 RUX 等硬编码泄漏。
- [ ] P8-B、assurance 和本报告第 11 节测试矩阵全部通过。
- [ ] 医学写作现有 API、数据、版本、文档和导出回归全部通过且无写入。

## 14. 下一安全动作

后续实施应先完成“风险单一权威 + 运行态加载 P8”这一条纵向切片，再做共享来源/方案事实与完整深链。原因是当前总看板和收件箱仍可能生成第二套风险；在该冲突解除前接入更多消费者，会扩大不一致面。

推荐实施顺序：

1. 总看板、收件箱、旧 GET 路由改为持久化快照只读投影。
2. 重启受控运行态并完成 P8 路由与 OpenAPI 验收。
3. 修订陈旧前端合同测试，完成 P8-B/assurance。
4. 实现完整深链校验、替代风险重定向和项目切换清场。
5. 引入共享来源内容修订和模块绑定兼容层。
6. 引入共享方案事实只读消费者投影。
7. 完成审批/Safety-PV/医学写作交叉回归和桌面端真实页面验收。
