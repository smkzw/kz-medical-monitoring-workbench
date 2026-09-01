# R5-S7 产品最小接入与真实浏览器验收合同 v0.1

状态：CANDIDATE_FOR_INDEPENDENT_REVIEW

日期：2026-08-26（CST）

执行角色：worker_01；本文件是合同架构交付，不是产品实现、8911 运行记录或最终接受记录。

## 1. 目的与不可越过的边界

本合同冻结 R5-S7 的最小产品接入路线，解决四个边界问题：

1. 已接受的 R5-S5/S6 renderer-neutral 对象如何进入现有医学监查产品；
2. 前端、后端、只读 adapter、共享身份授权代码和证据文件各自允许写哪些路径；
3. 迁移、回滚、8911 临时服务和医学写作保护如何做到可复现、可审计、可停止；
4. 后续真实浏览器和视觉角色必须提交什么证据，何时可以关闭。

本阶段只冻结合同，不执行下列动作：

- 不修改产品源码、既有路由、数据库、运行时 SQLite 或 medical-writing 文件；
- 不启动 8911、Vite、FastAPI、Playwright、浏览器、模型或真实项目；
- 不调用 AI gateway，不产生 provider/model/attempt/backend 运行记录；
- 不把旧医学监查页面的可见、复合读取结果当作 R5 权威；
- 不以本文件替代 Codex 的最终产品、浏览器、视觉、临床或监管接受。

产品入口沿用现有 `/monitoring` pathname，但由独立 R5 route-state 的 closed `view=overview|site_overview|journey|profile|timeline|evidence` 精确进入 R5；旧 `view=checklist|ae-mh` 仍进入旧页面并构成回滚路径。不得另造第二个顶层导航入口，也不得把缺失或非法 `view` 静默解释为 R5。R5-S7 通过前不替换旧默认入口；后续如切换默认入口，必须在同一份接受记录中记录前后字节摘要和可逆接线补丁。

## 2. 权威输入与接受锚点

以下文件是本合同的输入；哈希用于确认读取的是已接受的版本，不表示本 worker 接受了下游产品。

| 输入 | 用途 | 证据锚点 |
|---|---|---|
| reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md | R5 总体语义、禁止分支、浏览器预算、S7/S8 边界 | 文档 SHA-256 1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6 |
| artifacts/medical_monitoring_r5_contract_v0_3/manifest.json | R5 exact contract、challenge、quota 及生成器锚点 | contract SHA 1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6；exact raw 3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949 |
| context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_acceptance_record_20260826.md | S5 Subject Workspace / Patient Journey 合同接受范围 | ACCEPT_R5_S5_CONTRACT；contract content 803757c2993109b681b6facefc8c28e88bf2076e75950798abcce3e50d716e91；manifest content 9077286a64c0b846a46d050f7181fb1eb6067a1e1c1800b852100e42583fe747 |
| context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_acceptance_record_20260826.md | S5 离线 renderer-neutral runtime 接受范围 | ACCEPT_R5_S5_SUBJECT_WORKSPACE_RUNTIME_V0_1；S5 11 个运行时/测试路径已接受 |
| context/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1_acceptance_record_20260826.md | S6 深链接、返回、密度、键盘、非颜色、性能语义 | ACCEPT_R5_S6_CONTRACT_V0_1；contract content ba083b9a60b09560a045ef03ce7df73196467e2473ba19a9e8c7ff747ec6f4ec；manifest content d22b27cd11fedbbd059c4b99248516be704bf6f58f866d149c3641d5832f07b9 |
| context/medical_monitoring_r5_s6_navigation_density_accessibility_runtime_v0_1_acceptance_record_20260826.md | S6 离线 renderer-neutral runtime 接受范围 | ACCEPT_R5_S6_RUNTIME_V0_1；S6 10 个运行时/测试路径已接受 |
| frontend/src/App.jsx | 当前医学监查入口、全局读取与写入面、medical-writing 导航保护 | 当前产品入口只作为接线点，不能作为 R5 权威实现 |
| frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs | 现有混合读写 API 客户端 | 既有 client 同时包含 GET、POST、PATCH、下载和运行/规则/Query 写方法，不能直接注入 R5 |
| frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs | 既有监查 URL 状态 | 只有旧 project/scope/site/subject/risk/view 键，缺少 R5 run/snapshot/cutoff/spine/window/anchor 集合 |
| services/api/app/medical_monitoring_router.py | 现有医学监查后端路由 | 读写路由共存；R5 不在此文件追加入口 |
| services/api/app/monitoring_read_action_contract.py | 现有只读授权交接 seam | R5 只允许增加三个 surface 映射，不修改写权限和角色矩阵 |
| services/api/app/monitoring_runtime_principal.py、services/api/app/monitoring_runtime_route_context.py、services/api/app/monitoring_identity_authorization.py | 服务端验证身份、路由上下文、动作授权 | R5 只能使用服务端验证的 principal，不接受 client actor |
| services/api/app/runtime_readiness.py | 现有运行时 readiness 和 API contract 版本 | 不改 medical-writing contract middleware；8911 readiness 使用既有 endpoint |

### 2.1 从 S5/S6 继承的语义

产品 adapter 只能投影已接受的 typed authority 和 renderer-neutral 对象。它不得在浏览器中重算事实、风险级别、分母、覆盖率、来源、访视日期或共识。

必须原样继承以下约束：

