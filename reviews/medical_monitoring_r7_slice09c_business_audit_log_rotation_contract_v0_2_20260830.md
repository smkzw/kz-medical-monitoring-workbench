# R7 Slice-09C 业务审计核验与技术日志轮转合同 v0.2

日期：2026-08-30  
状态：`REVISED_AFTER_CONFERENCE_ROUND_1`  
范围：synthetic/offline；不启动服务、模型或浏览器；不读取或改写真实项目；不触碰医学写作；不进入风险看板或 Patient Journey；不包含安全专项。

## 1. 用户结果与验收边界

本切片只向医学监察员回答一个问题：当前项目记录是否能够沿“来源 → 运行 → 发布 → 连续性 → 备份/恢复/升级”完整对账。

09C 核验结果 DTO 只允许三个固定结果：

- `记录完整`：只表示本次只读核验覆盖的证据链、项目身份和当前持久化状态一致，不等同于某次备份、恢复或升级成功。
- `发现异常`：存在可证明的篡改、缺失、重复、错项目、摘要不一致或状态重写。
- `需重新恢复`：操作停在可恢复边界、目录切换结果无法唯一确定，或启动后必须重新进入既有恢复协调器。

必要时可另给出操作结果文案，如“恢复完成”“保持原项目未变”“需人工处理”，但不得用它替代上述核验结果。成功终态文本可与“记录完整”同时出现，但二者不是同一事实：`记录完整` 不得作为进度终态的等价物；restore/migration 的 `progress_percent=100` 仍只属于各自已接受合同中的真实成功终态，并必须能定位到内部事件锚点。操作结果文案与里程碑继续遵循 09A v0.3/09B v0.2 的既有规定，本切片不重定义。

09C 新增核验 DTO 不返回轮询句柄，也不得暴露路径、表名、数据库名、哈希、项目/运行/事件/操作内部标识、锁、schema、进程、session、token、provider/model、prompt、原始异常或技术日志细节。既有 09A/09B 路由的 `operation_id` 仍是已接受的机器控制面不透明句柄，本切片不重命名、不把它加入任何新 09C JSON shape，也不把它渲染为用户文案。

## 2. 权威事实分层

### 2.1 项目级业务审计链

新增根级、项目目录之外的 append-only 项目审计链。它是 R7 项目级核验结论的唯一权威记录，按 canonical project scope 维护单调序号和链头；不得被项目包恢复覆盖。

它不复制医学数据，只记录不可变的业务生命周期事件、恢复边界事件和核验签注，并锚定以下从属证据：

- R1 audit chain head、来源版本和监查运行身份；
- 发布身份、状态和 R5/R6/receipt/artifact closure 摘要；
- 连续性计划、条目及来源/目标关系摘要；
- backup/restore/migration 的操作投影、包指纹、目录边界和恢复结果；
- 本次 verifier 使用的 schema/version 与最终核验结果。

R1 audit chain 继续证明 R1 业务库内部事实；发布/连续性摘要继续证明各自领域闭包；根级操作账本继续控制当前进度。它们都是从属证据或控制投影，不得成为第二个项目级核验权威。

### 2.2 技术日志

技术日志仅用于诊断容量、时延和组件结果。它不是医学事实、业务审计、恢复完成、风险判断或用户决策的证据；技术日志缺失不能推导“记录完整”，写入失败也不能自行把业务结果改成“发现异常”。

## 3. 项目审计事件合同

### 3.1 物理位置与表

- 与 09A/09B 根级操作账本共用根级 `backup_operations.sqlite3` 和事务边界；不得放入 live workspace、staging、rollback、R1 runtime、artifact 或 backup package。
- 新增 append-only `project_audit_events` 与每项目 `project_audit_heads`；历史事件禁止 UPDATE/DELETE，链头只能随合法 append 前进。
- 包内只携带导出截点、审计链头和所覆盖事件前缀的只读快照/摘要，供恢复前后核对；包内副本不是恢复后的权威链。
- 命名空间严格互斥：`project_audit_events/project_audit_heads` 只存在于根库；R1 `audit_events/audit_chain_head` 只存在于 R1 runtime SQLite。两者禁止交叉写入，09C 使用独立 `ProjectAuditLedger`，不提供可按 scope 切换目标库的通用 append helper。测试必须同时检查表来源和错误库拒绝。
- `project_audit_heads` 使用每项目一行、`canonical_project_id` 主键及 `head_seq/head_hash` CAS；event append、head CAS 与同根库操作投影更新必须在一个 `BEGIN IMMEDIATE` 事务中完成，不另创第二套链头更新规则。

