# 医学监查 Field Mapping 输入形状防护（LOOP 3.78）

**时间：** 2026-08-02 06:48 CST  
**范围：** 前端 Field Mapping 只读状态消费与合同测试；不启动服务、不调用 API/provider、不打开浏览器、不运行真实项目、不写权威运行库。

## 结论

Field Mapping 面板原先直接消费 `job_details`、候选 `structured_payload.field_mappings`、草稿 `fields`、启动/确认回执，并在多个位置使用 `|| []`、可选链或数值隐式转换。若上游返回 scalar、缺失数组、错误计数或字符串置信度，界面可能抛错、清空为假数据，或继续允许医学映射确认。

本 LOOP 新增 `frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingView.mjs`，对以下入口统一 fail-closed：

- 启动回执：批次、profile/input hash 字段类型、非负 `field_count`/`job_count`、`jobs` 数量与计数一致、job id/status；
- 状态回执：`job_details` 必须为数组，`job_count` 与其长度一致；每个 job detail 的 candidates、candidate id、`structured_payload.field_mappings` 必须为受检数组；
- 字段映射：domain、source field、recommended role、closed field kind、有限 0–1 confidence、uncertainty/user action，以及可选血缘/证据数组；
- 草稿/正式版本：draft id、非负 version、draft status、fields 数组；正式 revision 的 revision id/version/fields；
- 语义质量：closed status/disposition、显式非负计数、finding/capability 数组和状态枚举。

面板所有状态、启动、草稿编辑、正式版本读取与确认回执均先过 guard。Malformed shape 进入错误状态；不把异常集合降级成空集合，不把错误 count/版本转成 0；状态读取异常时清理旧映射状态。确认后的 activation 保存完整对象，不再只保存 `activation.state` 字符串。共享 `semanticQualityPresentation` 也会对直接传入的 malformed count/array 返回阻断态，避免绕过入口 guard 后误显示可确认。

## 验证

- `node frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingView.test.mjs`：**11 passed**；覆盖合法状态、scalar 数组、候选嵌套数组、计数不一致、字符串 confidence/count、语义质量及正式 revision；
- `node frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingState.test.mjs`：**8 passed**；
- `node frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：**35 passed**；锁定 Field Mapping 状态/启动/草稿 guard 和不再静默消费 malformed collections；
- 全部 `frontend/src/features/medical-monitoring/*.test.mjs`：**18 个文件全部通过**；
- `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_unified_risk_workbench_contract.py tests/test_frontend_timeline_contract.py`：**54 passed**；
- `npm run build`（工作目录 `frontend/`）：Vite **1921 modules transformed**，构建成功；仅保留既有大 bundle warning。

本次构建产物：

- `frontend/dist/assets/index-DCdgcMd4.js` SHA-256 `ea49eb43ef7cd9d4a80dfd7d35fa1a998b849aa3bc73fcc0a9aeb4af6fdd53ed`；
- `frontend/dist/index.html` SHA-256 `07171276f0a66d90c4086ec0830bdeb30e2ec8a8567e4f5a5b2ac340ac08c2cd`；
- `frontend/dist/runtime-build.json` SHA-256 `1091dc3037c0ab5bd8cfc77c98b0ad0a796115391db35d8ac7e4a56b067167e6`；
- `medicalMonitoringFieldMappingView.mjs` SHA-256 `74d7ce42af6da88719b113f34ea2bffd4d88fc487f8c73567b0cb114575c8e87`；
- `medicalMonitoringFieldMappingView.test.mjs` SHA-256 `ea5f8d1523aa6dd63135225aa1cea695bc2712ebb3c247a6ca22e9f4fc44b84b`；
- `medicalMonitoringFieldMappingState.mjs` SHA-256 `7c91966809ceca0b27d82b3799c0c2e5a1a0892f1d214a2765def1cd5fd1116a`；
- `medicalMonitoringFieldMappingState.test.mjs` SHA-256 `71387b8aa77eaf168905e352ee3c739c6fe2083e313cd043ab2787d0f62593bb`；
- `MedicalMonitoringFieldMappingPanel.jsx` SHA-256 `ed051b1687e4e2f89b1859ea2f5f727448f98ed1c817ef1807c0dfcb685a4583`；
- `medicalMonitoringProjectSwitchIsolation.test.mjs` SHA-256 `bcb8d24a6af5fdd51ea4a3b0c3965ef3835c8f4dbee527050f0239061d3f510d`。

## 边界与未证明项

这是前端输入形状/显示安全合同，不是后端 schema、AI 语义质量、B6 授权、aggregate/CAS、source-token lineage、真实 listing、连续全量批次、浏览器视觉验收或商业上线证据。B6 仍 `pending_review`（5 candidates、0 outcomes、2 blockers、`migration_ready=false`、`write_permitted=false`）；C13 仍 blocked；8911/5174 必须继续停止。当前 Product Design 视觉审计也未宣称完成：该技能要求本轮截图，而当前边界禁止启动 8911/5174/浏览器。

下一安全动作仍是：授权 B6 reviewer outcome → 实际 aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run；之后才能重新申请受控 runtime、三项目真实 LOOP 和浏览器/科学性验收。