- 八个医学域固定为 AE、MH、CM、IP 给药、检验与检查、住院与操作、症状与疗效、方案符合性；未知域或非法 domain/subtype 组合 fail closed；
- 严重度映射固定为 critical/high/medium/low 到 紧急/高/中/低；旧 severe/moderate/mild 只能按已冻结映射转换；不得把 high 升为 critical；
- 缺失、不可评估、不适用、partial、truncated、failed 不得变成 0、空值或无风险；
- 项目、中心、受试者、risk instance、run、snapshot、cutoff 和 authority hash 必须在同一份权威 receipt 中相互绑定；
- 中心视图没有 score、rank、top-N；risk inspector 不泄露 provider、model、attempt、backend、内部 hash 或运行日志；
- 受试者默认视图是「受试者医学旅程」，与「指标趋势」「事件明细」共享同一 temporal spine、window、selection；
- 深链接找不到精确 target 时显示不可用/待确认状态，禁止 nearest fallback、自动吸附到相邻访视或用当前 source 替代冻结 source；
- 键盘选择、密度切换、semantic zoom、返回和 Inspector 展开都是非医学状态写入。

## 3. 现状检查与产品切入点

当前产品入口的相关事实如下：

1. App.jsx 直接挂载旧版 MedicalMonitoringScopeSummary、MedicalMonitoringAssurancePanel、MedicalMonitoringBatchPanel、MedicalMonitoringRiskChecklist 和旧 SubjectViews。旧面板中存在 Checklist、待行动等 R5 禁止的普通页面词语，不能作为新 R5 页面组件。
2. App.jsx 既有医学监查读取包括模块 summary、risk snapshot、taxonomy、raw-intake、subjects、subject monitoring、workbench-inbox、AI runs；同时保留 workbench actions、risk-disposition、AI runs from sources、provider/profile/role 设置等写入口。R5 不得沿用这条混合调用链。
3. medicalMonitoringApi.mjs 虽然会移除 client actor 字段，但仍提供大量 POST/PATCH/下载、批次、日运行、规则、协议、Query 和候选决策方法。R5 adapter 不得 import 这些写方法，也不得以“调用后不点击”为保护。
4. medical_monitoring_router.py 的旧版 GET 和写路由共存；main.py 对一部分 dashboard、inbox 和 AI-run 复合读取明确使用 fail-closed policy-gap。R5 使用独立 router 和独立 surface，不向旧路由补权限缺口。
5. 当前 route state 没有完整 R5 identity；仅保留 project_id、旧 scope、subject/site、risk key、view、snapshot 等有限键。R5 使用独立 route state 文件，避免把旧 route 的降级行为带入新深链接。

结论：最小安全接入是「新增 R5 feature + 新 GET-only router + 一个 App route branch」，而不是改造旧页面或扩展混合 API。

## 4. 精确、闭合的写入 allowlist

下表是未来实现阶段的闭合集合。除列出的文件外，不得创建、修改、删除或重命名任何产品、服务、测试、证据或接受记录文件。目录名不构成通配符授权。

### 4.0 只读输入集合

以下文件只允许作为 source/contract 输入读取，不能由 S7 实现重新生成、覆盖或当作运行时写入目标：

- poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_adapter.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_contracts.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_navigation.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_accessibility.py
- poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_validator.py
- artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json
- artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json
- artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json
- artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/exact_contract.json
- artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/navigation_schema.json
- artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/audience_encoding_registry.json
- artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/performance_corpus_registry.json
- artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/manifest.json

S5/S6 tests、fixtures 和 challenge artifacts 只能用于离线验证，不得被 product adapter 动态 import 作为事实来源；fixture/path/file name 不是 authority。adapter 的真实输入必须由服务端只读 dependency 注入并经 authority receipt 验证。

### 4.1 前端 allowlist

| 精确路径 | 允许内容 | 禁止内容 |
|---|---|---|
| frontend/src/App.jsx | 增加 R5 Page import、`/monitoring` 下 R5 closed-view 分支、返回旧入口的最小接线，并在 R5 分支短路旧 monitoring summary/inbox/AI-run/subject/raw-intake effects | 不改 medical-writing guard、写入 handler、旧监查组件语义；R5 路由不得触发旧 monitoring effects 或 AI gateway |
| frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx | R5 项目总览、中心/受试者选择、Inspector、Subject Workspace 三视图、返回/键盘/非颜色交互 | 不直接 fetch 旧 endpoint；不产生事实或风险派生；不调用写 API |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs | 仅 GET 请求、响应 schema/identity/content hash 校验、accepted projection 的中文投影 | 不包含 POST/PATCH/PUT/DELETE/download/FormData/actor/provider/model/AI gateway；不 fallback 到旧 API |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs | R5 canonical identity、canonical return state、ephemeral state 分离、精确 target 验证 | 不复用旧 route 的 nearest/degrade 语义；不把 scroll/Inspector width 写入医学状态 |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css | R5 layout、事件形状、双折角徽标+外圈、非颜色编码、1440x900/1600x1000 自适应 | 不改全局 CSS、medical-writing 样式或旧监查组件样式 |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Fixtures.mjs | 仅离线 synthetic fixture 和 identity-negative fixture；不得含真实项目/真实受试者/真实 provider | 不作为产品生产数据，不在浏览器中替代后端权威 |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.test.mjs | GET-only、身份、digest、fail-closed/no-nearest、错误状态单测 | 不调用外部服务，不创建真实项目 |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.test.mjs | canonical/ephemeral、精确深链接、返回、窗口/锚点和非法状态测试 | 不接受缺失 identity 的隐式 nearest |
| frontend/src/features/medical-monitoring/r5/medicalMonitoringR5ProductContract.test.mjs | 对产品依赖、禁止词、HTTP method、文件边界的静态契约检查 | 禁止词检查只扫描 R5 production source、App route branch 和最终 DOM；测试/合同/证据文件中的规则字符串不算用户文案；不把字符串存在、配置项存在或非空响应当作浏览器验收 |