### 3.2 最小字段

每个事件至少包含：schema version、project scope、project sequence、opaque event id、event class/kind、operation kind/reference、boundary token、server-verified principal snapshot hash、authorization decision hash、before/after aggregate version or digest、domain anchors、result/reason enum、UTC time、previous hash、payload hash、chain hash。

- stable canonical JSON：UTF-8、排序键、固定分隔符、禁止 NaN/Infinity、时间统一 UTC；哈希输入不包含数据库自增键或本机路径。
- event id 与 `(project scope, sequence)` 唯一；边界事件另以 `(operation reference, boundary token, event kind)` 唯一。
- 客户端 actor 不得作为主体事实；主体只来自既有服务端验证上下文。
- 不存原始医学数据、自然语言风险描述、受试者/中心/访视明文、prompt、模型输出或绝对路径。

### 3.3 事件类别

本切片最小接入及字段 allowlist：

| kind | 必需类字段 | 允许的可选锚点 |
|---|---|---|
| `boundary_intent` | operation、boundary token、expected state、before digest | package/source/plan digest、slot presence |
| `boundary_committed` | operation、boundary token、observed durable phase、after digest | marker/member/workspace digest |
| `boundary_verified` | operation、boundary token、verifier outcome、after digest | R1/publication/continuity anchors |
| `verification_started` | verifier version、snapshot fingerprint、before digest | requested domain set |
| `verification_completed` | verifier version、snapshot fingerprint、verification result | exact domain anchors、reason enum |
| `recovery_classified` | operation、observed durable phase、classification | slot/marker/root-ledger anchors |
| `recovery_completed` | operation、terminal outcome、after digest | exact domain anchors |
| `triage_retained` | operation、observed durable phase、reason enum | slot/marker anchors |
| `rollback_release_intent` | operation、verified event id、rollback digest | none |
| `rollback_evidence_released` / `rollback_evidence_release_failed` | operation、release intent id、outcome | diagnostic enum only |

字段集合由 `ProjectAuditEventKind` 和每类固定 allowlist 校验；未知 kind、缺少必需字段或多出未声明字段一律拒绝，不使用自由 `payload` 扩展。

本切片不重写 R1 历史事件，也不为既往未知状态伪造回填事件。历史项目首次核验以 `verification_started` 建立明确基线；无法证明的既往范围必须进入“发现异常”或“需重新恢复”。

## 4. 提交、崩溃与恢复

### 4.1 同一根库事务

根级操作状态转换与对应审计 append 必须在同一 SQLite transaction 中提交。审计 append、链头 CAS、规范化编码或 fsync 失败时，不得发布成功终态。

参与存储固定如下，不允许实现自行扩展：

- backup/restore/migration 的 boundary、recovery、triage、rollback-release 事件：唯一写参与者是根级 `backup_operations.sqlite3`，操作投影与项目审计事件同事务；project/R1/launch SQLite 只作为 intent 之后的文件系统或只读验证对象。
- `verification_started/completed`：唯一写参与者仍是根库；R1、launch publication 与 continuity 均只读并以摘要锚定。
- 09C 不给 publication/continuity writer 新增跨库事务，也不伪造其历史转换事件；任何锚点变化会令旧核验结论失效并要求新核验。
- 事件 kind 与允许参与存储的映射是 schema 常量；出现未声明 store 时在写入前失败。

### 4.2 跨 SQLite/文件系统边界

使用唯一 boundary token：

1. 在根库事务中追加 intent，并记录预期状态和现有证据锚点；
2. 执行 copy/rename/fsync/marker-last；staging/live/marker 及 WAL 处理严格引用 09B v0.2 §20，09C 不以缩写重新定义；
3. 独立关闭并重开 live，完成 quick_check、R1 链、发布/连续性闭包和身份核验；
4. 在根库事务中追加 committed/verified，并推进操作投影；
5. 仅在完整核验事件落盘后发布成功终态。

intent 与 verified 之间崩溃时，不得事后补写并伪称原子完成；同一 recovery coordinator 依据持久化目录/SQLite/marker 证据幂等续接或分诊。`(operation_id, boundary_token, kind)` 是幂等键；重复 intent 以唯一约束/`INSERT OR IGNORE` 返回原 intent，不追加第二条，也不重做边界，随后进入同一 coordinator 核验。无法唯一判断时为“需重新恢复”；链或身份已明确不一致时为“发现异常”。

