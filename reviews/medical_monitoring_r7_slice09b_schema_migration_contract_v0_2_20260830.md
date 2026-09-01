# R7 Slice-09B 项目格式升级、兼容与恢复合同 v0.2 冻结补充

日期：2026-08-30  
状态：`FROZEN_R7_SLICE_09B_SCHEMA_MIGRATION_CONTRACT_V0_2`

本补充与 v0.1 合并构成 Slice-09B 实施合同；冲突时 v0.2 优先。它吸收第一次独立会商的全部 P0 和关键 P1，并纠正其中关于 staging 位置的一处不安全建议。

## 16. 只读识别与 constructor 边界

1. `ProjectSchemaInspector`（暂定内部名，最终代码名不构成产品合同）必须是所有项目打开入口的第一条同步持久化调用；它只允许 SQLite URI `mode=ro`、`query_only=ON` 和 PRAGMA/SELECT，不创建目录、文件、表、列、索引或 marker。
2. R1 `Store`、R7 `ProfileStore`、`RunBindingStore`、`LaunchRegistry`、`RiskRuleRegistry` 的普通构造路径在看到受支持旧格式、未知格式、缺失 marker 或结构不匹配时必须 fail closed；它们只接受当前格式。
3. 旧格式只允许由 migration runner 在已验证 staging 副本上调用专用迁移函数。专用函数不对产品 router 暴露，也不允许指向 live 路径。
4. `LaunchRegistry.open()` 必须改为 current-v4-only；v1/v2/v3 的现有 DDL/backfill 迁移语义移动到 staging-only 专用函数。具体方法名不冻结，冻结的是“普通 open 不能迁移，专用 migration 不能指向 live”。
5. 直接调用任一普通 constructor 打开 legacy/unknown/malformed fixture 必须稳定失败且源文件逐字节不变；不是只测试 product router 旁路。

这比仅在 router 增加 preflight 更深一层，防止 CLI、后台任务或内部调用绕过检查。

## 17. 冻结的结构指纹来源

- implementation 必须新增一份显式、只读、stdlib-only 的 schema manifest，逐库列出当前及每个受支持旧格式的表、列顺序、SQLite declared type、NOT NULL、默认值、主键、外键、索引和 marker 规则。
- runtime/control 与 risk rules 虽无独立 marker，仍以该 manifest 中的 exact-shape fingerprint 识别；不允许从“当前 constructor 成功打开”反推兼容。
- schema manifest 的 canonical JSON SHA-256 形成 `schema_manifest_digest`；migration plan 引用该 digest。测试必须比较 manifest 与当前 frozen DDL，而不是迁移器自己生成 expected 再验证自己。
- `PRAGMA user_version` 当前未被既有库用作权威 marker；v0.2 不把它新增为版本真相，只记录并要求与已知值一致，避免未来漂移被静默忽略。
- profile、binding、risk、execution-control 为验证成员；R1 runtime 和 launch registry 为迁移成员。验证成员只读核验，不进入 `BEGIN IMMEDIATE`，不更新 marker 或业务记录。

## 18. 更早格式、未完成运行与完整可读

- R1 marker `3` 属于“更早且本版本暂不支持升级”，不是“由更新版本创建”。固定文案：“项目格式较早，当前版本暂不支持升级。请保留原项目并联系支持。”
- 更高/未来 marker 固定文案：“此项目由更新版本创建，当前应用无法安全打开。请使用更新版本打开。”
- v0.2 完全禁止 `dataCoverage=limited`。只有 record 数量、主键关系、项目/run/profile/risk/publication/continuity 身份和必需字段均可独立重建一致时，才可返回 `legacy_readonly`；否则 `blocked`。
- 允许 `legacy_readonly` 的组合必须满足：profile=current、binding=current 或精确当前空表、risk=current 或合同允许的真正缺省、control=current 或合同允许的真正缺省、runtime=4/5、launch=v1/v2/v3 或真正缺省，并通过跨库身份核验。任一成员存在但无法识别即阻断。
- `interrupted_resumable` 只有在没有活动 writer/attempt、状态与审计一致且恢复点包含该状态时可升级；升级后必须保持同一 `interrupted_resumable` 语义和“包含未完成监查任务”的用户提示，不得改写为完成。

