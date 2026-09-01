# R7 Slice-09A 项目备份、恢复、导出与导入合同 v0.3 冻结补充

日期：2026-08-30  
状态：`FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3`

本补充与 v0.1、v0.2 合并构成完整合同；冲突时 v0.3 优先。它关闭第二轮会商中成立的 P1 缺口，并明确拒绝会增加范围或不符合当前边界的建议。

## 25. 维护门的固定实现合同

v0.2 第 15 节中的“共享/独占维护许可”固定为 POSIX advisory file lock，使用 Python 标准库 `fcntl.flock`：

- 每个 canonical project 在根级 `.maintenance-locks/` 下有一个由 canonical id 的 SHA-256 派生的内部 lock file；公开 DTO 不暴露该路径或摘要。
- 所有项目写入口与后台写事务在事务外层持有 `LOCK_SH`；备份一致点和恢复从最终状态复核至目录切换完成期间持有 `LOCK_EX`。
- 获取锁使用非阻塞尝试与单调时钟，默认等待 30 秒、硬上限 120 秒；等待时根级操作账本显示“正在等待项目空闲”，百分比不前进。超时返回稳定 `project_busy_retry_later`，清理仅属于本操作的临时文件，live 不变。
- OS 在进程退出或 fd 关闭时自动释放 flock，不另造 heartbeat/lease 表，不以 PID 存活或墙钟过期推断锁失效。
- 根级 `backup_operations.sqlite3` 记录 `waiting_for_project/maintenance_acquired/maintenance_released` 与终态，但不承担锁所有权，不随项目目录切换。
- `BEGIN IMMEDIATE; ROLLBACK`、launch state 和 R1 running attempt 检查均在 `LOCK_EX` 内执行，是一致性复核，不替代 flock。
- 锁获取、释放、超时、持锁进程异常退出和双进程 writer/restore 竞争均为固定故障/并发测试。

该合同明确把所有写入口接入同一门视为 09A 完成条件；若不能证明写面闭合，实施不得通过。

## 26. 包发布与工作区指纹

### 26.1 发布终态

最终 ZIP 只有在临时文件写完、fsync、关闭、重新读取、逐字节 SHA-256 与内存预期一致、并 `os.replace` 到 published 路径后，才把操作置为 `available`。此前 GET 只能返回“正在生成备份”，不返回下载位置。

重新读取不一致、原子发布失败或 published 目标冲突统一返回内部稳定码 `backup_package_publish_failed`；根级操作账本记录失败，临时文件按 `cleaned_up` 或 `retained_for_triage` 状态处理。不得覆盖既有 published 文件，不得删除既有可下载备份，不枚举宿主 errno 形成用户合同。

### 26.2 工作区指纹

`source_workspace_fingerprint = sha256(canonical_json({member_id: sha256(staged_member_bytes) for member_id in sorted(staged_member_ids)}))`

它只由验证后的 staging 成员字节计算，不读取 manifest 自报摘要，不含 ZIP metadata、生成时间、路径或显示名称。`terminal_outcome` 仅在第 20 节全部不变量通过后写入根级操作账本。

`already_current` 必须同时满足：package id 相同、source workspace fingerprint 相同、第 20 节从 live 独立重建的成员集合和业务投影均相同。单独 fingerprint 相同不能替代语义对账。

## 27. 第二轮非阻断建议的边界决定

1. 故障钩子不绑定任意“至少 31 个”数量。数量由 09A 实际生产源码的全部相变、文件发布和两次目录切换边界枚举得出；少一个实际钩子即失败，多造无业务边界的钩子也不计价值。冻结的是名称表与全命中证据，不是沿用 08D 的数字。
2. 09A 不新增取消/删除接口。备份/恢复有固定锁等待上限与终态恢复；在切换阶段引入取消会扩大半状态组合。若以后需要用户取消，须另立合同。
3. 09A 公开路由继续使用现有 project route context、principal 与 action authorization；本切片不新增、放宽或专项测试操作级鉴权，也不接受“持有 operation id 即可读取”的规则。
4. v0.1–v0.3 的公开路由和 DTO 属于后端产品合同，不新增复杂页面，因此 09A 不触发 08C 视觉重开；若实现新增可见 UI，另行启动视觉 execution/conference 与 ego(lite) 验收。

## 28. 最终合同完成门补充

实施开始前需独立确认：

- v0.1、v0.2、v0.3 合并后无当前源码不存在的表/API 前提；
- file-lock 维护门、package id、source workspace fingerprint、operation ledger 四者职责分离；
- 备份包发布前不可见，失败不覆盖既有包；
- `already_current` 由字节指纹和独立业务对账共同证明；
- 不以任意钩子数量、取消接口或新鉴权机制扩大 09A。

满足后合同状态可冻结为 `FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3`，只解锁 governed 09A implementation。