### 4.3 启动与多入口恢复

- app startup、open project、同 key retry 复用一个 coordinator，不建立 startup-only 切换逻辑。
- startup 只扫描合同固定的 09A/09B 可恢复状态；`retryable_failed` 仍只允许显式同 key 重试，不自动扩大；`retained_for_triage` 绝不自动清理或恢复。
- 进程内 worker map 丢失不能被解释为失败或成功；以根账本、事件链和目录证据重新分类。
- 本切片保持已接受的 `operation_id` 作为既有 09A/09B 不透明轮询句柄，不进行破坏性命名切换；09C 新 DTO 不包含它，产品文案不得显示该值。

### 4.4 rollback 证据

restore 与 migration 统一规则：在 live 独立重开、R1 链、发布/连续性闭包、项目审计链和最终 `verification_completed=record_complete` 全部通过前，不得删除 rollback。先追加 `rollback_release_intent`，再清理，最后追加 `rollback_evidence_released`；清理失败追加 `rollback_evidence_release_failed`，不回退已经通过的业务核验、不无限重试，并保留证据供下一次显式清理。

## 5. 只读 verifier

固定核验顺序：

1. 根库 schema、project scope、事件序号/唯一性/previous hash/payload hash/chain hash/head；
2. canonical project identity、package/source/plan/operation 归属；
3. current operation projection 与最后边界事件；
4. live/staging/rollback、marker、SQLite reopen/quick_check；
5. R1 source/run/artifact/audit closure；必须直接调用 R1 `store.verify_audit_chain()`（或由 R1 模块公开的等价公共 verifier），不得继续复制 `project_backup.py::_verify_audit_chain` 算法；
6. publication identity、R5/R6/receipt/exact output set；
7. continuity baseline/target/items/digest closure；
8. 本次 verification event 与所有领域锚点。

映射规则：

- 全部通过且无未完成边界 → `记录完整`；
- 链篡改、删除/插入/重排/重复、跨项目、主体/授权摘要错误、领域闭包不一致 → `发现异常`；
- 合法 intent 未闭合、可恢复目录边界、活动恢复操作或 worker 丢失但证据仍可续接 → `需重新恢复`；
- rollback failure 或 live/staging/rollback 无法唯一判定，操作文案可为“需人工处理”，核验结果仍为“需重新恢复”。

verifier 不做业务写入；只有自身 verification event append 属于核验记录。每次调用都追加一对 `verification_started/completed`；相同 snapshot 得到相同 fingerprint，但仍追加新的序号事件以记录本次核验，绝不覆盖或复用旧事件。产品结果由最新完整 `verification_completed` 与其所锚定的链头共同决定；snapshot 变化必须产生不同 fingerprint。

## 6. 技术日志轮转合同

### 6.1 格式与允许字段

使用 Python stdlib `logging/json/os/fcntl/threading` 的薄 handler，每行一个 canonical JSON，且只允许固定九字段：schema、UTC timestamp、severity、component、event enum、outcome enum、duration_ms、segment_bytes、degraded。不存在 `payload` 字段；任何扩展必须先修订合同与 schema version。

禁止记录医学事实、项目/受试者/中心/访视/风险内容、路径、workspace、数据库/表名、内部 operation/run/event/session/token、provider/model、prompt、raw output、异常参数、stack trace 或任何业务审计 payload。

### 6.2 默认容量

- active：1 MiB；写入后将超限时先轮转；
- archives：`.1`–`.4`，不压缩；active + archives 最大 5 MiB；
- 单条记录最大 8 KiB，超限整条丢弃，不产生半行；
- archive 最长 7 天；active 不按年龄删除；
- active/archive/lock 用 `os.open(..., O_CREAT|O_WRONLY, 0o600)` 创建，rename 后保持模式；不得依赖事后 `chmod` 才达到 `0600`。

权威目录固定为 `<runtime_root>/.technical-logs/`，与 `.maintenance-locks/` 同为 runtime root 的受控 sibling；只允许 handler 自建的 `medical-monitoring.jsonl`、`.1`–`.4` 和单一 lock file。realpath 必须仍位于该目录，且不得位于 canonical project workspace、staging、rollback、backup package、根级业务账本、R1 runtime/artifacts 或受保护 execution/conference/runs 证据内。不得把本合同用于清理 `logs/execution`、`logs/conference`、`runs`、浏览器 QC 或已接受报告。

