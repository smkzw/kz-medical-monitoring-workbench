# R7 Slice-09B 项目格式升级、兼容与恢复合同 v0.1

日期：2026-08-30  
状态：`PROPOSED_FOR_INDEPENDENT_CONFERENCE`

## 1. 本切片解决的用户问题

资深医学监察员打开较早版本的项目时，不应接触数据库、表、版本号或技术恢复步骤。系统必须先在不改动原项目的前提下判断项目是否可完整读取：可读取的旧项目允许继续查看；需要编辑时，由用户明确点击“开始升级”；升级前先生成并验证恢复点；升级失败则自动恢复原项目，绝不能要求用户删除工作区重来。

本合同只治理当前已经存在且有源码与测试证据的旧格式到当前格式的迁移，不虚构下一代业务字段或新版本。

## 2. 范围与停止线

### 2.1 本次纳入

- `runtime/monitoring_runtime.sqlite3`：R1 权威运行库及同一物理文件中的 `r7_execution_control`。
- `execution_profiles.sqlite3`：执行配置版本库。
- `monitoring_run_bindings.sqlite3`：运行与配置的不可变绑定。
- `launch_registry.sqlite3`：运行预约、结果发布和跨轮连续性。
- `risk_rules.sqlite3`：项目风险规则版本。
- 根级 `backup_operations.sqlite3`：升级操作、检查点、终态和重试依据；它不进入项目包，不随项目目录切换。
- R1 内容寻址 artifact 闭包：作为升级前备份、升级后身份与历史连续性核验的一部分，不把 JSON artifact 当成 schema 数据库。

### 2.2 本次不纳入

- 不新增 R1 v7、launch v5 或任何尚无权威 DDL 的目标格式。
- 不迁移真实项目，不调用真实模型，不启动 8911/5174。
- 不修改或调用医学写作子系统，不在 DTO 中增加医学写作字段。
- 不新增复杂页面，不重开 Patient Journey、Sankey 或其他视觉验收。
- 不承诺任意未知、更高版本或损坏项目均可恢复。

## 3. 当前目标格式与兼容矩阵

| 存储成员 | 可升级来源 | 当前目标 | 当前版本判定 | 未识别时的行为 |
|---|---|---|---|---|
| R1 runtime | `4`、`5` | `6` | `meta.schema_version` + 精确结构指纹 | 阻断，不覆盖 marker |
| execution control | 与受支持 R1 runtime 同文件的已知精确结构 | 当前 9 列结构 | 表、列、约束精确匹配 | 阻断 |
| profile store | 无业务迁移 | `mm-r7-profile-store-v1` | meta marker + 精确表/列/索引 | 阻断 |
| run binding | 无业务迁移 | `r7-slice01-run-binding-v1` | 精确表结构；非空行全部同一 schema，空表按当前结构识别 | 混合、空值或结构异常均阻断 |
| launch registry | v1、v2、v3 | v4 | meta marker + 对应来源结构 | 阻断；不得把缺 marker 的旧表当新库 |
| risk rules | 无业务迁移 | structural v1 | 当前无独立 marker，故只允许精确结构指纹 | 任一列、约束或索引不符即阻断 |

R1 marker `3` 不进入 v0.1 的可升级集合：现有 R1 constructor 虽能把它推进到 `6`，但 09A 恢复点合同不接受 `3`。本切片先保持阻断，避免在未重开 09A 合同的情况下形成无恢复点升级。未来若纳入，必须单独补齐备份、结构指纹、回填 oracle 与回归证据。

## 4. 打开旧项目的固定行为

打开项目必须先走只读检查器，使用 SQLite URI `mode=ro`，不得调用会执行 `CREATE TABLE`、`ALTER TABLE` 或更新 marker 的普通 constructor。

只读检查器按以下顺序判断：