前端实现不得修改以下既有文件：frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs、medicalMonitoringRouteState.mjs、任何既有监查 panel/SubjectViews、任何 frontend/src/features/medical-writing/ 文件。若接线确实要求修改旧 route/API，必须先由 Codex 更新本合同的 allowlist 和前后 digest；不能在实现中临时扩大。

### 4.2 后端 allowlist

| 精确路径 | 允许内容 | 禁止内容 |
|---|---|---|
| services/api/app/medical_monitoring_r5_product_router.py | 三个 R5 GET endpoint、query 白名单、服务端身份/授权交接、响应 envelope | POST/PATCH/PUT/DELETE、写 service、数据库迁移、旧 router 复用写入口 |
| services/api/app/medical_monitoring_r5_product_adapter.py | 把 accepted R5/S5/S6 typed objects 转成 R5 product read model；计算并绑定 source/response digest | 直接读取前端文件、fixture/path 名冒充 authority、重算医学事实、provider/model 调用、SQLite 写入 |
| services/api/app/main.py | 一个新 router import 和一个 include；必要的 dependency wiring | 任何既有 endpoint、medical-writing middleware、AI gateway、runtime store、旧监查 router 改写 |
| services/api/app/monitoring_read_action_contract.py | 增加 r5_overview、r5_subject_workspace、r5_source_evidence 三个只读 surface，并映射到既有 READ_MONITORING 或 READ_SOURCE_EVIDENCE；加入项目 target surface | 不增加新的 write action；不改变 READ_ACTIONS、WRITE_ACTIONS、角色矩阵、reauth、signature 或 audit 规则 |

后端不得修改 services/api/app/medical_monitoring_router.py、monitoring_identity_authorization.py、monitoring_runtime_principal.py、monitoring_runtime_route_context.py、runtime_readiness.py。若实际实现发现必须修改这些共享安全文件，应暂停并要求 Codex 重新冻结 allowlist。

### 4.3 后端测试 allowlist

| 精确路径 | 允许内容 |
|---|---|
| tests/test_medical_monitoring_r5_product_adapter.py | adapter 纯函数、typed projection、digest、identity 和 no-write 测试 |
| tests/test_medical_monitoring_r5_product_router.py | FastAPI route method、principal、route context、read handoff、query/body 拒绝、响应 identity 测试 |
| tests/test_medical_monitoring_r5_product_allowlist.py | 精确路径、导入面、禁止写方法、medical-writing import/route 排除和 inventory gate 测试 |

现有 S5/S6 POC 测试不在本次产品 allowlist 内，不得为接入而修改或重新生成。

### 4.4 证据和接受记录 allowlist

以下文件只在 Codex/runner 执行 S7 时按既定职责生成；worker_01 本阶段不生成：

| 精确路径 | 内容 |
|---|---|
| evidence/medical_monitoring_r5_s7_product_integration/allowlist_manifest.json | 代码、测试、路由、运行时和证据的实际路径与 raw SHA-256 |
| evidence/medical_monitoring_r5_s7_product_integration/identity_trace.json | 每一次成功/失败读取的最终 identity tuple、digest、HTTP status、fail-closed reason |
| evidence/medical_monitoring_r5_s7_product_integration/api_read_trace.json | 仅列 GET method、URL 去敏摘要、request/response contract、没有写请求的证据 |
| evidence/medical_monitoring_r5_s7_product_integration/protected_inventory_before.json | medical-writing 保护区 before count/SHA 和错误列表 |
| evidence/medical_monitoring_r5_s7_product_integration/protected_inventory_after.json | 同一算法的 after count/SHA 和错误列表 |
| evidence/medical_monitoring_r5_s7_product_integration/8911_lifecycle.json | preflight、启动、readiness、server identity、浏览器阶段、teardown、最终停止证据 |
| evidence/medical_monitoring_r5_s7_product_integration/browser_matrix.json | 视口、fixture/state、角色、deep link、操作预算、性能、截图和最终 identity |
| evidence/medical_monitoring_r5_s7_product_integration/console_network.json | 两个视口的 console、page error、request/response、失败/阻断记录 |
| evidence/medical_monitoring_r5_s7_product_integration/performance.json | 冷/暖导航、next-frame selection、连续 pan 的真实测量和环境 |
| evidence/medical_monitoring_r5_s7_product_integration/forbidden_terms.json | source/DOM/截图 OCR 适用的禁止词扫描结果 |
| evidence/medical_monitoring_r5_s7_product_integration/build_regression.json | production build、focused/adjacent regression、失败分类 |
| context/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_acceptance_record_20260826.md | Codex 最终接受或 REVISE 的外部记录；必须绑定本合同和所有证据 raw SHA |

runs/execution/mm_r5_s7_product_integration_browser_contract_v0_1_20260826/worker_01.md 由 runner 管理，不属于 worker 写入 allowlist，本 worker 不创建或修改。

## 5. 只读 API 合同

