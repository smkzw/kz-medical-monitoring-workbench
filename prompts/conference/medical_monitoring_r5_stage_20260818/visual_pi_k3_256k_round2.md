继续同一 R5 视觉/产品设计会商会话。只读复核最终合同，不编辑文件、不启动服务或浏览器。

Hard boundaries:

- 只读审阅，不修改任何文件。
- 不启动 8911、服务、浏览器或长任务。
- 不触碰医学写作、R4、真实项目或生产路径。

Read these files only:

- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
- `artifacts/medical_monitoring_r5_contract_v0_3/challenge_registry.json`
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`
- `artifacts/medical_monitoring_r5_contract_v0_3/quota_ledger.json`
- `artifacts/medical_monitoring_r5_contract_v0_3/manifest.json`

Output file:

Write exactly one output file: `runs/conference/medical_monitoring_r5_stage_20260818/visual_pi_k3_256k_round2.md`

- `runs/conference/medical_monitoring_r5_stage_20260818/visual_pi_k3_256k_round2.md`

Codex 已采纳并裁决你上一轮的 Q1-Q4：

- Q1：固定为八个主域；`症状与疗效` 是一个主域，以症状/疗效/量表/结局/趋势 subtype 区分。
- Q2：URL 保存 canonical identity/axis/window/anchor；session client state 保存 scroll/Inspector width/临时展开；验收比较 canonical hash 与声明的 ephemeral fields。
- Q3：现有 RiskEvidenceDock 内嵌 Profile/Timeline 退役，统一进入 Subject Workspace。
- Q4：S0/S1 仅合同、adapter 和离线 audience projection；浏览器/8911 延后到 S7。

最终合同：`reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`
唯一 canonical SHA256：`763747a931dc282a99680a8ad3ae1db0b6bd3620ca63c54d9c76f7b5e1691123`

本轮新增冻结项：

- 风险等级 closed enum `critical/high/medium/low`，普通受众中文固定为 `紧急/高/中/低`；R5 不得自行升级，旧 severity 仅经冻结映射进入。
- `background treatment`、`non-drug treatment` 仅在冻结项目映射明确成立时归入 CM/治疗 subtype；否则 unknown fail-closed，禁止 `OTHER` 与 fixture/project/file-name 分支。
- 事件形状与风险覆盖层是两级独立编码；风险覆盖层唯一固定为 `double_chevron_badge`（双折角徽标）并列入全部事件禁用形状；风险直接写“域内风险类型·等级”。
- 明确 1+1 操作预算、返回上下文、八域、性能阈值、P0-P4、S0-S8 与写入边界。
- S0 只冻结 204 条后续阶段可执行 challenge specification；不冒充这些行为已在 S0 执行。每条必须在 planned stage 以真实 fixture/evaluator 或浏览器 trace 关闭。
- 当前上游不够的中心语义格、当前风险集、逐成员定量度量和 Inspector 证据叶均诚实标记具名 deferred contract；S1 后续实现，不以计数字段伪造完成。

派生证据：

- challenge registry 204 条，SHA `136d42de137a268b2cd5fa55966c7339549771296f0faa843350ff70b5219367`
- exact contract SHA `db71687f7e763bfa48e9972b8d285793838bf54b11b10d51ae410ce584a6e191`
- quota ledger 204 个唯一实例，SHA `e8897f95346a694b88e577d4ddd60205ccd4d25b1f850f4cf7cfc27a461b3d02`
- manifest SHA `5bc5c8154989975ba91e814ce18da193ddcd9063e48cef67d9c6007d46bedc35`
- normal 与优化模式 verifier 当前均 `ok=true`；fresh isolated reviewer 已给 `ACCEPT_R5_CONTRACT`（仅解锁 S1）；8911 无监听。

请以你上一轮的视觉/交互缺口为检查清单，复核这个最终 SHA 是否已经足以冻结 R5 视觉输入。重点检查：八域与 subtype 是否无第二套约定、severity 是否唯一、event/risk 非颜色编码是否消歧、深链/返回是否可实现、普通中文是否清晰、首屏与点击/密度/性能预算是否可验。

只返回：

1. `R5_VISUAL_CONTRACT_READY` 或 `REVISE_R5_VISUAL_INPUTS`；
2. 尚未关闭的 P0-P4（若无明确写无）；
3. 对 S1 的 3-8 条不可丢失实现约束；
4. 明确本结论不等于 UI、浏览器、真实项目、真实模型或生产接受。
