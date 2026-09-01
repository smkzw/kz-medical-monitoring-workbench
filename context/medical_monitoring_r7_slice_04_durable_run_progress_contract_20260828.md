# R7 Slice-04 持久化 Run 进度事实面合同

日期：2026-08-28  
状态：`FROZEN_R7_SLICE_04_PROGRESS_CONTRACT_V0_2`  
冻结依据：两席独立会商、Codex 源码复核与本文件验收矩阵

## 1. 目标与停止线

把已绑定 ExecutionProfile 的 R7 Monitoring Run 显式连接到已接受的 R1
`ExecutionManifest`、work-unit ledger 与中文受众进度投影，形成后续后台执行和恢复所需的
唯一事实源。刷新或重新打开项目时，completed/total/percent 必须从 SQLite 权威账本重建，
API 或内存不得保存第二套进度。

本切只接受 synthetic/offline 的显式准备和只读进度。不得启动后台线程/进程、调用模型、运行
真实项目、修改前端或医学写作，也不得暴露继续/重试/取消入口。

## 2. 产品路由与权限

仅在现有项目级前缀 `/api/projects/{project_id}/modules/medical-monitoring/r7` 增加并在
catch-all 之前注册：

- `POST /runs/{run_id}/execution/prepare`：使用既有“管理运行配置”权限，显式准备本 Run 的
  execution manifest。
- `GET /runs/{run_id}/progress`：使用既有“读取 AI 运行”权限，只读返回当前范围版本的中文
  进度。

不得把两条路由挂到隔离 `/api/medical-monitoring/r7` 表面。请求体使用 `extra=forbid`；客户端
不得传入或覆盖项目、模式、全量/增量、截止点、source revision、既往快照、ExecutionProfile、
provider/model、node 或内部图身份。

## 3. 产品 Run 与 R1 身份

- 先使用 Slice-03 resolver 得到 canonical 项目；别名与 canonical URL 共用同一工作区。
- 产品 `run_id` 与 R1 `MonitoringRun.run_id` 使用同一字符串，不建立第二公共 ID 或映射表。
- 创建任何 runtime 文件前，先从既有绑定库读取 Run；不存在或 `binding.project_id` 与 canonical
  项目不一致时返回 `404 run_binding_not_found`，runtime 零 I/O。
- mode、data cutoff、execution basis、source revision、既往快照与冻结 profile digest 只来自
  既有 Run 绑定。
- R1 runtime 首次准备依次建立 synthetic POC 的 `StudyProject`、由绑定身份派生的
  `SourceRevision`、`MonitoringRun`，再设置 manifest。`SourceRevision.content_hash` 只代表本切
  synthetic 绑定身份摘要，不冒充真实 listing 内容哈希。
- R1 `create_run` 和 `add_source_revision` 的既有重放只按 ID；适配层必须在重放后逐项比较项目、
  模式、截止点、source revision、全量/增量等绑定身份。任何不一致均 fail closed，且不得调用
  `set_manifest`。

## 4. Runtime 路径与写入边界

每个 canonical 项目使用一个 runtime Store，可容纳该项目多个 Run：

```text
{runtime_dir}/medical_monitoring_r7/{canonical_project_id}/runtime/
  monitoring_runtime.sqlite3
  artifacts/
```

配置库、Run 绑定库和 R1 runtime 库物理分离；不同 canonical 项目不得共享 runtime 文件。

- import、router 构建、catch-all、未 bootstrap、未绑定、项目不匹配、请求校验失败：不得创建
  `runtime/`、runtime SQLite 或 artifacts。
- `GET progress` 在文件不存在时必须在构造 R1 `Store` 前短路，返回
  `422 execution_not_prepared`，中文为“请先准备本次监查工作范围。”
- 只有通过全部前置校验的 `POST prepare` 可创建 runtime 路径和 Store。
- R1 `Store.__init__` 会在既有库执行 schema/WAL 初始化。因此“已准备 GET 只读”精确定义为：
  不新增或修改任何项目、source revision、Run、manifest、work-unit、审计或工件业务事实；
  不把 SQLite 技术性 WAL/schema 检查的文件 mtime 误写成业务进度变化。

## 5. Prepare 请求、内部图与响应

请求必须显式提供非空 `work_units`；本切不自动生成默认清单，防止一个“开始”按钮在缺少真实
编排计划时伪造完整分母。每项仅允许：

`work_unit_id, stage, label, scope, target_ref, ordinal, mandatory, depends_on`

约束：ID 唯一；ordinal 为唯一正整数并按 `1..N` 连续；中文阶段和工作说明均含中文；依赖引用
存在、无自依赖、无环；scope/target_ref 通过既有受众投影校验；空清单拒绝。所有受众字段在
构造 Store 前预检，避免把不能展示的技术词、路径或内部标识写入账本。

产品内部合成一个不对外展示的 deterministic node：

- `node_id = r7-offline-monitor`
- `graph_version = mm-r7-slice04-offline-v1`
- `schema_version = mm-r7-slice04-schema-v1`
- `adapter_profile` 只保存绑定的 execution profile digest，不保存 provider/model/selector。