### 5.1 路由集合

R5 后端 prefix 固定为 /api/projects/{project_id}/modules/medical-monitoring/r5。业务路由只允许以下三个 GET 路径：

1. GET /api/projects/{project_id}/modules/medical-monitoring/r5/overview
2. GET /api/projects/{project_id}/modules/medical-monitoring/r5/subject-workspaces/{subject_id}
3. GET /api/projects/{project_id}/modules/medical-monitoring/r5/source-evidence

R5 浏览器阶段的业务 API 请求闭集为上述三个路径，以及仅用于启动 readiness 的 GET /api/runtime-readiness。静态资源、浏览器认证 transport 和 CORS 预检不属于业务 API；不得出现旧 monitoring summary、risk snapshot、taxonomy、raw-intake、subjects、subject monitoring、workbench-inbox、AI-run、batch、daily-run、rule、protocol、assurance、Query 或 provider/profile/role settings 请求。

请求规则：

- 只接受 GET；请求 body、POST、PUT、PATCH、DELETE、下载和表单均拒绝；
- OPTIONS 如果由 web 框架自动产生，只能是无业务副作用的预检，不得进入 adapter 或 service；
- 未知 query 参数返回 422；禁止透传任意 filter、sort、page、actor、provider、model、attempt、backend、debug 或 raw path；
- path 参数必须按 URL 编码传输，服务端先 canonicalize，再对照 authority packet；不能从 path 文本推断医学事实；
- 未授权、身份缺失、租户/项目越界、source 未绑定、snapshot/cutoff 不一致、projectable 集合之外的 target 均 fail closed；
- 旧 endpoint 返回的当前 source、当前 risk、workbench inbox、AI-run、raw-intake 或旧 subject payload 不得作为 R5 fallback。

### 5.2 query 白名单与分组约束

overview 允许的 query key 只有 run_ref、snapshot_ref、cutoff_ref。三个 key 可以全部缺省，仅用于首次取得服务端当前 authority receipt；一旦任一存在，三者必须同时存在且精确匹配。首次响应返回的 identity 以后必须完整带入 deep link。

subject-workspaces/{subject_id} 允许的 query key 只有：

- 必填：run_ref、snapshot_ref、cutoff_ref、site_ref、spine_ref、window_start、window_end；
- 可选：risk_instance_ref、risk_anchor_ref、visit_ref、event_ref。

必填 key 缺一返回 422；可选 target 如果不属于该 subject 的同一 packet 返回不可用，不降级到相邻 event/visit。

source-evidence 允许的 query key 只有 run_ref、snapshot_ref、cutoff_ref、risk_instance_ref、source_locator_ref，五者均必填。服务端必须验证 query 中的 source locator 与冻结 snapshot 的 locator 相同；当前 source 或同名 source 不能替代。

### 5.3 response envelope

每个成功响应都必须包含以下顶层字段；字段值由 accepted R5/S5/S6 contract 决定，adapter 不得添加未冻结的医学语义字段：

| 字段 | 约束 |
|---|---|
| schema | 固定为 medical-monitoring-r5-s7-product-read-model-v0.1，并纳入 allowlist manifest |
| authority_receipt | 包含 project、run、snapshot、cutoff、authority/source/visibility digest 和 projectable 状态 |
| identity | 完整 identity tuple，至少包含本节 6.1 所列字段 |
| projection | 已接受的 R5 project/center/current-risk 或 S5/S6 subject workspace projection |
| counts | 由同一 authority receipt 产生的 query/clue/center pattern/individual risk/affected subject/event 等分立计数；不得前端重算 |
| source_refs | 仅指向已绑定 locator/ref；不泄露未 projectable/hidden 集合 |
| response_snapshot_sha256 | 对 canonical response bytes 的小写 SHA-256 |
| read_handoff | 由只读 action contract 生成的 public handoff；raw session/idempotency material 不出现在响应 |

overview 不得返回 subject workspace 全量事件以规避按需读取；subject-workspaces 只返回该 subject 的同一 spine/window；source-evidence 只返回精确 locator 对应的证据片段和 lineage。所有响应必须声明 read_only=true、mutation_applied=false、persisted=false，并且服务端的 aggregate/CAS version 前后相等。

## 6. adapter、身份与状态边界

### 6.1 完整 identity tuple

每个成功 R5 API 读取对应的 `identity_trace.json` 记录都必须保存以下完整 tuple：

tenant_id, project_ref, run_ref, snapshot_ref, cutoff_state, cutoff_ref, site_ref, subject_ref, risk_ref, risk_instance_ref, spine_ref, view, axis_mode, window_start, window_end, visit_ref, event_ref, risk_anchor_ref, source_locator_ref, target_projection_content_hash, return_context_key, authority_hash, source_snapshot_sha256, response_snapshot_sha256, principal_identity_hash, authorization_decision_sha256, audit_id

浏览器矩阵逐行的 `final_identity_tuple` 是用户可见 target 的计划子集，固定为 `project_id/run_id/snapshot_id/site_id/subject_id/risk_instance_id/risk_key/spine_id/source_locator_ref`；它不得承载 tenant、principal、authorization、audit 或 hash。每行用 `console_network_assertion.evidence_id` 唯一连接到 `identity_trace.json` 的完整 tuple。执行时必须机械断言：逐行非空的九项公共 target 与关联完整 tuple 经 6.4 映射后完全相等，且关联完整 tuple 的其余必填字段齐全。没有该关联 trace 的行失败，不得仅凭截图或 URL 声称 identity 通过。