## 19. 恢复点漂移与幂等语义

- 取得 migration `LOCK_EX` 后，先由 09B 独立重算 live workspace fingerprint 并与已验证 backup manifest 比对，再进入任何 package preflight 或 staging 操作。
- 指纹漂移时，同一幂等键进入终态 `migration_operation_conflict`；不得静默重做备份、替换 package id 或继续升级。用户重新点击并确认“开始升级”后使用新幂等键，生成与新源状态一致的恢复点。
- 可复用已发布恢复点，但每次升级都必须在持锁状态下重新独立计算指纹；不能依赖 manifest 自报值或先前 preflight 结果。
- 迟到 callback 必须同时携带 operation id、migration plan digest 与 expected state；任一不等于 ledger 当前值即拒绝，不推进或回退状态。

## 20. staging、WAL 与跨文件系统

第一次会商建议把 staging 放到项目目录内部；该建议被拒绝，因为目录级 `live→rollback` 会把内部 staging 一并搬走，破坏第二次替换。

固定布局为：

```text
<runtime-root>/medical_monitoring_r7/
  <project-id>/                         # live
  .migration-staging/<operation-id>/workspace
  .migration-rollback/<project-id>-<operation-id>
```

- staging、rollback 与 live 必须位于同一个 `runtime-root`、同一父级文件系统；创建后比较 `st_dev`。不一致时在任何目录替换前阻断，内部码 `cross_filesystem_staging_not_supported`，用户只看到“暂时无法在当前位置升级项目”。
- staging 中所有 SQLite migration 提交后必须关闭连接、执行适用的 `wal_checkpoint(TRUNCATE)`、再次关闭重开，并确认 staging 不残留未合并的 `-wal`/`-shm`。
- 切换前在 `LOCK_EX` 内使 live writer 归零，对 live SQLite 做 checkpoint/关闭探针，并按 09A member allowlist 核对 live、staging、恢复点的权威成员集合。旧 live 整目录移动到 rollback，不拆分主库与 sidecar。
- 09B 必须直接复用 09A 的成员白名单、workspace fingerprint 和 artifact closure 实现或唯一共享 helper；禁止复制后产生第二套算法。

## 21. 崩溃恢复入口与保留现场

迁移恢复有三个入口，均调用同一 recovery coordinator：

1. `open_project` 发现非终态 migration operation；
2. `start_upgrade` 对同一操作重放；
3. 应用启动时的本地 recovery scan，仅扫描根级 ledger 中 `maintenance_acquired`、`staging`、`migrating`、`staged_verified`、`switching`、`live_verifying`、`rollback_in_progress` 的记录。

启动扫描不是定时监控或 09C 日志功能；它只把崩溃中断操作恢复到可判定终态。每次恢复先重新取得 `LOCK_EX`、重新读取目录状态和实际 schema/step digest，并重新计算源指纹。

账本必须记录每个迁移成员的 `member_step_digest = sha256(canonical_json(step manifest))`。commit 成功但账本未推进时，只有 marker、step digest、结构 oracle 与业务 oracle 同时匹配才能从下一 step 继续；否则从已验证恢复点重建 staging。

`retained_for_triage` 不自动解除、不允许新升级覆盖。v0.2 不实现人工处置工具；只保留 live/staging/rollback 和账本证据并阻断打开。后续独立、显式的处置合同才可解除，不能用删除目录代替判断。

## 22. 后端只读能力边界

