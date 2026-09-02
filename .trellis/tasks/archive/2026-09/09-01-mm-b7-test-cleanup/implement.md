# B7 实施计划

1. 生成候选清单，逐项标注为 whole-file pin、行为 digest、来源内容 SHA、CAS/identity 或历史一次性脚本；只处理前两类中的废止门与历史脚本。
2. 删除 30 个指向已删 POC 且无当前调用方的 R5 S3–S6 generator/verifier；复核 `pytest.ini`、package scripts、CI 与当前测试均未引用。
3. 对 D07–D10 artifact-generator 测试做最小清理：删除源文件整 SHA 与固定旧路径断言，保留 JSON 结构、条数/闭合、确定性再生成及领域结果断言。
4. 移除 optimizer/hash-seed 多矩阵与 digest-refresh 前置；保留一次正常解释器确定性检查。
5. 跑受影响测试、医学监查聚焦/集成回归、62 个前端 node 测试和 Vite build；运行医学写作保护性子集但不跨边界修复既有失败。
6. 记录删除/保留分类与验证证据到 Trellis journal，完成并归档 B7。
