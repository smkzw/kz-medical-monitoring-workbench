# Task Context: medical_monitoring_risk_identity_transition_20260806

Created: 2026-08-06 00:48:54
Objective: 补齐医学监查 risk_key 与 risk_instance_id 的跨批次 continuation/reopen/supersede 可追溯只读投影，不继承旧处置且保持真实运行门禁关闭
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P0-04: separate stable `risk_key` from batch/source-bound `risk_instance_id`, and define continuation, reopen and supersede.
- `docs/medical_monitoring_manual/医学监查子系统说明书.md` §6.2.1 and §10.5: unchanged facts continue with prior context; changed facts create a new instance linked by supersedes; closed risks that trigger again reopen without silently restoring closure.
- `services/api/app/medical_risk_repository.py` current batch classification and `risk_history` source; `services/api/app/main.py` history projection; `frontend/src/App.jsx` history dock.
- `packages/contracts/workbench_contracts/models.py` `RiskCase` identity and `batch_delta` contract; existing repository/bridge/reconciliation tests.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`: authoritative runtime gate remains `read_only / blocked` with all activation/provider/write booleans false.

## Scope

- In scope: add a pure, deterministic transition projection for risk history and expose it in the read-only history payload/UI so continuation, reopen and supersede are explicit without inheriting old dispositions; add focused regressions and durable evidence.
- Out of scope: runtime database migration, append-only disposition replay, B6/C14, source-token/CAS revalidation, provider/model calls, service/browser/Playwright/API login, real-project runs, medical facts, risk decisions, medical-writing source/components, and production activation.

## Success Criteria

- `risk_history` output distinguishes `new`, `continuation`, `reopen`, and `supersede` using stable identity plus current batch delta, and exposes predecessor instance only as read-only lineage.
- Existing history boundary remains explicit: prior dispositions are context only; no old disposition is automatically applied to the current instance.
- Frontend history dock displays transition semantics and predecessor/current instance relationship without changing action state.
- Focused backend/frontend/static tests and relevant Node suite/build pass; medical-writing protection remains unchanged; review-gate passes; runtime gate/listeners remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 00:48:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 00:49–00:54: Audited P0-04 sources and found that the repository already
  classified batch deltas but the history projection did not expose an explicit
  continuation/reopen/supersede relation. The batch classifier also treated only
  `RESOLVED` as a reopening predecessor; a closed risk could be mislabeled as
  persisting.
- 2026-08-06 00:54–00:58: Added the pure read-only
  `medical_risk_identity_transition.py` contract. It maps baseline to new,
  persisting to continuation, reopened to reopen, and changed/rereview/engine
  replacement to supersede. Reopen/supersede expose the predecessor instance and
  `history_only` disposition lineage; reused instance ids fail closed. The history
  API now includes the transition projection and the desktop history dock displays
  the instance relationship. The repository now treats `CLOSED` as a reopening
  predecessor. No RiskCase schema, disposition store, runtime database or old
  disposition was changed.
- 2026-08-06 00:58: Focused identity/repository/reconciliation/mapping tests passed
  **45**, including the new closed-risk regression; adjacent rule-bridge, daily-run
  and medical-monitoring API/static contracts passed **198**; Python compilation
  passed for the touched backend modules. The frontend Node suite remained **35/35
  files / 0 failures** and the Vite build passed with **1,957 modules transformed**;
  the existing >500 kB advisory remains.
- 2026-08-06 00:59: The medical-writing protection sample remained **197 passed / 2
  existing translation-batch contract failures** in the untouched translation-batch
  component (`setSelectedAnchors([...payload.anchor_filter])` and related scope
  preview assertions). No medical-writing source/component was edited.
- 2026-08-06 01:00: Current real-loop gate remains `read_only / blocked`, all
  authority booleans false, and ports 8911/5174/8910/4173 are empty. No service,
  browser, provider, API login, real project, runtime write, B6/C14 action,
  source-token/CAS replay or release activation occurred.
