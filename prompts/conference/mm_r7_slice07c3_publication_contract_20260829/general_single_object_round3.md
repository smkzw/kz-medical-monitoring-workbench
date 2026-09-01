# R7 Slice-07C-3 合同同会话终审 Round 3

请保持原 CodeBuddy/DeepSeek V4 Flash max session，不重启任务，不修改文件。Codex 已将 Round 2 的
2 个 P1 和 5 个 P2 全部按最小修复写入
`reviews/medical_monitoring_r7_slice07c3_result_publication_contract_v0_2_20260829.md`：

- 请求级 fingerprint 已严格枚举冻结身份字段，排除 receipt set/attempt state，receipt-set digest
  只在 finalize 绑定；
- publication 状态机、CAS 合法转移及 available 终态已钉死；
- reserve 明确先于 runtime/authority 读取；
- publication 表明确具有 `(project_id, run_id)` 和 `(project_id, idempotency_key)` 两个 UNIQUE；
- result-entry 明确仅 available 签发，未完成不回退其他运行；
- site_label 明确由产品投影确定性生成 `中心 {site_ref}`；
- snapshot option token 与产品 packet snapshot_ref 明确通过冻结 run options 确定性映射对账。

请只读核验上述修订是否完整关闭 Round 2 的 2×P1 + 5×P2，并检查修订本身是否引入新的 P0-P2。
若关闭，请明确输出 `ACCEPT`；若仍有问题，只列可复现的 P0-P2 阻断和最小修复。不要扩大到源码实现。
