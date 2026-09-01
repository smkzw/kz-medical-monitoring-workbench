# 医学监查批次/来源消费形状防护（LOOP 3.79）

**时间：** 2026-08-02 07:00 CST  
**范围：** 前端“原始 listing → 来源身份 → 批次状态机”只读消费与确认回执；不启动服务、不调用 API/provider、不打开浏览器、不执行真实项目、不写权威运行库。

## 结论

批次面板原先直接消费批次列表/详情、来源注册、完整性校验、来源分类和状态变更回执。`payload.batches || []`、`detail.validation?.checks || []`、未校验的 `sources`/`domain_counts` 可能把 malformed payload 变成空列表、可冻结来源或错误的确认状态；错误的来源身份尤其可能让界面继续推进“完整全量快照”路径。

本 LOOP 新增 `frontend/src/features/medical-monitoring/medicalMonitoringBatchView.mjs`，统一校验：

- 批次列表与项目绑定：project id、批次数组、batch id/project id/state/version、expected domains、mapping revision、快照 proof 和时间字段；
- 批次详情：来源数组、来源身份/文件名/hash/大小/技术状态/警告、非负 row count 与 domain count；
- intake/transition/freeze 回执：嵌套 batch identity 与 replay 状态；
- 来源内容校验：validation id/revision/use status、检查项数组、`match/warning/mismatch/not_assessed` outcome；
- 来源分类确认：closed source class、technical status、content warnings；
- project/batch 面板所有列表、详情、导入、转换、冻结、选择和刷新路径均先过 guard。Malformed 回执会清空旧批次状态并停止继续推进；刷新失败不再产生未处理 Promise。

面板保留来源分类语义：比较文件、混合文件、格式异常、还原过渡和未知来源不能被改写成原始全量基线；处理后快照仍需 B 级医学确认，且不改变其来源身份。

## 验证

- `node frontend/src/features/medical-monitoring/medicalMonitoringBatchView.test.mjs`：**13 passed**；
- `node frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：**40 passed**；
- 全部 `frontend/src/features/medical-monitoring/*.test.mjs`：**19 个文件全部通过**；
- `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_unified_risk_workbench_contract.py tests/test_frontend_timeline_contract.py`：**54 passed**；
- `npm run build`（工作目录 `frontend/`）：Vite **1922 modules transformed**，构建成功；仅保留既有大 bundle warning。

本次关键 SHA-256：

- `medicalMonitoringBatchView.mjs`：`f70be5e9d017a65a579d3c2d8d00128410de66a9d5b960f3375f0af38ac7296b`；
- `medicalMonitoringBatchView.test.mjs`：`df446011f91e568a8ecd1e8b32cd9238ac155ca14242ea3b5888d3d86948f1ae`；
- `MedicalMonitoringBatchPanel.jsx`：`f0415f8c83565d543c36c33cfd4352aa9c8f16e34166a731597d7d30c0a9165e`；
- `medicalMonitoringProjectSwitchIsolation.test.mjs`：`a85cabe71bf2fd795dd5bf193dc4385ae9e9923fd078b9191427f54d266ffe58`；
- `tests/test_frontend_monitoring_contract.py`：`90f8e617a2590a45c10d80424fc5445ad3c9fae7c65dbd03df06d2074ecae651`；
- `frontend/dist/assets/index-CWTL8rBP.js`：`bff8ca35053bbfe8fba679fc28257b2fa78b79aaaff1b0b030f68cb6bf7c6c17`；
- `frontend/dist/index.html`：`8be3f1c727638f9cd4c8a0ab616e4f2b3199e1792c74e03ae8c17331a5f5d9db`；
- `frontend/dist/runtime-build.json`：`418e5165ca4906ed1b5e0cc06fd7eea3224067b12da178bbab93d58e7f0e21f7`。

## 边界与未证明项

这是前端批次/来源消费安全合同，不是原始 listing bytes 的真实性证明、内容校验执行、来源注册 authority、连续全量批次、字段映射语义、B6 aggregate/CAS、真实项目 runtime、浏览器/科学性验收或商业上线证据。B6 仍 `pending_review`（5 candidates、0 outcomes、2 blockers、`migration_ready=false`、`write_permitted=false`）；C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；8911/5174 必须继续停止。

下一安全动作仍为：授权 B6 reviewer outcome → aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run；之后才能重新申请受控 runtime、三项目真实批次 LOOP 和浏览器/科学性验收。

