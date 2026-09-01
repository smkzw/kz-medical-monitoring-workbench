# 医学监查工作台离线边界审计检查点 — 2026-08-03

## 当前目标与硬边界

持续把医学监查工作台推进到可审计、可回归、可商业化验收的状态；本检查点
只覆盖离线源代码/合成测试边界。B6/C14 未放行时，不创建 reviewer outcome，
不启动 8911/5174、服务、provider、浏览器登录、CAS/source-token 写入或真实项目。

## 本阶段完成（P10 LOOP 4.88–5.20）

- 4.88：协议准备 evidence-context 的 `primary_match`/
  `eligible_for_rule_fact` 只接受 Boolean，阻断 truthy 字符串/数字进入规则事实证据。
- 4.89：AI 作业 SQLite `retryable` 只接受 Boolean/0/1，异常持久化值 fail-closed。
- 4.90：项目适配器风险处置完成状态只接受字面量 `True`。
- 4.91：日常运行 AI runtime `available` 只接受字面量 `True`，异常状态在创建运行前阻断。
- 4.92：风险快照 `resolution_complete` 写入只接受 Python `bool`，SQLite 读取/冲突比较只接受 Boolean/0/1，总览批次投影只把字面量 `True` 展示为 complete。
- 4.93：医学监查总览、受试者深链目录和显式运行门只把注册器 `has()` 的字面量 `True` 视为已注册。
- 4.94：风险证据快照 `available` 使用 `StrictBool`；字符串、数字和 `None`
  不再被 Pydantic 静默转换为证据可用。
- 4.95：监查风险详情路径显式接收 API-backed `monitoringSubjectCatalog`，不再
  通过 `buildSubjectView` 的 `demoSubjects` 默认值补充真实项目受试者元数据；
  demo/legacy helper defaults 保持不变。

## 验证证据

- 协议准备：44 通过；相邻协议/AI/规则集合 524 通过；全量监查 1813 通过。
- AI 仓储：42 通过；全部 `test_monitoring_ai_*.py` 645 通过；完整监查日志记录
  1818 通过、25 warnings、515.18s。外层 zsh 仅在 pytest 完成后错误赋值只读变量，
  pytest 摘要已由 `/tmp/medical_monitoring_full_489_recheck_20260803.log` 独立断言。
- 项目适配器：模块合同 23 通过；相邻适配器/风险集合 38 通过。
- 日常 AI readiness：聚焦 2 通过；日常运行/AI/仓储/路由 65 通过；record-rule/
  release-chain 51 通过。
- 风险快照 resolution：聚焦 22 通过；相邻集合 129 通过；完整监查日志更新为
  1819 通过、25 warnings、527.93s。
- 注册可用性：聚焦 malformed-registry 10 通过；模块/风险/MY009 相邻 61 通过；
  完整监查日志更新为 1819 通过、25 warnings、502.53s。
- 四个 active-slice review-gate 均为 `ok: true`；4.93 的 workbench-path review-gate
  已在补齐 `Boundary` 记录段后重新核验为 `ok: true`（无 warnings/errors）；Ruff
  与 Python compile 均通过。
- 4.94 聚焦/相邻 70 通过；共享高信号集合 508 通过、1 个与本切片无关的本地
  oMLX 翻译可用性断言失败；长监查套件本次尝试在约 75% 收到 SIGTERM，未计为
  4.94 全量通过。
- 4.95 前端监查合同 23 通过；医学监查 Node 测试 22 个 suite 全部通过；Vite
  production build 通过（仅已有大 chunk advisory）；Python contract Ruff 通过。
- 4.95 追加 MG-K10-SAR、Ruxolitinib-AD、MY009 目录/适配器合同 35 通过、19 个
  既有 warning；使用 in-process TestClient/适配器检查，未启动服务。
- 4.95 追加 Timeline/统一风险/安全性投影跨面合同 65 通过。
- 4.96：受试者目录响应在写入前核对 canonical active project；错项目响应
  fail-closed，MY009 alias→canonical 语义保持。
- 4.97：受试者 profile 下钻响应在缓存前同时核对 canonical project 与
  requested subject；错项目/错个例 payload fail-closed。
