# R7 Slice-07C-2 同会话第三轮复审补充

Codex 已完成你二轮指出的最后窄边缘：

1. `launch_registry.py` 的 `waiting_start` 现在允许校准到完整运行态集合，包括 `stopping`、`completed` 与 `ended_incomplete`，覆盖“已准备但首次后台启动失败，管理员随后启动并快速完成”的真实恢复序列。
2. `GET /runs` 的逐记录校准同时捕获 `LaunchRegistryError`，单条异常记录不会击穿整个项目历史接口。
3. 新增产品回归：首次 prepare-and-start 返回 `waiting_start` → 管理员对同一内部 run 调用 start → 轮询公开历史直到 `completed`；断言接口始终 200、`result_available` 仍为 false。
4. Codex 复跑产品路由：`43 passed in 4.04s`。

请保持只读，仅复审这三项差异与此前两轮相关代码，判断是否已关闭最后反例。若无新的 P0-P2 或合同阻断，请明确给出 `ACCEPT`；否则只列仍可复现的阻断及最小修复。不要扩大到 07C-3。
