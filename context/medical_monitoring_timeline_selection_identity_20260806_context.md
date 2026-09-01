# Task Context: medical_monitoring_timeline_selection_identity_20260806

Created: 2026-08-06 06:03:23
Objective: 为 Subject Timeline 的 SVG 与明细行建立显式优先、来源定位降级、可去重的稳定展示选择键，避免 event_id 缺失或重复导致交互覆盖
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The Timeline raw-fact inspector (P1 slice) now supports SVG/detail-row selection, but both paths used `event.event_id` directly for state, React keys and lane lookup. A source payload with a missing or duplicate `event_id` could make two events share a key or make a selected event impossible to recover, especially across structurally different listings.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P1-01 and P1-06 (Timeline usability, sparse/malformed data fail-closed behavior).
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs` `referenceTimelineLanes` and `medicalMonitoringSubjectModels.test.mjs`.
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx/.css` Timeline SVG/detail-row selection and inspector.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked).

## Scope

- In scope: derive a display-only `selectionKey` per lane event from explicit `event_id`, then explicit source record/locator, then a lane/index fallback; deterministically suffix duplicates; use that key consistently in SVG/detail selection, React keys and inspector lookup; add model/static regression tests.
- Out of scope: changing or inventing clinical IDs, risk IDs, source identity, backend/API/schema/database, source registry, provider/service/browser/Playwright/API login, real projects, runtime/SQLite/CAS/B6/C14/source-token/P8/Safety-PV, shared App/styles/main or medical-writing.

## Success Criteria

- Events with missing `event_id` remain selectable when an explicit source record/locator exists; otherwise a deterministic display-only fallback prevents React collisions.
- Duplicate bases are suffixed only for this display collection; the original event object and medical/risk IDs remain untouched.
- SVG blocks, detail rows and inspector use the same key; malformed source fields remain visible as unknowns and no risk identity is synthesized.
- Focused/full Node, Python static and Vite checks pass; 8911/5174/8910/4173 remain stopped.

## Risk Boundaries

- Only feature-owned Timeline model/view/tests/static contract may change; preserve App/styles/main and medical-writing hashes.
- Selection keys are UI-only and must never be sent to APIs, used as risk IDs, or displayed as source truth.
- No backend/runtime/provider/browser/real-project/SQLite/CAS/B6/C14/source-token/P8/Safety-PV/medical-writing or mutation/approval action; keep the real-loop gate and ports stopped.
- Direct Codex is final authority; no delegated agent or external model is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:03:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 06:04:xx: Source audit confirmed direct `event_id` usage in SVG/detail selection and React keys; selected a display-only stable-key correction.
