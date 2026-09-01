# Slice-08B 独立验收最终复核状态

请在同一 session 中进行最后只读复核并覆盖输出完整最终报告；末尾只给 `ACCEPT` 或 `REVISE`。

Round 2 提出的 O1-O3 已继续闭合：

1. `finalize_publication` 首次 available 现在强制 `len(artifact_member_ids) == 4`，与冻结 R6 每模式四输出一致；Bridge 仍是输出种类/内容校验权威，Registry 只执行数量与摘要防御性闸门。
2. `_row_to_publication` 对存在 v4 闭包的 available 行做读时复核：四成员、64 位 output-set digest、member-set digest 相等；全空的迁移前 legacy available 行仍可只读回放。
3. 产品路由最外层未知异常不再标记为可恢复 `runtime_read_failed`，而是 `internal_error`、不可恢复；已知 LaunchRegistry/RunSetup/Runtime 错误仍走各自明确分层。
4. 新增测试同时覆盖单成员 direct Registry 注入拒绝和 DB 成员 JSON/摘要不一致的读时篡改阻断。
5. 相关测试：registry+continuity 50 passed，产品路由 61 passed；全 R7+产品 320 passed；核心 74 项在 `PYTHONHASHSEED=0/1/42 × 普通/-O/-OO` 九格全部通过。

相邻边界保持前述状态：R1 56 passed；R5/R6 仅并行医学写作文件计数/旧固定哈希基线漂移，本 Slice 未修改。8911/5174 停止。

请核对 O1-O3 是否闭合；O4 orphan 仍按 R1 content-addressed、非 publication 成员即非权威的既有协议处理；O5 synthetic defaults 仍属本 Slice 显式 synthetic provider 接线，真实 provider 接入时必须另行去除/改为必填，不得将本次 synthetic 接线表述为真实项目贯通。
