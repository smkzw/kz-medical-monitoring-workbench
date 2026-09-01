# Slice-08B 独立验收 Round 2 状态

请在同一 session 中只读复核以下纠偏，并返回完整更新报告，末尾明确 `ACCEPT` 或 `REVISE`。

## 已修复

1. `launch_registry.finalize_publication` 现在在首次转为 available 前强制：显式成员集非空、`r6_output_set_digest` 为 64 位、成员摘要与 `content_digest(member_ids)` 一致；空 R6 闭包保持 publishing，结果入口不开放。
2. 新增 `test_finalize_rejects_empty_r6_artifact_closure`。
3. `extract_atomic_items` 对非 mapping payload 改为 `OUTPUT_PAYLOAD_INVALID` fail closed；新增聚焦测试。
4. `_ensure_store_run` 不再吞掉任意异常；R1 project/source revision/run 绑定失败转换为明确桥接错误，并校验已有 run 的 project/mode/cutoff/source revision/execution basis 不漂移。
5. 合同要求的 canonical 改为直接复用 `launch_registry.content_digest`；R5 包自校验不再导入 R5 私有 digest helper，而通过 frozen dataclass `replace(packet)` 触发 R5 自有校验。
6. 旧 07C 产品测试已改为确认“缺 R6 闭包仍 blocked”；真实 typed R5 测试增加 synthetic R6 provider 后继续覆盖正向发布与重新取证。

## 当前证据

- `test_continuity_bridge.py + test_continuity_registry.py`: 49 passed。
- `test_launch_registry.py`: 24 passed。
- 产品路由：61 passed。
- R1 相邻 `test_domain_store_graph.py`: 56 passed。
- R6 `test_mode_output.py`: 350 functional passed，只有医学写作聚合计数旧基线失败（当前 445 vs 测试常量 542），属于并行医学写作工作区漂移，本切片未修改。
- R5 选定相邻：12 functional passed，只有 R5 readonly gate 对 `mm_r5/__init__.py` 的旧固定哈希失败；本切片未修改 R5。
- 8911/5174 均无监听。

## 请重点核对

- 新 available 闸门是否已关闭 D1；非空而非在 Registry 硬编码 4 个，是因为桥接器已冻结并验证每模式恰好 4 个，Registry 只持显式成员闭集，避免存储层复制 R6 数量规则。
- G1/G2 是否闭合。
- 旧 available 行只读回放是否仍可用；新 transition 是否不能空闭包。
- synthetic 默认字段仍只在 08B 显式注入 provider 的 offline 测试接线中使用；若你认为产品代码仍可能无标记泄漏，请给出可复现路径与最小修复。
- 不要修改文件、启动服务或访问真实项目。
