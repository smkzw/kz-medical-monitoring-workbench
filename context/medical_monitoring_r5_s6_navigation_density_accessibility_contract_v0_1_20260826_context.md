# R5-S6 Navigation / Density / Accessibility Contract v0.1 Context

日期：2026-08-26  
状态：`CANDIDATE_CONTRACT_ONLY`

## 范围

本批次只冻结 renderer-neutral 的 R5-S6 深链、canonical 返回上下文、桌面高密度与 semantic zoom、键盘和非颜色编码，以及离线性能 corpus 身份。它不实现 frontend、browser、service、security、真实项目或模型，也不启动 8911。

## 上游权威

- R5 stage：`reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md`；raw SHA 由 manifest 固定。
- 已接受 S5 contract/runtime：`artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json`、其 acceptance record 与 runtime acceptance record；raw SHA 由 manifest 固定。
- S6 机器权威：`artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/exact_contract.json`；schema、非颜色注册表和 performance corpus registry 分别由 `artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/navigation_schema.json`、`artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/audience_encoding_registry.json`、`artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/performance_corpus_registry.json` 提供。

## 冻结语义

- 深链逐项绑定 project/run/snapshot/cutoff/site/subject/risk/spine、view、axis/window、visit/event/risk-anchor/source-locator、target projection content hash 和 return-context key；目标不一致、不可投影、缺失或 artifact 缺失时 `not_emitted`，fallback policy 只有 `none`。
- 返回上下文把 canonical identity/filter/sort/page/selection/axis/window 与 ephemeral scroll/Inspector/temporary expansion/focus 分开；canonical hash 只覆盖 canonical fields，恢复必须 canonical-equivalent，不要求 URL 字节相同。
- semantic zoom 只有 `overview/detail/evidence`；overview 只能聚合低风险普通事件，critical/high/medium risk anchor 在每一级保持单独可见；density 只改变间距，不得成为隐藏内容的机制。
- 键盘绑定为闭集，所有动作 `medical_state_mutation=false`。事件使用固定域形状/短标签/线型，风险使用独立 `double_chevron_badge + outer ring + explicit severity text`，颜色仅为辅助。
- 离线性能 corpus 精确为 1000 events / 40 indicators / 300 risk anchors，cold/warm 各 7 次，latency p95、pan FPS p05；当前结果状态必须保持 `unmeasured_contract_only`。
- exact contract 只冻结四个 worker-02 contract-freeze validation path、present-evidence role、oracle categories 和 scope restrictions；不含任何 raw hash。四个 present artifact 的 raw bytes 只在 manifest 绑定。
- acyclic binding graph：exact contract -> semantic requirements/paths；quota -> `exact_contract.contract_content_hash`；manifest -> raw hashes for exact/quota/challenge/verifier/tests and other present owned artifacts；manifest excludes its own raw hash。
- 当前 worker-02 semantic-link state：`ready`；worker-02 rebind 完成前，verifier/quota checks 保持 pending，不得宣称最终 `CHECK_OK`。
- 后续 synthetic/offline S6 runtime 另用 `manifest.future_runtime_allowlist` 的十个 exact absent create-only 路径，接受前不得创建，且不解锁 frontend、browser、services、真实项目/模型、security、medical-writing 或 8911。

## 保护边界

manifest 固定 8911 stopped、medical-writing 542 文件及 inventory SHA、已接受 R1-R5 输入 immutable。当前 contract-freeze evidence 计数为 4，后续 runtime allowlist 计数为 10 且全部 absent。

worker 不发出接受 token；最终 verifier、独立 review 和 Codex acceptance 另行完成。
