# Task Context: medical_monitoring_daily_diff_ux_safety_reasons_20260805

Created: 2026-08-05 09:22:07
Objective: 在不启动前端运行时的前提下，将日常增量差异快照中的结构/域/删除/全量证明阻断转换为清晰可操作的监查员提示，并补离线视图回归
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/AGENTS.md` — desktop-first medical-monitoring UI and source-bound
  acceptance contract.
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyDiffSummary.jsx`
  and `medicalMonitoringDailyDiffView.mjs` — current diff consumer and pure
  normalization contract.
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyDiffView.test.mjs`
  — deterministic offline view tests.
- `services/api/app/monitoring_daily_run_service.py` — source of the new
  fail-closed drift semantics consumed by this UI.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  — no provider/runtime/browser activation in this slice.

## Scope

- In scope: derive concise Chinese safety reasons from already validated diff
  counts/proof and show them in the daily diff summary; preserve existing
  partial/malformed fail-safe behavior; add pure-function regression evidence.
- Out of scope: server/runtime/browser activation, new APIs, subject data,
  medical conclusions, frontend architecture changes, and medical-writing
  surfaces.

## Success Criteria

- A monitor can tell at a glance why a run must be reviewed before rules/AI:
  structure drift, missing expected domains, blocked removal resolution or
  missing/unconfirmed full-snapshot proof.
- Valid snapshots keep the current compact metric layout and do not show a
  false warning; malformed/partial payloads remain fail-safe.
- Pure view tests and frontend build pass; no dev/preview server is started
  while the authority gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:22:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