其中：

- tenant_id、principal 原文、session、idempotency 原文只留在服务端审计/内存交接中；前端只接收必要的 hash/public handoff；
- 项目 path 和服务端 canonical project 必须相等；用户输入的别名不得改变 receipt 中的 project_ref；
- risk_ref、risk_instance_ref、spine_ref、source_locator_ref 任何一个与 packet 不一致都返回不可用；
- target_projection_content_hash 是深链接 target 的权威内容 hash，不是前端新生成的 hash；
- 同一页面展示的 cutoff、coverage、change band、current high/medium 和数量必须来自同一 authority receipt；
- 深链接不可用时只显示中文的“当前定位无法确认，请返回上一级”类状态，并保留 requested identity；禁止显示邻近 risk 或当前 source。

### 6.2 服务端授权交接

adapter 的固定顺序：

1. 从 host 的 server-verified envelope 得到 MonitoringAuthenticatedPrincipal；
2. 用 build_monitoring_runtime_route_context 绑定 canonical tenant、project 和 surface action；
3. 用 authorize_monitoring_action 完成只读授权；
4. 从只读 service 取得 immutable source snapshot、CAS/aggregate version 和 typed authority；
5. 生成 server-owned read handoff，绑定 source_snapshot_sha256、response_snapshot_sha256、audit id 和不变的 CAS；
6. 调用纯 adapter 生成 R5 product response，验证 response identity 与 route identity 完全一致；
7. 返回 response；任何一步失败都不调用写 service，也不转换为旧版成功响应。

R5 不解析 query/header/cookie 中的 actor、bearer token、client session 或 provider/model。server_actor 只能来自 MonitoringAuthenticatedPrincipal。不得修改 monitoring_runtime_principal.py 的 server-verified 边界。

### 6.3 前端 R5 adapter

前端 adapter 只有一个私有 GET transport 和三个对应方法。它必须：

- 每次请求发送 Accept: application/json，不发送 actor；
- 验证 HTTP status、schema、required fields、identity tuple、response digest 和 read-only flags；
- 将八域、严重度、非值状态、日期状态、risk overlay、事件形状映射到中文投影；
- 只执行列表选择、视图切换、窗口显示和 source drawer 展开，不计算风险或事实；
- 对任何 mismatch 抛出可区分的 fail-closed error，页面展示不可用状态；
- 不 import medicalMonitoringApi.mjs，不 import 旧 batch/daily/rule/assurance/Query 写模块；
- 不把异常、空数组、0 计数、请求失败或未返回字段解释为无风险。

### 6.4 route state

R5 独立 route state 的 canonical keys 固定为：

project_ref, run_ref, snapshot_ref, cutoff_state, cutoff_ref, site_ref, subject_ref, risk_ref, risk_instance_ref, view, spine_ref, axis_mode, window_start, window_end, visit_ref, event_ref, risk_anchor_ref, source_locator_ref, return_context_key

canonical state 还可以包含 S6 已接受的 filter/sort/page/selection anchor，但不能删除上述 identity。ephemeral state 只允许：

scroll_refs, inspector_width, inspector_expanded, temporary_expansion_refs, focus_ref

URL 只承载 canonical identity、view、window、anchor 和 return key；ephemeral state 可以在当前页面内恢复，但不能伪装为医学事实或 authority。浏览器返回、刷新和深链接均重新验证 packet membership；不允许最近匹配。

公共 URL、前端 canonical state 与后端 API 的字段方言固定按下表一一转换，不允许其他 alias：

| 公共 URL | canonical state / API | 规则 |
|---|---|---|
| `project_id` | path `{project_id}` 与 `project_ref` | URL path/query 项目必须相等；响应 receipt 再确认 |
| `run_id` | `run_ref` | 必填、原样传输 |
| `snapshot_id` | `snapshot_ref` | 必填、原样传输 |
| `cutoff` | `cutoff_ref` | 必填；`cutoff_state` 只来自响应，不由 URL 推断 |
| `site_id` | `site_ref` | scope 为 site/subject 时按合同必填 |
| `subject_id` | path `{subject_id}` 与 `subject_ref` | 两处必须相等 |
| `risk_key` | `risk_ref` | 风险聚焦时与 `risk_instance_id` 同时必填 |
| `risk_instance_id` | `risk_instance_ref` | 风险聚焦时必填 |
| `spine_id` | `spine_ref` | subject scope 必填 |
| `start` / `end` | `window_start` / `window_end` | 仅 ISO 日期；两者同时存在 |
| `view`、`axis_mode`、`visit_ref`、`event_ref`、`risk_anchor_ref`、`source_locator_ref`、`return_context_key` | 同名 canonical 字段 | closed enum 或 exact member ref |

`scope=trial|site|subject` 是页面编排字段而非 authority identity，因此列入每条 deep link 的 presence policy，但不列入 `canonical_deep_link_fields` 或 API identity tuple；它只能由必填 target 组合验证，不能覆盖响应身份。矩阵沿用公共 URL 名，adapter 只在请求边界执行上表的确定性重命名；任何缺失、重复、冲突或未知 query key 均 fail closed。

## 7. 医学写作保护合同

### 7.1 路径、接口和运行时保护

R5 实现的强制保护如下：

