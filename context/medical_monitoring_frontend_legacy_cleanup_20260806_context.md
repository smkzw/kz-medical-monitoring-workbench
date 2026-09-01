# Task Context: medical_monitoring_frontend_legacy_cleanup_20260806

Created: 2026-08-06 01:42:37
Objective: 在已记录现场快照和共享所有权清单下，移出 frontend/src/App.jsx 中已确认无活动调用点的 legacy/demo Subject Timeline/Profile 代码；保持现行 feature-owned 监查路由、医学写作和运行时门禁不变
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/App.jsx` (shared shell under review)
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/` (active feature-owned routes and data helpers)
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/records/active_slices/medical_monitoring_frontend_ownership_contract_20260806/` (prior ownership contract, static mount evidence, and pre-cleanup App/styles snapshots)
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (current real-loop gate; read-only/blocked)
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/reviews/codex_medical_monitoring_frontend_ownership_contract_20260806_review.md` and its metrics file (prior source-level acceptance evidence)
- Current pre-edit App SHA-256: `5edf834e7df93083910bdc5367cd8664c9551e3699d3ee4c701c41530e75f0e1` (801,394 bytes)
- Current pre-edit styles SHA-256: `dbd1a99c31cb4877c7f9b13dc8dee7804a39d20a3c0ee805eb4b4a70a76bcefd` (429,030 bytes)
- Pre-edit rollback snapshot: `records/active_slices/medical_monitoring_frontend_legacy_cleanup_20260806/snapshots/pre_edit/`

## Scope

- In scope: remove only confirmed-unreferenced legacy/demo `SubjectProfile`, `SubjectTimelinePageLegacy`, `PatientProfilePageLegacy`, unreferenced local timeline/profile rendering helpers, and their demo fixture fallback references from the shared `App.jsx` shell; preserve active feature imports and active route mounts.
- In scope: remove only local helper definitions proven by repository-wide token search to have no live call sites, while retaining shared helpers still used by active App code (`timelineLaneDefs`, `laneForEvent`, and the local timeline event-category label chain used by the active risk dock).
- In scope: source-level dependency audit, targeted static/Node regression, production build if it remains non-invasive, protected-file hash recheck, and durable review/checkpoint records.
- Out of scope: `medical_monitoring_real_loop_gate_audit_20260804` B6/C14 review or activation; any service/provider/API/browser/Playwright/real-project login; any write to medical-writing feature files; any redesign, new feature, data-source change, route migration, or deletion of active feature-owned components; any change to `styles.css`.

## Success Criteria

- The shared shell no longer contains the confirmed-unreferenced legacy/demo Subject Timeline/Profile definitions or their unreferenced local renderer helpers.
- Active `MedicalMonitoringSubjectTimelinePage` and `MedicalMonitoringPatientProfilePage` imports and route mounts remain present, use the project-bound `monitoringSubjectCatalog`, and do not resolve to the deleted local definitions.
- The active App risk-dock path still has its local event-category helper chain and `laneForEvent` dependency intact.
- Targeted frontend contract tests and the complete `frontend/src/features/medical-monitoring/*.test.mjs` suite pass after the edit; if a build is run, it passes.
- App changes are bounded to the declared dead-code deletion; styles/main/runtime/medical-writing protected hashes remain unchanged; all listeners remain stopped and the real-loop gate remains `read_only`/`blocked`.

## Risk Boundaries

- This is a source-only, local, reversible patch in the workbench checkout. The pre-edit App/styles snapshot is retained for rollback/audit.
- Do not touch active feature-owned monitoring files, the medical-writing surface, styles, project source folders, runtime data, ports, services, providers, or real-project data.
- Do not infer runtime/E2E or medical correctness from source tests; report those surfaces as unverified while the real-loop gate is blocked.
- Do not remove any symbol that has an active call site outside the dead legacy/demo block; if dependency evidence is ambiguous, keep it and record the residual.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 01:42:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Repository-wide source audit confirmed the target legacy/demo definitions have no live route mounts, but the existing frontend contract suite intentionally requires those definitions as static audit sentinels and validates their CM/IP lane separation. A deletion attempt caused 10 contract failures; no tests were edited.
- 2026-08-06: `frontend/src/App.jsx` was restored from the pre-edit snapshot; current SHA-256 is again `5edf834e7df93083910bdc5367cd8664c9551e3699d3ee4c701c41530e75f0e1`. No product source change is accepted in this slice.
- 2026-08-06: Medical-monitoring Node suite remained green at 36/36 during the attempted edit; Python contracts must be rerun after exact rollback before closing this slice.
