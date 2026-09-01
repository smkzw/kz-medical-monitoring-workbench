# R7 Slice-09A 项目备份、恢复、导出与导入合同 v0.1

日期：2026-08-30  
状态：`DRAFT_FOR_INDEPENDENT_CONFERENCE`

## 1. 用户结果与范围

本切片把一个医学监查项目的可用状态做成可验证、可携带、可恢复的项目备份。资深医学监察员只需要选择项目、查看截止点与影响范围、确认恢复；无需认识数据库、目录、哈希、WAL、schema 或内部运行编号。

本合同仅覆盖隔离 synthetic/offline 项目工作区：

- 项目备份与导出；
- 备份包预检、导入与恢复；
- 同值重放、冲突、损坏、跨项目与中断恢复；
- 恢复后项目、运行、发布、连续性、风险、中心、受试者、Patient Journey 与来源身份对账；
- 最小中文产品 DTO 和后台进度语义。

本切片不启动 8911/5174，不运行真实项目或模型，不修改医学写作，不做复杂页面、移动端、系统安全专项、schema 迁移、日志轮转或容量压测。09B–09D 分别承接迁移、审计与容量事项。

## 2. 当前权威项目边界

项目工作区由产品路由固定为：

`<runtime-root>/medical_monitoring_r7/<canonical_project_id>/`

09A 只允许处理一个已授权的 canonical project。任何调用方传入的展示名称、原始路径、文件名或包内字段都不能改变目标项目身份。

当前可进入备份闭包的权威成员如下：

| 逻辑成员 | 当前路径 | 要求 |
|---|---|---|
| 执行配置 | `execution_profiles.sqlite3` | 必需 |
| 运行绑定 | `monitoring_run_bindings.sqlite3` | 必需 |
| 运行登记、发布与连续性 | `launch_registry.sqlite3` | 存在时纳入；无历史项目可缺省 |
| 项目风险规则 | `risk_rules.sqlite3` | 存在时纳入；无自定义规则可缺省 |
| R1 运行事实、审计与工件登记 | `runtime/monitoring_runtime.sqlite3` | 存在运行历史时必需 |
| R1 内容寻址工件 | `runtime/artifacts/*.json` | 与运行数据库登记严格闭包，不多不少 |

SQLite 的 `-wal`、`-shm`、临时文件、缓存、日志、隔离区、旧备份与 staging 不作为包成员。未知常规文件默认拒绝纳入并在内部诊断中列出，避免把并行子系统或用户文件悄然打包。

## 3. 包格式与确定性

导出物为单一 `.mmbackup` 文件，使用 Python 标准库 ZIP 容器。固定规则如下：

1. 包根仅含 `manifest.json` 与 `members/`；成员路径由 09A 常量白名单生成，不接受用户拼接。
2. 成员按 UTF-8 字节序排序；ZIP 时间戳、权限、压缩算法和 metadata 固定；同一输入状态必须生成逐字节相同的包。
3. `manifest.json` 使用 canonical JSON：UTF-8、键排序、紧凑分隔、末尾换行固定。
4. manifest 记录合同版本、canonical project id、项目显示名称快照、生成截止时间语义、模式/数据基础摘要、数据库 schema 版本、成员相对路径、大小、SHA-256、工件闭包摘要、运行/发布/连续性计数与包内容摘要。
5. 包内容摘要只覆盖 canonical manifest 的无自指字段和已排序成员字节；不得以 ZIP 自身字节产生自指摘要。
6. 公开 DTO 不返回包路径、成员路径、数据库名、表名、schema 字符串、哈希或内部运行/工件编号。

包不使用自定义加密、签名或第三方归档库；本切片用完整性、身份和原子性证明可恢复，不扩展为安全产品设计。

## 4. 一致快照

### 4.1 SQLite

每个 SQLite 成员必须通过 SQLite online backup API 写入任务专属临时目录，再执行：

- `PRAGMA quick_check` 返回 `ok`；
- 读取并记录权威 schema/version；
- 对快照文件计算大小与 SHA-256；
- 关闭所有临时连接后再封包。

禁止直接复制正在 WAL 模式使用的数据库主文件。备份创建不得关闭、替换或移动当前项目工作区。

### 4.2 工件

R1 数据库快照先冻结工件登记集合，再从当前 `runtime/artifacts` 读取对应内容寻址 JSON。每个文件名、登记 content hash 与实际字节 SHA-256 必须一致。登记缺失、文件缺失、额外受管 JSON、临时文件混入或读取期间字节变化均失败关闭，不生成“可恢复”包。

### 4.3 活跃运行

项目存在 `preparing/running/interrupted/recoverable` 等未终态运行时，允许创建一致备份，但 manifest 与中文摘要必须明确“包含未完成监查任务”；恢复后继续沿既有恢复合同处理，不能把它改写为已完成。若无法形成数据库与工件闭包，则备份失败，不降级为部分包。