1. 项目身份与成员集合；
2. `PRAGMA quick_check`，适用时执行 `foreign_key_check`；
3. marker、表、列、索引和约束的精确结构指纹；
4. R1 audit chain、注册 artifact 与实际字节闭包；
5. profile、binding、run、publication、continuity、risk rule 的跨库身份关联；
6. 是否存在活动 writer、处理中运行、未处置 staging/rollback 或另一升级操作。

产品决策只有四类：

| 决策 | 用户看到的状态 | 允许动作 |
|---|---|---|
| 当前格式且完整 | 正常打开 | 原有查看与编辑能力 |
| 支持升级的旧格式且完整可读 | “项目格式较旧，当前可以只读查看” | 继续查看、开始升级、稍后处理 |
| 由更高版本创建 | “当前应用无法安全打开此项目，请使用更新版本打开” | 关闭、联系支持 |
| 内容不完整、损坏、身份不一致或恢复状态不明 | “暂时无法安全打开此项目” | 关闭、联系支持 |

只读状态必须由后端写入口统一阻断；前端禁用按钮只用于解释，不是执行保证。未知状态一律映射为阻断，不得默认允许编辑。支持升级的旧项目允许检索、筛选和浏览已经核验完整的看板、风险与 Patient Journey；v0.1 不引入“部分字段缺失仍展示”的有限模式，避免监察员把不完整页面误认为全量记录。

## 5. 用户触发与产品语言

- 打开旧项目绝不自动升级。
- 主操作为“开始升级”，次操作为“先只读查看”“稍后处理”。
- 开始前固定提示：“升级前会先准备恢复点。准备完成后才会更新项目；升级期间项目暂不能编辑。”
- 页面不出现 `schema`、`migration`、SQLite、数据库名、表名、列名、SQL、事务、hash、digest、worker、锁、内部路径、内部版本号、provider/model 或原始异常。
- 错误必须给出下一步，但不得作“绝不会丢失数据”等绝对承诺。

## 6. 升级状态机

固定状态与允许转移如下：

```text
requested
  -> inspecting
  -> already_current | legacy_readonly | blocked

legacy_readonly
  -> backup_required
  -> backup_in_progress
  -> backup_verified
  -> waiting_for_project
  -> maintenance_acquired
  -> staging
  -> migrating
  -> staged_verified
  -> switching
  -> live_verifying
  -> completed

任一阶段失败
  -> retryable_failed            # live 尚未切换且仍完整
  -> rollback_in_progress
       -> rolled_back             # 原项目已独立重开核验
       -> retained_for_triage     # 无法唯一确认完整 live，阻断打开
```

`already_current`、`completed`、`rolled_back`、`blocked`、`retained_for_triage` 为明确终态；`legacy_readonly` 是可查看且等待用户决定的稳定状态。相同幂等键复用同一操作；不同幂等键在已有非终态操作时返回冲突，不创建第二次升级。

## 7. 升级前恢复点与维护门

1. 必须创建或复用同项目、同源工作区指纹且状态为 `available` 的 09A `.mmbackup`。
2. “已提交备份”“文件存在”或 manifest 自报摘要均不算恢复点完成；必须完成包发布、逐成员哈希、项目身份、SQLite、artifact 闭包和重开核验。
3. 迁移取得同一项目的 `LOCK_EX` 后重新计算 live 指纹；若与恢复点源指纹不同，停止并要求重新准备恢复点。
4. 等待项目空闲时进度不前进；默认等待 30 秒、硬上限 120 秒；不强杀、不接管当前任务。
5. 从最终源复核到 live 重开或恢复完成，全程持有维护门；正常 writer 必须继续使用 09A 的共享门。

## 8. staging-only 迁移与 marker-last

