# Task Context: medical_monitoring_source_only_project_ui_20260804

Created: 2026-08-04 16:31:46
Objective: Ensure source-manifest-only medical-monitoring projects cannot be presented as activated or executable in the medical manager workbench; preserve existing project isolation and offline-only boundaries.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Frontend shell and monitoring surface: `frontend/src/App.jsx`.
- Canonical project contract: `services/api/app/project_source_manifest.py` and
  `records/active_slices/medical_monitoring_my008_3_02_manifest_20260804/`.
- The target state is a manifest binding with `implementation_status=source_manifest_only`.
- Current runtime authority remains read-only and the B6/C14/real-loop gates remain closed.

## Scope

- In scope: make the workbench distinguish source-manifest-only monitoring projects from activated
  monitoring projects; suppress misleading monitoring actions and child-side reads; add focused
  frontend contract tests and evidence.
- Out of scope: backend route/adapter changes, source parsing, runtime/provider/browser/Playwright
  work, database writes, real project intake, medical-writing changes, and any listener startup.

## Success Criteria

- A `source_manifest_only` monitoring binding cannot render upload/assurance/risk-action controls or
  trigger child monitoring reads; it shows a concise read-only readiness boundary and a safe return
  path to project overview.
- Normal `real_source_slice` monitoring behavior remains unchanged and project identity guards remain
  covered.
- Focused frontend tests and the existing monitoring contract/build checks pass without touching
  medical-writing source or runtime authority.

## Risk Boundaries

- The guard is a UX/read contract only; it does not grant or revoke backend authority.
- Do not introduce fallback data, demo subjects, fabricated readiness, or hidden provider calls.
- Do not edit medical-writing source; preserve unrelated concurrent changes.
- No service/API/browser/provider/real project/8911/5174/8910/4173 execution.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 16:31:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 16:32–16:37: Added `medicalMonitoringSourceReadiness` as the single frontend contract for
  active, source-only, and unconfirmed monitoring bindings. Source-only/unconfirmed projects now
  suppress parent inbox/subject/profile reads, child risk/raw-intake reads, upload/assurance/risk
  action controls, and show a concise read-only readiness boundary. The overview module matrix marks
  source-only modules `未启用` and disables their action row. Existing demo/legacy statuses remain
  active to preserve prior behavior.
- 2026-08-04 16:38: Focused helper and static UI QC passed (`25` and `10` assertions), all 32
  medical-monitoring Node suites passed, frontend monitoring Python contract **30 passed**, and Vite
  build passed with `1952` modules; only the existing >500 kB chunk advisory remains.
- 2026-08-04 16:39: No backend/API/runtime/provider/browser/Playwright or medical-writing source was
  touched; no listener was started. This slice remains an offline UX/read contract and does not alter
  B6/C14 or real-loop authority.
- 2026-08-04 16:40: Review-gate returned `ok=true` with no warnings/errors. Final read-only recheck:
  B6 `pending_review` (`accepted_review_ids=[]`, `migration_ready=false`, `write_permitted=false`),
  C14 `blocked_pending_b6_review` (activation/event/projection/migration/write all false), real-loop
  audit `blocked` with read-only authority, and 8911/5174/8910/4173 all stopped.
