# 医学监查规则发布/影子证据形状防护（LOOP 3.80）

**时间：** 2026-08-02 07:25 CST  
**范围：** 前端规则包列表/详情、影子样本与运行、谱系证据、差异、发布回执和日常就绪投影；不启动服务、不调用 API/provider、不打开浏览器、不运行真实项目、不写权威运行库。

## 结论

规则发布面板原先对多个发布链响应直接使用 `items || []`、可选嵌套 pack 或宽松的 `Number(...)`：规则包、真实影子样本、已确认运行、谱系恢复、冻结批次和日常就绪状态的 malformed/cross-project 响应可能被继续带入发布链，或把缺失身份显示成空状态。

本 LOOP 新增 `frontend/src/features/medical-monitoring/medicalMonitoringRuleReleaseView.mjs`，并让规则发布面板统一先过守卫：

- 规则包列表/详情/草稿/阶段转换/确认/发布回执：校验项目、方案版本、规则包身份、闭合状态、正整数修订、规则身份和规则包—规则一致性；后端公开视图不包含内部 `content_sha256` 时由合同明确允许，不把内部裁剪字段误当成 UI 必需字段；
- 影子样本：校验 `provisional` 状态、批次/映射身份、样本计数与数组一致、命中/未命中/不可判定状态及证据正文；后端未在每一行重复项目/规则修订字段时，仅由已验证的顶层项目/规则包上下文补足，不猜测医学字段；
- 影子运行：校验完成状态、标准/诊断样本计数守恒、结果数组长度和每条结果的判定/证据字段；列表项缺少后端裁剪的项目/规则包字段时绑定到请求的项目/规则包；
- 谱系证据：校验目标规则包、影子祖先、样本集和确认记录；确认样本集不在返回谱系中时 fail-closed；
- 差异与日常就绪：校验差异数组、project/batch identity、`ready/state_code/message/next_action`，异常就绪状态不显示旧结论；
- 面板读取/操作遇到异常形状时清空旧规则发布状态；发布链不再把 malformed collection 静默转为空数组。规则发布 UI 仍不展示 `shadow_passed`/“验证通过”等把 provisional 样本冒充可信通过的词汇。

## 验证

- `node frontend/src/features/medical-monitoring/medicalMonitoringRuleReleaseView.test.mjs`：**21 passed**；覆盖合法公开响应、后端裁剪字段补足、跨项目、规则身份、样本/运行计数、谱系确认和就绪 batch identity；
- `node frontend/src/features/medical-monitoring/medicalMonitoringRuleRelease.test.mjs`：**63 passed**；
- `node frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：**49 passed**；
- 全部 `frontend/src/features/medical-monitoring/*.test.mjs`：**20 个文件全部通过**；
- `python3 -m pytest -q tests/test_frontend_monitoring_contract.py tests/test_frontend_unified_risk_workbench_contract.py tests/test_frontend_timeline_contract.py`：**54 passed**；
- `npm run build`（工作目录 `frontend/`）：Vite **1923 modules transformed**，构建成功；仅保留既有大 bundle warning。

本次关键 SHA-256：

- `frontend/src/features/medical-monitoring/medicalMonitoringRuleReleaseView.mjs`：`2cdaa51c56b51506cded30f48e2032b71d2aa1ca22287e76bc304564fa61622c`；
- `frontend/src/features/medical-monitoring/medicalMonitoringRuleReleaseView.test.mjs`：`31d4ac8d547849a845d4352fb48dc70c0be1154d4afba34079857d1334f828a7`；
- `frontend/src/features/medical-monitoring/MedicalMonitoringRuleReleasePanel.jsx`：`3958e6d808bebc1fd907dd874dbfdbf3729d9c809e69d20fbcab06db64756f99`；
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`：`a31cbac93cccb3cea81abd3906762bfbd7fff7a92189a5ef5872611b7ee1babc`；
- `frontend/dist/assets/index-Bn83Ac4x.js`：`586ac0c93e11013cf97f92c241e2a928cf226044398bdd33cd0fe3f5146ef8df`；
- `frontend/dist/index.html`：`d33d7e3f5e74e69d88a54cfcce54e4d47cf9d405c6d879078c395c18cab0622e`；
- `frontend/dist/runtime-build.json`：`b3a8b4904ff49fce5772886bb16445301b4c4c521de80dae77b4f4645da829df`。

## 边界与未证明项

这是规则发布 UI 的输入形状/项目隔离/证据显示安全合同，不是后端影子算法正确性、规则医学科学性、真实原始 listing、连续全量批次、B6 reviewer outcome、aggregate/CAS、source-token lineage、真实 runtime、浏览器视觉验收或商业上线证据。B6 当前仍 `pending_review`（5 candidates、0 outcomes、`migration_ready=false`、`write_permitted=false`，未解决 blocker 仍为 append-only disposition chain aggregate replay 与 legacy source revision token revalidation）；C13 仍 3 个 schema-only reports 且 `activation_allowed=false`；8911/5174 必须继续停止。

下一安全动作仍是：授权 B6 reviewer outcome → 实际 aggregate snapshot/CAS replay 与 MY009 source-token revalidation → approved-input 内存 dry-run；之后才能重新申请受控 runtime、三项目真实批次 LOOP、浏览器与科学性验收。

