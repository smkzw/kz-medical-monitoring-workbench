# 医学监查身份边界离线审查上下文

Date: 2026-08-03 CST  
Task: `medical_monitoring_identity_boundary_audit_20260803`  
Mode: direct Codex, offline static audit only

## Objective

核对 Phase G 身份/RBAC 合同是否已经接入医学监查真实 API 与前端写入路径，区分
兼容性默认 actor、UI 展示值、只读查询参数和可伪造写入身份。该审查不改变产品
源码、测试、运行库、服务或真实项目。

## Source of truth

- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/monitoring_audit_contract.py`
- `services/api/app/monitoring_assurance_router.py`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_protocol_preparation_router.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md`
- 当前 B6/C14 gate JSON 与 `context/medical_monitoring_offline_boundary_checkpoint_20260803.md`

## Scope and boundary

本切片只做源码检索、字段计数、依赖关系核对和风险记录。不得：

- 给 B6 创建或推断正式 reviewer outcome；
- replay aggregate/CAS、revalidate source token 或写 approved input；
- 启动 8911/5174、服务、Playwright、provider、API 登录或真实项目；
- 把离线 `monitoring_identity_authorization.py` 合同误报为运行时认证/RBAC。

## Initial observations

1. `monitoring_identity_authorization.py` 只被自身的 audit contract 与测试导入；
   `main.py`、医学监查路由和 assurance 路由没有导入或依赖真实 principal。
2. `monitoring_assurance_router.py` 的 5 个写入身份字段、
   `medical_monitoring_router.py` 的 9 个写入身份字段、
   `monitoring_ai_router.py` 的 4 个字段和
   `monitoring_protocol_preparation_router.py` 的 1 个字段仍有
   `default="medical_manager"`。这些是客户端可提供/省略的 body 字段，不是服务端
   session-derived identity。
3. `frontend/src/App.jsx` 有 32 个精确 `actor: "medical_manager"` 发送点；
   `MedicalMonitoringAssurancePanel.jsx` 的任务创建 payload 另有 1 个。它们需要
   在真实身份接线后改为 correlation/idempotency 之外不伪造 actor。
4. Assurance 面板当前已正确要求完整冻结身份和显式
   `assurance_write_permitted === true` 才显示创建入口；这是 UI fail-closed，
   不能替代 API 端 principal、project scope、role 和签名校验。
5. 当前 B6=`pending_review`、C14=`blocked_pending_b6_review`、write/migration
   均为 false；该身份审查不能以此为理由跨过 B6。

## Acceptance criteria

- 记录可复核的文件、字段和计数证据；
- 明确哪些是直接观察、哪些是对商业发布风险的推断；
- 给出不改变当前运行边界的 Phase G 实施顺序；
- 更新 P10 ledger、需求追踪和离线 checkpoint，不声称运行时/商业完成。

## Next safe action

待 B6 正式 reviewer outcomes、aggregate/CAS replay、legacy source-token revalidation
和 approved-input 通过后，先在隔离测试中落地 runtime principal adapter 与 API dependency，
再逐路移除 client-supplied actor，补齐负向测试和 Playwright 身份证据；在此之前只可
继续做不写运行库的契约审查。