- 不修改任何路径包含 medical-writing 或 medical_writing 的文件；
- 不修改 frontend/src/features/medical-writing/、services/api/app 中路径含 medical_writing 的既有文件、既有 writing reference 文件或 packages contract；
- 不修改 packages/contracts/workbench_contracts/runtime_contract.json；
- 不改变 API_CONTRACT_VERSION=medical-writing-api-2026-07-17.1、X-Workbench-Api-Contract middleware 或 /medical-writing path 判定；
- 不新增指向 medical-writing 的 import、route、navigation guard、write handler 或 runtime database；
- 不调用现有 /api/projects/{project}/workbench-inbox 写接口、risk-disposition、AI run creation、source content mutation 或任何 medical-writing POST/PATCH；
- 不把 R5 失败导航到 writing page；writing guard 和 writing query keys 保持 byte-stable。

### 7.2 可复现 protected inventory

before/after 必须使用同一算法。算法来源是 S6 verifier 和已接受的 S5 public-authority boundary：

- workspace root 是当前 workbench 根目录；
- roots 精确为 deploy、frontend、packages、runtime、services；
- 以相对 workspace 的 POSIX 路径运行正则 medical[-_]writing；
- 使用 os.walk(root, topdown=True, followlinks=False)；directory names 和 file names 逐层排序；
- 对匹配路径执行 task-scoped symlink resolution 后以 stat.S_ISREG 判断 regular file；非 regular file 不计入；
- 每个匹配 regular file 读取 bytes，计算小写 SHA-256；
- 按 UTF-8 path byte order 排序；
- 聚合 payload 为每一行 relative_path_utf8 + NUL + lowercase_file_sha256_ascii + LF 的拼接，再计算 SHA-256；
- 只输出 count、aggregate SHA 和 error 列表用于证据；除定位失败所需信息外，不把 medical-writing 文件内容写入证据。

accepted baseline：

- file count：542
- aggregate SHA-256：feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca

before 与 after 必须 count 和 aggregate SHA 完全相同。任一差异都是 P0/REVISE；不得为了“修复”差异而覆盖、删除、回滚或重新生成 protected 文件。除该 aggregate gate 外，还要逐项检查 protected runtime SQLite、WAL/SHM、durable jobs 和既有 writing contract 的 raw SHA 未变。

## 8. 迁移、发布和回滚

### 8.1 迁移分阶段

| 阶段 | 允许动作 | 退出条件 |
|---|---|---|
| M0 冻结 | 读取输入、确认 allowlist、记录 current raw SHA、执行 protected before inventory、确认 8911 无 listener | 输入和 boundary 与本合同一致 |
| M1 新增代码 | 只创建 4.1、4.2、4.3 列出的新文件，并对 App.jsx/main.py/read-action seam 做最小接线 | focused unit/contract tests 通过；旧文件和 protected inventory 未变 |
| M2 离线 product probe | 使用 synthetic/offline packet 检查 response schema、identity、route mismatch、no-nearest、禁词和无写请求 | 所有负例 fail closed；不产生服务/模型/项目写入 |
| M3 临时浏览器 | 只在 M0/M1/M2 通过后启动隔离 8911，运行真实浏览器任务和截图/console/network/performance 证据 | browser matrix、两个视口、生命周期和性能证据齐全 |
| M4 关闭 | 停止进程组，验证 8911 无 listener，执行 protected after inventory、raw SHA、build/regression 和 evidence manifest | 所有 P0-P4 清零或明确 REVISE，不在 pending 状态伪装完成 |

不允许数据库 schema migration、SQLite 迁移、数据复制回写、R4/R5 accepted POC 修改、真实项目注册、provider/model 配置改变或 production deployment。R5 的“迁移”只表示新增 route/adapter 和可撤销的 UI 接线。

### 8.2 回滚

触发条件包括任何写请求、protected inventory drift、identity mismatch、旧 endpoint fallback、深链接 nearest、浏览器 console/network P0、8911 未停止、真实项目/模型意外出现或 P0-P4 未清零。

回滚顺序固定：

1. 立即停止浏览器任务和 8911 进程组；确认 connect_ex(127.0.0.1, 8911) != 0；
2. 保留 logs、screenshots、network、console、before/after inventory 和 raw SHA，不删除失败证据；
3. 从 App.jsx 移除唯一 R5 route import/branch，从 main.py 移除唯一 R5 router include；
4. 删除仅由本阶段创建且在 4.1/4.2 中列出的 R5 新文件；不得删除、重置或覆盖既有文件；
5. 若 M1 对共享 monitoring_read_action_contract.py 做了最小 delta，按记录的 inverse patch 恢复；恢复后重新计算该文件 raw SHA；
6. 重新执行旧入口加载/medical-writing route smoke 和 protected after inventory；
7. 在 acceptance record 标记 REVISE，写明首个违反的 contract id、路径、HTTP method、identity 或进程证据。

不得使用 git reset --hard、宽范围 checkout、递归删除、整目录替换或以旧版本文件覆盖用户现有修改。

## 9. 8911 临时生命周期

本阶段不启动 8911。后续 M3 才允许一次临时生命周期；每次重试必须是经 Codex 授权的同一 run 内恢复，不得并行启动第二个 8911。

### 9.1 preflight

在启动前记录：

- lsof -nP -iTCP:8911 -sTCP:LISTEN
- 一个 Python socket connect_ex(("127.0.0.1", 8911)) 结果，必须非 0；
- 5174 或实际 frontend port 是否空闲；
- workspace protected before inventory；
- accepted code/input raw SHA；
- no running uvicorn/Vite/Playwright/model process owned by this run。

