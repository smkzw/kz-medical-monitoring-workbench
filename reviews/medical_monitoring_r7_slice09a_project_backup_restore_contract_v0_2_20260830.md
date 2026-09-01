# R7 Slice-09A 项目备份、恢复、导出与导入合同 v0.2 纠偏附录

日期：2026-08-30  
状态：`DRAFT_FOR_SAME_SESSION_REVIEW`

本附录与 v0.1 合并构成完整合同；冲突时本附录优先。它吸收独立会商中经当前源码核实成立的问题，并纠正不适用于当前实现的建议。09A 仍只做合同冻结，不实施产品代码。

## 15. 项目维护门与一致点

v0.1 中“active writer/lease”统一替换为可实施的项目维护门：

1. 09A 新增根级、不可随项目目录切换的 `backup_operations.sqlite3`。它位于 `medical_monitoring_r7/` 根目录，只保存备份/恢复操作、幂等键、包身份、进度、维护门和 rollback 指针；它不是项目业务数据，不进入 `.mmbackup`。
2. 所有可能修改项目工作区的 09A 入口、现有产品写入口和后台恢复写入口，在写入前必须取得同一 canonical project id 的共享维护许可。备份/恢复的一致点取得独占维护许可。未接入维护门的写入口存在时，09A 不得宣称原子恢复完成。
3. 独占许可只在现有单次写事务结束后取得，不强杀、不取消、不接管任务；许可期间禁止新写事务开始。
4. 备份可在未完成运行存在时进行：先取得独占许可，关闭本操作持有的工作区连接，使用 SQLite online backup API 和冻结的工件闭包形成同一一致点，然后释放许可；运行状态仍按原值记录为未完成。等待许可超时返回“项目正在处理数据，请稍后重试”，不生成部分包。
5. 恢复必须同时满足：独占许可已取得；launch state 不属于 `waiting_start/running/stopping`；R1 恢复报告不存在运行中的 node attempt；当前项目状态在预检后未变化。`interrupted_resumable` 可恢复，因为它没有活动写者；恢复后仍保持可继续状态。
6. 独占许可获取、状态核验、SQLite `BEGIN IMMEDIATE` 探测、关闭本操作连接和两次目录切换之间不得释放许可。`BEGIN IMMEDIATE; ROLLBACK` 是数据库写事务空闲的补充证据，不能替代所有写入口都遵守维护门。
7. 测试必须以两个进程验证：进程 A 持有共享写许可及 SQLite 写事务时，进程 B 的恢复只能等待或返回稳定阻断；绝不能发生目录切换。许可释放后，同一恢复操作可继续且只切换一次。

## 16. 备份包与确定性修正

### 16.1 ZIP 固定字段

继续采用单一 `.mmbackup` ZIP，因为它符合用户导出、搬运和导入的单文件心智。容器只用 Python 标准库并固定：

- `ZIP_STORED`；
- 所有条目 `date_time=(1980, 1, 1, 0, 0, 0)`；
- `create_system=3`、`create_version=20`、`extract_version=20`；
- `extra=b""`、`comment=b""`；
- 普通文件 `external_attr=(0o100644 << 16)`；
- UTF-8 路径仅来自固定 ASCII 白名单；
- `manifest.json` 第一项，随后 `members/` 下成员按相对路径 UTF-8 字节序插入；central directory 保持相同插入顺序；
- 不写目录条目，不继承宿主 umask、权限、时区或文件 mtime。

相同冻结状态在不同时区、locale、umask、PID、`PYTHONHASHSEED` 与 `-O/-OO` 下必须生成逐字节相同 ZIP。生成时间不进入决定包字节的字段；用户可见“备份时间”来自根级操作记录，不参与包身份。

### 16.2 包身份

`package_id = sha256(final_zip_bytes)`。最终 ZIP 写入任务临时文件，fsync、关闭、重新读取并验证后才计算 package id，再以原子 `os.replace` 发布为可下载文件。manifest 内不自报 package id；内容摘要继续按 v0.1 的无自指 canonical 规则记录。

## 17. 工件闭包与非权威文件

R1 工件闭包严格定义为当前 store 中 `artifacts.content_hash` 与 `listing_snapshots.content_hash` 的并集：

