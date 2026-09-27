# D对照·G1-G8指标报告（CM+MH，A=09-26热启动重跑 vs B=本轮冷启动语义证据）

生成时间：2026-09-27T11:23:25.957487+00:00  
数据源：D1基线导出 + D2终态导出 + 运行库（只读）+ list_for_review同会话投影

## 结论

**是否建议在已验证范围启用B：是**

- 理由：G1-G8无fail门：B在已验证范围（CM+MH共52字段、双盲独立、诚实台账、同服务会话投影可定位）满足启用条件。保留决策上下文：G1 partial（确定性作业revision与单元不一致（合同性，身份已全回链））。B-vs-A分歧字段逐条见per_field_comparison（分歧分析非错误判定），最终采纳由医学经理人工复核。本报告不切换任何生产路由。

- 启用前置：确定性作业revision与单元作业不一致（工具合同对非chunk画像重算profile_sha256所致）——如需修订级全cohort统一，需登记新的确定性画像合同版本
- 启用前置：工具版本身份的修订摘要与v19逐字不同（绑定冻结文档源所致），画像级已逐字一致
- 启用前置：重启后live库B证据链失效，以D2导出为准

## G1 来源与身份（partial）

- attempt：`stg-e9d5050c73ef44be818e1f44920fdb5f`；共享冻结画像 profile_sha256：`ab23d774811dfc17…`
- A修订摘要：`2d2e35625a0918cb…`；B模型作业修订摘要：`f0593847643d8c02…`（工具合同绑定文档源所致）
- 回链：A候选 104 字段、B候选 104 字段均回链candidate_id；B确定性作业4个同cohort同prompt版本回链，但revision与单元不一致（例外已记录）

## G2 工具可达（pass）

- A：10作业、evidence_reads=0 → single_call（如实登记无工具）
- B模型：52作业 = executed 10 + idle 42，回执共21条
- B确定性：tool_loop_idle（登记有工具合同、零读取，如实标注）
- 分类口径：evidence_tool_contract.classify_tool_usage：按实际回执数事后分类，不按版本名声称

## G3 完整覆盖（pass）

- A：CM 32/32（主/盲核）、MH 20/20，每字段显式；元数据不对称：主CM 14含SUBJSTA(source_metadata) vs 盲核13；元数据结论由确定性规则并入候选
- B：每cohort覆盖 52/52，缺失 0 字段（元数据，确定性作业stale），缺失清单见JSON b_missing_fields

## G4 独立复核（pass）

- B盲核：26单元、前缀`listing-field-mapping-verifier:stg-e9d50…`、自有取证回执19条；隔离标识=业务键前缀/profile/独立worker
- A盲核：5作业（verifier-v8，单次调用0取证回执）

## G5 诚实结果（pass）

- A：52字段双侧均恰1条结论（0缺失、0多值）；A双盲分歧 19/52；未知条目 0
- B：52字段双侧恰1条；0字段0条（显式列出，不凑数）；B双盲分歧 15/26；未知条目 0

## G6 恢复（pass）

- B：模型失败 0；确定性第一代退役 4；确定性固定代际stale 0；重试作业 1；superseded候选 0
- A：attempt内失败 0；重试作业 14
- 成功无重复推理：B每字段仅一条结论（56候选覆盖52字段×双侧，单元字段集两两不相交）；A同构（104条覆盖52字段×双侧）

## G7 可用交付（pass）

- D2同会话捕获（2026-09-27T09:53:04.314631+00:00）：HTTP True，field_count 52/52（每cohort，应52）
- 本次同服务会话再核验：server_reachable=True（2026-09-27T11:23:25.957220+00:00）
- 浏览器走查：未做（工作令不含浏览器走查，如实标注）
- 任意后续重启会把live库B全部作业（含completed）翻STALE_INPUT、候选翻SUPERSEDED（N5后无v19存活例外）；live库B证据链随即全报废，以本导出为准。

## G8 质量与效率（pass）

- B-vs-A 主侧：比较 52 字段，一致 32，分歧 20；盲核侧：比较 52，一致 32，分歧 20（分歧分析非错误判定；逐条见JSON b_vs_a_*：divergent_details）
- A热启动：提交 2026-09-26T10:49:04，耗时 5.62h（复用文档权威与既有入库）
- B冷启动：提交 2026-09-27T05:08:35，耗时 0.78h（全新提交+逐单元取证）
- 模型用量：A 314次调用（已知usage行 0）；B 67次调用（已知usage行 66，prompt 2011217 / completion 317916 tokens，usage_unknown行不计入、不推算总量）
- 失败开销：第一代确定性作业4个已退役（实现修复前构造，系统作业无模型开销）；修复代际4个全部completed；模型作业0失败；0个失败作业（attempt内）
- 人工介入待决：A 0 字段、B 0 字段

## 附注

- 逐字段对照与三重回链（A候选ID + v275确认链field_sources + B候选ID）见 `d_comparison_cm_mh.json` 的 per_field_comparison（52条）。
- 本报告不切换任何生产路由；B的启用前置条件见结论。