### 6.3 并发与失败降级

- 进程内 `RLock`；独立技术日志 lock file 使用非阻塞 `flock(LOCK_EX|LOCK_NB)`；不得复用或等待业务 maintenance gate。
- 锁竞争、open/write/flush/fsync/rename/ENOSPC/EROFS 失败不得传播至业务调用栈，不回退 stdout/stderr，不无限重试。
- 失败后进入有界 process-local degraded 状态，仅维护 dropped count/小型 ring buffer；下一次显式初始化才恢复尝试。
- 无法安全删除旧 archive 时停止继续扩张，不删除未知文件、目录或 symlink，不覆盖有效 active。
- 技术 sink 失败不改变业务核验结果；业务审计 append 失败则必须阻止成功状态，这两个失败面不得混淆。

## 7. 最小实现与禁止扩张

本切片允许新增：根级审计链、统一 verifier、09A/09B 边界接入、三入口恢复协调接线、最小中文 DTO、独立技术日志 handler 及 synthetic tests。

不允许：

- 重做 R1 audit chain、全量事件溯源平台、事件总线、分布式锁、签名/证书、Merkle 树、外部日志框架或云日志；
- 把技术日志接入风险、Journey 或医学内容；
- 修改医学写作、移动端、视觉页面、真实项目、真实 provider/model；
- 自动清理历史 execution/conference/runs、accepted evidence、staging/rollback/triage 或原始临床材料；
- 用日志存在、manifest 非空、进度 100 或测试数量替代真实核验。

## 8. 验收矩阵

### 8.1 P0/P1 业务审计与恢复

- event payload/head/sequence 篡改，删除、插入、重排、重复、截断、跨项目复制；
- 主体/授权/project scope/operation/boundary token 不一致；
- 根级状态和 event append 任一提交失败；
- intent 前后、live→rollback、staging→live、marker 前后、live verifying、terminal append 前后崩溃；
- source drift、package/member 字节变化、wrong project、wrong schema/plan；
- 进程重启 worker map 丢失，三入口同 coordinator；
- same-key replay、digest conflict、late callback、重复终态；
- rollback failure、retained-for-triage、unknown directory state；
- source→run→publication→continuity identity/digest/member closure 缺失或错配；
- 恢复不得新增业务 run/publication/continuity/risk，package/staging/rollback 不得被当成新 source。

### 8.2 P1/P2 技术日志

- 1 MiB 前一字节/等于/超过边界、8 KiB 超长记录、4 archive/7 天边界；
- 两进程并发写/轮转、锁竞争、重启扫描；
- open/write/flush/fsync/rename/ENOSPC/EROFS 与无法删除旧 archive；
- unknown file/directory/symlink 不被清理；staging/rollback/ledger/artifact/evidence 不被触碰；
- 输入含路径、token、prompt、raw output、模型/医疗样例时输出不得泄漏；
- ledger 成功而 sink 失败时不误报业务异常；业务证据失败时不由日志猜测。

### 8.3 确定性与相邻回归

- 固定时钟、固定事件序列、`PYTHONHASHSEED={0,1,17,42,31415926}` × normal/`-O`/`-OO`，链字节、verifier fingerprint 和 JSONL 字节稳定；
- TZ、locale、umask 变化不改变规范化内容，权限仍为 0600；测试至少覆盖 `umask=0o077` 与 `umask=0o022`；
- R1、09A、09B、product router、publication/continuity 相邻回归；
- compileall；8911/5174/8984 保持停止。

## 9. 完成定义

只有以下条件全部满足，才可接受 Slice-09C synthetic/offline：

1. 项目审计链、只读 verifier、边界接入、恢复协调和日志轮转均有源代码与测试；
2. 中文 DTO 只出现允许语义且禁止字段/文本扫描通过；
3. 故障注入、跨进程、确定性与相邻回归通过；
4. 独立会商所有 P0–P4 清零；
5. Codex 重开实际文件、复跑决定性命令并确认端口停止；
6. 形成 contract、execution、conference、acceptance record 与 manifest；
7. 明确不外推到真实项目、真实模型、浏览器视觉、性能容量 Slice-09D、R7 总体或 R8。
