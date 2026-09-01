# R7 Slice-03 产品挂载验收无损暂停检查点

日期：2026-08-28
状态：`PAUSED_DURING_ACCEPTANCE_SYNTHESIS`

## 1. 当前结论边界

Slice-03 产品挂载实现、Codex 纠偏、聚焦/全量/相邻回归及两席独立会商均已完成；尚未完成最终验收文档、receipt 最终回写、review-gate 与 README 状态切换，因此当前仍不得称为 Slice-03 受限接受，更不得称为 R7 完成。

本阶段始终未启动 8911/5174、未调用真实模型、未运行真实临床项目、未修改前端或医学写作子系统。

## 2. 已落地文件与当前哈希

- `services/api/app/main.py`
  - SHA256 `e2d78af34b0ea2af9949be10514bed0df8f37326509a9316ec37664d5bd80fba`
  - 仅增加 R7 产品 router import/include。
- `services/api/app/medical_monitoring_r7_product_router.py`
  - SHA256 `aa783c3f48c78ad51f875042f09f9eff10309b9e93505028c46c76c0da774ca3`
  - 当前包含：项目级工作区、双库就绪检查、别名 canonical 化、局部中文错误、未知 R7 路径/错误 method catch-all、自动 project/run scope、每请求关闭连接。
- `tests/test_medical_monitoring_r7_product_router.py`
  - SHA256 `238450d3c85926c8943ffb9f1266f690eb52f94c96b874ee784eebace6ce55e5`
  - 当前 15 项测试。
- `poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`
  - 已把 `evidence/r7_product_mount_receipt.json` 加入 R7 create-only 白名单。
- `poc/medical_monitoring_ai_native_r7/evidence/r7_product_mount_receipt.json`
  - 已有中间态 Codex 更新，但仍记录上一轮 14 passed 和旧 router/test 哈希；恢复后必须先回写最终 15 passed 与上述当前哈希，不能把当前 receipt 当最终证据。

冻结合同仍为：
`context/medical_monitoring_r7_slice_03_product_mount_contract_20260828.md`
SHA256 `23a01f905fa1d19566873b0f04bd8a55f38f37e9ce28529a09a39a1f75f89b9b`。

## 3. 本轮 Codex 纠偏

1. 工作区就绪从只检查 `execution_profiles.sqlite3` 改为同时检查配置库与 `monitoring_run_bindings.sqlite3`，防止非 bootstrap 请求静默补建缺失数据库。
2. project 层 scope 允许项目别名经宿主 resolver 规范化，并只以 canonical project id 存储/读取；修复真实宿主别名 URL 下的 422 接缝缺陷。
3. 增加 R7 router 内局部 catch-all，使未知子路径和错误 method 返回顶层中文 `{code,message}`，不改变非 R7 错误形状。
4. 产品层 RunEntry 错误不再转发核心动态详情，只按稳定 code 映射中文消息。
5. 测试直接读取临时 frozen profile，证明项目层 timeout 77、别名项目层 timeout 81 确实进入冻结配置，并证明名称型 DeepSeek 冻结为 `reasoning_effort=max` 且无 fallback。

## 4. 已完成验证

- 产品聚焦：`15 passed in 0.37s`；Grok 同会话续审独立复跑为 `15 passed in 0.40s`。
- 改动专属 Ruff：通过。
- 改动专属 `compileall`：通过。
- R7 全套（最终补丁后）：`93 passed in 8.38s`。
- R6 全套（最终补丁后）：`763 passed in 6.79s`。
- 相邻产品/principal/route-context 六文件：`132 passed in 4.78s`。
- 8911、5174：最后探测 `connect_ex=61`，均无监听。
- R7 全套中的医学写作边界校验通过：542 文件，聚合 SHA256 `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。

完整 `main.py` Ruff 仍有并行医学写作区域既有告警；未越界修复，不属于本切新增失败。

## 5. 会商终态

会商任务：`mm_r7_slice_03_product_mount_acceptance_20260828`

- Pi / `google-antigravity/gemini-3.7-flash:high`：同一 session 两轮，最终建议受限接受，未发现剩余 P0-P2。
  - session `01a04535-69a6-7000-aa2c-c8d9737a58c2`
- Grok Build / `grok-4.6:medium`：同一 session 两轮；首轮发现别名、catch-all、动态错误详情与测试预言缺口，纠偏后续轮复核关闭，未发现剩余 P0-P2。
  - session `08fd55a8-82d2-4b62-a392-4cce947126d6`

注意：Pi 续轮报告声称测试还断言了 `requested_provider/requested_model`，当前测试实际只明确断言 DeepSeek `reasoning_effort=max` 与空 fallback；最终 Codex 结论不得复述该未由当前测试支持的附加声称。Grok 续轮的实际 pytest/Ruff/compileall 证据可采用。

## 6. 尚未完成，恢复后严格按序执行

1. 重新计算当前最终哈希，把 `r7_product_mount_receipt.json` 更新为 15/93/763/132 的最终证据并移除“pending independent acceptance”旧状态。
2. 填写：
   - `reviews/codex_conference_mm_r7_slice_03_product_mount_acceptance_20260828_review.md`
   - `metrics/mm_r7_slice_03_product_mount_acceptance_20260828_conference_metrics.md`
3. 运行 conference `review-gate --require-verification`；再运行 execution/conference 对应审计，确认两个参与者均为同 session 两轮、无 fallback、无 pending/rejected。
4. 创建 `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`，明确仅为离线受限接受。
5. 把 `poc/medical_monitoring_ai_native_r7/README.md` 中 Slice-03 的 `pending Codex` 改为受限接受，并重跑最小决定性检查；更新 receipt 的 README 哈希。
6. 只有以上全部通过后，才清理本切不再需要的临时执行/会商缓存；保留合同、报告、review、metrics、acceptance record、receipt 和必要日志索引。
7. 完成 Slice-03 收口后再按 R7 计划冻结下一纵切合同；当前尚未开始后台运行、进度、恢复/重试或真实 harness 调用。

## 7. 下一安全动作

从本检查点重新锚定当前文件哈希，先完成 receipt/review/metrics/review-gate/acceptance record/README 的原子收口；不得重做已通过的实现，不得启动服务、真实模型或真实项目，也不得触碰医学写作和前端。