- 迁移只发生在同父目录、同文件系统的任务 staging；禁止直接在 live DB 上执行 DDL 或回填。
- staging 从已验证恢复点或同一一致点快照建立，成员集合与 artifact 闭包保持完整。
- 每个物理 SQLite 是一个事务单元；跨库 all-or-none 由完整目录 staging、原子目录切换与恢复目录保证，不宣称分布式事务。
- 固定迁移顺序：R1 runtime/control → profile 验证 → binding 验证 → launch → risk 验证 → 全项目对账。
- 每个有变更的 DB step 固定为：读取来源指纹 → `BEGIN IMMEDIATE` → DDL → 确定性回填 → 结构/数量/身份/审计/业务 oracle → 最后更新 marker → commit → 关闭重开 → 独立复核。
- 禁止 `executescript` 破坏外层显式事务；禁止用写入目标 marker 掩盖未完成迁移。
- v0.1 只实现 R1 `4/5→6` 与 launch `v1/v2/v3→v4`；profile、binding、risk 只验证为当前格式，不改业务记录。

## 9. 切换、重开与失败恢复

固定目录序列：

```text
validated live
  -> os.replace(live, rollback)
  -> fsync(parent)
  -> os.replace(staging, live)
  -> fsync(parent)
  -> close/reopen/independent verify
```

- 第一次替换前失败：live 不变，只清理本操作 staging。
- 第二次替换失败：立即尝试 `rollback→live`。
- 新 live 的项目身份、所有 DB、audit、artifact、publication、continuity 或风险规则任一复核失败：立即恢复旧 live。
- 只有旧 live 独立关闭重开并通过完整核验后，才能向用户显示“原项目仍可只读查看”。
- 恢复失败或 live/staging/rollback 无法唯一判定：保留全部证据，状态 `retained_for_triage`，阻断普通打开；不得覆盖、删除或自动猜测。
- rollback 至少保留到新 live 完成一次完整关闭重开核验；本切片不扩大为自动历史清理策略。

## 10. 崩溃恢复与重试

重启后不得只看 marker 推断成功。恢复判定必须同时读取操作账本检查点、live/staging/rollback 实际目录、每个成员实际结构与 marker、源工作区指纹和跨库语义对账。

- staging 中断：检查点与实际 step 一致时从下一 step 继续；不一致则仅清理本操作 staging，并从已验证恢复点重建。
- switching 中断：阻断普通打开，依据目录和独立核验决定完成切换或恢复旧 live。
- live_verifying 中断：新 live 全部通过则完成，否则恢复旧 live。
- rollback 中断：优先恢复唯一完整旧 live；无法唯一判定则保留现场并阻断。
- commit 成功但账本未推进时，通过实际 step digest、marker 和 oracle 识别已完成 step，不重复业务迁移。

## 11. 真实进度与中文 DTO

公开 DTO 只提供产品状态，不透传内部事件：

```json
{
  "state": "verifying",
  "phaseLabel": "检查升级结果",
  "percent": 86,
  "message": "正在检查升级结果，完成后可重新打开项目。"
}
```

固定里程碑：请求已受理 5、项目检查完成 12、恢复点完成 28、项目已空闲 35、升级副本建立 45、内容更新完成 72、升级副本核验完成 86、项目切换完成 94、最终重开核验完成 100。百分比只在对应证据完成后推进且单调不降；无法映射到确定节点时使用不确定进度，不按耗时、行数或文件大小伪造百分比。

公开状态只使用：

- `preparing` / 准备升级
- `upgrading` / 更新项目内容
- `verifying` / 检查升级结果
- `restoring` / 恢复原项目

成功结果：“项目格式已升级。请重新打开项目后继续使用。”  
恢复成功：“升级未完成，原项目仍可只读查看。可稍后重试。”  
状态不明：“升级未完成，暂时无法安全打开项目。请保留原项目并联系支持。”

公开对象不得包含 operation id、路径、数据库名、schema/storage 版本、内部 step、错误堆栈、主键、trace/request/session/token、摘要、锁、进程、线程、重试次数或原始医学记录。内部寻址仅通过既有路由上下文或不展示的 opaque token 完成。

## 12. 操作账本与故障注入