## 5. 操作状态机

### 5.1 导出

`requested → collecting → snapshotting → verifying → packaging → available`

任一步失败进入 `failed`；只清理本任务临时目录，现有项目不变。相同项目状态与相同 idempotency key 重放返回原备份身份；相同 key 对应不同项目状态返回稳定冲突。

### 5.2 导入预检

`received → inspecting → verifying_members → reconciling_identity → ready_for_confirmation`

预检只读包并写任务专属 staging，不修改当前项目。必须在解压前拒绝绝对路径、`..`、反斜杠逃逸、重复路径、大小/数量超限、符号链接或非普通文件；解压后拒绝缺失/额外成员、摘要不符、损坏 SQLite、不支持的合同/schema、工件闭包不完整和目标身份不符。

### 5.3 恢复

`confirmed → staging → verifying_staged_workspace → quiescing_project → switching → verifying_live_workspace → completed`

- 恢复前必须再次验证包、staging 和当前目标项目状态未变化。
- 当前项目若有 active writer/lease，恢复返回“项目仍有监查任务正在处理，请稍后重试”，不得强杀、隐式取消或覆盖。
- 切换前将当前项目目录原子改名为任务专属 rollback 目录，再将已验证 staging 原子改名为正式项目目录；两者必须位于同一父目录/文件系统。
- live verification 失败时必须立即恢复原目录；若自动回滚也失败，返回稳定硬阻断并保留两个目录供 09C/人工核验，不能继续开放该项目。
- 完成后 rollback 目录保留到本次恢复记录完成并通过 reopen 对账；删除策略不在 09A 自动扩展。

## 6. 身份、重放与冲突

### 6.1 项目身份

默认只允许原项目恢复：包内 canonical project id 必须与路由授权项目一致。09A 不提供“复制为新项目”或跨项目导入；这些是独立产品决策，不能用改 manifest 或改文件名绕过。

### 6.2 同值重放

- 同一包、同一目标且当前 live workspace 已等同于包内容：返回 `already_current`，不再次切换、不新增业务运行/发布/连续性记录。
- 同一恢复 key、同一包、同一目标：返回原恢复结果。
- 同一 key 但包摘要或目标状态不同：稳定 `backup_operation_conflict`。

### 6.3 旧包恢复

允许用户明确确认把当前项目恢复到较早的可支持包，但预检必须展示：备份截止点、当前截止点、预计回退的运行/发布/风险规则数量，以及“当前项目将保留为可回退版本”。默认推荐动作是保留当前状态并先导出一份新备份。09A 不自动替用户选择。

## 7. 恢复后对账

恢复只有在关闭并重新打开全部权威存储后，通过以下不变量才算完成：

1. canonical project id 与授权目标一致；
2. profile/run binding/launch registry/risk rule/runtime schema 均为本版本支持值；
3. 运行、快照、数据截止点、模式、数据基础和中心范围与 manifest 一致；
4. publication、continuity plan/item 和其成员摘要与 manifest 一致；
5. R1 工件登记与实际 JSON 一一对应，字节摘要一致；
6. 公开项目/中心/受试者/风险/Journey 路由使用恢复前同一业务身份；
7. 已完成项目可重新读取结果；未完成项目保持原未完成/可恢复状态；
8. 不新增业务运行、发布、连续性事项或风险记录；只有独立的备份/恢复操作记录可增加。

manifest 计数只能用于快速定位；actual 必须从恢复后的权威存储独立重建，不能把 manifest 自报值当验证结果。

## 8. 中文产品 DTO

公开对象固定使用医学监察员语言：

### 8.1 备份摘要

- `status_label`：准备中 / 正在整理项目 / 正在核对 / 已可下载 / 未能完成；
- `project_name`；
- `backup_cutoff_label`；
- `monitoring_scope_summary`；
- `unfinished_work_notice`（无则省略）；
- `recommended_next_action`；
- `progress_percent` 与 `current_step_label`。

### 8.2 恢复预检

- `decision_label`：可恢复 / 已是当前版本 / 需确认回退 / 无法恢复；
- `backup_project_name`、`backup_cutoff_label`、`current_cutoff_label`；
- `impact_summary`；
- `items_preserved`：监查结果、风险规则、受试者历程、中心汇总等中文枚举；
- `items_rolled_back`：运行/发布/规则数量与中文含义；
- `recommended_action`；
- `confirmation_required`。

### 8.3 恢复结果

- `result_label`：恢复完成 / 项目已是此版本 / 保持原项目未变 / 需要人工处理；
- `project_name`、`restored_cutoff_label`；
- `verification_summary`；
- `next_action_label`。

