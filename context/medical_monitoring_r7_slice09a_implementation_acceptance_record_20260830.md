# R7 Slice-09A 项目备份/恢复实现接受记录

日期：2026-08-30  
决定：`ACCEPT_R7_SLICE_09A_SYNTHETIC_OFFLINE`

## 接受结果

- 已实现根级操作账本、项目级 POSIX 共享/独占维护门、deterministic `.mmbackup`、六类工作区成员闭包、SQLite 在线副本、R1 工件闭包和原子包发布。
- 已实现恢复预检、项目身份/schema/成员核验、旧包回退确认、staging、两段目录切换、自动回滚、需人工处理保留、重开对账和同值重放。
- 五个项目级产品路由保持既有项目解析与授权边界，长时备份/恢复在后台执行，GET 返回同一持久操作的中文进度；无取消/删除接口，无复杂页面。
- 后台 worker 初始化前失败也会进入持久终态；确认等待态不会被错误改写，用户可继续同一恢复操作。

## 决定性证据

- 冻结合同：`reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_1_20260830.md`、v0.2、v0.3。
- 实现审阅：`reviews/codex_execution_mm_r7_slice09a_execution_20260830_review.md`。
- 当前哈希清单：`artifacts/mm_r7_slice09a_execution_20260830/manifest.json`。
- 独立会商：`runs/conference/mm_r7_slice09a_implementation_acceptance_20260830/general_single_object_round2.md`。
- 会商结论：P0/P1/P2/P3/P4=`0/0/0/0/0`，`ACCEPT_R7_SLICE_09A`。
- Codex 当前复跑：聚焦 5 项、R7+产品 511 项、相邻 R1 327 项全部通过；compileall 通过。
- execution audit、conference validate、execution/conference review gate 均通过。

## 历史缺陷说明

`worker_03.md` 中两项红色发现是修复前历史快照，保留不改写。当前源码已修复忙碌重试重新打开同一恢复操作及 triage rollback 指针，两个精确回归均通过。随后同一 worker_02 session 关闭确认等待态被错误终结的相邻 P1。

## 边界

本记录只接受 Slice-09A synthetic/offline 后端能力，不接受 Slice-09、R7、R8、真实项目/模型医学质量、生产或商业使用。09A 未新增可见页面，因此未重开 08C 视觉验收。

8911/5174 保持停止；未运行五个真实项目、真实模型或浏览器，未修改医学写作。

## 下一安全动作

进入 Slice-09B schema 迁移、升级与回滚合同：先盘点当前 R7/R1 schema 版本与现有 additive migration，再冻结“升级前备份、逐步故障注入、版本最后推进、失败回滚、旧项目只读兼容”最小合同；不得让用户删除工作区重来。
