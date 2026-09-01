# R7 Slice-04 持久化运行进度有限验收记录

日期：2026-08-28  
状态：`ACCEPT_R7_SLICE_04_DURABLE_PROGRESS_LIMITED`

## 验收对象

本记录只接受 synthetic/offline 条件下的显式运行范围准备、R1 SQLite 权威 work-unit
账本，以及从账本重建的项目级中文只读进度。它不接受后台执行、进程所有权、中断恢复、
真实模型/项目、前端或 R7 总体。

冻结合同为
`context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`，SHA-256
`a5033b871ffd025cc5dd6345fb9a1bd214e41f01e3893ef2f94ca7ac6d830745`。

## 已实现能力

- 项目级 `POST /runs/{run_id}/execution/prepare` 与只读
  `GET /runs/{run_id}/progress`，权限分别为管理运行配置与读取 AI 运行。
- R1 manifest/work-unit ledger 是唯一进度事实源；R7 不保存第二套 completed/total。
- 当前范围幂等重放；日常/锁库前追加新范围版本；A→B→A 历史回退阻断；核查前首次准备后冻结。
- canonical 项目别名共用一套 runtime；跨项目相同 Run ID 保持隔离。
- 八种 R1 状态、阶段进度、当前工作与最新动态仅以稳定中文受众字段返回。
- 未 bootstrap、未绑定、未 prepare、身份篡改、账本/审计篡改均失败闭合。

## 会商纠偏

独立 Grok 验收复现了跨切片产品陷阱：Slice-03 产品入口可以绑定内部哈希式
`data_cutoff`，而 Slice-04 为避免技术标识进入界面会拒绝该值，造成“绑定成功、准备失败”。
Codex 选择在产品入口源头阻断并复用同一公开截止点校验，没有放宽进度输出。对应增加了
非法截止点、产品级 A→B→A、核查前冻结和 R1 幂等冲突回归。

## 决定性证据

- 聚焦 adapter + product：`38 passed in 0.95s`。
- R7 全量：`108 passed in 6.84s`。
- R1 全量：`327 passed in 10.80s`；R6 全量：`763 passed in 6.10s`。
- 隔离缓存 compileall：通过，69 个字节码文件。
- R6 四个固定文件哈希不变；医学写作 542 文件聚合 SHA-256 仍为
  `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911/5174 均 `connect_ex=61`，没有监听。
- 实施 audit-execution 通过；独立会商 review-gate 通过。

## 独立验收

- Pi / google-antigravity / Gemini 3.7 Flash high：一轮完成，无 fallback；确认冻结合同范围内
  的进度事实面成立，建议把并发所有权与快照切换留给 Slice-05。
- Grok Build / Grok 4.6 medium：一轮完成，无 fallback；发现并复现 cutoff 产品陷阱与覆盖缺口。
- Codex 复现、修复、补测并完成最终有限验收；没有把参与者自述当作接受证据。

## 下一安全动作

进入 Slice-05 前先冻结“后台执行与可恢复状态机”合同。必须明确单一运行所有者、原子领取、
checkpoint、崩溃重建、继续/重试/取消语义、一致受众快照，以及与当前 prepare/progress API
的兼容关系。仍不启动 8911/5174、不调用真实模型、不运行真实项目、不修改前端或医学写作。