所有文案简短、中文原生、面向查看与判断，不出现“正式事实”“候选信号”“只读”、技术日志或内部后端标识。

## 9. 进度与后台运行

进度百分比必须由固定细节节点计算，不允许按计时器虚增：

| 节点 | 百分比 |
|---|---:|
| 请求已接收 | 5 |
| 项目身份与状态已确认 | 12 |
| SQLite 快照完成 | 35 |
| 工件闭包完成 | 50 |
| 成员核验完成 | 65 |
| 包生成/恢复 staging 完成 | 78 |
| 最终对账完成 | 94 |
| 可下载/恢复完成 | 100 |

后台任务可在用户离开进度页后继续；重新进入显示同一操作状态。公开滚动文案只说明当前工作，例如“正在核对受试者历程和风险结果”，不播出文件名、SQL、哈希或模型日志。

## 10. 故障注入与原子性矩阵

实现必须提供显式测试钩子并由测试从源码枚举、逐一命中：

- 每个 SQLite snapshot 前后；
- 工件集合冻结、逐成员复制、工件闭包核验前后；
- manifest 生成、包生成、包最终改名前后；
- 预检解包、逐成员核验、staging workspace 核验前后；
- quiesce 检查前后；
- current→rollback、staging→live 两次改名前后；
- live reopen/identity/artifact/publication/continuity 核验前后；
- rollback 开始、rollback 完成前后；
- operation record 提交前后。

每个故障点断言：旧项目完整可读，或新项目完整可读，绝无混合/半目录；临时项可识别；同操作重放可以安全完成或返回稳定阻断。

## 11. 固定验收矩阵

至少覆盖：

1. 无运行历史、完整历史、含自定义规则、含未完成运行四类项目；
2. daily full、daily incremental、pre-lock full、post-lock-pre-CFDI fixed-total full；
3. 同状态确定性导出、同 key 重放、同 key 不同状态冲突；
4. 缺 manifest、缺成员、额外成员、成员字节篡改、SQLite 损坏、工件缺失/额外/错 hash；
5. ZIP path traversal、绝对路径、重复路径、符号链接、异常数量/大小；
6. 包项目与目标不符、schema/合同版本不支持、旧包需确认回退；
7. active writer 阻断、quiesce 后状态漂移、两次 rename 各故障点、live verify 失败与自动回滚；
8. 完成后关闭重开、公开读取、Patient Journey/风险/中心/项目身份不变；
9. `PYTHONHASHSEED={0,1,17,42,31415926}` × `normal/-O/-OO` 的包 manifest、成员顺序、摘要、公开 DTO 与稳定错误码确定性；
10. 并发同值导出、并发冲突恢复和迟到 callback 不重复切换。

expected 必须由输入侧冻结事实与独立 stdlib oracle 重建；不得从产品 DTO、manifest 自报摘要或被测数据库反算。测试不得把 fixture 名、case id 或 mutation label 送入产品决策。

## 12. 相邻回归与保护门

- 复跑 R7 run entry、runtime progress、launch registry、continuity、三模式产品路由与公开中文合同；
- 复跑直接共享的 R1 Store 工件/审计/恢复决定性测试；
- 复跑 R6 医学写作保护基线，只允许更新经当前文件系统重新计算且可解释的保护常量；
- compileall、项目/路径中性、未知内部字段不进入公开 DTO；
- 8911/5174 保持停止；真实项目目录和医学写作文件哈希不变。

09A 不重新进行 08C 浏览器视觉会商。若新增可见页面而不只是 DTO，则必须另行执行视觉实现与 ego(lite) 独立验收；本合同默认不新增复杂页面。

## 13. 完成门

满足以下全部条件才可接受 09A：

- 包闭包、确定性、一致快照、预检与原子切换全部通过；
- 故障钩子全枚举全命中，损坏/跨项目/冲突/回滚矩阵通过；
- 恢复后实际存储、工件与公开业务身份独立对账通过；
- 中文 DTO 不暴露内部实现，进度真实可恢复；
- 相邻回归与边界保护全部通过；
- 独立实现审阅列出 P0–P4 且全部为 0；
- Codex 复核当前源码、运行日志、artifact、端口和医学写作边界。

09A 接受只解锁 09B，不代表 Slice-09、R7 总体或 R8 完成。

## 14. 待独立会商挑战的关键点

1. 单一 deterministic ZIP 是否比目录包更符合用户导出/导入价值且没有引入不必要复杂度；
2. 活跃运行时是否允许一致备份，还是应统一阻断；
3. R1 工件目录的“额外 JSON”应视为闭包错误还是可忽略未登记历史；
4. 旧包恢复的默认推荐与确认语义是否足够清楚；
5. rollback 目录保留到何时，09A 是否需要最小清理策略；
6. 当前权威成员与恢复后对账是否遗漏任何 R7 项目状态面。
