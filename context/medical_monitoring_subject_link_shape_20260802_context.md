# Task Context: medical_monitoring_subject_link_shape_20260802

Created: 2026-08-02 18:08:29
Objective: 阻止 Subject Profile AE 与实验室关联字段的数字或标量 ID 被静默当作真实关联
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

这是医学监查项目总 Goal 下的窄范围离线代码审查：在不越过 B6/C14 authority、运行时和真实项目门的前提下，阻止个例 AE—实验室关系字段的形状异常被消费层误读为真实关联。任务由 Codex 直接完成，没有 delegated agent 或 provider dispatch。

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` V1.1；`docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`；`docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`。
- 当前源：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs` 及同名 Node 测试；4.18 Subject lineage guard 与 P10 release audit/coverage。
- 当前阻断证据：B6 `pending_review`、C14 `blocked_pending_b6_review`、8911/5174 停止；本轮结果不得升级为临床关联正确性、运行时或商业发布证据。

## Scope

- In scope: Subject Profile `referenceRiskCards` 的 AE singular `event_id` 与 plural AE/实验室关联 ID 形状判定、最小消费提示、Node regression、任务/发布证据记录。
- Out of scope: `App.jsx`/`styles.css`、API/backend/SQLite、source registry/token、B6 reviewer outcome、aggregate/CAS、provider/runtime/browser、真实项目、医学写作和临床结论。

## Success Criteria

1. numeric/object/scalar relationship fields cannot trigger automatic AE—lab association.
2. Valid string event IDs and array relationships preserve existing linked-lab behavior.
3. Shape anomalies are visible in the AE card with a return-to-source warning and no inference of no risk.
4. Subject model, all Node tests, focused frontend contracts, Vite, release-gate/hash replay and review-gate have reproducible evidence.

## Risk Boundaries

- 只允许修改 Subject model、同名测试和 task/release evidence records；不得修改产品 shell、后端、运行库或权威 gate JSON。
- 不生成或代填 B6 outcome，不启动 8911/5174、服务、provider、API、SQLite、browser、adapter 或真实项目。
- Codex 保留最终验证与接受权；本轮没有 delegated agent。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 18:08:29: Task initialized by `tools/hermes_workflow_guard.py init-task --task-type finite_code_task`; no route was dispatched。
- 2026-08-02: Pre-change hashes: Subject model `e4620c5cf3f29588cef30b5a6d75e3976cd5a9757c29e767129a2e58166e157a`; Subject test `8d1d3cd5c1680be5f304695eb59452b9b48af84408bab7f4bbe062bdfd7f7e0f`; SubjectViews `8e8f6930447fe2d92da6aad9c0a3462f63c4cf30cbea60b6977f7c821939d80e`。
- 2026-08-02: Added `explicitReferenceToken`/`explicitReferenceIdList`; malformed relationship IDs no longer participate in auto AE—lab matching, and the AE card surfaces the anomaly. Added numeric AE/lab-link regression; valid string link behavior remains。
- 2026-08-02: Node **22/22**, focused frontend contracts **64 passed**, Vite **1925 modules** succeeded. Release audit LOOP 4.19 was appended and current coverage evidence was rebound read-only; status remains blocked with no authority grant。
- 2026-08-02: Final source hashes: Subject model `321e99531b857a64782677e7b1c0f0c6f6e8a08edf76ddc68dd6be15471dce54`; Subject test `c9a7e7cbd83b8d5f1a5df3920acd6734c1bac557c7766a09b8b2c737232bb286`; SubjectViews/protected App/styles unchanged. Final release hashes: audit `9814bba5f973e0d98dc7e0b315a52324cef988563fd3ff914021667406242cd8`, coverage `e2804caefba10376f8f84dcbd457f868b05be98e18c19c7365158cedd38f85f4`, decision `319249ab0fc045d918e537f25365775de55d429da4087c223412d20b6fc18431`。