- 4.98：风险快照、风险 taxonomy、focused-risk 与 raw-intake 四类只读响应
  在写入状态前核对 canonical project；错项目或缺失身份 fail-closed，MY009
  alias→canonical 语义保持。
- 4.99：App source-manifest 只读响应在写入 active manifest map 前核对
  canonical `activeProjectIdRef.current`；错项目或缺失身份 fail-closed，路由
  alias 绑定保持不变。
- 5.00：App dashboard、`refreshDashboard`、普通 workbench inbox 与监查 inbox
  只读响应在写入 state 前核对 canonical project；错项目或缺失身份
  fail-closed，route alias 语义保持。
- 5.01：PlannedModulePage 的 evidence manifest、TFL manifest/review 与 safety
  review-workbench 响应在写入 state 前核对 current canonical project；保留
  source registry 无 project identity 的 residual，不扩展其合同。
- 5.02：`/sources` API 返回 canonical top-level `project_id`，来源台账读取在
  写入 registry state 前核对 current canonical project；source-entry 与
  validation 语义未改变。
- 5.03：App AI-run 列表只有在数组且每个 run 的 `project_id` 匹配 current
  canonical project 时才写入 state；不执行 provider 或 AI 作业。
- 5.04：监查 intake POST 响应在写入 `intakeResult`、生成风险选择或刷新
  dashboard 前核对 `expectedMonitoringProjectId`；错项目响应 fail-closed，
  未执行 intake。
- 5.05：来源内容核验确认响应在写入 `confirmedRecord` 或重试规则前核对
  `expectedMonitoringProjectId`；错项目响应 fail-closed，未执行确认。
- 5.06：MonitoringPage 的风险快照、风险分类、风险定位与原始监查四类
  只读响应在发现缺失/错项目身份时清空受影响状态并展示明确的中文身份错误；
  合法响应路径保持不变，未执行运行时或确认/摄入操作。
- 5.07：RiskEvidenceDock 的批次历史、来源证据批量预览与单个原文片段
  响应在写入历史/预览/片段 state 前核对 canonical `project_id`；错项目或
  缺失身份会清空受影响证据视图并展示可见错误，MY009 alias→canonical
  请求路径保持不变。
- 5.08：MonitoringPage 的 mark-read 与医学处置 action 响应在触发
  inbox/snapshot 刷新或展示成功消息前核对 canonical `project_id`；错项目
  或缺失身份会显示明确失败原因且不刷新当前状态。
- 5.09：受试者目录与受试者画像响应的既有项目/个例身份 fail-closed 分支
  现在在 MonitoringPage 展示明确中文告警；错配仍清空受影响状态，项目重置
  会清除告警，未改变请求或数据写入语义。
- 5.10：PlannedModulePage 的 TFL 审阅与安全信号/PV 审阅成功响应在写入审阅
  状态、选择状态或成功提示前核对当前 canonical `project_id`；错配 fail-closed，
  既有 409 来源准入与选择竞态逻辑保持。
- 5.11：总览收件箱已读、原始资料候选登记与 AI-run 建立成功响应在刷新当前
  state 或展示成功提示前核对项目身份；总览动作失败可见且停留在当前页。
- 5.12：Safety/PV 风险投影分页 helper 对 module summary、首屏和所有后续页
  逐一核对 `project_id`；以 active canonical project 为期望身份，同时保留
  alias 请求路径，错配不返回合并风险索引。
- 5.13：共享 `ModuleSourceAdmissionBand` 来源确认成功响应在显示已确认、清理
  目标和调用刷新前核对当前项目身份；错配 fail-closed，既有逐项确认和冲突
  处理保持。
- 5.14：PlannedModulePage 的来源登记、竞品证据清单、TFL 清单/审阅工作台、
  安全资料清单/审阅工作台及 PV 协同交接只读响应在错项目或缺失身份时清空
  受影响 stale state 并展示明确中文错误；request-id 竞态与合法响应路径保持。
- 5.15：运行共享根 App 的完整前端 Node 回归（医学监查、医学写作、writing-reference）、
  完整 `tests/test_monitoring_*.py` 回归与 Vite production build；前端 28 个
  test files/subtests 全部通过，Python **1819 passed、25 warnings**，Vite 1926 modules
  构建通过，仅保留既有大 chunk advisory；未发现共享消费者或监查后端回归。