- legacy 项目只通过独立 `ReadOnlyProjectView`/等价只读 facade 返回查询能力；它不暴露 mutable Store/Registry 实例。
- mutable Store/Registry constructor 只接受 current 项目，并在最深持久化入口 fail closed；router 同时做中文错误映射，但不能成为唯一阻断层。
- 所有监查写入口继续经过共享 project compatibility gate 与 09A maintenance gate；legacy 状态下统一拒绝，不允许 no-op 假成功。
- 测试必须枚举当前源码中的所有公开写方法和后台 writer，逐一证明 legacy handle 不可取得或写入失败且源字节不变。具体方法清单从源码生成并进入测试快照，不能靠手写不完整列表。
- v0.2 不增加、调用或测试医学写作接口；只通过 git/path 边界证明该子系统未修改。

## 23. 产品 DTO 修订

- `dataCoverage` 在 v0.2 中只允许 `complete` 或 `incomplete`；`incomplete` 强制 `openMode=blocked`、`canView=false`。不支持 `limited`，收到未知值同样阻断。
- v0.2 不引入 `supportCode`。
- 成功结果必须返回 `requiresReopen=true`；前端关闭旧项目上下文并回到项目列表，由用户重新打开，禁止在旧对象状态上直接切成编辑态。
- `rolling_back` 时进度冻结在最后已完成里程碑，不再上升；`rolled_back` 与 `unresolved` 不强制显示 100%。只有全部 live reopen/identity/closure 核验完成的 `succeeded` 才到 100%。
- 状态命名以 v0.1/v0.2 为唯一权威：内部 `inspecting`，公开映射为 `preparing`；不另增 `preflight`。`staged_verified` 与 `live_verifying` 保持两个不同状态。

## 24. 验收补充

除 v0.1 §13 外，必须新增：

1. 普通 constructor 对 legacy/unknown/malformed 全部 fail closed、零字节改动；专用 migration 函数拒绝 live 路径。
2. exact schema manifest 与 frozen DDL 的独立对账；risk/control 结构多一列、少一列、默认值/索引/约束漂移均阻断。
3. marker 3 与 future marker 的不同中文 reason/文案快照。
4. `interrupted_resumable` 升级前后状态、审计与提示保持一致。
5. 指纹漂移同键冲突、新键重新确认；late callback 的 expected-state 拒绝。
6. sibling staging 路径、`st_dev`、WAL/SHM、member allowlist、`EXDEV` 与两次目录替换矩阵。
7. 三个 crash recovery 入口逐一覆盖，尤其是 commit 后 ledger 前、第一次替换后、第二次替换后和 live verify 中断。
8. 所有公开写入口/后台 writer 的 legacy 阻断枚举测试；源 workspace 前后字节哈希相同。
9. DTO fixture：current、legacy_complete、legacy_required_missing、future、marker3、corrupt、upgrade_in_progress、upgrade_rolled_back、upgrade_unresolved；不包含 limited 模式和医学写作内容。
10. `rolling_back/rolled_back/unresolved` 进度冻结，只有 succeeded=100；requiresReopen 行为快照。
11. 09B fixture 复用 09A member/fingerprint/artifact helper，并运行 09A 全部 adversarial fixture。

## 25. 严重度定义与冻结结论

- P0：可能改坏/覆盖 live、错误放行未知或不完整项目、绕过只读、无法恢复或错误宣称恢复成功。
- P1：迁移/身份/审计不变量缺失，合同内部冲突，或关键行为无法独立验证。
- P2：稳定接口、状态、边界或测试矩阵不完整，但不直接造成 live 错写。
- P3：中文文案、信息层级或交互一致性问题。
- P4：低影响维护性、命名或过程清理问题。

v0.1 + v0.2 合并后，第一次独立会商提出的 6 条 P0 均有明确处置：A2、C1、E1、F1、F2 接受；D2 接受“同父级同文件系统”原则，但纠正其把 staging 放入 live 项目目录的具体路径。B1、C2、D1、I1 等关键 P1 同时吸收。

合同现进入同一 conference session 的第二轮核验。第二轮若 P0–P4 全部为 0，则状态保持 `FROZEN_R7_SLICE_09B_SCHEMA_MIGRATION_CONTRACT_V0_2` 并解锁 governed implementation；否则继续在合同层修订，不写产品源码。
