# 医学监查 P10 LOOP 3.16 v6 身份/原子性纠偏无损暂停

日期：2026-08-01

## 当前结论

- 当前细分任务已完成并通过离线验收；主 Goal 未完成。
- v5 visit canary 已失败关闭，不得 retry/reuse，也不得捞取失败 prose。
- v6 离线实现已接受，但尚未做任何真实 v6 startup/canary/runtime 验证。
- RUX 协议门仍 blocked；MY009 与三个真实项目不得启动。
- 所有候选 accept/reject/adopt/confirm/activate 决策仍属用户权限，本轮为 0。

## 当前运行状态

- 8911：必须保持停止，0 listener。
- 5174：停止，0 listener。
- 未留下本医学监查任务的 pytest、runner、Pi、Kimi 或 Codex reviewer 后台任务。
- 只读进程核查观察到另一个会议纪要任务的独立
  `meeting_minutes_stage3_wave1c_selection_exec` runner 正在运行；它不属于本任务，
  本轮未读取、干预或停止。
- 未写 runtime DB，未启动真实项目，未修改医学写作业务源码。

## 已完成工作

1. 启动恢复缺陷已闭合：
   - 错误首启前无 canary POST；
   - 仅 `medical_monitoring_ai.sqlite3` 从 pre-canary 一致备份恢复；
   - 第二次真实启动保留 v4 的 2 completed / 6 failed / 8 proposed；
   - 启动修复 Codex 聚焦 55 passed。
2. v5 visit canary：
   - job `monai_5e1ed560631e7e0d6be5a948571a`；
   - attempt `monattempt_8f67d5f58b534b33b946fbb3699df33e`；
   - failed / invalid_ai_output / non-retryable / 0 candidates；
   - response SHA-256
     `8bd02c480ac4deec97e84bcef7110e42e1997741717081ded39e0f353c799e97`。
3. v6 离线纠偏：
   - evidence packet v3；
   - structural repair v2；
   - prompt `monitoring-protocol-clause-structuring-v6`；
   - terminal legacy versions v3/v4/v5；
   - 稳定 list bundle、严格 list role、provider focus 防孤儿；
   - required fact_type、visit topic/atomicity gate；
   - study-treatment/IP 与 concomitant-medication/non-IP 精确冲突配对；
   - 协议 output schema 移除 `system_generated_evidence` 伪字段。

## 最终文件与 SHA-256

- `services/api/app/monitoring_ai_source_packet.py`
  `32f041c4a8662f5524eac6db3cb968ac6a1625c1efc01c08940e99e97cb520aa`
- `services/api/app/monitoring_ai_service.py`
  `6ae0e01037880bc881cf03017ae10ebf5e62660c5eafcad5c4d671cfec48bb3f`
- `services/api/app/monitoring_protocol_preparation_service.py`
  `d8492de18b734fdc3cf9caeffc2a0f79a3d741c51fce52945221df8adcc3fb1b`
- `tests/test_monitoring_ai_source_packet.py`
  `835e220bc6473a1ed50f3e5077744220f0bdee60efcd6e22701c1361b765f639`
- `tests/test_monitoring_ai_service.py`
  `0021244e30eab4f9ded74d39114d2c498dc43707dc2ae40ffa6d8c81b4030c0e`
- `tests/test_monitoring_protocol_preparation.py`
  `d0f540980f01fb722c38c9cfcaf4d60831e7358a6e02a589664b404609fb6689`
- `tests/test_monitoring_ai_api.py`
  `db209f15b4af69958d9bb50ff516680740ac20302d3a72afef9e142357644a80`

## 验证证据

- v6 聚焦三文件：241 passed，0 failed。
- 第一次全监查：1205 passed / 1 failed；唯一失败为相邻 API fake provider
  缺 v6 required `fact_type`。
- 补齐该测试 fixture 后单点：1 passed。
- 第二次全监查：1206 passed / 4299 deselected / 27 warnings / 0 failed。
- 医学写作相邻五文件：200 passed / 0 failed。
- 三个实现模块 `py_compile` 通过。
- 警告为既有 SWIG/FastAPI/openpyxl 警告，无新失败信号。

## 路由与 session

- Pi initial/follow-up 共用 session：
  `019fb977-9636-7000-876b-15f3ea49de8a`。
- 初始 1 pass；Codex 发现 provider orphan 与 IP/CM conflict pairing 两个缺口；
  同 session 仅一次合并 follow-up；无 re-dispatch、无 fallback。
- 独立 v5 reviewer 复用既有 `rux_protocol_v4_audit` Luna session，未新建 reviewer。

## 关键记录

- v6 context：
  `context/monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_context.md`
- v6 worker：
  `runs/pi_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801.md`
- v6 follow-up：
  `runs/pi_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_followup1.md`
- v6 review：
  `reviews/codex_monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801_review.md`
- v5 reviewer：
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v5_visit_canary_20260801.md`
- LOOP ledger：
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`

## 下一安全动作

下次用户明确要求继续时：

1. 先只读核对 8911/5174 仍为 0 listener、上述七个哈希未漂移、无中断的
   Kimi/Pi/Codex runner 修改。
2. 重新读取本暂停文件、v6 review、v5 independent review 和 LOOP ledger。
3. 只通过 `scripts/start_stable_backend.zsh` 启动唯一 8911，先验证 startup 不会
   supersede v4/v5 terminal history。
4. 在确认不存在现有 v6 visit job、冻结八主题 job/attempt 计数后，只创建一次新的
   `visit_window_and_order` v6 canary。
5. 使用一次长硬等待，不固定轮询、不重复 POST、不 retry；终态后停止 8911。
6. 复用既有 Luna reviewer session 做独立只读候选/失败审查。
7. 只有 v6 单主题 canary、聚焦/相邻回归与 Codex review 全部通过，才讨论 RUX
   protocol gate；仍需等待用户后续指令，不能自行启动 MY009。

## 明确禁止

- 8911 在暂停期间必须保持停止。
- 不启动 5174、MY009 或三个真实项目。
- 不 retry/reuse v5。
- 不自动决定任何候选、draft 或 activation。
- 不把本证据恢复续作表述为恢复了已删除的原始逐条对话。