- 5.18：Assurance 前端新增严格 `monitoring_principal` 规范化合同与可见身份门；要求
  `server_verified=true`、固定 schema、authenticated、租户/角色/项目范围、时间窗口和
  SHA-256 引用，错误/过期/缺失 principal fail-closed。完整冻结身份和 authority 仍是必要条件，
  但不再被当作认证身份；面板会在 principal 到期时自动重评估，当前无 principal 的运行态仍不显示创建能力。
- 5.19：新增 route-free `MonitoringRuntimeRouteContext`，在未来 API 路由进入授权前绑定
  server-verified principal、tenant、canonical project、action 与 target scope；错租户、越权项目、
  过期 principal、空 request id、非法 scope 和任意 client actor 均 fail-closed。上下文停在
  `authorize_monitoring_action` 之前，不接 FastAPI、不写 audit/CAS/source revision/运行库。
- 5.20：新增纯内存 `MonitoringAuthorizedRouteContext`，把 5.19 的 server-derived principal
  转换为既有 ACL snapshot，计算 authorization decision，并生成 hash-bound、non-mutating
  `MonitoringAuditEvent`。它校验 principal/request/project/action/scope/decision/audit 的一致性；
  即使 ACL `write_permitted=true`，也强制 `execution_write_permitted=false`、
  `mutation_applied=false`、aggregate 版本不变、`persisted=false`，敏感 payload/decision
  drift fail-closed。

## 5.20 验证

- 授权/审计接缝聚焦 **40 passed**；完整 `tests/test_monitoring_*.py` 更新为
  **1842 passed、25 warnings、498.95s**；compileall、Ruff 与 workflow review-gate 通过。
- 无 FastAPI/provider/service/browser/API login、runtime DB、B6/C14 action、aggregate/CAS
  replay、source-token revalidation 或真实项目运行；8911/5174 无监听。

## 当前真实状态

- B6：`pending_review`，5 个 candidate、5 个仅为工程预审 defer 的 outcome、0 个
  accepted review、`write_permitted=false`；3 个 monitoring candidate 仍缺
  `legacy_source_revision_token` revalidation，另有 1 个 candidate 仍需
  append-only disposition chain aggregate replay。该 JSON 不是正式 reviewer approval。
- C14：`blocked_pending_b6_review`；activation/event/projection/write/migration 全为 false。
- 8911/5174：无监听；未触碰无关 8900 上现有进程。
- 当前产品仍未完成 provider、Playwright、科学性、真实项目、商业化/UAT 验收；本检查点
  不作这些完成性声明。

## 下一安全顺序（B6 正式 reviewer outcome 出现后）

1. 仅核验正式 B6 reviewer outcomes 与身份/证据/残余阻断。
2. 通过 aggregate/CAS replay 与 source-token revalidation。
3. 重新生成并核验 approved-input；仍保持 diagnostic/read-only 直到明确放行。
4. 在受控窗口按不同 prompt/项目运行 Playwright 真实登录、科学性复核与回归 LOOP；
   每轮由 Codex 复核，连续两轮 P0–P4 清零后再讨论商业化门禁。

## 记录索引