1. 在独占维护许可内冻结集合并复制 `<hash>.json`；
2. 文件名、登记 hash、实际 SHA-256 与复制后 SHA-256 四者一致；
3. `Store.find_orphan_artifacts()` 非空时备份失败，返回中文“项目中有未完成清理的数据，请先核对后再备份”；09A 不自动清理、不把 orphan 纳入包，也不提供 `include_known_orphans` 旁路；
4. `*.tmp`、缺失文件、额外未登记 `*.json` 或复制期间变化均为闭包失败。

项目根已知无业务意义的 `.DS_Store`、`._*` 与 `Thumbs.db` 可忽略且不入包；其他未知普通文件、目录或符号链接仍失败关闭。不得因备份自动删除或移动任何文件。

## 18. staging、切换、回滚与清理边界

1. staging、live、rollback 必须由 09A 在 `medical_monitoring_r7/` 同一根目录下创建和验证；开始前比较 `st_dev`，并在 `os.replace` 返回 `EXDEV` 时稳定失败关闭。
2. rollback 名称由根级操作 id 派生并要求不存在；存在同名目录表示未完成操作，先进入恢复判定，不通过递增编号掩盖残留。
3. 切换顺序固定为 `live → rollback`、`staging → live`。每次 `os.replace` 后 fsync 根目录；第二步失败立即 `rollback → live`。任何自动回滚失败都保留 live/staging/rollback 和根级操作状态 `retained_for_triage`，项目读取返回“项目恢复尚未完成，请稍后核对”。
4. 恢复完成后保留本次 rollback，直到新 live 至少关闭重开一次并通过第 20 节全部对账。09A 不删除该 rollback；后续受控清理由 09C/09D 定义。新恢复发现已有未处置 rollback 时阻断，避免无界堆积和误删可回退版本。
5. 无原 live 的首次导入只执行 `staging → live`，失败时目标项目仍不存在；不得创建半工作区。

## 19. 幂等、重放与旧包恢复

根级操作账本固定映射：

`(operation_kind, idempotency_key, canonical_project_id) → package_id, source_workspace_fingerprint, terminal_outcome`

- 同 key、同项目、同 package/source fingerprint 返回原操作；
- 同 key 但 package 或 source fingerprint 不同，返回 `backup_operation_conflict`；
- 同 package、同项目且 live 经第 20 节独立对账已等同包状态，返回 `already_current`，不切换、不新增业务数据；
- 迟到 callback 只能补全原操作，不能创建第二次切换或覆盖不同 package；
- 包内 canonical project id 必须与经产品路由解析后的 canonical id **逐字节精确相等**；不 trim、不 casefold、不从展示名重新规范化。空值、控制字符或不同项目稳定拒绝。

旧包恢复继续允许显式确认。预检默认推荐“保留当前状态，并先导出一份当前备份”；必须显示旧包截止点、当前截止点、将回退的运行/发布/规则数量和“当前项目会保留为可回退版本”。恢复后的业务身份应与**包内一致点**一致，而不是与恢复前较新 live 状态一致；较新 live 只在 rollback 中保留。

## 20. 恢复后独立对账

manifest 是经包摘要保护的期望声明，但不是独立 oracle。恢复成功必须同时满足：

1. 重新关闭并打开每个 SQLite，执行 `PRAGMA quick_check`，从各数据库实际 meta/schema 读取并确认在支持集合内；
2. 从恢复后的数据库与工件重新计算项目、运行、快照、截止点、模式、数据基础、中心范围、发布、连续性 plan/item、风险规则和工件集合；与 hash-bound manifest 的期望逐项比较；
3. 测试 expected 由独立 stdlib oracle 从输入侧冻结 fixture 重建，禁止调用被测 manifest/DTO/helper 反算；故意篡改 manifest 计数、成员摘要或语义值均失败；
4. `Store.verify_audit_chain()` 为真，`Store.find_orphan_artifacts()` 为空，每个登记工件和 listing snapshot 文件存在且实际 SHA-256 一致；
5. 从恢复后存储独立生成公开项目/中心/受试者/风险/Journey 路由身份与摘要；它们应与包内一致点的冻结公开投影相同；
6. 已完成运行保持完成且内容寻址结果相同；未完成运行保持原未完成/可恢复状态；
7. live 业务数据库不得因备份/恢复新增运行、发布、连续性或风险行。备份/恢复事件只写根级 `backup_operations.sqlite3`，不得假设当前不存在的 `r7_continuity_audit` 表；
8. 对账失败立即执行第 18 节回滚，不能把 manifest 自报“通过”当作恢复完成。

