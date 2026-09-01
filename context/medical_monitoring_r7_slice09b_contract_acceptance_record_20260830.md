# R7 Slice-09B 合同冻结记录

日期：2026-08-30  
状态：`ACCEPT_R7_SLICE_09B_CONTRACT_V0_2`

## 接受对象

- 基础合同：`reviews/medical_monitoring_r7_slice09b_schema_migration_contract_v0_1_20260830.md`
- 优先补充：`reviews/medical_monitoring_r7_slice09b_schema_migration_contract_v0_2_20260830.md`
- 合并冻结状态：`FROZEN_R7_SLICE_09B_SCHEMA_MIGRATION_CONTRACT_V0_2`

## 已冻结的核心决定

- v0.1 只治理当前已有 legacy→current：R1 4/5→6、launch v1/v2/v3→v4；profile/binding/risk/control 只做严格当前格式验证。
- 所有普通 constructor current-only；旧项目先只读识别，支持来源完整时只读查看，用户明确点击后才升级。
- 升级前必须有同源、已发布且独立核验的 09A 恢复点；源漂移同幂等键冲突，不静默重备份。
- 迁移只在同 runtime root 的 sibling staging 进行；每库 marker-last，跨库由目录级切换/恢复闭合。
- 崩溃恢复由 open、同操作重放和启动扫描三个入口进入同一 coordinator。
- legacy 读路径不给 mutable store；limited 数据展示、supportCode、工程字段和医学写作耦合均不进入本切片。
- 只有 succeeded 达 100%；恢复和状态不明保留最后真实节点；成功后必须重新打开项目。

## 会商结论

- Round 1：6 个 P0 与关键 P1，要求修订。
- Codex v0.2：全部吸收并纠正 staging-inside-live 的不安全建议。
- Round 2：同一 session `01a05136-008a-7000-b015-9928f6ad0ea7` 对 v0.1+v0.2 逐条复核，P0=P1=P2=P3=P4=0。

## 边界

本记录只冻结 synthetic/offline 09B 实施合同。未修改产品源码，未运行测试、服务、浏览器、模型或真实项目，未触碰医学写作。它不接受 09B 实现、Slice-09、R7、R8、生产或商业化。

## 下一安全动作

连续进入 governed 09B implementation：

1. 只读 schema manifest/inspector 与 legacy fixture；
2. migration plan/ledger/coordinator 与 09A 原语复用；
3. R1 与 launch staged-only migration；
4. 中文 DTO、只读 facade 与 mutable writer 阻断；
5. 故障注入、确定性、09A/R1/R7 回归、独立实现会商。

继续保持 8911/5174 停止，不触碰五个真实项目、真实模型、视觉页面或医学写作子系统。