- P10 ledger：`records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- 需求追踪：`records/active_slices/medical_monitoring_goal_p10_20260730/REQUIREMENTS_TRACEABILITY.md`
- 4.88 slice：`records/active_slices/medical_monitoring_protocol_evidence_bool_20260803/`
- 4.89 slice：`records/active_slices/medical_monitoring_ai_retryable_bool_20260803/`
- 4.90 slice：`records/active_slices/medical_monitoring_adapter_resolution_bool_20260803/`
- 4.91 slice：`records/active_slices/medical_monitoring_daily_ai_runtime_bool_20260803/`
- 4.92 slice：`records/active_slices/medical_monitoring_risk_resolution_bool_20260803/`
- 4.93 slice：`records/active_slices/medical_monitoring_registry_availability_bool_20260803/`
- 4.94 slice：`records/active_slices/medical_monitoring_evidence_available_strict_bool_20260803/`
- 4.95 slice：`records/active_slices/medical_monitoring_frontend_subject_fixture_isolation_20260803/`
- 4.96 slice：`records/active_slices/medical_monitoring_frontend_subject_catalog_project_guard_20260803/`
- 4.97 slice：`records/active_slices/medical_monitoring_frontend_subject_profile_identity_guard_20260803/`
- 4.98 slice：`records/active_slices/medical_monitoring_frontend_read_response_project_guards_20260803/`
- 4.99 slice：`records/active_slices/medical_monitoring_app_source_manifest_identity_guard_20260803/`
- 5.00 slice：`records/active_slices/medical_monitoring_app_dashboard_inbox_identity_guards_20260803/`
- 5.01 slice：`records/active_slices/medical_monitoring_planned_module_review_response_guards_20260803/`
- 5.02 slice：`records/active_slices/medical_monitoring_source_registry_project_identity_contract_20260803/`
- 5.03 slice：`records/active_slices/medical_monitoring_app_ai_runs_identity_guard_20260803/`
- 5.04 slice：`records/active_slices/medical_monitoring_intake_post_response_identity_guard_20260803/`
- 5.05 slice：`records/active_slices/medical_monitoring_content_confirmation_response_identity_guard_20260803/`
- 5.06 slice：`records/active_slices/medical_monitoring_identity_mismatch_visible_fail_closed_ux_20260803/`
- 5.07 slice：`records/active_slices/medical_monitoring_risk_evidence_response_identity_guards_20260803/`
- 5.08 slice：`records/active_slices/medical_monitoring_action_response_identity_guards_20260803/`
- 5.09 slice：`records/active_slices/medical_monitoring_subject_identity_mismatch_visible_ux_20260803/`
- 5.10 slice：`records/active_slices/medical_monitoring_planned_action_identity_guards_20260803/`
- 5.11 slice：`records/active_slices/medical_monitoring_project_action_success_identity_20260803/`
- 5.12 slice：`records/active_slices/medical_monitoring_safety_projection_page_identity_20260803/`
- 5.13 slice：`records/active_slices/medical_monitoring_source_admission_confirm_identity_20260803/`
- 5.14 slice：`records/active_slices/medical_monitoring_planned_read_identity_visible_ux_20260803/`
- 5.15 slice：`records/active_slices/medical_monitoring_frontend_shared_consumer_regression_20260803/`
- 5.16 slice：`records/active_slices/medical_monitoring_identity_boundary_audit_20260803/`
- 5.17 slice：`records/active_slices/medical_monitoring_runtime_principal_contract_20260803/`
- 5.18 slice：`records/active_slices/medical_monitoring_frontend_principal_gate_20260803/`
- 5.19 slice：`records/active_slices/medical_monitoring_runtime_route_context_20260803/`
- 5.20 slice：`records/active_slices/medical_monitoring_authorized_route_audit_context_20260803/`

## 本次离线边界复核

- 2026-08-03 当前切片：5.18 前端 principal gate 聚焦 15、完整共享 Node 29、监查前端静态 pytest 28、Vite 1927 modules build 通过；5.19 route context 聚焦 31；5.20 authorized route/audit handoff 聚焦 40、完整监查 Python **1842 passed/25 warnings/498.95s**、compileall/Ruff/review-gate 通过。仍仅为离线合同证据；更宽的 browser QC 在前一切片进入前因 `Missing button: 医学监查` 失败，未计为本阶段验收证据。
- 最近 5.02–5.15 以及当前 5.18 切片的 workbench review-gate 与 CxH mirror review-gate 均返回 `ok: true`、无 warnings/errors；当前切片 workflow route 仅记录、未 dispatch。
- 5.19 的 workbench 与 CxH mirror review-gate 也返回 `ok: true`、无 warnings/errors；route workflow 仅记录、未 dispatch。
- 5.20 的 workbench review-gate 返回 `ok: true`、无 warnings/errors；workflow route 仅记录、未 dispatch。CxH mirror 仅保存同步 context/review/metrics，不代表独立运行态。
- 复核未发现 8911/5174 listener；B6/C14 状态保持不变。以上均为离线证据，不是 browser/scientific/UAT/commercial acceptance。

## LOOP 5.16 — Phase G identity boundary audit

- 离线静态审查确认：`monitoring_identity_authorization.py` 尚未接入
  `main.py` 或医学监查/assurance 路由；它仍是有测试的 offline authorization/audit
  contract，不是运行时认证或 RBAC middleware。
- 四组 API 仍有 19 个 `default="medical_manager"` actor/confirmed-by 字段；前端
  有 33 个精确 actor literals（App 32、Assurance panel 1）。这是 P1 商业发布残余，
  不是 B6 正式结论，也没有因此执行任何写入。
- Assurance UI 的完整冻结身份 + 显式 `assurance_write_permitted=true` fail-closed
  保持不变；正式 Phase G 顺序为 runtime principal adapter、API server-derived actor、
  authorization/audit wiring、frontend session bootstrap、负向 API 与 Playwright 角色证据。
- 本切片无源码/测试/运行库变更；无服务、provider、浏览器/API 登录、aggregate/CAS
  replay、source-token revalidation 或真实项目运行。B6=`pending_review`、
  C14=`blocked_pending_b6_review`，8911/5174 继续停止。

## LOOP 5.17 — server-verified monitoring principal envelope

- 新增 `services/api/app/monitoring_runtime_principal.py` 与对应 focused tests，固定
  上游已验证 principal 的输入合同：`server_verified=true`、验证引用 hash、时间窗口、
  authenticated session、directory revision、非 wildcard project scope 和显式 roles。
- `public_dict` 不暴露原始 session；`require_server_derived_actor` 只返回 principal id，
  对任何非空 client actor fail-closed。该模块不解析 token/cookie/header，不接 FastAPI，
  不授权路由，不持久化 audit。
- focused 7、identity/audit 24、最新完整监查 1826 passed/25 warnings、473.99s；compileall
  与 python ruff 通过。当前 B6/C14 与 8911/5174 边界不变。
- 下一安全动作仍为：B6 正式 reviewer outcome → aggregate/CAS replay → source-token
  revalidation → approved-input；之后才把实际认证提供方映射到 envelope，再做单路由
  API principal dependency、负向测试和浏览器双角色证据。

## LOOP 5.18 — frontend server-principal visible gate

- Assurance 面板新增 `medicalMonitoringPrincipal.mjs` 规范化合同：只接受
  `monitoring_runtime_principal_v1`、`server_verified=true`、非 wildcard project scope、
  唯一已知 roles、authenticated、租户、目录修订、时间窗口与 SHA-256 session/verification
  引用；错项目、缺字段、重复/未知角色和异常 digest 均 fail-closed。
- `MedicalMonitoringAssurancePanel` 新增“认证身份”卡和明确中文阻断文案；创建门现在是
  `complete frozen identity + assurance_write_permitted + current project-scoped principal`。
  到期计时器会在页面长开时重算；当前 snapshot/sourceManifest/rawMonitoring 均未提供 principal，
  因而创建分支仍不可达，未伪造登录或授权。
- principal focused 15、完整共享前端 Node 29、监查前端静态 pytest 28、Vite 1927 modules
  build 和 Ruff 均通过。无 service/provider/browser/API login、runtime write、B6/C14 action、
  aggregate/CAS、source-token 或真实项目运行；B6=`pending_review`、C14=`blocked_pending_b6_review`，
  8911/5174 继续停止。
- 这是 Phase G 的可见 UX/shape contract，不是 runtime authentication、RBAC、audit、Playwright、
  scientific/UAT 或 commercial acceptance。下一安全动作仍是 B6 正式链完成后，接真实认证提供方、
  单路由 server-derived actor 和负向 API，再进入浏览器角色证据。

## LOOP 5.19 — server-principal route context seam

- 新增 `services/api/app/monitoring_runtime_route_context.py` 与 focused tests，要求 live
  `MonitoringAuthenticatedPrincipal`、canonical tenant/project、request id、action 和 target scope；
  principal 失效、tenant mismatch、project scope denial、空请求 id、非法 scope 与 client actor
  均在 route context 构建前 fail-closed。
- `MonitoringRuntimeRouteContext.public_dict()` 只输出 principal identity hash 与安全 request
  摘要，不含 raw session；context 明确不生成 authorization decision、不做 e-sign/reauth、
  source revision/CAS/audit append 或 mutation。
- route/identity/authorization/audit 聚焦 **31 passed**；完整 `tests/test_monitoring_*.py`
  **1833 passed、25 existing warnings、485.87s**；compileall/Ruff 通过。B6=`pending_review`、
  C14=`blocked_pending_b6_review`、8911/5174 无监听，未运行服务/provider/browser/API login 或真实项目。
- 这是单路由接线前的 Phase G offline seam，不是 runtime authentication、RBAC、UAT 或 commercial
  acceptance。下一安全动作仍是 B6 正式链完成后再映射实际 provider、注入单一路由并补负向 API。

## LOOP 5.20 — authorized route decision and audit handoff

- 新增 `MonitoringAuthorizedRouteContext`，把 5.19 的 live server principal 转换为既有 ACL
  snapshot，计算 authorization decision，并生成 hash-bound、non-mutating audit event；校验
  principal/request/project/action/scope/decision/audit 一致性。
- 即使 ACL `write_permitted=true`，handoff 也明确 `execution_write_permitted=false`、
  `mutation_applied=false`、aggregate version unchanged、`persisted=false`；敏感 payload、
  client actor、source/audit/target 缺失和 decision drift fail-closed。
- 这仍不接实际 provider、FastAPI、audit persistence、CAS/source revision 或 route mutation，
  不越过 B6/C14，也不构成 Playwright/scientific/UAT/commercial evidence。

## 2026-08-03 continuation re-anchor — current formal boundary

- Re-opened the current B6 gate, C14 activation gate, formal provenance package,
  candidate matrix, release audit and the fresh B6 packet revalidation. B6 is
  still `pending_review` with five engineering-defer outcomes, zero accepted
  formal review IDs, and unresolved aggregate-chain/source-token blockers.
- The new refresh packet revalidation is `fresh` with zero issues and complete
  source-manifest replay, but it remains a read-only reviewer handoff:
  `medical_approval_granted=false`, `write_authority=false`,
  `migration_authority=false`, `activation_allowed=false`.
- The current listener check found 8911 and 5174 stopped. Protected frontend
  hashes were captured again (`App.jsx`:
  `ae83f5e95af67e6fc3b1523792f7507f89c6be0e4eedb30ace561b53fce3b0fa`;
  `styles.css`:
  `35f2e0119a0175d58d81775ca8140aa057a4ab6b01a8007ae9e2ec62764d3a43`).
- A bounded current-record scan found no current monitoring Kimi attribution;
  historical Kimi files belong to the medical-writing lane and were not touched.
- No new product-source change was justified: the next real step requires five
  formal reviewer outcomes and cannot be safely replaced with another offline
  micro-contract. The full project goal remains active and this checkpoint is
  not a commercial or browser acceptance claim.
- **Next safe action:** submit
  `records/active_slices/medical_monitoring_b6_packet_freshness_20260803/B6_REVIEW_PACKET_REFRESH.json`
  to an authorized formal reviewer. After outcomes appear, re-open all hashes;
  then perform aggregate/CAS replay and legacy source-token revalidation,
  approved-input dry-run, controlled runtime identity wiring and only then the
  three-project Playwright/scientific/UAT LOOP.

## 2026-08-03 rendered UI audit continuation

- A Codex-led in-app browser audit used safe Vite preview port 4173 only. The
  actual dashboard was checked at 1280×720, including the settled empty state
  and new-project validation dialog. 8911/5174 remained stopped.
- The previous frontend state conflated a failed `/api/projects` request with
  “暂无项目”. A minimal `frontend/src/App.jsx` correction now separates
  `projectsLoadError`, shows `项目服务暂不可用/项目列表读取失败`, provides a
  GET-only `重新读取`, and disables new-project creation while loading or
  unavailable. Medical-monitoring navigation remains disabled without an active
  project. `styles.css` was preserved unchanged.
- Evidence and a detailed audit report are under
  `evidence/medical_monitoring_ui_audit_20260803/`. Vite build passed; browser
  DOM/screenshot recheck passed; console error/warn collection was empty.
  App hash is now
  `d746bdfee64bc6641bfc3ae5f01602335f90d6db1856a3f3549ebb4119e124b7`;
  the prior hash in the earlier checkpoint is historical, not the current
  source. This does not alter B6/C14, runtime identity, or backend authority.
- **Next safe action remains:** formal B6 reviewer outcome → hash re-open →
  aggregate/CAS and source-token revalidation → approved-input → controlled
  runtime identity → real-project Playwright/scientific/UAT loop.