## 21. 中文公开面与固定路由

09A 最小公开面固定为：

- `POST /api/projects/{project_id}/modules/medical-monitoring/r7/backups`
- `GET /api/projects/{project_id}/modules/medical-monitoring/r7/backups/{operation_id}`
- `POST /api/projects/{project_id}/modules/medical-monitoring/r7/restores/preflight`
- `POST /api/projects/{project_id}/modules/medical-monitoring/r7/restores`
- `GET /api/projects/{project_id}/modules/medical-monitoring/r7/restores/{operation_id}`

所有状态从根级操作账本的同一记录投影；重新进入页面不重启操作。终态 `available/failed/already_current/completed/kept_current/retained_for_triage` 返回稳定的中文标签、百分比和下一步。

恢复预检必须包含 `unfinished_work_notice`；包中存在未完成运行时显示“此备份包含未完成的监查任务，恢复后仍需继续处理”，并要求显式确认。内部状态、路由、路径、数据库名、schema、hash、operation id 和技术错误不进入用户文案。

固定进度节点保留 v0.1 百分比，但恢复路径中 35/50/65 分别解释为“项目副本已准备 / 监查结果已核对 / 恢复前检查已完成”，避免向用户展示 SQLite/工件术语。失败终态保留最后完成节点的百分比，不伪装为 100%。

## 22. 故障钩子与确定性补充

每个钩子命名为 `<phase>.<step>.before|after`。测试从生产源码枚举并逐一命中，至少断言：

- 操作状态属于 `cleaned_up/retained_for_triage/rollback_in_progress/completed` 之一；
- live 要么保持旧版本完整可读，要么为新版本完整可读；不存在混合成员；
- staging/rollback 的保留或清理与操作状态一致；
- 重放可安全完成或稳定阻断；
- 测试在固定 deadline 内终止，无无限等待。

确定性网格增加 `TZ ∈ {UTC,Asia/Shanghai}`、`LC_ALL=C.UTF-8`、`umask ∈ {022,077}`、冻结时钟；逐字节比较 ZIP、manifest、每个成员、公开 DTO 与稳定错误码。不得把 `SOURCE_DATE_EPOCH=0` 直接当 ZIP 1980 时间戳。

额外固定场景：双进程 writer/restore 竞争、预检后状态漂移、残留 rollback、无 live 首次导入、manifest 语义篡改、orphan 工件、跨文件系统/EXDEV、两次 replace 各故障点、自动回滚失败、终态进度重读和迟到 callback。

## 23. 六项决策冻结

1. 使用 deterministic single-file ZIP，不采用目录包。
2. 允许未完成运行的一致点备份；活动写入期间恢复阻断，`interrupted_resumable` 在无 writer 时可恢复。
3. R1 orphan/额外受管 JSON 为硬闭包失败，不静默忽略。
4. 旧包恢复必须显式确认，默认推荐先保留并备份当前状态。
5. rollback 至少保留到新 live 重开并完成全部对账；09A 不自动删除，已有未处置 rollback 时阻断新恢复。
6. v0.1 列出的六类物理成员完整；launch registry 内的 launch/publication/continuity plan/item 是恢复后逻辑对账面。当前源码不存在 `r7_continuity_audit`，不得把它写入合同或实现假设。

## 24. 纠偏后的完成门

v0.1 第 13 节继续有效，并增加：所有产品写入口遵守维护门；双进程竞争与旧包回退语义通过；根级操作账本不随项目切换；ZIP 跨环境逐字节确定；没有把当前源码不存在的表或 API 当作实现前提。

通过本附录仍只允许进入 09A governed implementation；不得外推为 09A 实现完成、Slice-09 完成或 R7 总体完成。
