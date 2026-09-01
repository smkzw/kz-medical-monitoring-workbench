# Task Context: medical_monitoring_removal_resolution_guard_20260805

Created: 2026-08-05 09:06:06
Objective: 在不启动运行时的前提下，阻断日常监查对身份不确定或删除完整性不足的增量批次继续进入规则阶段，并补充源代码与回归证据
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_service.py` — P7 orchestration and transition gate.
- `services/api/app/monitoring_batch_diff.py` — row identity, schema and removal-resolution diff contract.
- `tests/test_monitoring_daily_run_service.py` and `tests/test_monitoring_batch_diff.py` — focused regression evidence.
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` — P7 deletion/structure-drift acceptance intent.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` — runtime/provider/browser authority boundary; remains read-only/blocked.

## Scope

- In scope: make the daily-run service fail closed before deterministic rules when an incremental diff contains unresolved row-removal identity, missing snapshot domains, or schema drift; expose deterministic reason codes in the persisted transition payload; add focused unit coverage and update the P9/P7 evidence ledger.
- Out of scope: runtime/provider/browser/Playwright activation, real project ingestion, B6/C14 writes or replay, medical approval, frontend changes, database migrations, and changes to the parallel medical-writing subsystem.

## Success Criteria

- A frozen incremental run with `removal_blocked_keys` transitions to `drift_review_required` and never to `rules_running`.
- Existing schema/domain drift behavior remains unchanged and the transition payload identifies all deterministic reasons without exposing subject data.
- Focused tests, the all-real-loop source suite, compile checks and workflow review-gate pass; reserved ports remain empty.
- The result is explicitly classified as source-only evidence and does not alter the authoritative runtime gate.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:06:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