发现既有 listener 时停止 M3，不杀未知进程，不借用既有服务。

### 9.2 启动与隔离

仅允许使用临时目录中的 runtime：

WORKBENCH_RUNTIME_DIR=<S7 临时目录> python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911

实际启动命令、Python 可执行文件、临时目录绝对路径、进程组 ID 和环境摘要写入 8911_lifecycle.json；secret/token 不写入证据。临时目录必须位于 /private/tmp 或 runner 明确分配的临时根，不能是 workbench 的 runtime/，不能连接真实 user_projects.sqlite3 或 medical-writing SQLite。

启动后只接受：

1. GET http://127.0.0.1:8911/api/runtime-readiness 返回 ready；
2. R5 overview 返回预期的 server identity、schema、synthetic fixture/project binding、authority digest；
3. response 的 project/run/snapshot/cutoff 与 browser fixture 完全一致。

/api/health 不是 R5 authority；不得把 health 200 当作 server identity 或医学数据可用。

### 9.3 teardown

浏览器成功、失败、超时或异常都必须执行 finally teardown：

- 停止进程组并等待退出；
- 再次执行 lsof、socket connect_ex 和进程检查；
- 最终必须 connect_ex != 0、无 8911 LISTEN、无本 run 的服务子进程；
- 保留临时运行证据和摘要；不把临时 SQLite 复制回 workspace；
- 8911 未停止时，S7 不得形成 accepted record。

## 10. 中文用户语义和医学写作保护

R5 普通页面的用户可见标签要短、自然、医学监查可理解。推荐固定投影：

- 项目总览、风险概览、中心概览、受试者医学旅程、指标趋势、事件明细、来源证据；
- 紧急、高、中、低；当前风险、变化、覆盖范围、数据截止时间；
- 依据、发现、建议；Query 草稿固定三部分为「依据」「发现」「行动项」，只有适用时显示 PD；
- 日期待确认、来源待确认、当前定位无法确认等明确状态。

普通页面禁止出现以下 R5/S5 已冻结的词：

已记录事项、正式事实、候选信号、通用风险点、只读xx、Checklist、待行动、未读

同时禁止把以下内部技术词放在普通页面、空状态、tooltip 或按钮中：attempt、provider、model、backend、原始 UUID、session、audit、fixture、test、debug、raw path、内部 hash。必要的技术信息只进入去敏后的 console/network/evidence，不进入用户语义。

浏览器扫描必须覆盖 source text 和最终 DOM；如果截图 OCR 是接受需要，则一并扫描截图。规则名本身可在工程证据中出现，但不能泄露到普通页面。

## 11. 后续浏览器验收合同

本节是后续 Codex/worker_02/视觉角色的输入，本 worker 不执行浏览器。

### 11.1 每行 browser matrix 的固定字段

机器矩阵 `row_field_contract` 与每一个 task/state 行必须恰好包含以下 canonical 字段：

`id`, `viewport`, `fixture_state`, `role_task`, `starting_deep_link`, `required_visible_evidence`, `major_operation_budget`, `timing_performance_assertion`, `keyboard_non_colour_assertion`, `forbidden_terms`, `screenshot_id`, `console_network_assertion`, `final_identity_tuple`, `teardown_dependency`

运行时证据不得改写计划矩阵；按下列唯一映射生成独立 evidence row：`id→stable_case_id`，`fixture_state→fixture_or_state`，`role_task.role→user_role`，`role_task.task→user_goal`，`starting_deep_link→deep_link`，`final_identity_tuple→expected_visible_identity`，`required_visible_evidence→expected_visible_evidence`，`major_operation_budget.maximum→max_major_operations`，`keyboard_non_colour_assertion→keyboard_path/non_colour_signal`，`screenshot_id→screenshot_path`，`console_network_assertion.evidence_id→console_path/network_path`，`timing_performance_assertion.global_synthetic_profile→perf_sample_id`，`teardown_dependency.lifecycle_id→teardown_status`。实际 path/status/timestamp/count 只写运行证据，不能回填为“已测量”到本冻结矩阵。

不得用“测试通过”“页面有数据”“response 非空”替代这些字段。

### 11.2 最低任务与操作预算

- risk card 到正确 Subject Workspace 和风险时间锚：最多 1 次 major operation；
- 已定位 risk 到 listing row/cell 或 protocol/IB source：最多再 1 次 major operation；
- 三个受试者视图切换各 1 次操作，不丢失同一 spine、window、selection；
- browser back/return 一次操作，canonical return 100% 恢复；
- scroll 偏差不超过 24 px，Inspector width 偏差不超过 8 px；
- 1440x900 首屏在 10 秒内能辨认 project identity、cutoff、coverage、change、当前全部 high 和 medium；
- 1440x900 与 1600x1000 均要有全屏截图，且截图中的 identity 与 trace 相符；
- medium/high risk 不得因折叠、分页、密度或 viewport 被隐藏；low 可折叠但不能伪装计数。

### 11.3 性能证据

沿用 R5-S6/R5 v0.3 的冻结 corpus：1000 events、40 indicators、300 risk anchors。使用 lockfile 对应 Playwright/Chromium，从新 browser context 冷启动（无 HTTP cache），同一 context 第二次 warm navigation；每项 7 trials，报告 nearest-rank p95。

必须测量并记录硬件、OS、CPU/RAM、浏览器/Node/Python 版本和 commit/raw manifest：