- 复用并扩展 09A 根级 operation ledger，新增独立的 `migration` 操作类型、source/target schema-set digest、plan digest、当前成员/step、恢复点 package id、源指纹、目录切换阶段与终态。
- operation ledger 不进入项目包或目录切换，因此即使项目恢复也保留失败与处置记录。
- 故障 hook 从实际源码相变枚举，不固定任意数量；至少覆盖只读预检、恢复点委托、维护门、源复核、staging 建立、每个真实 DDL/回填/oracle/marker/commit、全项目核验、两次目录替换、live 重开、恢复与账本提交的 before/after 边界。
- pre-switch 故障必须保持旧 live 完整；marker/commit 故障必须回滚该 DB step；switch/live-verify 故障必须恢复或进入保留现场阻断态；所有故障测试在固定 deadline 内终止。

## 13. 验收矩阵

### 13.1 来源与结构

- R1 `4/5/6`，以及 `3`、未知、更高、缺 marker、缺列、错误列型/约束。
- launch v1/v2/v3/v4，及未知、更高、缺 marker、部分旧表。
- profile 当前/未知/缺 marker/缺列。
- binding 空表、全当前行、混合版本、空版本、结构损坏。
- risk 精确 v1 结构、缺列、多列、索引/约束异常。
- runtime/control 精确结构与缺表、缺列、多列。

### 13.2 一致性与恢复

- 打开旧项目零写入；普通 constructor 不在只读识别路径出现。
- 只读状态的保存、删除、导入、发布及所有监查写入口均由后端拒绝。
- 恢复点失败不建立 staging、不改 live。
- 同键重试、异键冲突、迟到回调、源漂移、writer 竞争、`EXDEV`、两次 rename、重开失败、恢复失败。
- 每个实际 hook 的 pre/post 不变量。
- 迁移前后 project/run/profile/risk/publication/continuity 身份、数量、内容摘要、audit chain 与 artifact 实际字节闭包一致。
- 进度节点精确、单调、终态文案和下一打开模式一致；公开 DTO/错误文本不含禁用工程字段。

### 13.3 回归与边界

- 09A focused/adversarial 回归、R1 全量相邻回归、R7 聚焦及全量回归、`compileall`。
- `PYTHONHASHSEED={0,1,17,42,31415926}` × `normal/-O/-OO` 的确定性矩阵。
- 8911/5174 保持停止；医学写作路径哈希或版本控制状态不变；不接触五个真实项目。

## 14. 实施顺序

1. 独立会商冻结本合同，不在合同未冻结时写迁移产品代码。
2. 建立只读 schema inspector、结构指纹与 synthetic legacy fixture 生成器。
3. 建立 migration plan/ledger/state machine，并复用 09A backup、maintenance gate、workspace fingerprint、staging/switch/rollback 原语。
4. 实现 R1 `4/5→6`、launch `v1/v2/v3→v4` 的 staged-only step；current members 只做严格验证。
5. 接入最小产品 DTO 和后端只读写阻断，不新增复杂页面。
6. 运行聚焦、故障注入、确定性、全量和相邻回归。
7. 独立实现会商 P0–P4 归零后，冻结 09B synthetic/offline acceptance，再连续进入 09C。

## 15. 完成定义

只有同时满足以下条件，才能接受 Slice-09B：

- 受支持旧项目打开零写入，可完整只读查看；未知/损坏/更高版本 fail closed。
- 升级必须有同源、已验证恢复点并在 staging 中完成；live 不出现跨库混合版本。
- 所有实际 migration hook 的旧 live、marker-last、恢复和崩溃重试不变量通过。
- 成功升级或恢复后，项目、中心、受试者、风险、Patient Journey、发布与连续性身份可独立重建一致。
- 用户只看到简洁中文状态、真实进度与可执行下一步；无工程化字段。
- 09A、R1、R7 和边界回归通过，独立会商 P0–P4 全部为 0。

该完成定义只接受 synthetic/offline Slice-09B，不外推到真实项目、真实模型医学质量、R7 总体、R8、生产或商业化使用。
