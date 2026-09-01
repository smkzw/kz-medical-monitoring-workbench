# Task Context: medical_monitoring_subject_lineage_shape_20260802

Created: 2026-08-02 17:53:39
Objective: 严格阻止 Subject Timeline/Profile 将非字符串 source revision 或 batch token 静默当作真实来源绑定
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

本轮是医学监查项目总 Goal 下的窄范围离线代码审查：在不越过 B6/C14 authority、运行时和真实项目门的前提下，补齐 Subject Timeline/Profile 来源谱系 token 的形状安全。

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` V1.1 §§22、23、25、38、40。
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` §§2.4–2.5、3、4、5。
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` P5/P6/P10 与每轮 LOOP 记录合同。
- 当前源：`frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs` 及同名 Node 测试；`MedicalMonitoringSubjectViews.jsx` 仅作消费边界核对。
- 当前阻断证据：B6 `pending_review`、C14 `blocked_pending_b6_review`、8911/5174 停止；不得把本轮离线结果升级为运行时或商业发布证据。

## Scope

- In scope: 对 Subject/Profile 的 `source_revision/source_version/subject_source_revision` 与批次字段做严格 token 形状判定；合法字符串继续可读，非字符串 fail-closed 进入 `partial`/形状异常；补充单元回归、记录和证据重绑。
- Out of scope: B6 reviewer outcome、aggregate/CAS、source-token 权威迁移、API/SQLite/provider/runtime、8911/5174、真实项目、浏览器科学性/UAT、`App.jsx`/`styles.css`、医学写作和其他共享运行时。

## Success Criteria

1. 非字符串来源修订或批次 token 不再通过 `String(...)` 被视为可靠绑定。
2. 合法字符串/legacy/占位符、批次-only、缺失、混合 locator 现有语义保持不变。
3. 新回归明确暴露 `malformedLineageFields`、`来源绑定形状异常` 和“不能据此证明来源真实性/完整性/趋势可比”边界。
4. Subject model、全部医学监查 Node suite、四份前端合同、Vite build、release-gate/hash replay 和 review-gate 均有可复核证据。

## Risk Boundaries

- 只允许修改指定 Subject model、同名测试、任务记录/证据记录和当前 release evidence 绑定；不修改权威运行库或生产服务。
- 不生成或代填 B6 医学/工程 reviewer outcome；不执行 migration、CAS 写入、adapter、API POST、真实 onboarding。
- Codex 自行完成最终代码、测试、哈希、停止状态和 release-gate 判定；本轮没有 delegated agent。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:53:39: Task initialized by `tools/hermes_workflow_guard.py init-task`; initial `--task-type code` was rejected by guard and produced no file change, then `finite_code_task` initialized successfully.
- 2026-08-02: Read the three authoritative product documents in full, current P10 ledger/release audit and B6/C14 evidence.
- 2026-08-02: Pre-change hashes recorded: Subject model `018864b3235c55dadbfe68a7840c64e9e4fe3648dbc3e1b949c028ac2f608960`; test `6cb8ad08361b9cd089da5539ee9b60b96b789270ffe10d92f29159470c41765d`; SubjectViews `8e8f6930447fe2d92da6aad9c0a3462f63c4cf30cbea60b6977f7c821939d80e`.
- 2026-08-02: Implemented strict lineage-token states and one numeric revision + valid batch regression. No protected source/runtime file changed.
- 2026-08-02: Node model and all 22 medical-monitoring Node files passed; four frontend contracts passed 64; Vite build passed 1925 modules with existing chunk warning.
- 2026-08-02: Root `npm run build` first failed because the product root has no `package.json`; rerun from `frontend/` passed and made no source changes.
- 2026-08-02: Release audit appended LOOP 4.18; coverage rebind is read-only evidence maintenance, with decision status still blocked and no authority granted.
- 2026-08-02: Final hashes after the bounded change: Subject model `e4620c5cf3f29588cef30b5a6d75e3976cd5a9757c29e767129a2e58166e157a`; Subject test `8d1d3cd5c1680be5f304695eb59452b9b48af84408bab7f4bbe062bdfd7f7e0f`; SubjectViews `8e8f6930447fe2d92da6aad9c0a3462f63c4cf30cbea60b6977f7c821939d80e`; protected `App.jsx`/`styles.css` unchanged.
- 2026-08-02: Final checks: Node **22/22**, focused frontend contracts **64 passed**, Vite **1925 modules**, release-gate **7 passed**, coverage replay passed, both task review-gates `ok=true`, 8911/5174 no listeners.