- cold navStart 到所有 controls enabled 不超过 2.5 s；
- warm 不超过 1.5 s；
- pointer/keyboard event 到下一帧 canonical selection 不超过 100 ms；
- continuous pan p05 不低于 30 fps。

失败时必须显示真实 loading/degraded/error 状态，不能隐藏风险、伪造通过、降采样后声称 corpus 通过或用静态截图替代 runtime。

### 11.4 console/network

每个 case 都记录：

- page error、console error/warn、unhandled rejection；
- 所有 request/response method、status、route family、duration、是否写 method；
- 关键 response 的 schema/identity/digest 检查结果；
- blocked request 及其 fail-closed reason；
- 最终 route URL 和 canonical return state。

出现 POST/PATCH/PUT/DELETE、下载、未声明 URL、client actor、provider/model、source substitution 或 401/403 被静默吞掉，case 失败。

## 12. 后续用户指定视觉角色与关闭条件

视觉/浏览器阶段使用用户指定的角色身份，不能把它们改名、换成未声明模型或将结果冒充 Codex 接受：

1. codebuddy cli/hy3(max)
2. pi/cms-router/minimax-m3
3. pi/google-antigravity/gemini-3.7-flash:high

每个角色必须：

- 使用 fresh role session；
- 从零打开真实产品、完成实际登录/入口定位/交互，并使用当前 screenshots/DOM/network 证据；
- 不用自身生成的医学监查内容替代产品真实后端 projection；
- 报告路径、浏览器版本、视口、实际操作、发现的 P0-P4 和证据文件；
- 只提供独立观察，不自行关闭产品 acceptance。

关闭条件：

- 三个角色的可执行任务均完成，所有 P0-P4 已由 Codex 逐项复核并清零，或形成明确 REVISE；
- 1440x900 和 1600x1000 截图、console/network、performance、identity 和 teardown 证据齐全；
- GET-only、no-write、no-nearest、S5/S6 identity、中文禁词和 protected inventory gates 全部通过；
- 8911 最终无 listener；
- Codex 完成最终产品/浏览器/视觉/临床语义接受并绑定 acceptance record。

本 worker 不启动或管理上述角色，不作视觉结论。

## 13. 接受门槛与失败分类

S7 只能产生两类明确结果：

- ACCEPT_R5_S7_PRODUCT_INTEGRATION_BROWSER_V0_1：所有闭合 allowlist、只读/身份、医学写作保护、browser、performance、console/network、8911 teardown 和独立角色证据均通过；
- REVISE_R5_S7_PRODUCT_INTEGRATION_BROWSER_V0_1：任一门槛失败，记录首个失败路径、方法、响应/进程证据和最小修复范围。

以下任一项直接 P0/REVISE：

- 任何未列出的产品/服务/测试/证据路径被修改；
- 任意 R5 UI 或 adapter 触发写 API、client actor、provider/model 或 AI gateway；
- 任何前端重算风险/事实/分母/日期，或以旧 endpoint/当前 source/nearest target fallback；
- identity tuple 不一致，hidden/non-projectable target 泄漏；
- medical-writing protected count/SHA、contract/header、SQLite/WAL/SHM 或导航 guard 变化；
- 8911 启动前已有 listener、结束后仍监听，或运行时使用 workspace/真实项目/真实模型；
- 首屏或截图隐藏 medium/high risk，console/network 证据缺失，或性能用静态/伪造数据宣称通过；
- ordinary page 出现冻结禁止词或内部技术词。

## 14. 当前阶段记录

本合同绑定的机器可执行验收矩阵为：

- 路径：`artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json`
- 状态：`planned_unmeasured`，不得解释为任何浏览器 case 已执行；
- raw SHA-256：`6a5f8db3146ab170d1c186bd3478a3c98955070883a5e81b18383800c721ab7e`；
- 结构：13 个 required state × 2 个桌面视口 = 26 条唯一 row；冻结六个医学监察任务、八域编码、深链接 identity、截图/console/network、性能和 teardown 依赖；
- 任一字节变化都使本合同接受失效，必须重新计算 SHA 并由同一独立 reviewer 复核。

本 worker 已读取并核对：

- R5 v0.3 stage contract；
- S5 subject workspace contract/runtime acceptance；
- S6 navigation/density/accessibility contract/runtime acceptance；
- 当前 App.jsx、旧 route state、旧 API client、旧 backend router；
- server principal、route context、read action contract、identity authorization、runtime readiness；
- S5/S6 accepted POC 的 authority adapter、projection、navigation 和 accessibility seam；
- protected inventory 的 accepted verifier 算法。

当前读取观察：

- 用 accepted S6 verifier 的 protected-boundary 函数重新计算当前 workspace，得到 542 和 feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca，与 accepted baseline 一致；
- 直接整套运行 S6 contract-era verifier 会报告十个 S6 future runtime path 已存在；这些路径与 ACCEPT_R5_S6_RUNTIME_V0_1 一致，不能把该旧“契约期 absent”检查当作 S7 产品失败；
- 当前产品源码仍是旧医学监查入口，不能被描述为已满足 R5-S7；
- 当前 workbench 不提供可用 Git repository status，后续证据必须依赖 exact path/raw SHA、运行时 trace 和 rendered/browser 事实，不能声称有 Git diff。

本文件没有修改产品源码、S5/S6 accepted POC、medical-writing 文件、数据库或运行时；没有启动任何服务。
