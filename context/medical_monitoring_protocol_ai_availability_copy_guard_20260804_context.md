# Task Context: medical_monitoring_protocol_ai_availability_copy_guard_20260804

Created: 2026-08-04 15:52:42
Objective: 使方案监查准备面板在独立AI不可运行时不把queued/running状态误报为AI正在分析，并完成离线回归和证据记录
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`: topic
  status copy and project-scoped panel props.
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`: existing normalized
  monitoring AI status passed to adjacent preparation panels.
- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`: queued/running
  topic-state contract.
- `services/api/app/monitoring_ai_service.py`: independent-AI runtime failures are fail-closed and
  become blocked job outcomes; queued/running is not proof of a candidate.
- Current gates: B6 `pending_review`, C14 `blocked_pending_b6_review`, real LOOP `blocked`; reserved
  ports 8911/5174/8910/4173 must stay stopped.

## Scope

- In scope: pass the existing normalized AI status into the protocol-preparation panel and make the
  queued/running explanatory copy status-aware; add static/unit assertions and durable evidence.
- Out of scope: protocol API/server behavior, provider configuration, job submission, database or
  runtime activation, real projects, medical conclusions, Playwright, visual acceptance, B6/C14 or
  commercial-release authority.

## Success Criteria

- Ready status retains the existing “独立AI正在分析” explanation.
- Unready status explicitly says the queue/running state is not proof that a semantic candidate was
  generated and that the AI gate must be available.
- Project isolation and all medical-monitoring Node suites plus the frontend build remain green.
- Hermes review-gate is `ok=true` with no warnings/errors; reserved ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 15:52:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 15:53:00: Audited protocol-preparation status and confirmed that the frontend's queued/running copy was unconditional while the backend can fail jobs closed on unavailable AI. Selected a prop-only copy correction; no start gate or API behavior change.
- 2026-08-04 16:00:00: Implemented the ready/unready topic copy branch, passed focused checks, all 31 medical-monitoring Node suites, the 30-test frontend contract, Vite build and Hermes review-gate (`ok=true`). B6/C14 and real-loop boundaries remain unchanged.
