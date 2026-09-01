# Task Context: medical_monitoring_contract_migration_20260806

Created: 2026-08-06 01:56:26
Objective: 将现有前端静态哨兵断言迁移到 feature-owned MedicalMonitoringSubjectViews/Models，保持风险 dock、CM/IP lane、Subject Timeline/Profile 和源证据合同等价；在迁移验证通过后再评估共享 App legacy/demo 清理，严格不启动真实 LOOP
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` (active route surface and current static sentinels)
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx` (feature-owned Subject Timeline/Profile, timeline graph and metric renderer)
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs` (feature-owned lane/category models)
- `tests/test_frontend_monitoring_contract.py`, `tests/test_frontend_timeline_contract.py`, `tests/test_frontend_unified_risk_workbench_contract.py` (accepted static contracts that rejected direct legacy deletion)
- `records/active_slices/medical_monitoring_frontend_legacy_cleanup_20260806/` (rollback evidence and negative decision)
- `records/active_slices/medical_monitoring_frontend_ownership_contract_20260806/APP_DRIFT_RECONCILIATION.md` (current App drift and static-sentinel boundary)
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (`read_only`/`blocked`)

## Scope

- In scope: migrate only static contract parsing boundaries that currently depend on unmounted App legacy definitions to feature-owned Subject Views/Models or explicit stable App anchors; preserve every material assertion about active route ownership, CM/IP separation, source evidence, risk focus, sparse empty-state semantics, and feature-owned rendering.
- In scope: update the three named Python contract files only where their source locator must follow the accepted feature-owned implementation; add no test bypasses, broad regex weakening, or deletion-only assertions without an equivalent positive contract.
- In scope: after contracts are migrated, rerun the full named Python suite and complete medical-monitoring Node suite; only if green, reassess a separate App cleanup patch in a later bounded slice.
- Out of scope: real-loop/B6/C14 activation, services/listeners, provider/API/browser/Playwright/real-project login, medical-writing source, runtime data, styles redesign, broad test refactor, or direct App legacy deletion in this slice.

## Success Criteria

- Contract tests no longer rely on deleted/unmounted App legacy function bodies as parsing delimiters, but retain equivalent positive checks against feature-owned implementations.
- Existing 169-test baseline remains green or any changed count is explained by a strict one-to-one contract relocation; no assertion is removed without a replacement.
- Medical-monitoring Node suite remains 36/36; active feature module files and App hashes remain unchanged in this contract-only slice.
- A later cleanup slice can be evaluated from a stable contract result; this slice itself does not claim that deletion is safe until those results are demonstrated.

## Risk Boundaries

- Only the named workbench test files may be edited, and only via minimal context-preserving patches. Do not modify App or feature source in this slice.
- Do not weaken tests by replacing exact semantics with existence-only checks, broad regexes, or unconditional skips. Preserve CM/IP, risk-focus and source-evidence coverage.
- Do not infer runtime/E2E or medical correctness from static contract migration; report those surfaces as unverified while the gate is blocked.
- Keep 8911/5174/8910/4173 stopped and do not invoke provider/browser/API/real projects.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 01:56:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Direct legacy cleanup was rejected in the preceding slice because accepted contracts use the old definitions as static sentinels. This task is limited to relocating those assertions to feature-owned source before any future cleanup.
- 2026-08-06: Updated only the three named Python contract files: RiskDetail parsing now ends at the stable `timelineLaneDefs` anchor; legacy CM/IP lane assertions now target `medicalMonitoringSubjectModels.mjs`; sparse empty-state/risk-focus assertions target `MedicalMonitoringSubjectViews.jsx`; active route tests now assert the legacy local page definitions are absent.
- 2026-08-06: Removed the confirmed-unmounted App legacy/demo Subject/Profile block, local renderer helpers, and `demoSubjects` import using a recoverable/context-bound patch. Retained App's active `timelineLaneDefs`, `laneForEvent`, and event-category label helper used by `buildSubjectView`/risk dock; feature-owned Subject Views/Models remain the active render path.
- 2026-08-06: Named Python contracts passed 169/169; medical-monitoring Node suite passed 36/36; Vite production build passed (1,956 modules). Full pytest collection remains blocked by the pre-existing unrelated ImportError for `_REQUIRED_CORE_BODY_SEMANTIC_IDS` in `tests/test_medical_writing_dynamic_section_matrix.py`.
- 2026-08-06: Protected styles/main/runtime/medical-writing hashes stayed unchanged. App post-change SHA is `57905f6bcac75ec8e7793fc339651223dfef365c8227b34dbe465d8f98fbc77b`; all four service ports remain stopped and the real-loop gate remains read-only/blocked.
