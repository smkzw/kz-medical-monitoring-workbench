# Task Context: medical_monitoring_ai_candidate_provenance_disclosure_20260806

Created: 2026-08-06 04:28:30
Objective: Expose source-bound identity details for daily independent-AI candidates without mutation or runtime activation
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Authoritative requirements: `docs/medical_monitoring_manual/医学监查子系统说明书.md`, `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`, and P10 records under `records/active_slices/medical_monitoring_goal_p10_20260730/`.
- Candidate contract: `services/api/app/monitoring_daily_run_router.py`, `services/api/app/monitoring_daily_run_ai_service.py`, `frontend/src/features/medical-monitoring/MedicalMonitoringDailyAiCandidates.jsx`, `medicalMonitoringDailyAiCandidates.mjs`, and focused tests.
- Current gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains read-only/blocked; no provider/runtime/browser/real-project action is permitted.

## Scope

- In scope: default-collapsed, read-only provenance disclosure for daily independent-AI candidate rows; display candidate input revision, prompt version, generation time, source entry/locator and source-content hash identity; fail-closed wording for partial payloads; focused contract tests and production build.
- Out of scope: provider calls, services/ports, Playwright/API login, real project onboarding, candidate accept/reject/submit/retry actions, backend/database/CAS/B6/C14 changes, evidence-authority choice, Safety/PV permissions, App.jsx/shared medical-writing paths, raw source values or quote expansion.

## Success Criteria

- Source identity is available without increasing first-screen density; disclosure is collapsed by default.
- Missing or malformed identity remains `待核对`/partial and cannot be read as a verified candidate; no mutation control is added.
- Hashes/locators are identity aids only, never medical conclusions or raw-value evidence.
- Existing focused and full medical-monitoring tests, syntax checks, and Vite build pass; ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 04:28:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 04:29:00: Re-anchored the prior AI contract audit and daily-run payload. The row currently exposes source entry/locator but hides input revision, prompt version and source hash; the next bounded patch targets only this read surface.