成功响应只返回：`replayed`、`scope_version_text`、`total`、`data_cutoff_text`、`mode_text`、
`basis_text`。不得返回 run/node/work-unit ID、`manifest_revision` 字段、哈希、路径或模型身份。

## 6. 当前版本幂等与范围演进

幂等比较对象是当前 manifest 的规范化定义（清除 revision/created_at 后，包含内部 node、
work units 与 profile digest）：

1. 与当前定义相同：不调用 `set_manifest`，返回当前“第 N 版监查范围”，`replayed=true`。
2. 与当前不同且从未出现：调用 R1 `set_manifest` 追加 N+1，切换当前分母；新单元全部 pending，
   历史版本完整保留。
3. 与历史非当前版本相同：本切返回 `409 superseded_scope_replay_forbidden`，不得让 R1 全局
   content-hash replay 返回旧 revision，也不得改变当前分母。是否允许重新采用历史范围留待
   Slice-05/08 在明确并发和恢复语义后设计。
4. `post_lock_pre_cfdi` 在首次成功 prepare 后固定总量；后续不同定义返回
   `409 frozen_scope_revision_forbidden`，相同当前定义仍可重放。
5. 日常与锁库前模式允许显式追加范围版本，但 Slice-04 只支持本地单进程产品。跨进程并发准备、
   worker 所有权与恢复锁在 Slice-05 闭合，不在本切虚构保证。

旧 revision 的 begin/complete 直接复用 R1 `StaleCallbackError` / `IdempotencyConflictError`；
聚焦测试从 Store 层证明拒绝，不增加产品状态推进端点。

## 7. 中文进度投影

计数、阶段和动态只可来自 R1 `structured_progress` 经 `project_audience_progress` 对账后的结果。
产品包装层从当前绑定和当前 revision 增加：

- `scope_version_text`：“第 N 版监查范围”；
- `mode_text`：“日常监查 / 锁库前监查 / 核查前监查”；
- `basis_text`：“全量 / 增量”；
- `data_cutoff_text`：当前 Run 的数据截止点。

返回还必须包含：已处理数、总数、精确百分比、中文总体状态、各阶段“已处理 x/y 项”、当前
工作与已用时间、有界中文工作动态，以及等待、进行中、已完成、复用既有结果、跳过、不适用、
受阻、未完成等互不混淆的数量。

整个响应通过字段 allowlist 和受众泄漏扫描。禁止输出内部 run/node/work-unit/attempt ID、
provider/model、adapter/harness/backend、哈希、数据库或路径、内部状态码、日志标签，亦不得出现
“正式事实”“候选信号”“只读”等研发词。错误不得把 `str(exc)` 原样透传。

manifest、work-unit ledger、审计链或投影任一对账失败均返回稳定中文错误并 fail closed，不得
输出局部计数。运行 elapsed 可随时间变化；权威计数和分母不得因刷新跳变。

## 8. 明确不在本切

- `BackgroundProgressFacade`、`prepare_synthetic_shell`、后台队列、自动推进、checkpoint、继续/
  重试/取消；
- 真实 harness preflight、MTPLX/DeepSeek 调用或模型输出；
- 真实项目、三模式端到端、carry-forward、通知、备份迁移和性能基准；
- 前端、ego(lite) 浏览器验收、受试者阶段流向看板、Patient Journey；
- 医学写作子系统和系统安全功能。

Slice-05 必须复用同一 runtime Store；后台 worker 存在后，读取切换为 R1 `audience_snapshot`
的一致快照路径。不得为 Slice-05 再造一套进度表。

## 9. 验收矩阵

1. import/router 构建无新 R7 路径；未 bootstrap、未绑定、项目不匹配、未 prepare 的 GET/POST
   均验证 runtime 零 I/O。
2. 请求额外身份字段、空清单、重复 ID/ordinal、未知依赖、环依赖、不合格中文均在创建 Store
   前拒绝。
3. 首次 prepare 创建指定 runtime 文件、revision 1 和全 pending 分母；产品响应无内部 ID。
4. 当前相同内容重放不新增 manifest/work-unit；日常/锁库前不同新内容追加版本；A→B→A
   拒绝；核查前模式首次后拒绝不同范围。
5. 既有 R1 Run/source identity 与绑定不一致时 fail closed，不调用 `set_manifest`。
6. alias/canonical 共用一份 runtime；两项目同名 run 仍物理隔离。
7. 测试直接使用 R1 Store 模拟 pending/running/passed/failed/blocked/skipped/not-applicable/reused，
   产品 GET 与权威 ledger、阶段分母和中文状态逐项一致。
8. 新 revision 后旧 revision 回调拒绝；账本/审计篡改后 GET fail closed，不返回 200 部分进度。
9. 已准备 GET 不新增任何业务事实或工件；响应全 JSON 通过内部字段/技术词/路径/哈希扫描。
10. R7 聚焦、R7 全量、相邻 R1/R6 和产品路由回归通过；R1 源码、前端、医学写作不变。
11. 8911/5174 停止；未调用模型、未运行真实项目，只使用离线 TestClient/Store。

