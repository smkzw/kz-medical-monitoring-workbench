# R7 Slice-07C-2 同会话复审补充

Codex 已根据你上一轮的 revise 意见完成有界修订。请保持只读，在同一 session 中仅复审以下变更与结论，并给出 `ACCEPT`、`REVISE` 或 `BLOCK`：

1. F-1：`GET /runs` 现在读取已冻结 manifest 对应的真实运行进度，将 launch registry 的 `run_state` 校准为 `running`、`completed`、`interrupted_resumable` 等公开状态；产品测试等待并证明合成运行最终显示 `completed`，且结果入口仍不可用。
2. F-2：同一幂等请求重放时，仅当 `manifest_digest` 已存在才直接返回；若只完成 reservation、尚未完成 prepare，则继续对同一个内部 run 执行幂等 bind/prepare/start。测试模拟首次 prepare 中断，证明仅保留一条公开运行、重试复用同一 public token。
3. F-3：新增产品路由层跨项目 current snapshot 与 baseline token 的 fail-closed 回归，并证明失败前 launch history 为空。
4. F-5：新增纯 `medical_monitor` 可启动、纯 `medical_writer` 返回 403 的角色级路由测试。
5. Codex 独立复跑：产品路由 `42 passed in 3.04s`；R7 全套 `181 passed in 21.25s`；compileall 通过；8911 与 5174 均无监听。

重点核查当前文件：
- `services/api/app/medical_monitoring_r7_product_router.py`
- `tests/test_medical_monitoring_r7_product_router.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py`

请确认两项关键反例是否已真正关闭、是否引入重复启动/状态非法迁移/公开字段泄漏，并给出简洁的二轮最终建议。不要修改文件，不要扩大到 07C-3。
