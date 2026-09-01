# Task Context: medical_monitoring_project_completion_audit_20260804

Created: 2026-08-04 19:54:54
Objective: 建立医学监查子系统从当前状态到商业化完成的 P0-P10 完成度总账，逐项绑定 PRD/说明书/计划/发布门证据与下一安全动作，不把离线合同冒充真实验收
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` (V1.1) — product target and medical boundaries.
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` — current truth table, P0/P1/P2 gaps and release recommendation.
- `docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md` — P0–P10 workstreams and exit gates.
- `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md` — current evidence audit and hard blockers.
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json` — current 16-gate status and blocked decision.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` — B6/C14/runtime authority boundary.
- `records/active_slices/medical_monitoring_real_loop_mode_coverage_20260803/MODE_COVERAGE.json` — current three-mode evidence state (empty/blocked).
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` — durable implementation history through LOOP 5.127.

## Scope

- In scope: a compact project-level completion matrix that maps the 16 release gates and P0–P10 stages to direct evidence, status, gap and next safe action; current blocker and release interpretation.
- Out of scope: source reparse, runtime/provider/browser/Playwright, B6/C14 migration or replay, database/API writes, real-project tests, product code changes and medical-writing files.

## Success Criteria

- Every required release gate appears exactly once with the current persisted status.
- Every P0–P10 stage is classified as verified/partial/unproven/blocked without upgrading offline contracts to real acceptance.
- The matrix names the next safe sequence and explicitly preserves candidate/canonical project identity and authority boundaries.
- The record is suitable as the next-goal/resume index and does not claim commercial release.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is an audit artifact, not a release decision and not a medical signoff.
- Do not copy secrets, credentials, subject IDs or absolute source paths into the artifact.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 19:54:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
